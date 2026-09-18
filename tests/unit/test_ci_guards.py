"""Unit tests for the session execution guards (ENG-3544, ENG-3684).

The guards' whole job is to turn a dishonestly-green session into a red one, so
their own logic has to be exercised without needing a dishonestly-green session:
these tests drive the pure predicates and the ledger directly.
"""

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.ci_guards import (
    DEFAULT_MIN_EXECUTED_RATIO,
    EXIT_NO_TESTS_COLLECTED,
    MIN_EXECUTED_RATIO_ENV,
    NON_EXECUTING_OPTIONS,
    REQUIRE_EXECUTED_ENV,
    ExecutionLedger,
    is_non_executing_session,
    low_execution_ratio_message,
    min_executed_ratio,
    module_of,
    no_executed_tests_message,
    should_fail_for_low_execution_ratio,
    should_fail_for_no_executed_tests,
    skip_reason,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class _Report:
    """Minimal stand-in for a pytest TestReport."""

    def __init__(self, when, outcome, wasxfail=None, nodeid="tests/sample_test.py::test_x", longrepr=None):
        self.when = when
        self.outcome = outcome
        self.nodeid = nodeid
        self.longrepr = longrepr
        if wasxfail is not None:
            self.wasxfail = wasxfail


class _Item:
    """Minimal stand-in for a collected pytest Item."""

    def __init__(self, nodeid):
        self.nodeid = nodeid


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
    """A second in-process session must not inherit the first one's counts."""
    ledger = ExecutionLedger()
    ledger.record_collected([_Item("tests/a_test.py::test_x")])
    ledger.record(_Report("call", "passed", nodeid="tests/a_test.py::test_x"))
    ledger.record(_Report("setup", "skipped", nodeid="tests/a_test.py::test_y"))
    assert ledger.executed == 1
    assert ledger.collected == 1

    ledger.reset()
    assert ledger.executed == 0
    assert ledger.collected == 0
    assert ledger.executed_by_module == {}
    assert ledger.collected_by_module == {}
    assert ledger.skipped == []


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


# ---------------------------------------------------------------------------
# ENG-3684: the ratio floor.
#
# `tests/functional/v2` executed 12 of 195 collected tests and exited 0, because
# the ENG-3544 floor above only asks for one. These cover the proportional floor
# and the per-module/skip-reason bookkeeping the failure message rests on.
# ---------------------------------------------------------------------------

ON = {REQUIRE_EXECUTED_ENV: "1"}


def _env(**overrides):
    env = dict(ON)
    env.update(overrides)
    return env


@pytest.mark.parametrize(
    ("executed", "collected", "exitstatus", "env", "expected"),
    [
        # Off by default: the ratio floor shares the ENG-3544 opt-in.
        (12, 195, 0, {}, False),
        (12, 195, 0, {REQUIRE_EXECUTED_ENV: "0"}, False),
        # The defect itself: 12 of 195 clears "at least one ran" and must not.
        (12, 195, 0, ON, True),
        # A leg carrying a few credential-gated skips stays green at 0.8.
        (180, 195, 0, ON, False),
        # Exactly at the floor passes; a hair under does not.
        (80, 100, 0, ON, False),
        (79, 100, 0, ON, True),
        # A red session keeps its own failure rather than being rewritten.
        (12, 195, 1, ON, False),
        (12, 195, 2, ON, False),
        # Nothing collected belongs to the ENG-3544 guard; 0/0 is not a shortfall.
        (0, 0, EXIT_NO_TESTS_COLLECTED, ON, False),
        (0, 0, 0, ON, False),
        # An explicit 0 floor switches the ratio check off and leaves ENG-3544.
        (12, 195, 0, _env(**{MIN_EXECUTED_RATIO_ENV: "0"}), False),
        # A raised floor rejects what the default would have allowed.
        (95, 100, 0, _env(**{MIN_EXECUTED_RATIO_ENV: "1"}), True),
        # A lowered floor accepts what the default rejects.
        (12, 195, 0, _env(**{MIN_EXECUTED_RATIO_ENV: "0.05"}), False),
    ],
)
def test_should_fail_for_low_execution_ratio(executed, collected, exitstatus, env, expected):
    assert should_fail_for_low_execution_ratio(executed, collected, exitstatus, env=env) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, DEFAULT_MIN_EXECUTED_RATIO),
        ("", DEFAULT_MIN_EXECUTED_RATIO),
        ("   ", DEFAULT_MIN_EXECUTED_RATIO),
        ("0", 0.0),
        ("1", 1.0),
        ("0.5", 0.5),
        (" 0.95 ", 0.95),
    ],
)
def test_min_executed_ratio_parses_the_env_var(raw, expected):
    env = {} if raw is None else {MIN_EXECUTED_RATIO_ENV: raw}
    assert min_executed_ratio(env) == expected


@pytest.mark.parametrize("raw", ["eighty percent", "80%", "-0.1", "1.5", "nan"])
def test_an_unusable_floor_raises_rather_than_falling_back(raw):
    """Silently using the default would make the workflow claim a floor it does not enforce."""
    with pytest.raises(ValueError, match=MIN_EXECUTED_RATIO_ENV):
        min_executed_ratio({MIN_EXECUTED_RATIO_ENV: raw})


def test_the_ratio_guard_surfaces_a_bad_floor_instead_of_standing_down():
    """The predicate must not swallow the misconfiguration into a quiet False."""
    with pytest.raises(ValueError):
        should_fail_for_low_execution_ratio(1, 10, 0, env=_env(**{MIN_EXECUTED_RATIO_ENV: "later"}))


