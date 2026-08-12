"""Guard: workflow tokens stay least-privilege and the release stays tokenless (ENG-3428).

Three things this repo relied on, none of which anything checked:

* `main.yaml` and `pre-commit.yaml` declared no `permissions:` at all, so they
  inherited the repository default `GITHUB_TOKEN` -- write-all here -- while
  running `pytest`, `pip install`, and third-party pre-commit hooks;
* there was no release pipeline: 0.2.47 was `twine upload`-ed from a laptop, so
  the file on PyPI has no attestation tying it to a commit;
* the contexts that *should* gate `main` were written down nowhere, which is
  part of why `required_status_checks.contexts` is still empty.

The workflows added by ENG-3428 fix all three, but each fix is one deleted line
away from being undone, and none of them fails visibly when removed: a
workflow that quietly regains a write-all token still goes green, and a
required-checks doc that no longer matches the matrix still renders. So this
file asserts them statically.

Credential-free and YAML-only on purpose: it runs in the `unit-coverage` job and
in pre-commit on every branch push, so drift is caught when the YAML is edited
rather than at the next release. This is the same idiom as
tests/unit/test_ci_matrix_coverage.py and tests/unit/test_packaging_config.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
MAIN_WORKFLOW = WORKFLOW_DIR / "main.yaml"
RELEASE_WORKFLOW = WORKFLOW_DIR / "release.yaml"
REQUIRED_CHECKS_DOC = REPO_ROOT / "docs" / "ci" / "required-checks.md"

#: The complete set of write-capable grants allowed anywhere under
#: .github/workflows/, keyed by (workflow file, scope). Anything else -- a new
#: workflow, a widened scope, an `id-token` that drifts onto another job -- is a
#: test failure, so the allowlist doubles as the written justification.
ALLOWED_WRITE = {
    # docs.yaml pushes a branch and opens a PR via peter-evans/create-pull-request.
    ("docs.yaml", "contents"): "docs.yaml opens the regenerated-API-docs PR",
    ("docs.yaml", "pull-requests"): "docs.yaml opens the regenerated-API-docs PR",
    # release.yaml's `publish` job exchanges the OIDC token for a short-lived
    # PyPI upload token (Trusted Publishing). Job-scoped; see the tests below,
    # which additionally assert it never lands on a job that runs repo code.
    ("release.yaml", "id-token"): "release.yaml publish job: PyPI Trusted Publishing",
}

#: Inputs to `pypa/gh-action-pypi-publish` that would mean a stored credential
#: rather than OIDC. Their absence is the whole point of Trusted Publishing.
TOKEN_INPUTS = ("password", "user")

#: Permission values that grant nothing writable. `read-all` is the only
#: bare-string form of `permissions:` that is not a write grant.
READ_ONLY_VALUES = {"read", "none", "read-all"}


def _workflow_files() -> list[Path]:
    return sorted(p for p in WORKFLOW_DIR.glob("*.y*ml"))


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _triggers(workflow: dict) -> dict:
    """The `on:` block.

    YAML 1.1 resolves the bare key `on` to the boolean `True`, so
    `workflow["on"]` is a KeyError and `workflow.get("on", {})` silently returns
    an empty dict -- which would make every trigger assertion pass vacuously.
    """
    return workflow.get("on", workflow.get(True)) or {}


def _permission_grants(path: Path) -> dict:
    """Map (scope -> every value that scope is granted) for the `permissions:` blocks in *path*.

    Top-level and per-job blocks are collected together: for the allowlist below
    the question is only "can anything in this file write?", and a grant is
    equally dangerous wherever it is declared. `permissions: write-all` (a bare
    string rather than a mapping) is normalised to a single sentinel scope so it
    cannot slip past a mapping-shaped check.

    The *union* of values per scope, not the last one seen: a dict merge lets a
    later block mask an earlier one, so a workflow with `contents: write` at the
    top and `contents: read` on its only job would read back as read-only --
    while every job added afterwards silently inherits the write token. Keeping
    both values means the write still has to be justified in ALLOWED_WRITE.
    """
    workflow = _load(path)
    blocks = [workflow.get("permissions")]
    blocks.extend(job.get("permissions") for job in (workflow.get("jobs") or {}).values())

    grants: dict[str, set] = {}
    for block in blocks:
        if block is None:
            continue
        if isinstance(block, str):
            # `permissions: write-all` / `read-all`.
            grants.setdefault("<all-scopes>", set()).add(block)
            continue
        for scope, value in block.items():
            grants.setdefault(scope, set()).add(str(value))
    return grants


def _holds_oidc(block_owner: dict) -> bool:
    """Does this workflow's or job's `permissions:` block carry `id-token`?

    `permissions: write-all` grants every available scope, `id-token` included,
    so the bare-string form counts -- and has to be handled explicitly, because
    on a string `"id-token" in block` is a substring test that answers False.
    """
    block = block_owner.get("permissions")
    if isinstance(block, str):
        return block != "read-all"
    return "id-token" in (block or {})


def test_the_scan_finds_the_workflows_it_is_meant_to_check():
    """Without this, a moved workflow directory makes every test below vacuous."""
    names = {p.name for p in _workflow_files()}
    assert {"docs.yaml", "main.yaml", "pre-commit.yaml", "release.yaml"} <= names, (
        f"expected workflows are missing from {WORKFLOW_DIR}; found {sorted(names)}"
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_every_workflow_declares_top_level_permissions(path: Path):
    """A workflow with no `permissions:` inherits the repository default token.

    Membership, not truthiness: `release.yaml` declares `permissions: {}`, the
    tightest possible block, and an `in` check is the only one that tells that
    apart from declaring nothing at all.
    """
    workflow = _load(path)
    assert "permissions" in workflow, (
        f"{path.name} declares no top-level `permissions:` block, so it runs with the repository "
        "default GITHUB_TOKEN (write-all) while executing repository code (ENG-3428). Add "
        "`permissions: contents: read`, or `permissions: {}` plus per-job grants."
    )


@pytest.mark.parametrize("path", _workflow_files(), ids=lambda p: p.name)
def test_no_workflow_grants_write_outside_the_allowlist(path: Path):
    """Every write-capable grant in the repo must be justified in ALLOWED_WRITE.

    Parametrised over the directory rather than a fixed list so that a *new*
    workflow -- the easiest way to reintroduce a write-all token -- fails here
    on the day it is added.
    """
    offenders = {
        scope: sorted(values)
        for scope, values in _permission_grants(path).items()
        if values - READ_ONLY_VALUES
        if (path.name, scope) not in ALLOWED_WRITE
    }
    assert not offenders, (
        f"{path.name} grants write-capable permissions that are not justified in ALLOWED_WRITE "
        f"in {Path(__file__).name}: {offenders}. Narrow the scope, or add an entry saying why the "
        "workflow needs it."
    )


def test_a_job_level_narrowing_cannot_hide_a_workflow_level_write(tmp_path: Path):
    """The scanner is the only thing standing between this repo and a write-all token.

    Its one interesting failure mode is masking: `contents: write` at the top
    with `contents: read` on the job that happens to exist today reads back as
    read-only under a plain dict merge, and every job added later inherits the
    write. Checked here directly because no workflow in the tree is currently
    shaped that way -- so nothing else would notice if the union were lost.
    """
    workflow = tmp_path / "masked.yaml"
    workflow.write_text(
        "permissions:\n"
        "  contents: write\n"
        "jobs:\n"
        "  only-job:\n"
        "    permissions:\n"
        "      contents: read\n"
        "    steps: []\n"
    )

    grants = _permission_grants(workflow)
    assert grants["contents"] == {"write", "read"}
    assert grants["contents"] - READ_ONLY_VALUES, "the workflow-level write was masked by the job-level read"


def test_the_allowlist_does_not_outlive_the_grants_it_justifies():
    """A stale entry silently pre-approves a scope nobody needs any more."""
    actual = {(path.name, scope) for path in _workflow_files() for scope in _permission_grants(path)}
    stale = sorted(entry for entry in ALLOWED_WRITE if entry not in actual)
    assert not stale, (
        f"ALLOWED_WRITE entries no longer correspond to any declared permission: {stale}. "
        "Remove them so the allowlist keeps meaning what it says."
    )


def test_release_workflow_is_tag_triggered_only():
    """A branch push must not be able to publish.

    The artifact has to come from an immutable ref: the tag is the version's
    only identity, and a `push: branches:` trigger here would publish whatever
    was on a branch at the time.
    """
    triggers = _triggers(_load(RELEASE_WORKFLOW))

    assert set(triggers) == {"push"}, (
        f"release.yaml triggers on {sorted(map(str, triggers))}; it must trigger on tag push alone, "
        "so that what is published is always a tagged, immutable commit."
    )
    push = triggers["push"]
    assert "branches" not in push, (
        "release.yaml has a `branches:` trigger, so a branch push could publish to PyPI. "
        "PyPI filenames are immutable -- a wrong upload can only be yanked, never replaced."
    )
    assert push.get("tags") == ["v*"], f"expected release.yaml to trigger on tags ['v*'], got {push.get('tags')!r}"


def test_release_build_job_asserts_the_tag_matches_the_declared_version():
    """The version is hardcoded in pyproject.toml; nothing else links tag -> metadata.

    Asserted on the moves rather than the wording: the guard has to read the tag,
    read `[project].version`, and compare them as PEP 440 versions (so that
    `v0.2.48.rc1` and `0.2.48rc1` -- one PyPI filename -- are not treated as two
    different releases).
    """
    build = _load(RELEASE_WORKFLOW)["jobs"]["build"]
    script = "\n".join(step.get("run", "") or "" for step in build["steps"])
    env_refs = " ".join(str(step.get("env", "")) for step in build["steps"])

    assert "github.ref_name" in env_refs, "the release build job never reads the tag it is building"
    for move, what in (
        ("pyproject.toml", "read the declared [project].version"),
        ("Version(", "compare tag and version as PEP 440 versions, not strings"),
        ("sys.exit", "fail the job on a mismatch"),
    ):
        assert move in script, f"release.yaml's tag/version guard no longer seems to {what} ({move!r} is gone)"


def test_release_build_job_installs_and_imports_the_built_wheel():
    """"pip install succeeded" proves nothing.

    The ENG-3543 wheel shipped 3 of 169 modules, installed cleanly, and only
    failed at first import -- so the build job has to actually import the
    artifact, from outside the source tree.
    """
    build = _load(RELEASE_WORKFLOW)["jobs"]["build"]
    script = "\n".join(step.get("run", "") or "" for step in build["steps"])

    for move, what in (
        ("egg-info", "drop the stale egg-info that can mask broken package discovery"),
        ("-m build", "build the distribution"),
        ("-m venv", "install it into a clean venv"),
        ("site-packages", "assert the import came from the wheel and not the source tree"),
    ):
        assert move in script, f"release.yaml's pre-publish gate no longer seems to {what} ({move!r} is gone)"


def test_release_publishes_with_attestations_over_trusted_publishing():
    publish = _load(RELEASE_WORKFLOW)["jobs"]["publish"]
    steps = [step for step in publish["steps"] if str(step.get("uses", "")).startswith("pypa/gh-action-pypi-publish")]

    assert len(steps) == 1, f"expected exactly one pypa/gh-action-pypi-publish step, found {len(steps)}"
    inputs = steps[0].get("with") or {}

    # `attestations` defaults to true on current versions; declared explicitly so
    # that a default change upstream cannot silently drop provenance.
    assert inputs.get("attestations") is True, (
        "release.yaml must publish with `attestations: true`; without it the artifact reaches PyPI "
        "with no PEP 740 provenance binding it to this repo, workflow, and commit (ENG-3428)."
    )
    present = [name for name in TOKEN_INPUTS if name in inputs]
    assert not present, (
        f"release.yaml passes {present} to the publish action, which means a stored credential "
        "instead of Trusted Publishing. Remove it: OIDC is the point."
    )


def test_release_yaml_is_the_only_thing_that_uploads_to_pypi():
    """A second publish step elsewhere would defeat the pipeline invisibly.

    The checks above only look inside `release.yaml`'s `publish` job, and the
    text scan below only catches the two conventional secret *names* -- so a
    `pypa/gh-action-pypi-publish` step added to another workflow with
    `password: ${{ secrets.SOMETHING_ELSE }}` would slip past both while
    `release.yaml` still read as correct. Every publish step in the directory,
    wherever it lives, has to be tokenless.
    """
    found = {}
    for path in _workflow_files():
        for job_name, job in (_load(path).get("jobs") or {}).items():
            for step in job.get("steps") or []:
                if str(step.get("uses", "")).startswith("pypa/gh-action-pypi-publish"):
                    found[f"{path.name}:{job_name}"] = step.get("with") or {}

    assert set(found) == {"release.yaml:publish"}, (
        f"PyPI publish steps found in {sorted(found)}; the only one should be release.yaml's "
        "`publish` job, which is the job the trusted publisher is registered against."
    )
    with_tokens = {where: [n for n in TOKEN_INPUTS if n in inputs] for where, inputs in found.items()}
    offenders = {where: names for where, names in with_tokens.items() if names}
    assert not offenders, (
        f"publish steps carrying a stored credential instead of using OIDC: {offenders}."
    )


def test_no_workflow_carries_a_pypi_token_or_a_manual_twine_upload():
    """Belt and braces: the credential must not reappear anywhere in the directory.

    A token added to a *different* workflow, or a `twine upload` step bolted onto
    an existing one, would defeat the pipeline while `release.yaml` itself still
    looked correct.

    Matched against the re-serialised parse tree rather than the file text, so
    that the comments explaining the defect ("0.2.47 was `twine upload`-ed from
    a laptop") are not mistaken for the defect -- the parser drops comments, and
    every executable part of the workflow survives the round trip.
    """
    offenders = {}
    for path in _workflow_files():
        text = yaml.safe_dump(_load(path))
        hits = sorted({m.group(0) for m in re.finditer(r"twine\s+upload|PYPI_API_TOKEN|TEST_PYPI_API_TOKEN", text)})
        if hits:
            offenders[path.name] = hits
    assert not offenders, (
        f"stored-PyPI-credential or manual-upload markers found in .github/workflows/: {offenders}. "
        "Publishing goes through Trusted Publishing in release.yaml (ENG-3428)."
    )


def test_the_job_holding_the_oidc_token_runs_no_repository_code():
    """`id-token: write` must never share a job with checked-out repository code.

    That separation is the reason `build` and `publish` are two jobs: a
    compromised build dependency should never be in the same process as the
    credential that can upload to PyPI. A single merged job would still publish
    correctly, which is exactly why nothing else would notice.
    """
    workflow = _load(RELEASE_WORKFLOW)

    # `_scopes` and not a bare `in`: `permissions: write-all` is a *string*, so
    # `"id-token" not in block` would be a substring test that quietly says
    # "no id-token here" about a block that grants every scope there is.
    assert not _holds_oidc(workflow), (
        "release.yaml grants `id-token` at workflow level, so every job -- including the one that "
        "checks out and executes repository code -- holds the PyPI credential. Grant it per job."
    )

    for name, job in workflow["jobs"].items():
        if not _holds_oidc(job):
            continue
        uses = [str(step.get("uses", "")) for step in job["steps"]]
        assert not any(u.startswith("actions/checkout") for u in uses), (
            f"release.yaml's `{name}` job holds `id-token: write` and checks out the repository. "
            "The privileged job must only download the artifact and publish it."
        )
        assert not [step for step in job["steps"] if step.get("run")], (
            f"release.yaml's `{name}` job holds `id-token: write` and runs shell steps. Keep it to "
            "`download-artifact` plus the publish action, so no repository code sees the token."
        )


def _matrix_legs() -> list[str]:
    """The `setup-and-test` matrix leg names, from main.yaml.

    GitHub names a matrix job `<job> (<base matrix values>)`; keys contributed
    only by `include` (`path`, `timeout`) are not part of the name, so the
    contexts are `setup-and-test (agent)` and so on.
    """
    matrix = _load(MAIN_WORKFLOW)["jobs"]["setup-and-test"]["strategy"]["matrix"]
    return list(matrix["test-suite"])


def test_required_checks_doc_lists_exactly_the_matrix_legs():
    """The doc is the input to a settings change, so drift there is a real defect.

    Someone will paste these strings into branch protection. A leg renamed in
    the matrix but not here yields a required context that no check ever
    reports -- every PR stuck on "Expected — waiting for status to be reported",
    which is a merge deadlock rather than a merge gate. A leg *added* and not
    listed here is the quieter half: it simply never becomes required.

    This is the 04dea96e failure mode (matrix names drifting from reality
    without anything failing), applied to documentation.
    """
    assert REQUIRED_CHECKS_DOC.is_file(), f"{REQUIRED_CHECKS_DOC.relative_to(REPO_ROOT)} is missing"

    expected = {f"setup-and-test ({leg})" for leg in _matrix_legs()}
    assert len(expected) > 5, f"only {len(expected)} matrix legs found; the comparison would be near-vacuous"

    # Table rows only. The doc's prose also spells out context strings while
    # explaining GitHub's matrix naming ("not `setup-and-test (agent, ...)`"),
    # and those illustrations are the opposite of what should be pasted into
    # settings. The table is the list a human copies from, so the table is what
    # has to match.
    rows = [line for line in REQUIRED_CHECKS_DOC.read_text().splitlines() if line.lstrip().startswith("|")]
    documented = set(re.findall(r"`(setup-and-test \([^`)]+\))`", "\n".join(rows)))

    assert documented == expected, (
        "docs/ci/required-checks.md and main.yaml's matrix disagree. "
        f"In the matrix but not documented (these would never become required): {sorted(expected - documented)}; "
        f"documented but not in the matrix (these would block every PR forever): {sorted(documented - expected)}."
    )


def test_required_checks_doc_lists_the_non_matrix_contexts_too():
    """The three job-level contexts are the ones that are realistically requireable.

    They are also the credential-free ones, so leaving them out of the doc would
    lose the only tier that can be turned on without waiting for the functional
    suites to go green.
    """
    text = REQUIRED_CHECKS_DOC.read_text()
    for context in ("unit-coverage", "package-integrity", "pre-commit"):
        assert f"`{context}`" in text, (
            f"docs/ci/required-checks.md does not list the `{context}` context; it is one of the "
            "checks that should gate main (ENG-3428)."
        )
