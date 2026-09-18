"""Guard: the PR trigger, the nightly run, and the release's functional gate (ENG-3683).

Before this ticket `main.yaml` ran on `push` to `main`/`test` and nothing else,
so:

* the seven-leg functional matrix never ran on a pull request -- the earliest a
  functional regression could surface was a push to `test`, after review;
* `release.yaml` gated a PyPI upload on `pytest tests/unit` alone, so no
  live-backend suite stood between a tag and an immutable upload;
* several env vars the functional suites read were simply never set, which does
  not fail anything: `tests/functional/v2/test_trigger.py`'s event-trigger
  classes skipped every run in CI and the leg still reported green.

Every fix here is one deleted line from being undone, and none of them fails
visibly when removed -- a workflow that stops running on PRs is still a valid
workflow, and a leg that skips its tests is still green. So they are asserted
statically, in the same credential-free idiom as
`tests/unit/test_ci_permissions.py` and `tests/unit/test_ci_matrix_coverage.py`:
this file runs in `unit-coverage` and in pre-commit on every branch push, so
drift is caught when the YAML is edited.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
MAIN_WORKFLOW = WORKFLOW_DIR / "main.yaml"
RELEASE_WORKFLOW = WORKFLOW_DIR / "release.yaml"
PRE_COMMIT_WORKFLOW = WORKFLOW_DIR / "pre-commit.yaml"
V2_CONFTEST = REPO_ROOT / "tests" / "functional" / "v2" / "conftest.py"
REQUIRED_CHECKS_DOC = REPO_ROOT / "docs" / "ci" / "required-checks.md"

#: The job that decides whether the functional matrix runs for a given event.
SCOPE_JOB = "functional-scope"

#: The label that forces a functional run on a PR whose paths do not ask for one.
FUNCTIONAL_LABEL = "functional-tests"

#: Path prefixes whose change is taken as "this PR can break a functional suite".
FUNCTIONAL_PATHS = ("aixplain/", "tests/functional/")

#: The backend CI runs the functional suites against on every ref that is not
#: `main` or a `v*` tag. The v2 conftest has to agree with it -- see the test at
#: the bottom of this file.
TEST_BACKEND_URL = "https://test-platform-api.aixplain.com"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _triggers(workflow: dict) -> dict:
    """The `on:` block.

    YAML 1.1 resolves the bare key `on` to the boolean `True`, so `workflow["on"]`
    is a KeyError and `workflow.get("on", {})` returns an empty dict -- which
    would make every trigger assertion below pass vacuously.
    """
    return workflow.get("on", workflow.get(True)) or {}


def _job(path: Path, name: str) -> dict:
    jobs = _load(path)["jobs"]
    assert name in jobs, f"{path.name} has no `{name}` job; found {sorted(jobs)}"
    return jobs[name]


def _script(job: dict) -> str:
    return "\n".join(step.get("run", "") or "" for step in job["steps"])


def _functional_env_step() -> dict:
    """The `setup-and-test` step that writes the suite's env into $GITHUB_ENV."""
    steps = [step for step in _job(MAIN_WORKFLOW, "setup-and-test")["steps"] if "GITHUB_ENV" in (step.get("run") or "")]
    assert len(steps) == 1, f"expected exactly one step writing to $GITHUB_ENV, found {len(steps)}"
    return steps[0]


def _matrix() -> dict:
    return _job(MAIN_WORKFLOW, "setup-and-test")["strategy"]["matrix"]


# ---------------------------------------------------------------------------
# main.yaml: when the workflow runs at all
# ---------------------------------------------------------------------------


def test_main_workflow_runs_on_pull_requests():
    """The whole point: a functional regression has to be visible before merge.

    Without a `pull_request` trigger none of `main.yaml`'s contexts ever report
    on a PR, so requiring them on `main` would leave every PR stuck on
    "Expected -- waiting for status to be reported" (docs/ci/required-checks.md).
    """
    triggers = _triggers(_load(MAIN_WORKFLOW))
    assert "pull_request" in triggers, (
        "main.yaml no longer triggers on `pull_request`, so unit-coverage, "
        "package-integrity and the functional legs cannot gate a PR (ENG-3683)."
    )


