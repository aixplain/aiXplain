"""Guard: the PR trigger, the nightly run, and the release's functional gate (ENG-3683).

Before this ticket `main.yaml` ran on `push` to `main`/`test` and nothing else,
so:

* the functional matrix never ran on a pull request -- the earliest a
  functional regression could surface was a push to `test`, after review;
* `release.yaml` gated a PyPI upload on `pytest tests/unit` alone, so no
  live-backend suite stood between a tag and an immutable upload;
* several env vars the functional suites read were simply never set, which does
  not fail anything: `tests/functional/v2/test_trigger.py`'s event-trigger
  classes skipped every run in CI and the leg still reported green.

Every fix here is one deleted line from being undone, and none of them fails
visibly when removed -- a workflow that stops running on PRs is still a valid
workflow, and a leg that skips its tests is still green. The wiring is asserted
statically, in the same credential-free idiom as
`tests/unit/test_ci_permissions.py` and `tests/unit/test_ci_matrix_coverage.py`.

The *decisions* are not: a substring check passes just as well on `if false`
as on the real fork test, and mutation testing showed several such guards
surviving a broken script (ENG-3683). So the `functional-scope`
script, the `functional-result` verdict and the release gate's run filter are
lifted out of the YAML and executed -- with bash, git and jq, against throwaway
repositories and fixture JSON. This file runs in `unit-coverage` and in
pre-commit on every branch push, so drift is caught when the YAML is edited.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

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

#: The non-matrix job that reports the matrix's outcome under one fixed name.
RESULT_JOB = "functional-result"

#: The label that forces a functional run on a PR whose paths do not ask for one.
FUNCTIONAL_LABEL = "functional-tests"

#: The repository the scope script compares a PR's head repository against.
THIS_REPO = "aixplain/aiXplain"

#: The backend CI runs the functional suites against on every non-production
#: run. The v2 conftest has to agree with it -- see the tests at the bottom.
TEST_BACKEND_URL = "https://test-platform-api.aixplain.com"

needs_bash = pytest.mark.skipif(shutil.which("bash") is None, reason="bash is not on PATH")
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not on PATH")
needs_jq = pytest.mark.skipif(shutil.which("jq") is None, reason="jq is not on PATH")


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


def _needs(job: dict) -> list:
    needs = job.get("needs")
    return [needs] if isinstance(needs, str) else list(needs or [])


def _script(job: dict) -> str:
    return "\n".join(step.get("run", "") or "" for step in job["steps"])


def _functional_env_step() -> dict:
    """The `functional` step that writes the suite's env into $GITHUB_ENV."""
    steps = [step for step in _job(MAIN_WORKFLOW, "functional")["steps"] if "GITHUB_ENV" in (step.get("run") or "")]
    assert len(steps) == 1, f"expected exactly one step writing to $GITHUB_ENV, found {len(steps)}"
    return steps[0]


def _include() -> list:
    """The `functional` matrix's `include` entries, one per leg."""
    return _job(MAIN_WORKFLOW, "functional")["strategy"]["matrix"]["include"]


def _leg(suite: str) -> dict:
    entries = [entry for entry in _include() if entry["suite"] == suite]
    assert len(entries) == 1, f"expected one `include` entry for the `{suite}` leg, found {len(entries)}"
    return entries[0]


def _run_tests_step() -> dict:
    """The `functional` step that runs a leg's pytest."""
    steps = [step for step in _job(MAIN_WORKFLOW, "functional")["steps"] if step.get("name") == "Run Tests"]
    assert len(steps) == 1, f"expected exactly one `Run Tests` step in `functional`, found {len(steps)}"
    return steps[0]


