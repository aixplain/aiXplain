"""CI integrity guards for the pytest session (ENG-3544).

A leg that collects tests, skips every one, and exits 0 is indistinguishable from
a leg that passed: pytest's exit code is 0 for an all-skipped session, and the
workflow has no other signal. `tests/functional/agent` (35 collected, 0 executed)
and `tests/functional/team_agent` (15 collected, 0 executed) were in exactly that
state, reporting green for ~2,300 LOC that never ran.

These helpers are kept out of `tests/conftest.py` so they can be unit-tested
directly; the conftest only wires them into pytest's hooks. The module name
matches neither `test_*.py` nor `*_test.py`, so pytest does not collect it.
"""

import os

#: Set this to a truthy value to make an all-skipped session a failure. It is
#: opt-in so that `pytest -k ...`, single-file runs, and no-credential laptops
#: behave exactly as they do today; only `.github/workflows/main.yaml` sets it.
REQUIRE_EXECUTED_ENV = "AIXPLAIN_REQUIRE_EXECUTED_TESTS"

_TRUTHY = frozenset({"1", "true", "yes", "on"})

#: pytest's exit code for "no tests were collected".
EXIT_NO_TESTS_COLLECTED = 5

#: `config.option` attributes that mean pytest was told to run no test bodies at
#: all. Such a session executes nothing *by design*, so the guard has nothing to
#: say about it. This is not hypothetical: the workflow exports the opt-in flag
#: for every job, and `tests/unit/utils/test_credential_free_collection.py`
#: spawns `pytest tests/unit --collect-only` with an inherited environment, so
#: without this exemption the guard fails the credential-free collection check
#: in CI while passing on every laptop.
NON_EXECUTING_OPTIONS = (
    "collectonly",  # --collect-only / --co
    "showfixtures",  # --fixtures
    "show_fixtures_per_test",  # --fixtures-per-test
    "setuponly",  # --setup-only
    "setupplan",  # --setup-plan
)


def is_non_executing_session(config) -> bool:
    """True if *config* asked pytest not to run any test body."""
    option = getattr(config, "option", None)
    if option is None:  # pragma: no cover - defensive
        return False
    return any(getattr(option, name, False) for name in NON_EXECUTING_OPTIONS)


class ExecutionLedger:
    """Counts test bodies that actually ran, as opposed to being skipped."""

    def __init__(self) -> None:
        self.executed = 0

    def reset(self) -> None:
        """Clear the tally at the start of a session.

        The conftest holds one ledger for the life of the *process*, but pytest
        can run more than one session in a process (``pytest.main()`` called
        twice, or the ``pytester`` fixture). Carrying a previous session's count
        forward would make the guard silently pass a session that ran nothing --
        a false negative in exactly the direction the guard exists to prevent.
        """
        self.executed = 0

    def record(self, report) -> None:
        """Count *report* if it represents a test body that ran.

        Only the ``call`` phase counts: a plain skip (whether from a marker or
        from ``pytest.skip()`` inside a fixture) is reported at ``setup`` and
        never reaches ``call`` at all, so setup/teardown reports say nothing
        about whether the body ran.
        """
        if getattr(report, "when", None) != "call":
            return
        # An xfail arrives as `skipped` at call time, but the body *did* run, so
        # it counts as executed -- `wasxfail` is the marker pytest sets for it.
        if report.outcome in ("passed", "failed") or hasattr(report, "wasxfail"):
            self.executed += 1


def should_fail_for_no_executed_tests(executed: int, exitstatus: int, env=None) -> bool:
    """True if this session must be failed for having run nothing.

    Args:
        executed: Number of test bodies that ran, per :class:`ExecutionLedger`.
        exitstatus: The exit status pytest is about to report.
        env: Environment mapping to read the opt-in flag from; defaults to
            ``os.environ``.
    """
    env = os.environ if env is None else env
    if str(env.get(REQUIRE_EXECUTED_ENV, "")).lower() not in _TRUTHY:
        return False
    # Sessions that are already failing are left alone: rewriting a real failure
    # as "executed nothing" would bury the actual error. 0 (all passed) and 5
    # (nothing collected) are the two statuses that can dishonestly read as OK.
    if exitstatus not in (0, EXIT_NO_TESTS_COLLECTED):
        return False
    return executed == 0


def no_executed_tests_message(collected: int) -> str:
    """The failure text shown when a session executed no test bodies."""
    return (
        f"CI integrity failure (ENG-3544): {collected} test(s) collected, 0 executed. "
        "A leg that skips everything must not report success. Either the suite is "
        "skipped at the directory level (fix the conftest), or its credential guard "
        "found no API key (fix the job env), or every test carries an individual skip "
        f"(then the leg should be removed from the matrix). Set {REQUIRE_EXECUTED_ENV}=0 "
        "to disable this guard."
    )