def test_pull_request_trigger_reacts_to_the_functional_label():
    """Labelling a PR has to start a run by itself.

    `types` defaults to opened/synchronize/reopened. Without `labeled`, adding
    `functional-tests` does nothing until the next push -- so the documented
    "add the label to run the suites" would be false for the one case it exists
    for: a PR that is already pushed and needs the suites re-run.
    """
    types = _triggers(_load(MAIN_WORKFLOW))["pull_request"].get("types")
    assert types, "main.yaml's pull_request trigger declares no `types`"
    assert "labeled" in types, (
        f"`labeled` is missing from main.yaml's pull_request types ({types}), so adding the "
        f"'{FUNCTIONAL_LABEL}' label does not start a functional run (ENG-3683)."
    )


def test_main_workflow_has_a_nightly_schedule():
    """The functional legs are the only live-backend coverage there is.

    Gating them on PR paths means a backend-side change under an untouched SDK is
    invisible until someone happens to edit `aixplain/**`. The nightly is what
    closes that, so its absence is a real regression rather than a preference.
    """
    schedule = _triggers(_load(MAIN_WORKFLOW)).get("schedule")
    assert schedule, "main.yaml declares no `schedule:`; the nightly functional run is gone (ENG-3683)"
    crons = [entry.get("cron") for entry in schedule]
    assert all(crons), f"a schedule entry has no `cron` expression: {schedule}"
    for cron in crons:
        fields = cron.split()
        assert len(fields) == 5, f"cron {cron!r} does not have five fields"
        assert fields[2:] == ["*", "*", "*"], (
            f"cron {cron!r} does not run every day; the nightly is meant to be nightly"
        )


# ---------------------------------------------------------------------------
# main.yaml: which events pay for the functional matrix
# ---------------------------------------------------------------------------


def test_the_functional_matrix_is_gated_by_the_scope_job():
    """Gating lives in an `if:`, never in `on.pull_request.paths`.

    A path filter suppresses the *check*, so a required context simply never
    reports on a docs-only PR and the PR can never merge. A job skipped by `if:`
    still reports, and GitHub counts a skipped job as satisfying a required
    check -- which is what keeps these legs requireable.
    """
    triggers = _triggers(_load(MAIN_WORKFLOW))
    assert "paths" not in triggers["pull_request"] and "paths-ignore" not in triggers["pull_request"], (
        "main.yaml's pull_request trigger has a path filter. That suppresses the checks "
        "themselves, so any required context becomes an unsatisfiable 'Expected' on a "
        f"docs-only PR. Gate the matrix with `if:` on the `{SCOPE_JOB}` job instead (ENG-3683)."
    )

    job = _job(MAIN_WORKFLOW, "setup-and-test")
    needs = job.get("needs")
    needs = [needs] if isinstance(needs, str) else (needs or [])
    assert SCOPE_JOB in needs, f"`setup-and-test` does not depend on `{SCOPE_JOB}`; its `if:` cannot read the decision"
    assert f"needs.{SCOPE_JOB}.outputs.run-functional" in str(job.get("if", "")), (
        f"`setup-and-test` no longer reads `{SCOPE_JOB}`'s decision, so every PR -- docs-only "
        "and fork PRs included -- runs seven backend-hitting legs (ENG-3683)."
    )


def test_the_scope_job_publishes_its_decision():
    outputs = _job(MAIN_WORKFLOW, SCOPE_JOB).get("outputs") or {}
    assert "run-functional" in outputs, f"`{SCOPE_JOB}` exposes no `run-functional` output: {sorted(outputs)}"