def _clean_env(**extra: str) -> dict:
    """The environment for a subprocess, minus anything git would obey.

    Pre-commit runs this file from inside a git hook, where GIT_DIR and
    GIT_INDEX_FILE point at the *real* repository. A `git commit` in a throwaway
    repository would then write to this one.
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(extra)
    return env


# ---------------------------------------------------------------------------
# A small evaluator for the `${{ }}` expressions these guards depend on
# ---------------------------------------------------------------------------


def _render(template: str, github: dict, env: Optional[dict] = None, matrix: Optional[dict] = None) -> str:
    """Evaluate every `${{ }}` in *template* the way Actions would, for the subset used here.

    Supported: `github.*`, `env.*` and `matrix.*` lookups, `==`/`!=`, `&&`/`||` (which, as in
    Actions, return an operand rather than a boolean), parentheses, string
    literals, `startsWith` and `format`. Anything else fails loudly, so an
    expression rewritten beyond this subset is a test to update, not a guard
    that silently stops evaluating. Comparisons are case-insensitive, as in
    Actions.
    """

    def lookup(root: dict, path: str):
        value = root
        for part in path.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        return value

    class _Caseless(str):
        def __eq__(self, other):
            return isinstance(other, str) and self.lower() == other.lower()

        def __ne__(self, other):
            return not self.__eq__(other)

        __hash__ = str.__hash__

    def wrap(value):
        return _Caseless(value) if isinstance(value, str) else value

    def evaluate(body: str):
        python = body.replace("&&", " and ").replace("||", " or ")
        python = re.sub(r"\bstartsWith\(", "_starts_with(", python)
        python = re.sub(r"\bformat\(", "_format(", python)
        python = re.sub(
            r"\b(github|env|matrix)\.([\w.-]+)", lambda m: f"_lookup({m.group(1)!r}, {m.group(2)!r})", python
        )
        bare = re.sub(r"'[^']*'", "''", python)
        unknown = set(re.findall(r"[A-Za-z_]\w*", bare)) - {"and", "or", "_starts_with", "_format", "_lookup"}
        assert not unknown, f"expression {body!r} uses {sorted(unknown)}, which this evaluator does not model"
        roots = {"github": github, "env": env or {}, "matrix": matrix or {}}
        return eval(  # noqa: S307 -- the input is this repository's own workflow file
            python,
            {"__builtins__": {}},
            {
                "_lookup": lambda root, path: wrap(lookup(roots[root], path)),
                "_starts_with": lambda s, prefix: str(s or "").lower().startswith(str(prefix).lower()),
                "_format": lambda fmt, *args: fmt.format(*("" if a is None else a for a in args)),
            },
        )

    def as_text(value) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return "" if value is None else str(value)

    return re.sub(r"\$\{\{(.*?)\}\}", lambda m: as_text(evaluate(m.group(1))), template, flags=re.S)


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


def _concurrency(event_name: str, **github: object) -> tuple:
    block = _load(MAIN_WORKFLOW).get("concurrency")
    assert isinstance(block, dict), "main.yaml has no `concurrency:` mapping"
    context = {"workflow": "Run Tests", "event_name": event_name, **github}
    return _render(block["group"], context), _render(str(block["cancel-in-progress"]), context)


def test_runs_of_the_same_pr_share_a_group_and_cancel_each_other():
    """A label storm or a run of pushes must leave one matrix going, not several.

    Every label starts a run (see the `labeled` test above), and the matrix is one
    leg per functional test file against a shared backend.
    """
    pr_7 = {"action": "synchronize", "pull_request": {"number": 7}}
    first = _concurrency("pull_request", event=pr_7, run_id=1, ref="refs/pull/7/merge")
    second = _concurrency("pull_request", event=pr_7, run_id=2, ref="refs/pull/7/merge")
    pr_8 = {"action": "synchronize", "pull_request": {"number": 8}}
    other = _concurrency("pull_request", event=pr_8, run_id=3, ref="refs/pull/8/merge")
    assert first[0] == second[0], f"two runs of PR #7 land in different groups: {first[0]!r} vs {second[0]!r}"
    assert first[0] != other[0], f"PR #7 and PR #8 share a concurrency group ({first[0]!r})"
    assert first[1] == "true", "a newer run on a PR does not cancel the superseded one"


@pytest.mark.parametrize(
    ("action", "label", "cancels"),
    [
        ("synchronize", None, "true"),
        ("labeled", FUNCTIONAL_LABEL, "true"),
        ("labeled", "bug", "false"),
        ("labeled", "needs-review", "false"),
    ],
    ids=["push", "functional-label", "unrelated-label", "another-unrelated-label"],
)
def test_only_new_code_or_the_functional_label_cancels_a_running_matrix(action: str, label, cancels: str):
    """Labelling a PR `bug` must not throw away a matrix that is halfway through.

    The run still joins the PR's group, so it queues behind the current one rather
    than running beside it on the shared backend.
    """
    event = {"action": action, "pull_request": {"number": 7}}
    if label is not None:
        event["label"] = {"name": label}
    group, cancel = _concurrency("pull_request", event=event, run_id=9, ref="refs/pull/7/merge")
    plain, _ = _concurrency("pull_request", event={"pull_request": {"number": 7}}, run_id=1, ref="refs/pull/7/merge")
    assert group == plain, f"a `{action}` run left the PR's concurrency group: {group!r} vs {plain!r}"
    assert cancel == cancels, f"a `{action}` run with label {label!r} has cancel-in-progress={cancel!r}"


@pytest.mark.parametrize("event", ["push", "schedule", "workflow_dispatch"])
def test_non_pr_runs_are_never_cancelled_or_dropped(event: str):
    """A dropped push run on `main` is a commit the release gate cannot release.

    GitHub keeps one *pending* run per group and cancels the rest even without
    `cancel-in-progress`, so a group shared across pushes to `main` would lose
    the middle one of three quick merges.
    """
    first = _concurrency(event, event={}, run_id=101, ref="refs/heads/main")
    second = _concurrency(event, event={}, run_id=102, ref="refs/heads/main")
    assert first[0] != second[0], f"two `{event}` runs on main share the concurrency group {first[0]!r}"
    assert first[1] == "false", f"a `{event}` run can be cancelled by a newer one"


# ---------------------------------------------------------------------------
# main.yaml: which events pay for the functional matrix
# ---------------------------------------------------------------------------


def test_the_functional_matrix_is_gated_by_the_scope_job():
    """Gating lives in an `if:`, never in `on.pull_request.paths`.

    A path filter suppresses the *check*, so a required context simply never
    reports on a docs-only PR and the PR can never merge. A job skipped by `if:`
    still reports something, which `functional-result` then turns into a
    verdict under one fixed name.
    """
    triggers = _triggers(_load(MAIN_WORKFLOW))
    assert "paths" not in triggers["pull_request"] and "paths-ignore" not in triggers["pull_request"], (
        "main.yaml's pull_request trigger has a path filter. That suppresses the checks "
        "themselves, so any required context becomes an unsatisfiable 'Expected' on a "
        f"docs-only PR. Gate the matrix with `if:` on the `{SCOPE_JOB}` job instead (ENG-3683)."
    )

    job = _job(MAIN_WORKFLOW, "functional")
    assert SCOPE_JOB in _needs(job), f"`functional` does not depend on `{SCOPE_JOB}`, so its `if:` cannot read it"
    assert str(job.get("if", "")).strip() == f"needs.{SCOPE_JOB}.outputs.run-functional == 'true'", (
        f"`functional` no longer runs exactly when `{SCOPE_JOB}` says so: {job.get('if')!r} (ENG-3683)."
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
    """The behavioural tests below inject these variables directly.

    So they cannot notice the workflow no longer *passing* one in: that wiring is
    what this checks.
    """
    step_env = " ".join(str(step.get("env", "")) for step in _job(MAIN_WORKFLOW, SCOPE_JOB)["steps"])
    assert signal in step_env, f"the `{SCOPE_JOB}` job no longer seems to {what} ({signal!r} is gone)"


def _git(repo: Path, *args: str, stdin: Optional[str] = None) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=ci-guard", "-c", "user.email=ci-guard@example.invalid", "-c", "commit.gpgsign=false"]
        + list(args),
        cwd=repo,
        input=stdin,
        capture_output=True,
        text=True,
        env=_clean_env(HOME=str(repo.parent / "home")),
        check=True,
    )
    return result.stdout.strip()


@pytest.fixture
def pr_repo(tmp_path):
    """A throwaway repository with one base commit; returns (repo, base_sha, commit_paths)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (tmp_path / "home").mkdir()
    _git(repo, "init", "-q")
    (repo / "README.md").write_text("base\n")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "--no-verify", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")

    def commit_paths(paths: list) -> str:
        """Commit *paths* as empty files via the index alone -- fast even for thousands of them."""
        blob = _git(repo, "hash-object", "-w", "--stdin", stdin="")
        _git(repo, "update-index", "--add", "--index-info", stdin="".join(f"100644 {blob}\t{p}\n" for p in paths))
        _git(repo, "commit", "-q", "--no-verify", "-m", "change")
        return _git(repo, "rev-parse", "HEAD")

    return repo, base, commit_paths


