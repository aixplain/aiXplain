"""Unit tests for the session execution guard (ENG-3544).

The guard's whole job is to turn a dishonestly-green session into a red one, so
its own logic has to be exercised without needing a dishonestly-green session:
these tests drive the pure predicate and the ledger directly.
"""

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.ci_guards import (
    EXIT_NO_TESTS_COLLECTED,
    NON_EXECUTING_OPTIONS,
    REQUIRE_EXECUTED_ENV,
    ExecutionLedger,
    is_non_executing_session,
    no_executed_tests_message,
    should_fail_for_no_executed_tests,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class _Report:
    """Minimal stand-in for a pytest TestReport."""

    def __init__(self, when, outcome, wasxfail=None):
        self.when = when
        self.outcome = outcome
        if wasxfail is not None:
            self.wasxfail = wasxfail


@pytest.mark.parametrize(
    ("flag", "executed", "exitstatus", "expected"),
    [
        # Off by default: local runs and `pytest -k ...` must not be blocked.
        (None, 0, 0, False),
        ("0", 0, 0, False),
        ("false", 0, 0, False),
        ("", 0, 0, False),
        # The defect itself: everything skipped, pytest exits 0.
        ("1", 0, 0, True),
        ("true", 0, 0, True),
        ("YES", 0, 0, True),
        ("on", 0, 0, True),
        # Nothing collected at all is the same lie with a different exit code.
        ("1", 0, EXIT_NO_TESTS_COLLECTED, True),
        # A real failure is never rewritten -- that would bury the actual error.
        ("1", 0, 1, False),
        ("1", 0, 2, False),
        ("1", 0, 3, False),
        # Something ran: nothing to complain about.
        ("1", 1, 0, False),
        ("1", 42, 0, False),
        ("1", 1, 1, False),
    ],
)
def test_should_fail_for_no_executed_tests(flag, executed, exitstatus, expected):
    env = {} if flag is None else {REQUIRE_EXECUTED_ENV: flag}
    assert should_fail_for_no_executed_tests(executed, exitstatus, env=env) is expected


def test_ledger_counts_only_test_bodies_that_ran():
    ledger = ExecutionLedger()

    ledger.record(_Report("setup", "passed"))  # every test emits this
    ledger.record(_Report("teardown", "passed"))
    ledger.record(_Report("setup", "skipped"))  # a plain skip stops here
    assert ledger.executed == 0

    ledger.record(_Report("call", "passed"))
    ledger.record(_Report("call", "failed"))
    assert ledger.executed == 2

    # A call-phase skip means `pytest.skip()` was hit part-way through the body;
    # the body did not complete, so it does not count as executed.
    ledger.record(_Report("call", "skipped"))
    assert ledger.executed == 2

    # An xfail is reported as skipped at call time, but the body did run.
    ledger.record(_Report("call", "skipped", wasxfail="expected to fail"))
    assert ledger.executed == 3


def test_reset_clears_a_previous_sessions_tally():
    """A second in-process session must not inherit the first one's count."""
    ledger = ExecutionLedger()
    ledger.record(_Report("call", "passed"))
    assert ledger.executed == 1

    ledger.reset()
    assert ledger.executed == 0


def test_ledger_tolerates_reports_without_a_phase():
    """Collection-error reports have no `when`; they must not crash the hook."""
    ledger = ExecutionLedger()
    ledger.record(object())
    assert ledger.executed == 0


def test_message_names_the_counts_and_the_escape_hatch():
    message = no_executed_tests_message(35)
    assert "35 test(s) collected, 0 executed" in message
    assert REQUIRE_EXECUTED_ENV in message
    assert "ENG-3544" in message


@pytest.mark.parametrize("option", NON_EXECUTING_OPTIONS)
def test_non_executing_session_detected_for_each_mode(option):
    config = SimpleNamespace(option=SimpleNamespace(**{name: name == option for name in NON_EXECUTING_OPTIONS}))
    assert is_non_executing_session(config) is True


def test_an_ordinary_run_is_an_executing_session():
    config = SimpleNamespace(option=SimpleNamespace(**{name: False for name in NON_EXECUTING_OPTIONS}))
    assert is_non_executing_session(config) is False


def test_missing_options_do_not_trip_the_exemption():
    """An older pytest without one of these options must still be guarded."""
    assert is_non_executing_session(SimpleNamespace(option=SimpleNamespace())) is False


def test_collect_only_still_exits_zero_under_the_guard():
    """End-to-end: `--collect-only` executes nothing, and that is not a failure.

    `tests/unit/test_ci_guard_wiring.py` proves the same exemption over a
    throwaway tree whose conftest re-exports the hooks; this one runs against a
    real path in this repo, so it additionally covers conftest *discovery* --
    the hooks being found for `tests/...` at all, which the re-export shim
    assumes rather than checks.

    Without the exemption this exits 1, which fails
    `tests/unit/utils/test_credential_free_collection.py` in CI (where the
    workflow exports the flag) while passing on any developer machine.
    """
    env = os.environ.copy()
    env[REQUIRE_EXECUTED_ENV] = "1"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "--collect-only", "-q", "-p", "no:rerunfailures"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, f"exit code {result.returncode}:\n{output[-4000:]}"
    assert "CI integrity failure" not in output, output[-4000:]
