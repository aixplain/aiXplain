"""Tests for ``.github/tools/fix_revert_check.py`` (ENG-3782, layer 6).

The pure helpers are tested directly. The verdicts are tested end to end
against a throwaway git repository whose "fix" commits reproduce the four
shapes ENG-3761 found by hand: a test that catches its bug, a test that only
fails because it imports a name the fix added, a test that passes with or
without the fix, and reverted code that hangs.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / ".github" / "tools" / "fix_revert_check.py"
_spec = importlib.util.spec_from_file_location("fix_revert_check", _SCRIPT)
assert _spec is not None and _spec.loader is not None
frc = importlib.util.module_from_spec(_spec)
sys.modules["fix_revert_check"] = frc
_spec.loader.exec_module(frc)


# ---------------------------------------------------------------------------
# classify_changes
# ---------------------------------------------------------------------------


def test_classify_changes_splits_tests_support_and_source() -> None:
    name_status = "\n".join(
        [
            "M\tpkg/core.py",
            "A\tpkg/new_module.py",
            "D\tpkg/old_module.py",
            "M\ttests/unit/test_core.py",
            "A\ttests/unit/core_test.py",
            "M\ttests/unit/conftest.py",
            "M\tdocs/guide.md",
            "M\t.github/workflows/ci.yml",
            "M\tpkg/data.json",
        ]
    )
    changed = frc.classify_changes(name_status, tests_dirs=["tests"], source_dirs=["pkg"])
    assert changed.tests == ["tests/unit/test_core.py", "tests/unit/core_test.py"]
    assert changed.support == ["tests/unit/conftest.py"]
    assert changed.source_modified == ["pkg/core.py"]
    assert changed.source_added == ["pkg/new_module.py"]
    assert changed.source_deleted == ["pkg/old_module.py"]


def test_classify_changes_turns_a_rename_into_delete_plus_add() -> None:
    changed = frc.classify_changes("R087\tpkg/a.py\tpkg/b.py", tests_dirs=["tests"], source_dirs=["pkg"])
    assert changed.source_deleted == ["pkg/a.py"]
    assert changed.source_added == ["pkg/b.py"]


def test_classify_changes_ignores_a_deleted_test_file() -> None:
    changed = frc.classify_changes("D\ttests/test_gone.py", tests_dirs=["tests"], source_dirs=["pkg"])
    assert changed.tests == []


# ---------------------------------------------------------------------------
# _test_functions: which test functions a file defines, with their source
# ---------------------------------------------------------------------------


def test_test_functions_include_nested_classes_and_decorators() -> None:
    source = dedent(
        """
        import pytest

        def helper():
            return 1

        @pytest.mark.parametrize("x", [1, 2])
        def test_top(x):
            assert x

        class TestOuter:
            def test_a(self):
                assert True

            class TestInner:
                async def test_b(self):
                    assert True

        class Helper:
            def test_not_collected(self):
                assert True
        """
    )
    found = frc._test_functions(source)
    assert set(found) == {"test_top", "TestOuter::test_a", "TestOuter::TestInner::test_b"}
    assert "parametrize" in found["test_top"]


def test_a_changed_decorator_counts_as_a_changed_test() -> None:
    before = frc._test_functions('import pytest\n@pytest.mark.parametrize("x", [1])\ndef test_x(x):\n    assert x\n')
    after = frc._test_functions('import pytest\n@pytest.mark.parametrize("x", [1, 2])\ndef test_x(x):\n    assert x\n')
    assert before["test_x"] != after["test_x"]


def test_unparseable_source_has_no_tests() -> None:
    assert frc._test_functions("def test_x(:\n") == {}


# ---------------------------------------------------------------------------
# classify_failure: assertion vs. a name the fix introduced
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "ImportError: cannot import name 'close_run_stream' from 'pkg.mod'",
        "ModuleNotFoundError: No module named 'pkg.session_merge'",
        "AttributeError: module 'pkg.client' has no attribute 'DEFAULT_TIMEOUT_CONNECT'",
        "AttributeError: <module 'pkg.agent_progress' from '/x.py'> does not have the attribute '_stdout_is_tty'",
        "TypeError: __init__() got an unexpected keyword argument 'model_entry_point'",
        "TypeError: run() got an unexpected keyword argument 'timeout'",
    ],
)
def test_missing_name_failures_are_api(message: str) -> None:
    assert frc.classify_failure(message) == frc.OUTCOME_API


@pytest.mark.parametrize(
    "message",
    [
        "AssertionError: assert 0 == 4",
        "Failed: DID NOT RAISE <class 'ValueError'>",
        "TypeError: 'NoneType' object is not subscriptable",
        "AttributeError: 'NoneType' object has no attribute 'status'",
        "Failed: Timeout >2.0s",
    ],
)
def test_wrong_behaviour_failures_are_behaviour(message: str) -> None:
    assert frc.classify_failure(message) == frc.OUTCOME_BEHAVIOUR


def test_decide_ignores_tests_that_were_red_at_head() -> None:
    outcomes = [
        frc.TestOutcome("t.py::a", baseline="failed", reverted=frc.OUTCOME_BEHAVIOUR),
        frc.TestOutcome("t.py::b", baseline=frc.OUTCOME_PASSED, reverted=frc.OUTCOME_API),
    ]
    assert frc.decide(outcomes) == frc.VERDICT_IMPORT_ONLY


def test_scrubbed_env_drops_credentials_and_then_sets_the_dummies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TEAM_API_KEY", "live-key")
    monkeypatch.setenv("GITHUB_TOKEN", "live-token")
    env = frc._scrubbed_env(tmp_path, ["."], extra={"TEAM_API_KEY": "dummy"})
    assert env["TEAM_API_KEY"] == "dummy"
    assert "GITHUB_TOKEN" not in env
    assert env["PYTHONPATH"].split(os.pathsep)[0] == str(tmp_path / ".")


# ---------------------------------------------------------------------------
# end to end against a throwaway repository
# ---------------------------------------------------------------------------

_GIT_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def _git(repo: Path, *args: str) -> str:
    env = {**os.environ, **_GIT_ENV}
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env
    ).stdout.strip()


def _write(repo: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(text))


def _commit(repo: Path, files: dict[str, str], message: str) -> str:
    _write(repo, files)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def toy_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "toy"
    repo.mkdir()
    _git(repo, "init", "-q")
    _commit(
        repo,
        {
            "pytest.ini": "[pytest]\n",
            "toy/__init__.py": "",
            "toy/calc.py": """
                def add(a, b):
                    return a - b
            """,
            "tests/test_existing.py": """
                from toy.calc import add

                def test_zero():
                    assert add(0, 0) == 0
            """,
        },
        "base: add is buggy",
    )
    return repo


def _run(repo: Path, head: str, *, per_test_timeout: int = 20) -> frc.Report:
    return frc.check(
        repo,
        f"{head}^1",
        head,
        tests_dirs=["tests"],
        source_dirs=["toy"],
        package="toy",
        cfg_python=sys.executable,
        per_test_timeout=per_test_timeout,
        session_timeout=120,
        extra_args=["-p", "no:randomly"],
    )


def test_a_test_that_observes_the_bug_catches(toy_repo: Path) -> None:
    head = _commit(
        toy_repo,
        {
            "toy/calc.py": "def add(a, b):\n    return a + b\n",
            "tests/test_fix.py": "from toy.calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n",
        },
        "fix: add",
    )
    report = _run(toy_repo, head)
    assert report.verdict == frc.VERDICT_CATCHES
    assert report.pr_tests == ["tests/test_fix.py::test_add"]
    assert [o.reverted for o in report.outcomes] == [frc.OUTCOME_BEHAVIOUR]


def test_a_test_that_only_imports_the_new_name_is_import_only(toy_repo: Path) -> None:
    head = _commit(
        toy_repo,
        {
            "toy/calc.py": "def add(a, b):\n    return a + b\n\nPRECISION = 2\n",
            "tests/test_fix.py": "from toy.calc import PRECISION, add\n\ndef test_add():\n    assert add(2, 2) == 4\n",
        },
        "fix: add, with a new constant the test imports",
    )
    report = _run(toy_repo, head)
    assert report.verdict == frc.VERDICT_IMPORT_ONLY
    assert report.outcomes[0].reverted == frc.OUTCOME_API


def test_an_uncollectable_file_does_not_hide_the_other_files(toy_repo: Path) -> None:
    # agents #318: one PR test file imports a module the fix added, so on
    # reverted code it fails collection; the other file must still report.
    head = _commit(
        toy_repo,
        {
            "toy/calc.py": "def add(a, b):\n    return a + b\n",
            "toy/merge.py": "def merge(a, b):\n    return a + b\n",
            "tests/test_merge.py": "from toy.merge import merge\n\ndef test_merge():\n    assert merge([1], [2]) == [1, 2]\n",
            "tests/test_fix.py": "from toy.calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n",
        },
        "fix: add, plus a new merge module",
    )
    report = _run(toy_repo, head)
    by_id = {o.nodeid: o.reverted for o in report.outcomes}
    assert by_id == {
        "tests/test_fix.py::test_add": frc.OUTCOME_BEHAVIOUR,
        "tests/test_merge.py::test_merge": frc.OUTCOME_API,
    }
    assert report.verdict == frc.VERDICT_CATCHES


def test_a_test_that_passes_without_the_fix_does_not_catch(toy_repo: Path) -> None:
    head = _commit(
        toy_repo,
        {
            "toy/calc.py": "def add(a, b):\n    return a + b\n",
            "tests/test_existing.py": "from toy.calc import add\n\ndef test_zero():\n    assert add(0, 0) == 0 + 0\n",
        },
        "fix: add, but the test only checks zero",
    )
    report = _run(toy_repo, head)
    assert report.verdict == frc.VERDICT_DOES_NOT_CATCH
    assert report.outcomes[0].reverted == frc.OUTCOME_PASSED


def test_reverted_code_that_hangs_is_a_behaviour_failure(toy_repo: Path) -> None:
    pytest.importorskip("pytest_timeout")
    _commit(toy_repo, {"toy/calc.py": "def add(a, b):\n    while True:\n        pass\n"}, "regress: add hangs")
    head = _commit(
        toy_repo,
        {
            "toy/calc.py": "def add(a, b):\n    return a + b\n",
            "tests/test_fix.py": "from toy.calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n",
        },
        "fix: add no longer hangs",
    )
    report = _run(toy_repo, head, per_test_timeout=2)
    assert report.verdict == frc.VERDICT_CATCHES
    assert "Timeout" in report.outcomes[0].detail


def test_a_source_only_change_has_no_tests(toy_repo: Path) -> None:
    head = _commit(toy_repo, {"toy/calc.py": "def add(a, b):\n    return a + b\n"}, "fix: add, untested")
    report = _run(toy_repo, head)
    assert report.verdict == frc.VERDICT_NO_TESTS
    assert report.outcomes == []


def test_the_worktree_is_removed_and_the_checkout_untouched(toy_repo: Path) -> None:
    head = _commit(
        toy_repo,
        {
            "toy/calc.py": "def add(a, b):\n    return a + b\n",
            "tests/test_fix.py": "from toy.calc import add\n\ndef test_add():\n    assert add(2, 2) == 4\n",
        },
        "fix: add",
    )
    _run(toy_repo, head)
    assert _git(toy_repo, "worktree", "list").count("\n") == 0
    assert _git(toy_repo, "status", "--porcelain") == ""
    assert "a + b" in (toy_repo / "toy" / "calc.py").read_text()


def test_markdown_names_the_verdict_and_lists_still_green_tests() -> None:
    report = frc.Report(
        base="a" * 40,
        head="b" * 40,
        verdict=frc.VERDICT_CATCHES,
        changed=frc.ChangedFiles(source_modified=["pkg/x.py"]),
        pr_tests=["t.py::a", "t.py::b"],
        outcomes=[
            frc.TestOutcome("t.py::a", frc.OUTCOME_PASSED, frc.OUTCOME_BEHAVIOUR, "AssertionError"),
            frc.TestOutcome("t.py::b", frc.OUTCOME_PASSED, frc.OUTCOME_PASSED),
        ],
    )
    text = frc.render_markdown(report)
    assert "**CATCHES**" in text
    assert "`t.py::b`" in text
    assert "| behaviour | 1 |" in text


def test_enforce_exits_non_zero_only_for_failing_verdicts(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_check(*_a: object, **_k: object) -> frc.Report:
        return frc.Report("a" * 40, "b" * 40, frc.VERDICT_DOES_NOT_CATCH, frc.ChangedFiles(), ["t.py::a"])

    monkeypatch.setattr(frc, "check", fake_check)
    assert frc.main(["--base", "x", "--source-dir", "pkg"]) == 0
    assert frc.main(["--base", "x", "--source-dir", "pkg", "--enforce"]) == 1