def _run_scope(repo: Path, event: str, **env: str) -> dict:
    """Run the real `functional-scope` script; returns its $GITHUB_OUTPUT as a dict."""
    steps = [step for step in _job(MAIN_WORKFLOW, SCOPE_JOB)["steps"] if step.get("id") == "decide"]
    assert len(steps) == 1, f"`{SCOPE_JOB}` has no single step with `id: decide`"
    script = repo.parent / "scope.sh"
    script.write_text(steps[0]["run"])
    output = repo.parent / "github_output"
    output.write_text("")
    defaults = {"LABELS": "null", "HEAD_REPO": "", "BASE_SHA": "", "HEAD_SHA": ""}
    result = subprocess.run(
        ["bash", str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
        env=_clean_env(
            HOME=str(repo.parent / "home"),
            GITHUB_OUTPUT=str(output),
            GITHUB_REPOSITORY=THIS_REPO,
            EVENT=event,
            **{**defaults, **env},
        ),
        timeout=60,
    )
    assert result.returncode == 0, f"the scope script failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    return dict(line.split("=", 1) for line in output.read_text().splitlines() if "=" in line)


@needs_bash
@needs_git
@pytest.mark.parametrize("event", ["push", "schedule", "workflow_dispatch"])
def test_non_pull_request_events_always_run_the_full_matrix(pr_repo, event: str):
    """`push`, `schedule` and `workflow_dispatch` must not inherit the PR filter.

    They are what `release.yaml`'s functional gate reads: narrowing them by path
    would leave a release commit with no functional run to point at.
    """
    repo, _, _ = pr_repo
    assert _run_scope(repo, event)["run-functional"] == "true"


@needs_bash
@needs_git
@pytest.mark.parametrize("head_repo", ["someone/aiXplain", ""], ids=["fork", "deleted-head-repo"])
def test_a_fork_pr_never_runs_the_matrix(pr_repo, head_repo: str):
    """A fork PR gets no secrets, so every leg would be red for no reason.

    An empty head repository is what a PR from a deleted fork reports; it has to
    fail closed, even when the PR touches `aixplain/` and carries the label.
    """
    repo, base, commit_paths = pr_repo
    head = commit_paths(["aixplain/v2/core.py"])
    decision = _run_scope(
        repo,
        "pull_request",
        HEAD_REPO=head_repo,
        LABELS=json.dumps([FUNCTIONAL_LABEL]),
        BASE_SHA=base,
        HEAD_SHA=head,
    )
    assert decision["run-functional"] == "false", decision


@needs_bash
@needs_git
@needs_jq
@pytest.mark.parametrize(
    ("labels", "expected"),
    [
        ([FUNCTIONAL_LABEL], "true"),
        (["docs", FUNCTIONAL_LABEL], "true"),
        (["docs"], "false"),
        (["functional-tests-later"], "false"),
        ([], "false"),
    ],
    ids=["label", "label-among-others", "other-label", "near-miss", "no-labels"],
)
def test_the_label_overrides_the_paths(pr_repo, labels: list, expected: str):
    """The label is an exact match, and any other label leaves the path decision alone."""
    repo, base, commit_paths = pr_repo
    head = commit_paths(["docs/readme.md"])
    decision = _run_scope(
        repo, "pull_request", HEAD_REPO=THIS_REPO, LABELS=json.dumps(labels), BASE_SHA=base, HEAD_SHA=head
    )
    assert decision["run-functional"] == expected, decision


@needs_bash
@needs_git
@needs_jq
@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (["docs/ci/required-checks.md", "README.md.orig"], "false"),
        (["aixplain/v2/core.py"], "true"),
        (["tests/functional/v2/test_agent.py"], "true"),
        (["pyproject.toml"], "true"),
        (["tests/conftest.py"], "true"),
        (["tests/ci_guards.py"], "true"),
        (["tests/cleanup_guards.py"], "true"),
        (["pytest.ini"], "true"),
        ([".github/workflows/main.yaml"], "true"),
        (
            ["tests/unit/test_x.py", "docs/pyproject.toml", "tests/conftest.py.bak", "docs/pytest.ini"],
            "false",
        ),
    ],
    ids=[
        "docs-only",
        "sdk",
        "functional-suite",
        "pyproject",
        "root-conftest",
        "ci-guards",
        "cleanup-guards",
        "pytest-ini",
        "workflow",
        "near-misses",
    ],
)
def test_the_paths_decide_a_same_repo_pr(pr_repo, paths: list, expected: str):
    repo, base, commit_paths = pr_repo
    head = commit_paths(paths)
    decision = _run_scope(repo, "pull_request", HEAD_REPO=THIS_REPO, LABELS="[]", BASE_SHA=base, HEAD_SHA=head)
    assert decision["run-functional"] == expected, decision