@pytest.mark.parametrize(
    ("signal", "what"),
    [
        ("github.event.pull_request.head.repo.full_name", "check whether the PR comes from a fork"),
        ("github.event.pull_request.labels", "read the PR's labels"),
        ("github.event.pull_request.base.sha", "diff the PR against its base"),
    ],
    ids=["fork", "labels", "base-sha"],
)
def test_the_scope_job_reads_every_signal_it_decides_on(signal: str, what: str):
    """Each signal has a distinct failure mode if it is dropped.

    Lose the fork check and an external PR runs seven legs with no secrets, all
    of them red for a reason that says nothing about the contribution. Lose the
    labels and the documented manual override silently stops working. Lose the
    base SHA and there is nothing to diff, so the path filter answers the same
    way for every PR.
    """
    step_env = " ".join(str(step.get("env", "")) for step in _job(MAIN_WORKFLOW, SCOPE_JOB)["steps"])
    assert signal in step_env, f"the `{SCOPE_JOB}` job no longer seems to {what} ({signal!r} is gone)"


def test_the_scope_job_matches_the_documented_paths_and_label():
    script = _script(_job(MAIN_WORKFLOW, SCOPE_JOB))
    assert FUNCTIONAL_LABEL in script, f"the '{FUNCTIONAL_LABEL}' override label is not honoured by `{SCOPE_JOB}`"
    for prefix in FUNCTIONAL_PATHS:
        assert prefix in script, (
            f"`{SCOPE_JOB}` does not treat a change under {prefix!r} as needing the functional matrix, "
            "so a PR editing exactly the code these suites cover would skip them (ENG-3683)."
        )


def test_non_pull_request_events_always_run_the_full_matrix():
    """`push`, `schedule` and `workflow_dispatch` must not inherit the PR filter.

    They are what `release.yaml`'s functional gate reads: narrowing them by path
    would leave a release commit with no functional run to point at, and the
    gate would block every release rather than gate it.
    """
    script = _script(_job(MAIN_WORKFLOW, SCOPE_JOB))
    assert re.search(r'\[\s*"\$EVENT"\s*!=\s*"pull_request"\s*\]', script), (
        f"`{SCOPE_JOB}` no longer short-circuits to the full matrix on non-pull_request events; "
        "a push or the nightly could now be filtered by paths (ENG-3683)."
    )


# ---------------------------------------------------------------------------
# main.yaml: the environment the functional legs actually get
# ---------------------------------------------------------------------------


def test_every_leg_declares_the_models_api_version():
    """`MODELS_RUN_URL=.../api/${MODELS_API}/execute` resolves to `/api//` without it.

    An `include` key that is simply absent expands to the empty string rather
    than failing, so a leg added without `models-api` would hit a malformed URL
    and read as a backend problem.
    """
    missing = [entry["test-suite"] for entry in _matrix()["include"] if not entry.get("models-api")]
    assert not missing, f"matrix include entries with no `models-api`: {missing}"


def test_the_v2_leg_is_the_one_on_the_v2_model_api():
    """CI hands the v2 leg a v2 URL; its conftest no longer has to correct one.

    `tests/functional/v2/conftest.py` used to patch the execution path at fixture
    time, which meant the workflow could be wrong about the model API for years
    without anything noticing (ENG-3683).
    """
    by_leg = {entry["test-suite"]: entry["models-api"] for entry in _matrix()["include"]}
    assert by_leg.get("v2") == "v2", f"the v2 leg is configured for the {by_leg.get('v2')!r} model API"
    others = {leg: api for leg, api in by_leg.items() if leg != "v2" and api == "v2"}
    assert not others, (
        f"legs other than `v2` are pointed at the v2 model API: {others}. Each leg declares the "
        "execution API its own suite speaks; sharing one setting is how a leg ends up silently "
        "exercising the wrong endpoint."
    )