def test_ledger_counts_collected_items_per_module():
    ledger = ExecutionLedger()
    ledger.record_collected(
        [
            _Item("tests/functional/v2/test_tool.py::test_a"),
            _Item("tests/functional/v2/test_tool.py::test_b"),
            _Item("tests/functional/v2/test_model.py::test_c"),
        ]
    )

    assert ledger.collected == 3
    assert ledger.collected_by_module == {
        "tests/functional/v2/test_tool.py": 2,
        "tests/functional/v2/test_model.py": 1,
    }


def test_ledger_records_skips_from_setup_and_from_the_body():
    """A fixture skip lands at setup, an inline `pytest.skip()` at call."""
    ledger = ExecutionLedger()
    ledger.record(
        _Report(
            "setup",
            "skipped",
            nodeid="tests/functional/v2/test_actions_inputs.py::test_a",
            longrepr=("test_actions_inputs.py", 46, "Skipped: No tool with actions found"),
        )
    )
    ledger.record(
        _Report(
            "call",
            "skipped",
            nodeid="tests/functional/v2/test_model.py::test_b",
            longrepr=("test_model.py", 317, "Skipped: Model does not support streaming"),
        )
    )

    assert [(entry.nodeid, entry.reason) for entry in ledger.skipped] == [
        ("tests/functional/v2/test_actions_inputs.py::test_a", "No tool with actions found"),
        ("tests/functional/v2/test_model.py::test_b", "Model does not support streaming"),
    ]


def test_an_xfail_is_not_recorded_as_a_skip():
    """The body ran; counting it as a skip would misreport the leg."""
    ledger = ExecutionLedger()
    ledger.record(_Report("call", "skipped", wasxfail="expected to fail"))

    assert ledger.skipped == []
    assert ledger.executed == 1


def test_a_skip_is_listed_once_even_if_reported_twice():
    """pytest-rerunfailures can re-report the same nodeid; the summary lists it once."""
    ledger = ExecutionLedger()
    for _ in range(3):
        ledger.record(_Report("setup", "skipped", nodeid="tests/a_test.py::test_x"))

    assert len(ledger.skipped) == 1


@pytest.mark.parametrize(
    ("longrepr", "expected"),
    [
        (("f.py", 3, "Skipped: No tool with actions found"), "No tool with actions found"),
        (("f.py", 3, "No tool with actions found"), "No tool with actions found"),
        ("Skipped: raw string form", "raw string form"),
        (None, "no reason given"),
    ],
)
def test_skip_reason_extraction(longrepr, expected):
    assert skip_reason(_Report("setup", "skipped", longrepr=longrepr)) == expected


def test_executed_ratio_treats_an_empty_collection_as_complete():
    """0/0 must not read as a shortfall -- `pytest -k <no match>` is not a lie."""
    assert ExecutionLedger().executed_ratio() == 1.0


@pytest.mark.parametrize(
    ("nodeid", "expected"),
    [
        ("tests/a_test.py::TestX::test_y[param]", "tests/a_test.py"),
        ("tests/a_test.py", "tests/a_test.py"),
    ],
)
def test_module_of(nodeid, expected):
    assert module_of(nodeid) == expected


def _v2_shaped_ledger():
    """A ledger in the shape this task exists for: one dead module, one healthy."""
    ledger = ExecutionLedger()
    ledger.record_collected(
        [_Item(f"tests/functional/v2/test_actions_inputs.py::test_{i}") for i in range(4)]
        + [_Item("tests/functional/v2/test_agent.py::test_ok")]
    )
    for i in range(4):
        ledger.record(
            _Report(
                "setup",
                "skipped",
                nodeid=f"tests/functional/v2/test_actions_inputs.py::test_{i}",
                longrepr=("test_actions_inputs.py", 46, "Skipped: No tool with actions found"),
            )
        )
    ledger.record(_Report("call", "passed", nodeid="tests/functional/v2/test_agent.py::test_ok"))
    return ledger


def test_ratio_message_names_the_counts_the_modules_and_the_reasons():
    message = low_execution_ratio_message(_v2_shaped_ledger(), 0.8)

    assert "ENG-3684" in message
    assert "1 of 5 collected test(s) executed (20%), below the 80% floor" in message
    # The dead module is flagged; the healthy one is listed without a marker.
    assert "! tests/functional/v2/test_actions_inputs.py: 0/4" in message
    assert "  tests/functional/v2/test_agent.py: 1/1" in message
    # The reason is the actionable part: it names the fixture that went missing.
    assert "test_actions_inputs.py::test_0: No tool with actions found" in message
    assert MIN_EXECUTED_RATIO_ENV in message


def test_ratio_message_truncates_a_very_long_skip_list():
    """A thousand-skip session must stay readable; the module table stays complete."""
    ledger = ExecutionLedger()
    items = [_Item(f"tests/functional/v2/test_x.py::test_{i}") for i in range(50)]
    ledger.record_collected(items)
    for item in items:
        ledger.record(_Report("setup", "skipped", nodeid=item.nodeid, longrepr=("x.py", 1, "Skipped: no fixture")))

    message = low_execution_ratio_message(ledger, 0.8, max_listed=10)

    assert "... and 40 more" in message
    assert "tests/functional/v2/test_x.py: 0/50" in message