@needs_bash
@needs_git
@needs_jq
def test_a_huge_pr_touching_the_sdk_still_runs_the_matrix(pr_repo):
    """The SIGPIPE regression (ENG-3683).

    `printf "$changed" | grep -q` under `pipefail`: grep exits on the first
    match, the writer dies of SIGPIPE once the list outgrows the pipe buffer,
    and the `if` is false. `aixplain/` sorts first, so the largest PRs -- mass
    reformats, removals -- skipped the matrix and showed green. ~200 KB of names
    here, comfortably past a 64 KB pipe buffer.
    """
    repo, base, commit_paths = pr_repo
    filler = [f"docs/generated/a-deliberately-long-file-name-to-fill-the-pipe-{i:05d}.md" for i in range(3000)]
    head = commit_paths(["aixplain/v2/core.py"] + filler)
    assert len("\n".join(filler)) > 64 * 1024
    decision = _run_scope(repo, "pull_request", HEAD_REPO=THIS_REPO, LABELS="[]", BASE_SHA=base, HEAD_SHA=head)
    assert decision["run-functional"] == "true", decision


# ---------------------------------------------------------------------------
# main.yaml: the one functional context that can be required
# ---------------------------------------------------------------------------


def test_the_result_job_is_a_single_always_reporting_context():
    """The per-leg contexts cannot be required: a skipped matrix reports one `functional`.

    `always()` matters as much as the needs list: the default `if` on a job with
    `needs` is "all of them succeeded", so without it this job would be skipped
    -- which a required check counts as passing -- exactly when a leg is red.
    """
    job = _job(MAIN_WORKFLOW, RESULT_JOB)
    assert "strategy" not in job, f"`{RESULT_JOB}` is a matrix; its context name would not be fixed"
    assert set(_needs(job)) == {SCOPE_JOB, "functional"}, f"`{RESULT_JOB}` needs {_needs(job)}"
    assert str(job.get("if", "")).strip() == "always()", f"`{RESULT_JOB}` runs on {job.get('if')!r}, not always()"


@needs_bash
@pytest.mark.parametrize(
    ("scope", "run_functional", "functional", "passes"),
    [
        ("success", "true", "success", True),
        ("success", "true", "failure", False),
        ("success", "true", "cancelled", False),
        ("success", "true", "skipped", False),
        ("success", "false", "skipped", True),
        ("failure", "", "skipped", False),
        ("cancelled", "", "skipped", False),
        ("success", "", "skipped", False),
    ],
    ids=[
        "ran-green",
        "ran-red",
        "ran-cancelled",
        "in-scope-but-skipped",
        "out-of-scope",
        "scope-failed",
        "scope-cancelled",
        "scope-said-nothing",
    ],
)
def test_the_result_job_verdict(tmp_path, scope: str, run_functional: str, functional: str, passes: bool):
    script = tmp_path / "result.sh"
    script.write_text(_script(_job(MAIN_WORKFLOW, RESULT_JOB)))
    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        env=_clean_env(SCOPE=scope, RUN_FUNCTIONAL=run_functional, REASON="fixture", FUNCTIONAL=functional),
        timeout=30,
    )
    assert (result.returncode == 0) == passes, (
        f"scope={scope} run-functional={run_functional!r} functional={functional}: exit {result.returncode}\n"
        f"{result.stdout}{result.stderr}"
    )


# ---------------------------------------------------------------------------
# main.yaml: the environment the functional legs actually get
# ---------------------------------------------------------------------------


def _is_prod(event: str, ref: str) -> bool:
    expression = _job(MAIN_WORKFLOW, "functional").get("env", {}).get("IS_PROD")
    assert expression, "the `functional` job no longer defines IS_PROD at job level"
    return _render(str(expression), {"event_name": event, "ref": ref, "ref_name": ref.rsplit("/", 1)[-1]}) == "true"


@pytest.mark.parametrize(
    ("event", "ref", "prod"),
    [
        ("push", "refs/heads/main", True),
        ("workflow_dispatch", "refs/tags/v0.3.1", True),
        ("workflow_dispatch", "refs/heads/main", True),
        ("schedule", "refs/heads/main", False),
        ("push", "refs/heads/test", False),
        ("pull_request", "refs/pull/12/merge", False),
        ("workflow_dispatch", "refs/heads/version_2", False),
        ("workflow_dispatch", "refs/heads/feature/main", False),
    ],
    ids=[
        "push-main",
        "dispatch-on-tag",
        "dispatch-on-main",
        "nightly",
        "push-test",
        "pull-request",
        "dispatch-on-v-branch",
        "dispatch-on-branch-ending-in-main",
    ],
)
def test_only_main_and_release_tags_run_against_production(event: str, ref: str, prod: bool):
    """The nightly used to run every leg against production.

    A scheduled run executes on the default branch, `main`, so a ref-only test
    called it production (ENG-3683). A tag still has to count:
    `release.yaml`'s gate reads the run on the tagged commit.
    """
    assert _is_prod(event, ref) is prod, f"IS_PROD for `{event}` on {ref} should be {prod}"


