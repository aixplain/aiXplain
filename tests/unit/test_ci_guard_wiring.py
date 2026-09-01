"""End-to-end wiring test for the execution guard (ENG-3544).

`tests/unit/test_ci_guards.py` covers the pure predicate and the ledger. Neither
proves the piece the acceptance criterion actually rests on: that the hooks in
`tests/conftest.py` turn a dishonestly-green *process* into a red one. That
depends on pytest internals which no pure function can exercise --
`pytest_sessionfinish` must be called with the pre-return exit status, and
assigning `session.exitstatus` there must still reach `wrap_session`'s return.
A rename, a wrong hook signature, or a pytest upgrade that snapshots the exit
status earlier would leave every unit test above passing while CI went back to
reporting green on a suite that ran nothing.

So these tests spawn a real pytest process over a throwaway tree whose conftest
re-exports the real hook functions, and assert on the exit code.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Re-exports the *real* hooks rather than copies of them: importing the names
# into a conftest namespace is enough for pytest to register them, so the code
# under test is the code that ships.
CONFTEST = """
import sys

sys.path.insert(0, {repo_root!r})

from tests.conftest import (  # noqa: F401
    pytest_runtest_logreport,
    pytest_sessionfinish,
    pytest_sessionstart,
)
"""

ALL_SKIPPED = """
import pytest

@pytest.mark.skip(reason="the ENG-3544 defect, in miniature")
def test_one():
    assert False

@pytest.mark.skip(reason="the ENG-3544 defect, in miniature")
def test_two():
    assert False
"""

ONE_PASSES = """
import pytest

@pytest.mark.skip(reason="only this one is skipped")
def test_one():
    assert False

def test_two():
    assert True
"""

ONE_FAILS = """
def test_one():
    assert False, "a genuine failure"
"""

NOTHING_COLLECTED = """
# No test functions at all: pytest exits 5.
def helper():
    return True
"""

MESSAGE_MARKER = "CI integrity failure (ENG-3544)"


def _run(tmp_path: Path, source: str, flag: str = None, *extra_args: str):
    """Run pytest over a one-file tree and return the CompletedProcess."""
    (tmp_path / "conftest.py").write_text(CONFTEST.format(repo_root=str(REPO_ROOT)))
    (tmp_path / "test_sample.py").write_text(source)

    env = os.environ.copy()
    env.pop("AIXPLAIN_REQUIRE_EXECUTED_TESTS", None)
    if flag is not None:
        env["AIXPLAIN_REQUIRE_EXECUTED_TESTS"] = flag

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(tmp_path),
            "-q",
            # Binds a socket at startup, which this does not need and which is
            # blocked in some sandboxed environments.
            "-p",
            "no:rerunfailures",
            *extra_args,
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("flag", ["1", "true", "on"])
def test_all_skipped_session_fails_when_the_flag_is_set(tmp_path, flag):
    """The defect itself: everything skipped, pytest would exit 0."""
    result = _run(tmp_path, ALL_SKIPPED, flag)

    output = result.stdout + result.stderr
    assert result.returncode == 1, f"expected exit 1, got {result.returncode}:\n{output[-4000:]}"
    assert MESSAGE_MARKER in output, f"guard fired without explaining itself:\n{output[-4000:]}"
    assert "2 test(s) collected, 0 executed" in output, output[-4000:]


@pytest.mark.parametrize("flag", [None, "0", "false", ""])
def test_all_skipped_session_still_passes_when_the_flag_is_absent(tmp_path, flag):
    """Opt-in: a laptop with no credentials must behave exactly as before."""
    result = _run(tmp_path, ALL_SKIPPED, flag)

    output = result.stdout + result.stderr
    assert result.returncode == 0, f"expected exit 0, got {result.returncode}:\n{output[-4000:]}"
    assert MESSAGE_MARKER not in output, output[-4000:]


def test_session_that_ran_one_body_passes(tmp_path):
    """A single executed test is enough; the guard is about zero, not about all."""
    result = _run(tmp_path, ONE_PASSES, "1")

    output = result.stdout + result.stderr
    assert result.returncode == 0, f"expected exit 0, got {result.returncode}:\n{output[-4000:]}"
    assert MESSAGE_MARKER not in output, output[-4000:]


def test_empty_session_fails(tmp_path):
    """Collecting nothing (exit 5) is the same lie with a different exit code."""
    result = _run(tmp_path, NOTHING_COLLECTED, "1")

    output = result.stdout + result.stderr
    assert result.returncode == 1, f"expected exit 1, got {result.returncode}:\n{output[-4000:]}"
    assert MESSAGE_MARKER in output, output[-4000:]


def test_a_real_failure_is_reported_as_itself(tmp_path):
    """The guard must never overwrite a genuine failure with its own message."""
    result = _run(tmp_path, ONE_FAILS, "1")

    output = result.stdout + result.stderr
    assert result.returncode == 1, f"expected exit 1, got {result.returncode}:\n{output[-4000:]}"
    assert MESSAGE_MARKER not in output, f"the guard buried the real error:\n{output[-4000:]}"
    assert "a genuine failure" in output, output[-4000:]


def test_collect_only_is_exempt(tmp_path):
    """`--collect-only` runs no body by design.

    The workflow exports the opt-in flag for every job, and
    tests/unit/utils/test_credential_free_collection.py spawns a `--collect-only`
    run with an inherited environment, so a guard that fired here would fail CI.
    """
    result = _run(tmp_path, ALL_SKIPPED, "1", "--collect-only")

    output = result.stdout + result.stderr
    assert result.returncode == 0, f"expected exit 0, got {result.returncode}:\n{output[-4000:]}"
    assert MESSAGE_MARKER not in output, output[-4000:]