def test_the_models_url_is_built_from_the_matrix_and_not_hardcoded():
    script = _script(_job(MAIN_WORKFLOW, "setup-and-test"))
    hardcoded = re.findall(r"MODELS_RUN_URL=\S*api/v\d/\S*", script)
    assert not hardcoded, (
        f"MODELS_RUN_URL still hardcodes an API version ({hardcoded}); every leg would get the same "
        "one regardless of `matrix.models-api` (ENG-3683)."
    )
    assert "MODELS_API" in script, "the env step does not use `matrix.models-api` to build MODELS_RUN_URL"


def test_the_functional_legs_set_the_canonical_api_key_alias_to_the_same_value():
    """AIXPLAIN_API_KEY is the fallback every functional conftest accepts.

    It cannot be a *second* credential: `aixplain/utils/config.py` raises when
    AIXPLAIN_API_KEY and TEAM_API_KEY are both set and differ, so a well-meant
    second secret here would fail every leg at import time.
    """
    script = _functional_env_step()["run"]
    team = re.findall(r"(?<![A-Z_])TEAM_API_KEY=\$\{?(\w+)", script)
    aixplain = re.findall(r"(?<![A-Z_])AIXPLAIN_API_KEY=\$\{?(\w+)", script)

    assert team, "the functional legs no longer export TEAM_API_KEY"
    assert aixplain, (
        "the functional legs do not export AIXPLAIN_API_KEY, the canonical fallback every "
        "functional conftest reads (ENG-3683)."
    )
    assert set(team) == set(aixplain), (
        f"TEAM_API_KEY is set from {sorted(set(team))} but AIXPLAIN_API_KEY from "
        f"{sorted(set(aixplain))}. They must carry the same value: aixplain/utils/config.py "
        "raises when the two are set and differ."
    )


@pytest.mark.parametrize("variable", ["TEST_COMPOSIO_INTEGRATION_ID", "TEST_CONNECTION_ID"])
def test_the_functional_legs_export_the_event_trigger_fixtures(variable: str):
    """Their absence is invisible: the tests skip and the leg still reports green.

    `tests/functional/v2/test_trigger.py`'s TestEventTriggerDiscovery and
    TestEventTriggerLifecycle gate on these two, so CI executed neither class
    while `setup-and-test (v2)` went green (ENG-3683).
    """
    script = _functional_env_step()["run"]
    assert re.search(rf"{variable}=", script), (
        f"{variable} is not exported by the functional legs, so the event-trigger tests in "
        "tests/functional/v2/test_trigger.py skip in CI and the leg is green anyway."
    )


def test_a_tag_is_released_against_the_production_backend():
    """`release.yaml`'s gate reads the functional run on the tagged commit.

    If a `workflow_dispatch` on the tag ran against the test backend, that run
    would satisfy the gate while proving nothing about the environment the wheel
    is published for.
    """
    step_env = str(_functional_env_step().get("env", ""))
    assert "refs/tags/v" in step_env, (
        "the functional legs no longer treat a v* tag as production, so a run dispatched on a "
        "release tag would validate against the test backend (ENG-3683)."
    )


def test_secrets_reach_the_env_step_through_env_and_not_string_interpolation():
    """`${{ }}` is textual substitution into the script body.

    A secret containing a quote or a newline pasted there is a shell injection
    with the workflow's own credentials -- and rotating a key is exactly when a
    value's shape changes.
    """
    step = _functional_env_step()
    assert "${{" not in step["run"], (
        "the functional env step interpolates `${{ }}` into its script body; pass the values "
        "through the step's `env:` block instead (ENG-3683)."
    )
    assert step.get("env"), "the functional env step has no `env:` block, so it has nothing to export"


# ---------------------------------------------------------------------------
# main.yaml: someone has to be told about a nightly failure
# ---------------------------------------------------------------------------


