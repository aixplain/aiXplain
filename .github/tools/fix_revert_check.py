#!/usr/bin/env python3
"""Check that a fix PR's tests fail when the fix is reverted (ENG-3782, layer 6).

ENG-3761 found 13 fixes whose existing test asserted the buggy behaviour, and
in its 21 manual revert-checks 3 tests caught their bug only through an
ImportError and 3 caught it only partly. This script is the automated version
of that manual check:

1. Diff ``--base`` .. ``--head`` and split the changed files into test files
   (``test_*.py`` / ``*_test.py`` under ``--tests-dir``), other test-support
   files, and source files (``*.py`` under one of ``--source-dir``). Docs, CI
   config and lock files are neither and are left at head.
2. "PR tests" are the test functions (module-level or in a class) whose source
   is new or changed between base and head, found by comparing the AST of each
   changed test file at both revisions.
3. In a scratch ``git worktree`` at head, run the PR tests (the baseline), then
   restore every source file to its base version (a file the PR added is
   deleted) and run the same tests again. Tests and test support stay at head.
4. Classify each PR test on the reverted code:

   * ``behaviour``: failed on an assertion, a wrong value, DID NOT RAISE, or a
     hang (a hang on reverted code is the bug showing, as in agents #311/#445).
   * ``api``: failed only because it imports, patches or calls a name the fix
     introduced (ImportError, ``cannot import name``, ``has no attribute`` on a
     module, ``unexpected keyword argument``), or was never collected.
   * ``passed``: still green without the fix.

The verdict is ``CATCHES`` when at least one PR test fails on behaviour,
``CATCHES_ONLY_VIA_IMPORT`` when the failures are all ``api``,
``DOES_NOT_CATCH`` when nothing fails, ``NO_TESTS`` when the PR changed no test
function, ``NO_SOURCE`` when it changed no source file, and ``BASELINE_RED``
when the PR tests do not pass at head (nothing can be concluded then).
An ImportError or a collection error never counts as catching the bug: the
ticket asks for at least one assertion failure.

The check is a report first. It exits 0 whatever the verdict unless
``--enforce`` is given, in which case only ``CATCHES``, ``NO_TESTS`` and
``NO_SOURCE`` exit 0. Make it blocking once the false-positive rate is known.

Hangs: the reverted run uses pytest-timeout's ``signal`` method when the
plugin is installed, so one hung test fails alone instead of killing the
session (the repo default ``thread`` method aborts the whole run). The whole
run is also bounded by ``--session-timeout``; on expiry each test is re-run on
its own and a test that times out by itself is recorded as a hang.

The worktree's source is put first on ``PYTHONPATH``, so an editable install
of the main checkout cannot shadow it. ``--package`` names the import the
script checks resolves inside the worktree before trusting a result.

Stdlib only and Python 3.9-safe, so the aiXplain SDK repo runs the same file.

Example (what .github/workflows/revert-check.yaml runs on a PR merge ref)::

    python3 .github/tools/fix_revert_check.py \\
        --base HEAD^1 --head HEAD \\
        --source-dir aixplain --tests-dir tests --package aixplain \\
        --python python \\
        --json revert-check.json --markdown revert-check.md
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

VERDICT_CATCHES = "CATCHES"
VERDICT_IMPORT_ONLY = "CATCHES_ONLY_VIA_IMPORT"
VERDICT_DOES_NOT_CATCH = "DOES_NOT_CATCH"
VERDICT_NO_TESTS = "NO_TESTS"
VERDICT_NO_SOURCE = "NO_SOURCE"
VERDICT_BASELINE_RED = "BASELINE_RED"

PASSING_VERDICTS = frozenset({VERDICT_CATCHES, VERDICT_NO_TESTS, VERDICT_NO_SOURCE})

OUTCOME_PASSED = "passed"
OUTCOME_BEHAVIOUR = "behaviour"
OUTCOME_API = "api"
OUTCOME_SKIPPED = "skipped"

# A failure message matching one of these is the test reaching for a name the
# fix introduced, not the test observing the bug. The mock.patch form covers a
# fixture that patches a module attribute the reverted module no longer has.
_API_FAILURE_PATTERNS = (
    re.compile(r"\b(ImportError|ModuleNotFoundError)\b"),
    re.compile(r"cannot import name "),
    re.compile(r"No module named "),
    re.compile(r"module '[\w.]+' has no attribute "),
    re.compile(r"<module '[\w.]+'.*> does not have the attribute "),
    re.compile(r"type object '\w+' has no attribute "),
    re.compile(r"got an unexpected keyword argument "),
    re.compile(r"__init__\(\) got an unexpected keyword"),
)
# pytest-timeout fails a test with "Failed: Timeout >Ns"; run_tests records a
# test that hung on its own as "Timeout: ...". Anchored, so a missing
# ``DEFAULT_TIMEOUT_CONNECT`` attribute is not read as a hang.
_HANG_PATTERN = re.compile(r"^(Failed: )?Timeout\b")


@dataclass
class ChangedFiles:
    tests: list[str] = field(default_factory=list)
    support: list[str] = field(default_factory=list)
    source_modified: list[str] = field(default_factory=list)
    source_added: list[str] = field(default_factory=list)
    source_deleted: list[str] = field(default_factory=list)

    @property
    def source(self) -> list[str]:
        return self.source_modified + self.source_added + self.source_deleted


@dataclass
class TestOutcome:
    nodeid: str
    baseline: str
    reverted: str
    detail: str = ""


@dataclass
class Report:
    base: str
    head: str
    verdict: str
    changed: ChangedFiles
    pr_tests: list[str]
    outcomes: list[TestOutcome] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for outcome in self.outcomes:
            counts[outcome.reverted] = counts.get(outcome.reverted, 0) + 1
        return counts


# --------------------------------------------------------------------------
# git helpers
# --------------------------------------------------------------------------


def _git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _show(repo: Path, rev: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{rev}:{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.stdout if proc.returncode == 0 else None


def _is_test_file(path: str, tests_dirs: Sequence[str]) -> bool:
    name = path.rsplit("/", 1)[-1]
    in_tests = any(path == d or path.startswith(d.rstrip("/") + "/") for d in tests_dirs)
    return in_tests and name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def _in_dirs(path: str, dirs: Sequence[str]) -> bool:
    return any(path.startswith(d.rstrip("/") + "/") for d in dirs)


def classify_changes(
    name_status: str,
    *,
    tests_dirs: Sequence[str],
    source_dirs: Sequence[str],
) -> ChangedFiles:
    """Split ``git diff --name-status`` output into tests, support and source.

    A rename is treated as a delete of the old path plus an add of the new
    one, so reverting it restores the old file and removes the new one.
    """
    changed = ChangedFiles()
    for line in name_status.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0][:1]
        renamed = status == "R" and len(parts) == 3
        entries = [("D", parts[1]), ("A", parts[2])] if renamed else [(status, parts[-1])]
        for kind, path in entries:
            if _is_test_file(path, tests_dirs):
                if kind != "D":
                    changed.tests.append(path)
            elif _in_dirs(path, tests_dirs):
                changed.support.append(path)
            elif path.endswith(".py") and _in_dirs(path, source_dirs):
                if kind == "A":
                    changed.source_added.append(path)
                elif kind == "D":
                    changed.source_deleted.append(path)
                else:
                    changed.source_modified.append(path)
    return changed


# --------------------------------------------------------------------------
# "PR tests": test functions new or changed between base and head
# --------------------------------------------------------------------------


def _test_functions(source: str) -> dict[str, str]:
    """Map ``Class::test_name`` / ``test_name`` to the function's source text.

    Decorators are part of the compared text, so a test whose parametrize
    cases changed counts as changed. Nested classes are walked, matching how
    pytest collects ``TestOuter::TestInner::test_x``.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    lines = source.splitlines()
    found: dict[str, str] = {}

    def text_of(node: ast.AST) -> str:
        decorators = getattr(node, "decorator_list", [])
        start = min([d.lineno for d in decorators] + [node.lineno]) - 1  # type: ignore[attr-defined]
        end = getattr(node, "end_lineno", None) or len(lines)
        return "\n".join(lines[start:end])

    def walk(body: Iterable[ast.stmt], prefix: str) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                found[prefix + node.name] = text_of(node)
            elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                walk(node.body, f"{prefix}{node.name}::")

    walk(tree.body, "")
    return found