def test_production_secrets_only_expand_on_production_runs():
    """A same-repo PR runs `pip install` on unreviewed dependency changes in this job.

    So a PR job must not even *hold* the production key: every `_PROD` secret
    expands through IS_PROD to the empty string otherwise.
    """
    step_env = _functional_env_step().get("env") or {}
    prod_entries = {name: value for name, value in step_env.items() if "_PROD" in str(value)}
    assert prod_entries, "the functional env step no longer reads any _PROD secret; update this test"
    for name, value in prod_entries.items():
        assert re.fullmatch(r"\$\{\{ env\.IS_PROD == 'true' && secrets\.\w+_PROD \|\| '' \}\}", str(value)), (
            f"{name}={value!r} expands a production secret on every run, PRs included (ENG-3683)."
        )
        secret = re.search(r"secrets\.(\w+)", value).group(1)
        for is_prod, expected in (("true", "<secret>"), ("false", "")):
            rendered = _render(str(value).replace(f"secrets.{secret}", "'<secret>'"), {}, {"IS_PROD": is_prod})
            assert rendered == expected, f"{name} renders {rendered!r} when IS_PROD={is_prod}"

    text = MAIN_WORKFLOW.read_text()
    everywhere = set(re.findall(r"secrets\.\w+_PROD\b", text))
    gated = set(re.findall(r"secrets\.\w+_PROD\b", " ".join(prod_entries.values())))
    assert everywhere == gated, f"_PROD secrets referenced outside the gated env step: {sorted(everywhere - gated)}"


def test_the_models_url_ships_the_endpoint_the_conftest_speaks():
    """One mechanism, not two (ENG-3683).

    A per-leg `models-api` matrix key used to build this URL, but the v2
    conftest keeps only the host and always builds the v2 path itself, so the
    key changed nothing. The workflow now exports the same endpoint the conftest
    would build.
    """
    include = _job(MAIN_WORKFLOW, "functional")["strategy"]["matrix"]["include"]
    assert not [entry["suite"] for entry in include if "models-api" in entry], "a leg declares `models-api` again"
    script = _functional_env_step()["run"]
    urls = re.findall(r"MODELS_RUN_URL=(\S+?)\"?$", script, re.MULTILINE)
    assert urls == [f"$models{_v2_conftest().MODELS_EXECUTE_PATH}"], f"MODELS_RUN_URL is exported as {urls}"


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
def test_the_event_trigger_fixtures_do_not_depend_on_secrets(variable: str):
    """The trigger tests find their integration and connection themselves.

    They used to read these two from secrets that were never created, so the
    `trigger` leg was red on every run and `release.yaml` could not release.
    The integration is now fetched by its `composio/gmail` path and the connection
    comes from `resolve_trigger_connection`; neither may drift back to a secret.
    """
    assert f"secrets.{variable}" not in MAIN_WORKFLOW.read_text(), f"main.yaml reads the {variable} secret again"
    assert f"{variable}=" not in _functional_env_step()["run"], f"the functional legs export {variable} again"
    trigger_tests = REPO_ROOT / "tests" / "functional" / "v2" / "test_trigger.py"
    assert f'"{variable}"' not in trigger_tests.read_text(), f"test_trigger.py reads {variable} again"


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


def _env_step_writes(tmp_path: Path, **values: str) -> dict:
    """Run the real env step with every `env:` key set; returns what it wrote to $GITHUB_ENV."""
    step = _functional_env_step()
    script = tmp_path / "env-step.sh"
    script.write_text(step["run"])
    github_env = tmp_path / "github_env"
    github_env.write_text("")
    env = {name: f"<{name}>" for name in step["env"]}
    env.update(values)
    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        env=_clean_env(GITHUB_ENV=str(github_env), **env),
        timeout=30,
    )
    assert result.returncode == 0, f"the env step failed:\n{result.stdout}{result.stderr}"
    return dict(line.split("=", 1) for line in github_env.read_text().splitlines() if "=" in line)


def _is_unconditional_skip(decorator: ast.expr) -> bool:
    """`@pytest.mark.skip` or `@pytest.mark.skip(...)` -- not `skipif`, which may run."""
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return isinstance(target, ast.Attribute) and target.attr == "skip" and ast.unparse(target) == "pytest.mark.skip"