def test_the_nightly_failure_notification_is_wired_to_the_whole_run():
    """A nightly nobody is told about is the same as no nightly at all.

    `always()` matters as much as the needs list: the default `if` on a job with
    `needs` is "all of them succeeded", so without it the notifier would run only
    when there is nothing to report.
    """
    job = _job(MAIN_WORKFLOW, "nightly-report")
    condition = str(job.get("if", ""))
    assert "always()" in condition, (
        "`nightly-report` does not use `always()`, so it is skipped by the very failures it "
        "exists to announce."
    )
    assert "schedule" in condition, (
        "`nightly-report` is not scoped to the `schedule` event; a Slack message per red PR is "
        "how an alert channel gets muted."
    )
    assert "setup-and-test" in (job.get("needs") or []), (
        "`nightly-report` does not depend on the functional matrix, so a red functional leg would "
        "never be reported."
    )

    step = next(step for step in job["steps"] if "curl" in (step.get("run") or ""))
    assert "failure" in str(step.get("if", "")), "the Slack step fires on a green nightly too"
    assert "github.run_id" in str(step.get("env", "")), (
        "the Slack message carries no link to the run, which is the only actionable part of it"
    )


# ---------------------------------------------------------------------------
# release.yaml: no PyPI upload without a green functional run on that commit
# ---------------------------------------------------------------------------


def test_nothing_is_built_or_published_without_the_functional_gate():
    workflow = _load(RELEASE_WORKFLOW)
    assert "functional-gate" in workflow["jobs"], (
        "release.yaml has no `functional-gate` job: a tag can publish a wheel whose functional "
        "suites never ran against a live backend (ENG-3683)."
    )

    build_needs = workflow["jobs"]["build"].get("needs")
    build_needs = [build_needs] if isinstance(build_needs, str) else (build_needs or [])
    assert "functional-gate" in build_needs, (
        "release.yaml's `build` job does not depend on `functional-gate`, so the gate runs "
        "alongside the release instead of in front of it."
    )


def test_the_functional_gate_checks_the_released_commit_against_the_real_leg_list():
    """Asserted on the moves, because each shortcut fails silently.

    Gating on the tag *name* rather than `github.sha` would accept a moved tag.
    A hardcoded leg list would quietly make a leg added in the same release
    optional on the release that first ships it.
    """
    job = _job(RELEASE_WORKFLOW, "functional-gate")
    script = _script(job)
    env_refs = " ".join(str(step.get("env", "")) for step in job["steps"])

    assert "github.sha" in env_refs, (
        "release.yaml's functional gate does not read `github.sha`; a tag can be moved, so the "
        "commit is the only thing that identifies what was tested."
    )
    for move, what in (
        ("main.yaml", "look up the functional workflow's runs"),
        ("head_sha", "restrict those runs to the released commit"),
        ("setup-and-test", "check the functional legs specifically, not the run's overall conclusion"),
        ("conclusion", "require a successful conclusion"),
    ):
        assert move in script, f"release.yaml's functional gate no longer seems to {what} ({move!r} is gone)"

    assert "strategy" not in job, "the gate is a single decision; a matrix would make a missing leg a skipped job"


def test_the_functional_gate_is_read_only():
    """It decides; it must not be able to re-run, cancel, or write anything.

    `actions: write` here would give a release job the ability to trigger the very
    runs it is checking.
    """
    permissions = _job(RELEASE_WORKFLOW, "functional-gate")["permissions"]
    assert isinstance(permissions, dict), f"expected a mapping of scopes, got {permissions!r}"
    writes = {scope: value for scope, value in permissions.items() if value != "read"}
    assert not writes, f"release.yaml's functional gate holds write-capable permissions: {writes}"
    assert permissions.get("actions") == "read", (
        "the gate needs `actions: read` to list workflow runs; without it the `gh api` calls 404 "
        "on a private repository and the gate cannot tell 'never ran' from 'no access'."
    )


# ---------------------------------------------------------------------------
# pre-commit.yaml: a credential it never needed
# ---------------------------------------------------------------------------


def test_pre_commit_is_not_handed_a_backend_credential():
    """`pre-commit run --all-files` runs third-party hook code.

    Its `pytest-check` hook runs `tests/unit`, which is credential-free by design
    (ENG-3431), so TEAM_API_KEY was only ever exposed, never used (ENG-3683).
    """
    text = yaml.safe_dump(_load(PRE_COMMIT_WORKFLOW))
    assert "TEAM_API_KEY" not in text, (
        "pre-commit.yaml is handed TEAM_API_KEY again. It runs `tests/unit` plus third-party "
        "hook code and needs no backend credential."
    )