def pr_test_ids(repo: Path, base: str, head: str, test_files: Sequence[str]) -> list[str]:
    """Node ids of the test functions added or changed by the PR."""
    ids: list[str] = []
    for path in test_files:
        head_src = _show(repo, head, path)
        if head_src is None:
            continue
        base_src = _show(repo, base, path) or ""
        before = _test_functions(base_src)
        for name, text in _test_functions(head_src).items():
            if before.get(name) != text:
                ids.append(f"{path}::{name}")
    return ids


# --------------------------------------------------------------------------
# running pytest and reading junit
# --------------------------------------------------------------------------


def _has_timeout_plugin(python: str, cwd: Path, env: dict[str, str]) -> bool:
    proc = subprocess.run(
        [python, "-c", "import pytest_timeout"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def _pytest_cmd(
    python: str,
    targets: Sequence[str],
    junit: Path,
    *,
    per_test_timeout: int | None,
    extra_args: Sequence[str],
) -> list[str]:
    cmd = [
        python,
        "-m",
        "pytest",
        *targets,
        "-p",
        "no:cacheprovider",
        "-q",
        "-o",
        "junit_family=xunit1",
        f"--junitxml={junit}",
        "--continue-on-collection-errors",
        # A repo-wide -m in addopts (e.g. "not integration") must not
        # silently deselect the PR's tests.
        "-m",
        "",
    ]
    if per_test_timeout:
        cmd += [f"--timeout={per_test_timeout}", "-o", "timeout_method=signal"]
    cmd += list(extra_args)
    return cmd


def _junit_outcomes(junit: Path) -> dict[str, tuple[str, str]]:
    """Map node-id prefix ``path::Class::name`` to (status, message).

    A parametrised test collapses to its function: it failed if any case
    failed. Status is one of ``passed``, ``failed``, ``skipped``.
    """
    results: dict[str, tuple[str, str]] = {}
    if not junit.exists():
        return results
    try:
        root = ET.parse(str(junit)).getroot()
    except ET.ParseError:
        return results
    for case in root.iter("testcase"):
        file_attr = case.get("file")
        classname = case.get("classname", "")
        name = case.get("name", "")
        base_name = name.split("[", 1)[0]
        parts = classname.split(".")
        class_parts = [p for p in parts if p[:1].isupper()]
        if file_attr:
            path = file_attr
        else:
            module_parts = [p for p in parts if not p[:1].isupper()]
            path = "/".join(module_parts) + ".py"
        nodeid = "::".join([path, *class_parts, base_name])
        status, message = OUTCOME_PASSED, ""
        for tag in ("failure", "error"):
            el = case.find(tag)
            if el is not None:
                status = "failed"
                message = (el.get("message") or "") + "\n" + (el.text or "")
                break
        else:
            if case.find("skipped") is not None:
                status = OUTCOME_SKIPPED
        previous = results.get(nodeid)
        worse = previous is not None and previous[0] != "failed" and status == "failed"
        ran = previous is not None and previous[0] == OUTCOME_SKIPPED and status == OUTCOME_PASSED
        if previous is None or worse or ran:
            results[nodeid] = (status, message)
    return results


def classify_failure(message: str) -> str:
    """``behaviour`` or ``api`` for one failed test's junit message."""
    if _HANG_PATTERN.search(message.split("\n", 1)[0]):
        return OUTCOME_BEHAVIOUR
    if any(p.search(message) for p in _API_FAILURE_PATTERNS):
        return OUTCOME_API
    return OUTCOME_BEHAVIOUR


def _lookup(results: dict[str, tuple[str, str]], nodeid: str) -> tuple[str, str] | None:
    if nodeid in results:
        return results[nodeid]
    # junit without a ``file`` attribute spells the path from the module
    # name; fall back to matching on the ``Class::name`` tail.
    tail = nodeid.split("::", 1)[1]
    stem = nodeid.split("::", 1)[0].rsplit("/", 1)[-1][:-3]
    for key, value in results.items():
        if key.endswith("::" + tail) and stem in key:
            return value
    return None


@dataclass
class RunConfig:
    python: str
    per_test_timeout: int | None
    session_timeout: int
    extra_args: Sequence[str]
    env: dict[str, str]


def run_tests(cfg: RunConfig, cwd: Path, nodeids: Sequence[str], junit: Path) -> dict[str, tuple[str, str]]:
    """Run the files holding ``nodeids``; on a session timeout re-run each test alone.

    Whole files, not node ids: pytest aborts the entire session with
    "ERROR: not found" when one requested node id cannot be collected, which is
    exactly what a test file that imports a name the fix added does on reverted
    code. Running the files lets the importable ones report while the broken
    one shows up as a collection error, and the caller reads back only the PR
    tests from the junit report.
    """
    files = sorted({nodeid.split("::", 1)[0] for nodeid in nodeids})
    cmd = _pytest_cmd(
        cfg.python,
        files,
        junit,
        per_test_timeout=cfg.per_test_timeout,
        extra_args=cfg.extra_args,
    )
    try:
        subprocess.run(cmd, cwd=str(cwd), env=cfg.env, timeout=cfg.session_timeout, check=False, capture_output=True)
        return _junit_outcomes(junit)
    except subprocess.TimeoutExpired:
        pass
    results: dict[str, tuple[str, str]] = {}
    alone_timeout = max(30, (cfg.per_test_timeout or 60) * 2)
    for i, nodeid in enumerate(nodeids):
        one = junit.with_name(f"{junit.stem}-{i}.xml")
        cmd = _pytest_cmd(
            cfg.python,
            [nodeid],
            one,
            per_test_timeout=cfg.per_test_timeout,
            extra_args=cfg.extra_args,
        )
        try:
            subprocess.run(cmd, cwd=str(cwd), env=cfg.env, timeout=alone_timeout, check=False, capture_output=True)
        except subprocess.TimeoutExpired:
            results[nodeid] = ("failed", f"Timeout: the test hung for {alone_timeout}s on its own")
            continue
        found = _lookup(_junit_outcomes(one), nodeid)
        if found is not None:
            results[nodeid] = found
    return results


# --------------------------------------------------------------------------
# the check
# --------------------------------------------------------------------------


def _scrubbed_env(
    worktree: Path, source_roots: Sequence[str], extra: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Environment for the pytest runs: no credentials, worktree source first.

    Live-gated tests must skip rather than reach a real backend, so every
    credential-looking variable is dropped (as ENG-3761's manual check did).
    ``extra`` is set afterwards: dummy values for code that refuses to import
    without one (older SDK revisions demand an API key at import time).
    """
    drop = re.compile(r"(API_KEY|_TOKEN|_SECRET|ACCESS_KEY|^AIXPLAIN|^TEAM_API|^BACKEND_URL$|^MODELS_RUN_URL$)")
    env = {k: v for k, v in os.environ.items() if not drop.search(k)}
    env.update(extra or {})
    roots = [str(worktree / r) for r in source_roots] + [str(worktree)]
    if env.get("PYTHONPATH"):
        roots.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(roots)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _check_import_root(python: str, worktree: Path, env: dict[str, str], package: str) -> str | None:
    proc = subprocess.run(
        [python, "-c", f"import {package}, os; print(os.path.realpath({package}.__file__))"],
        cwd=str(worktree),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return f"`import {package}` failed in the worktree: {proc.stderr.strip()[-400:]}"
    location = proc.stdout.strip()
    if not location.startswith(os.path.realpath(str(worktree))):
        return f"`import {package}` resolved to {location}, outside the worktree; results would test the wrong code"
    return None


def revert_source(worktree: Path, base: str, changed: ChangedFiles) -> None:
    for path in changed.source_modified + changed.source_deleted:
        _git(worktree, "checkout", base, "--", path)
    for path in changed.source_added:
        target = worktree / path
        if target.exists():
            target.unlink()


def decide(outcomes: Sequence[TestOutcome]) -> str:
    reverted = [o.reverted for o in outcomes if o.baseline == OUTCOME_PASSED]
    if OUTCOME_BEHAVIOUR in reverted:
        return VERDICT_CATCHES
    if OUTCOME_API in reverted:
        return VERDICT_IMPORT_ONLY
    return VERDICT_DOES_NOT_CATCH


def check(
    repo: Path,
    base: str,
    head: str,
    *,
    tests_dirs: Sequence[str],
    source_dirs: Sequence[str],
    package: str | None,
    cfg_python: str,
    per_test_timeout: int | None,
    session_timeout: int,
    extra_args: Sequence[str],
    workdir: Path | None = None,
    extra_env: Mapping[str, str] | None = None,
) -> Report:
    base_sha = _git(repo, "rev-parse", base).strip()
    head_sha = _git(repo, "rev-parse", head).strip()
    changed = classify_changes(
        _git(repo, "diff", "--name-status", "-M", base_sha, head_sha),
        tests_dirs=tests_dirs,
        source_dirs=source_dirs,
    )
    tests = pr_test_ids(repo, base_sha, head_sha, changed.tests)
    report = Report(base=base_sha, head=head_sha, verdict="", changed=changed, pr_tests=tests)
    if not tests:
        report.verdict = VERDICT_NO_TESTS
        return report
    if not changed.source:
        report.verdict = VERDICT_NO_SOURCE
        return report

    scratch = Path(tempfile.mkdtemp(prefix="revert-check-", dir=str(workdir) if workdir else None))
    worktree = scratch / "tree"
    _git(repo, "worktree", "add", "--detach", str(worktree), head_sha)
    try:
        env = _scrubbed_env(worktree, source_roots=["."], extra=extra_env)
        if package:
            problem = _check_import_root(cfg_python, worktree, env, package)
            if problem:
                report.notes.append(problem)
                report.verdict = VERDICT_BASELINE_RED
                return report
        timeout = per_test_timeout if _has_timeout_plugin(cfg_python, worktree, env) else None
        if per_test_timeout and timeout is None:
            report.notes.append("pytest-timeout is not installed; hangs are bounded by --session-timeout only")
        cfg = RunConfig(cfg_python, timeout, session_timeout, extra_args, env)

        baseline = run_tests(cfg, worktree, tests, scratch / "baseline.xml")
        revert_source(worktree, base_sha, changed)
        reverted = run_tests(cfg, worktree, tests, scratch / "reverted.xml")

        for nodeid in tests:
            before = _lookup(baseline, nodeid)
            after = _lookup(reverted, nodeid)
            base_status = before[0] if before else "not-collected"
            if after is None:
                rev, detail = OUTCOME_API, "not collected on reverted code (collection or import error)"
            elif after[0] == "failed":
                rev, detail = (
                    classify_failure(after[1]),
                    after[1].strip().splitlines()[0][:300] if after[1].strip() else "",
                )
            else:
                rev, detail = after[0], ""
            report.outcomes.append(TestOutcome(nodeid, base_status, rev, detail))

        green = [o for o in report.outcomes if o.baseline == OUTCOME_PASSED]
        if not green:
            report.verdict = VERDICT_BASELINE_RED
            report.notes.append("no PR test passed at head; fix the PR's tests before reading this check")
            return report
        report.verdict = decide(report.outcomes)
        return report
    finally:
        _git(repo, "worktree", "remove", "--force", str(worktree), check=False)
        shutil.rmtree(scratch, ignore_errors=True)


# --------------------------------------------------------------------------
# reporting
# --------------------------------------------------------------------------

_EXPLAIN = {
    VERDICT_CATCHES: "At least one of the PR's tests fails on an assertion when the fix is reverted.",
    VERDICT_IMPORT_ONLY: (
        "The PR's tests fail on reverted code only because they import, patch or call names the fix "
        "introduced. Add a test that reaches the fixed behaviour through an API that existed before the fix."
    ),
    VERDICT_DOES_NOT_CATCH: (
        "Every PR test still passes with the fix reverted, so none of them observes the bug. "
        "Add a test that fails on the pre-fix code."
    ),
    VERDICT_NO_TESTS: "The PR adds or changes no test function, so there is nothing to revert-check.",
    VERDICT_NO_SOURCE: "The PR changes no source file, so there is no fix to revert.",
    VERDICT_BASELINE_RED: "The PR's tests do not pass at head, so the reverted run proves nothing.",
}


def render_markdown(report: Report) -> str:
    icon = {"CATCHES": "✅", "NO_TESTS": "·", "NO_SOURCE": "·"}.get(report.verdict, "⚠️")
    lines = [
        "### Fix-PR revert check",
        "",
        f"{icon} **{report.verdict}**: {_EXPLAIN[report.verdict]}",
        "",
        f"`{report.base[:10]}..{report.head[:10]}`: {len(report.changed.source)} source file(s) reverted, "
        f"{len(report.pr_tests)} PR test function(s) checked.",
    ]
    counts = report.counts()
    if counts:
        lines += [
            "",
            "| on reverted code | tests |",
            "| --- | --- |",
        ]
        for key in (OUTCOME_BEHAVIOUR, OUTCOME_API, OUTCOME_PASSED, OUTCOME_SKIPPED):
            if counts.get(key):
                lines.append(f"| {key} | {counts[key]} |")
    still_green = [o for o in report.outcomes if o.reverted == OUTCOME_PASSED and o.baseline == OUTCOME_PASSED]
    if still_green and report.verdict != VERDICT_DOES_NOT_CATCH:
        lines += [
            "",
            "<details><summary>PR tests that still pass without the fix "
            f"({len(still_green)}): guards, or tests that do not observe the bug</summary>",
            "",
        ]
        lines += [f"- `{o.nodeid}`" for o in still_green]
        lines += ["", "</details>"]
    api_only = [o for o in report.outcomes if o.reverted == OUTCOME_API]
    if api_only:
        lines += ["", f"<details><summary>Failed only on a missing name ({len(api_only)})</summary>", ""]
        lines += [f"- `{o.nodeid}`: {o.detail}" for o in api_only]
        lines += ["", "</details>"]
    for note in report.notes:
        lines += ["", f"> {note}"]
    lines += [
        "",
        "_Non-blocking report (ENG-3782). See docs/testing-layers.md#a-fix-pr-must-include-a-test-that-fails-on-the-pre-fix-code._",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--repo", default=".", help="repository root (default: .)")
    parser.add_argument("--base", required=True, help="revision without the fix (e.g. HEAD^1 on a PR merge ref)")
    parser.add_argument("--head", default="HEAD", help="revision with the fix (default: HEAD)")
    parser.add_argument("--source-dir", action="append", required=True, help="source directory to revert (repeatable)")
    parser.add_argument(
        "--tests-dir", action="append", default=None, help="tests directory (repeatable, default tests)"
    )
    parser.add_argument("--package", help="import name that must resolve inside the worktree")
    parser.add_argument("--python", default=sys.executable, help="interpreter with the test dependencies installed")
    parser.add_argument(
        "--per-test-timeout", type=int, default=60, help="pytest-timeout seconds per test (signal method)"
    )
    parser.add_argument("--session-timeout", type=int, default=1200, help="seconds for one whole pytest run")
    parser.add_argument("--pytest-arg", action="append", default=[], help="extra pytest argument (repeatable)")
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="set in the pytest environment after credentials are dropped; for dummy values only (repeatable)",
    )
    parser.add_argument("--json", type=Path, help="write the report as JSON here")
    parser.add_argument("--markdown", type=Path, help="write the Markdown summary here")
    parser.add_argument(
        "--enforce", action="store_true", help="exit 1 unless the verdict is CATCHES/NO_TESTS/NO_SOURCE"
    )
    args = parser.parse_args(argv)
    if any("=" not in item for item in args.env):
        parser.error("--env takes NAME=VALUE")
    # pytest runs inside the worktree, so a relative interpreter path such as
    # .venv/bin/python must be pinned to the checkout it was written against.
    python = str(Path(args.python).absolute()) if os.sep in args.python else args.python

    report = check(
        Path(args.repo).resolve(),
        args.base,
        args.head,
        tests_dirs=args.tests_dir or ["tests"],
        source_dirs=args.source_dir,
        package=args.package,
        cfg_python=python,
        per_test_timeout=args.per_test_timeout,
        session_timeout=args.session_timeout,
        extra_args=args.pytest_arg,
        extra_env=dict(item.split("=", 1) for item in args.env),
    )
    markdown = render_markdown(report)
    if args.markdown:
        args.markdown.write_text(markdown, encoding="utf-8")
    if args.json:
        payload = asdict(report)
        payload["counts"] = report.counts()
        args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    sys.stdout.write(markdown)
    if args.enforce and report.verdict not in PASSING_VERDICTS:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