def _runs_a_slack_token_test(path: Path) -> bool:
    """Whether *path* has a test that requests `slack_token` and is not skipped outright.

    Only test functions are considered: they are where the fixture is requested,
    and a test that always skips never reads the token, so its leg need not hold it.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    module_skipped = any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets)
        and _is_unconditional_skip(node.value)
        for node in tree.body
    )
    if module_skipped:
        return False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            requests = any(arg.arg == "slack_token" for arg in node.args.args)
            if requests and not any(_is_unconditional_skip(d) for d in node.decorator_list):
                return True
    return False


def test_only_the_legs_that_read_slack_token_are_handed_it():
    """Least privilege: a same-repo PR runs unreviewed dependency changes in every leg.

    So SLACK_TOKEN expands only on legs with `slack: true`, and those must be
    exactly the legs that run a test using the `slack_token` fixture -- a leg that
    starts reading it without the key would fail its Slack tests, and a key left
    on a leg whose only reader is skipped is a token held for nothing.
    """
    value = str((_functional_env_step().get("env") or {}).get("SLACK_TOKEN", ""))
    assert "secrets.SLACK_TOKEN" in value, f"the functional env step no longer reads SLACK_TOKEN ({value!r})"
    assert MAIN_WORKFLOW.read_text().count("secrets.SLACK_TOKEN") == 1, "SLACK_TOKEN is read outside the gated entry"

    readers = {entry["suite"] for entry in _include() if _runs_a_slack_token_test(REPO_ROOT / entry["path"].split()[0])}
    assert readers, "no functional leg uses the `slack_token` fixture any more; drop SLACK_TOKEN and this test"
    for entry in _include():
        rendered = _render(value.replace("secrets.SLACK_TOKEN", "'<secret>'"), {}, matrix=entry)
        expected = "<secret>" if entry["suite"] in readers else ""
        assert rendered == expected, (
            f"the `{entry['suite']}` leg gets SLACK_TOKEN={rendered!r}; expected {expected!r} because it "
            f"{'runs' if expected else 'runs no'} test using the `slack_token` fixture. Set or drop `slack: true`."
        )


@needs_bash
@pytest.mark.parametrize("token", ["", "xoxb-fixture"], ids=["leg-without-slack", "slack-leg"])
def test_the_env_step_exports_slack_token_only_when_it_has_one(tmp_path, token: str):
    written = _env_step_writes(tmp_path, IS_PROD="false", SLACK_TOKEN=token)
    if token:
        assert written.get("SLACK_TOKEN") == token, written
    else:
        assert "SLACK_TOKEN" not in written, f"a leg without `slack: true` still exports SLACK_TOKEN: {written}"


def test_no_leg_is_handed_hf_token():
    """Nothing under tests/functional reads HF_TOKEN, so no leg should hold it."""
    readers = [path for path in (REPO_ROOT / "tests" / "functional").rglob("*.py") if "HF_TOKEN" in path.read_text()]
    assert not readers, f"{readers} read HF_TOKEN; export it to those legs only, like SLACK_TOKEN"
    assert "HF_TOKEN" not in MAIN_WORKFLOW.read_text(), "main.yaml exports HF_TOKEN, which no functional test reads"


def _run_leg(tmp_path: Path, suite: str, is_prod: str) -> tuple:
    """Run the real `Run Tests` step for *suite* with a stub `python`.

    Returns (exit code, stdout, the stub's argv or None if it was never called).
    The step's `env:` is rendered from the leg's real `include` entry, so a key
    dropped from the matrix is a key dropped here.
    """
    step = _run_tests_step()
    leg = _leg(suite)
    work = tmp_path / suite
    stub_dir = work / "bin"
    stub_dir.mkdir(parents=True)
    argv_file = work / "argv"
    stub = stub_dir / "python"
    stub.write_text(f'#!/bin/sh\nprintf \'%s\\n\' "$@" > "{argv_file}"\n')
    stub.chmod(0o755)
    script = work / "run-tests.sh"
    script.write_text(step["run"])
    env = {name: _render(str(value), {}, matrix=leg) for name, value in (step.get("env") or {}).items()}
    result = subprocess.run(
        ["bash", str(script)],
        capture_output=True,
        text=True,
        env=_clean_env(PATH=f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}", IS_PROD=is_prod, **env),
        timeout=30,
    )
    argv = argv_file.read_text().splitlines() if argv_file.exists() else None
    return result.returncode, result.stdout, argv


@needs_bash
@pytest.mark.parametrize(("is_prod", "runs"), [("true", False), ("false", True)], ids=["production", "test-backend"])
def test_the_issue_leg_never_files_issues_on_production(tmp_path, is_prod: str, runs: bool):
    """tests/functional/v2/test_issue.py files real issues, and there is no API to delete one.

    On production (every push to `main`) the leg must exit 0 without running
    pytest; everywhere else it runs against the test backend as usual.
    """
    code, stdout, argv = _run_leg(tmp_path, "issue", is_prod)
    assert code == 0, f"the issue leg exited {code} with IS_PROD={is_prod}:\n{stdout}"
    if runs:
        assert argv == ["-m", "pytest", "tests/functional/v2/test_issue.py"], argv
    else:
        assert argv is None, f"the issue leg ran pytest on production: {argv}"
        assert "::notice::" in stdout, "the skipped issue leg does not say why it was skipped"


@needs_bash
def test_every_other_leg_still_runs_on_production(tmp_path):
    """The production skip is for the issue leg only; a key copied to another leg would hide it."""
    for entry in _include():
        if entry["suite"] == "issue":
            continue
        code, stdout, argv = _run_leg(tmp_path, entry["suite"], "true")
        assert code == 0, f"`{entry['suite']}` exited {code}:\n{stdout}"
        assert argv == ["-m", "pytest", *entry["path"].split()], (
            f"`{entry['suite']}` did not run `pytest {entry['path']}` on production: {argv}"
        )


def test_the_run_tests_step_takes_matrix_values_through_env():
    """`${{ matrix.path }}` pasted into the script is the same textual substitution as a secret would be."""
    assert "${{" not in _run_tests_step()["run"], "the Run Tests step interpolates `${{ }}` into its script body"


# ---------------------------------------------------------------------------
# main.yaml: someone has to be told about a nightly failure
# ---------------------------------------------------------------------------


def test_the_nightly_failure_notification_is_wired_to_the_whole_run():
    """A nightly nobody is told about is the same as no nightly at all.

    `always()` matters as much as the needs list: the default `if` on a job with
    `needs` is "all of them succeeded", so without it the notifier would run only
    when there is nothing to report. `functional-scope` has to be in the list
    too: when it fails, `functional` is *skipped*, which is neither a failure nor
    a cancellation, and the nightly would go unreported.
    """
    job = _job(MAIN_WORKFLOW, "nightly-report")
    condition = str(job.get("if", ""))
    assert "always()" in condition, (
        "`nightly-report` does not use `always()`, so it is skipped by the very failures it exists to announce."
    )
    assert "schedule" in condition, (
        "`nightly-report` is not scoped to the `schedule` event; a Slack message per red PR is "
        "how an alert channel gets muted."
    )
    missing = {"unit-coverage", "package-integrity", SCOPE_JOB, "functional", RESULT_JOB} - set(_needs(job))
    assert not missing, f"`nightly-report` does not depend on {sorted(missing)}, so their failures go unreported"

    step = next(step for step in job["steps"] if "curl" in (step.get("run") or ""))
    assert "failure" in str(step.get("if", "")), "the Slack step fires on a green nightly too"
    assert "github.run_id" in str(step.get("env", "")), (
        "the Slack message carries no link to the run, which is the only actionable part of it"
    )


# ---------------------------------------------------------------------------
# release.yaml: no PyPI upload without a green production run on that commit
# ---------------------------------------------------------------------------


def test_nothing_is_built_or_published_without_the_functional_gate():
    workflow = _load(RELEASE_WORKFLOW)
    assert "functional-gate" in workflow["jobs"], (
        "release.yaml has no `functional-gate` job: a tag can publish a wheel whose functional "
        "suites never ran against a live backend (ENG-3683)."
    )
    assert "functional-gate" in _needs(workflow["jobs"]["build"]), (
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
    env = {k: v for step in job["steps"] for k, v in (step.get("env") or {}).items()}

    assert env.get("SHA") == "${{ github.sha }}", (
        "release.yaml's functional gate does not key on `github.sha`; a tag can be moved, so the "
        "commit is the only thing that identifies what was tested."
    )
    assert env.get("TAG") == "${{ github.ref_name }}", "the gate cannot recognise a dispatch on this tag"
    for move, what in (
        ("main.yaml", "look up the functional workflow's runs"),
        ("head_sha=$SHA", "restrict those runs to the released commit"),
        ('jq -r --arg tag "$TAG" "$runs_filter"', "filter the runs to production ones"),
        ('["jobs"]["functional"]["strategy"]["matrix"]["suite"]', "read the leg list from main.yaml"),
        ('select(.conclusion == "success")', "require a successful conclusion"),
        ('jq -rs "$jobs_filter"', "drop runs that did not use the production backend"),
        ('grep -Fxq "$leg"', "match each leg's job name exactly"),
    ):
        assert move in script, f"release.yaml's functional gate no longer seems to {what} ({move!r} is gone)"

    assert "strategy" not in job, "the gate is a single decision; a matrix would make a missing leg a skipped job"


def _runs_filter() -> str:
    match = re.search(r"runs_filter='([^']*)'", _script(_job(RELEASE_WORKFLOW, "functional-gate")))
    assert match, "release.yaml's functional gate no longer defines `runs_filter='...'`"
    return match.group(1)


def _run(run_id: int, event: str, branch: Optional[str], status: str = "completed") -> dict:
    return {"id": run_id, "event": event, "head_branch": branch, "status": status}


@needs_jq
def test_the_release_gate_counts_only_production_runs():
    """A test-backend pass on the same SHA must not satisfy a production release.

    The gate takes the union of successful legs across runs, so one test-backend
    run in the set is enough to mask a red production leg (ENG-3683 review
    findings).
    """
    page_one = {
        "workflow_runs": [
            _run(1, "push", "main"),
            _run(2, "push", "test"),
            _run(3, "pull_request", "ENG-3683-feature"),
            _run(4, "schedule", "main"),
            _run(5, "workflow_dispatch", "v0.3.1"),
        ]
    }
    page_two = {
        "workflow_runs": [
            _run(6, "workflow_dispatch", "version_2"),
            _run(7, "workflow_dispatch", "v0.3.0"),
            _run(8, "push", "main", status="in_progress"),
            _run(9, "push", None),
            _run(10, "workflow_dispatch", "main"),
            _run(11, "push", "main"),
        ]
    }
    # `gh api --paginate` without --jq prints one JSON document per page.
    stdin = json.dumps(page_one) + "\n" + json.dumps(page_two) + "\n"
    result = subprocess.run(
        ["jq", "-r", "--arg", "tag", "v0.3.1", _runs_filter()],
        input=stdin,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
        check=True,
    )
    assert result.stdout.split() == ["1", "5", "11"], (
        "the release gate counted the wrong runs: expected the pushes to main and the dispatch on "
        f"this tag only, got {result.stdout.split()}"
    )


@pytest.mark.parametrize(
    ("event", "ref"),
    [
        ("push", "refs/heads/main"),
        ("workflow_dispatch", "refs/tags/v0.3.1"),
        ("workflow_dispatch", "refs/heads/main"),
        ("schedule", "refs/heads/main"),
        ("push", "refs/heads/test"),
        ("pull_request", "refs/pull/12/merge"),
        ("workflow_dispatch", "refs/heads/v0.3.1"),
        ("workflow_dispatch", "refs/heads/version_2"),
    ],
)
def test_the_production_backend_job_runs_exactly_when_is_prod_is_true(event: str, ref: str):
    """The release gate's proof that a run used production has to mean what IS_PROD means.

    A job-level `if:` cannot read the `functional` job's env, so the expression
    is repeated; this fails the moment the copies disagree. The dispatch on a
    *branch* named like a tag is the case the job exists for.
    """
    condition = str(_job(MAIN_WORKFLOW, "production-backend").get("if", ""))
    assert condition, "the `production-backend` job has no `if:`, so it would run on every event"
    context = {"event_name": event, "ref": ref, "ref_name": ref.rsplit("/", 1)[-1]}
    runs = _render("${{ " + condition + " }}", context) == "true"
    assert runs is _is_prod(event, ref), f"production-backend runs={runs} but IS_PROD={_is_prod(event, ref)} on {ref}"


def _jobs_filter() -> str:
    match = re.search(r"jobs_filter='([^']*)'", _script(_job(RELEASE_WORKFLOW, "functional-gate")))
    assert match, "release.yaml's functional gate no longer defines `jobs_filter='...'`"
    return match.group(1)


def _green_jobs(*pages: list) -> list:
    """Run the gate's `jobs_filter` over one run's job pages, as `gh api --paginate` prints them."""
    stdin = "".join(json.dumps({"jobs": [{"name": n, "conclusion": c} for n, c in page]}) + "\n" for page in pages)
    result = subprocess.run(
        ["jq", "-rs", _jobs_filter()], input=stdin, capture_output=True, text=True, env=_clean_env(), timeout=30
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.split("\n")[:-1]


@needs_jq
def test_the_release_gate_ignores_a_run_that_did_not_use_production():
    """`head_branch` cannot tell a dispatch on the tag `v0.3.1` from one on a branch of that name.

    The branch run used the test backend, so its green legs must not count;
    only a run whose `production-backend` job succeeded contributes its jobs.
    """
    on_a_branch = _green_jobs([("production-backend", "skipped"), ("functional (agent)", "success")])
    assert on_a_branch == [], f"a run without a successful production-backend job was counted: {on_a_branch}"

    on_the_tag = _green_jobs(
        [("functional (agent)", "success"), ("functional (model)", "failure")],
        [("production-backend", "success"), ("functional (issue)", "success")],
    )
    assert sorted(on_the_tag) == ["functional (agent)", "functional (issue)", "production-backend"], on_the_tag


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
        "the gate needs `actions: read` to list workflow runs; without it the `gh api` calls are "
        "refused and the gate cannot tell 'never ran' from 'no access'."
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
        f"these suites against {TEST_BACKEND_URL!r} on every non-production run."
    )


@pytest.mark.parametrize(
    ("backend", "expected"),
    [
        ("https://test-platform-api.aixplain.com", "https://test-models.aixplain.com/api/v2/execute"),
        ("https://platform-api.aixplain.com", "https://models.aixplain.com/api/v2/execute"),
        ("https://dev-platform-api.aixplain.com", "https://dev-models.aixplain.com/api/v2/execute"),
        ("https://staging-platform-api.aixplain.com/", "https://staging-models.aixplain.com/api/v2/execute"),
        ("https://TEST-Platform-API.aixplain.com", "https://test-models.aixplain.com/api/v2/execute"),
    ],
    ids=["test", "prod", "dev", "staging", "mixed-case"],
)
def test_the_v2_model_url_follows_the_backend(monkeypatch, backend: str, expected: str):
    """Half the suite against prod and half against test is the worst outcome.

    A developer who sets BACKEND_URL and leaves MODELS_RUN_URL alone would get
    exactly that if the model URL were defaulted independently.
    """
    monkeypatch.delenv("MODELS_RUN_URL", raising=False)
    assert _v2_conftest()._models_run_url(backend) == expected


@pytest.mark.parametrize(
    "backend",
    [
        "http://localhost:8000",
        "https://platform-api.aixplain.com.evil.example",
        "https://my-proxy.example.com",
        "https://test.platform-api.aixplain.com",
        "https://platform-api.staging.aixplain.com",
        "not a url",
    ],
    ids=["localhost", "lookalike-suffix", "other-domain", "dotted-prefix", "dotted-suffix", "garbage"],
)
def test_a_backend_with_no_known_models_host_demands_an_explicit_url(monkeypatch, backend: str):
    """Guessing turned `http://localhost:8000` into `https://localhostmodels.aixplain.com`.

    And any host that merely started with `platform-api` -- a lookalike, a
    `platform-api.staging...` -- resolved to the *production* models host
    (ENG-3683). Only the `<env>-platform-api` naming maps to a models host;
    anything else has to say which one it means.
    """
    monkeypatch.delenv("MODELS_RUN_URL", raising=False)
    with pytest.raises(ValueError, match="MODELS_RUN_URL"):
        _v2_conftest()._models_run_url(backend)


def test_an_explicit_models_url_still_works_for_a_non_standard_backend(monkeypatch):
    monkeypatch.setenv("MODELS_RUN_URL", "http://localhost:9000/whatever")
    assert _v2_conftest()._models_run_url("http://localhost:8000") == "http://localhost:9000/api/v2/execute"


@pytest.mark.parametrize(
    ("explicit", "expected"),
    [
        (
            "https://test-models.aixplain.com/api/v2/execute",
            "https://test-models.aixplain.com/api/v2/execute",
        ),
        (
            "https://test-models.aixplain.com/api/v1/execute",
            "https://test-models.aixplain.com/api/v2/execute",
        ),
    ],
    ids=["already-the-v2-endpoint", "a-leftover-v1-url"],
)
def test_an_explicit_models_url_contributes_its_host_and_not_its_path(monkeypatch, explicit: str, expected: str):
    """These suites speak the v2 execution API and nothing else.

    So the host is honoured and the path is always built here: a `/api/v1/` URL
    left in a developer's shell cannot send them to the wrong endpoint. CI
    exports the matching v2 URL directly.
    """
    monkeypatch.setenv("MODELS_RUN_URL", explicit)
    assert _v2_conftest()._models_run_url("https://test-platform-api.aixplain.com") == expected


@pytest.mark.parametrize("explicit", ["test-models.aixplain.com", "/api/v2/execute", "https://"])
def test_an_explicit_models_url_without_scheme_or_host_is_rejected(monkeypatch, explicit: str):
    """`urlparse("test-models.aixplain.com")` has no scheme and no netloc.

    Building `://` + path from it produced a URL that failed far from here, as
    an obscure connection error in the first model test.
    """
    monkeypatch.setenv("MODELS_RUN_URL", explicit)
    with pytest.raises(ValueError, match="not an absolute URL"):
        _v2_conftest()._models_run_url("https://test-platform-api.aixplain.com")


# ---------------------------------------------------------------------------
# docs/ci/required-checks.md: the doc is the input to a settings change
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("term", [SCOPE_JOB, RESULT_JOB, FUNCTIONAL_LABEL, "functional-gate", "production-backend"])
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