# ---------------------------------------------------------------------------
# tests/functional/v2/conftest.py: CI and a laptop must mean the same backend
# ---------------------------------------------------------------------------


def _v2_conftest():
    """Import the v2 conftest as a plain module.

    Loaded by path rather than imported as `tests.functional.v2.conftest`, so
    pytest does not end up with the same conftest registered twice.
    """
    spec = importlib.util.spec_from_file_location("_v2_functional_conftest", V2_CONFTEST)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_v2_conftest_defaults_to_the_backend_ci_uses():
    """An unset BACKEND_URL used to mean dev-platform-api here while CI ran test.

    The hardcoded ids in tests/functional/v2/ exist on one backend at a time, so
    the two environments disagreed about which failures were real -- and each
    side read as "it passes for me" (ENG-3683).
    """
    module = _v2_conftest()
    assert module.DEFAULT_BACKEND_URL == TEST_BACKEND_URL, (
        f"tests/functional/v2/conftest.py defaults to {module.DEFAULT_BACKEND_URL!r}, but CI runs "
        f"these suites against {TEST_BACKEND_URL!r} on every ref that is not main or a v* tag."
    )


@pytest.mark.parametrize(
    ("backend", "expected"),
    [
        ("https://test-platform-api.aixplain.com", "https://test-models.aixplain.com/api/v2/execute"),
        ("https://platform-api.aixplain.com", "https://models.aixplain.com/api/v2/execute"),
        ("https://dev-platform-api.aixplain.com", "https://dev-models.aixplain.com/api/v2/execute"),
    ],
    ids=["test", "prod", "dev"],
)
def test_the_v2_model_url_follows_the_backend(monkeypatch, backend: str, expected: str):
    """Half the suite against prod and half against test is the worst outcome.

    A developer who sets BACKEND_URL and leaves MODELS_RUN_URL alone would get
    exactly that if the model URL were defaulted independently.
    """
    monkeypatch.delenv("MODELS_RUN_URL", raising=False)
    assert _v2_conftest()._models_run_url(backend) == expected


@pytest.mark.parametrize(
    ("explicit", "expected"),
    [
        (
            "https://test-models.aixplain.com/api/v2/execute",
            "https://test-models.aixplain.com/api/v2/execute",
        ),
        (
            "https://test-models.aixplain.com/some/other/path",
            "https://test-models.aixplain.com/api/v2/execute",
        ),
    ],
    ids=["already-the-v2-endpoint", "any-other-path"],
)
def test_an_explicit_models_url_contributes_its_host_and_not_its_path(monkeypatch, explicit: str, expected: str):
    """These suites speak the v2 execution API and nothing else.

    MODELS_RUN_URL is shared with the other functional legs, whose suites may
    target a different endpoint on the same host, so the host is honoured and the
    path is always built here. CI sets the matching URL directly.
    """
    monkeypatch.setenv("MODELS_RUN_URL", explicit)
    assert _v2_conftest()._models_run_url("https://test-platform-api.aixplain.com") == expected


# ---------------------------------------------------------------------------
# docs/ci/required-checks.md: the doc is the input to a settings change
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("term", [SCOPE_JOB, FUNCTIONAL_LABEL, "functional-gate"])
def test_the_required_checks_doc_describes_the_new_gates(term: str):
    """Someone pastes context strings out of this doc into branch protection.

    A gate that exists in YAML but not in the doc is a context that either never
    becomes required, or blocks every PR forever once it is.
    """
    text = REQUIRED_CHECKS_DOC.read_text()
    assert term in text, (
        f"docs/ci/required-checks.md does not mention `{term}`, so whoever configures required "
        "checks has no way to know it exists (ENG-3683)."
    )
