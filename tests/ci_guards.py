"""CI integrity guards for the pytest session (ENG-3544).

A leg that collects tests, skips every one, and exits 0 is indistinguishable from
a leg that passed: pytest's exit code is 0 for an all-skipped session, and the
workflow has no other signal. `tests/functional/agent` (35 collected, 0 executed)
and `tests/functional/team_agent` (15 collected, 0 executed) were in exactly that
state, reporting green for ~2,300 LOC that never ran.

These helpers are kept out of `tests/conftest.py` so they can be unit-tested
directly; the conftest only wires them into pytest's hooks. The module name
matches neither `test_*.py` nor `*_test.py`, so pytest does not collect it.

ENG-3684 extends the same idea one step further: "at least one test ran" is a
floor so low that a leg running 12 of 195 collected tests clears it. The ratio
guard below holds a leg to a *proportion* of its collected tests, and the ledger
records what was skipped and why so the summary names the fixtures to fix.
"""

import os
from collections import Counter

#: Set this to a truthy value to make an all-skipped session a failure. It is
#: opt-in so that `pytest -k ...`, single-file runs, and no-credential laptops
#: behave exactly as they do today; only `.github/workflows/main.yaml` sets it.
REQUIRE_EXECUTED_ENV = "AIXPLAIN_REQUIRE_EXECUTED_TESTS"

#: Minimum share of *collected* tests a leg must actually execute, as a float in
#: [0, 1]. Read only when `REQUIRE_EXECUTED_ENV` is on, so the two guards share
#: one opt-in and laptops stay unaffected. `0` disables the ratio floor and
#: leaves only the "nothing ran at all" check from ENG-3544.
MIN_EXECUTED_RATIO_ENV = "AIXPLAIN_MIN_EXECUTED_RATIO"

#: The floor when `MIN_EXECUTED_RATIO_ENV` is unset. 0.8 leaves room for the
#: credential-gated skips a leg legitimately carries (no SLACK_TOKEN on a fork's
#: run, say) while failing the `tests/functional/v2` shape this task exists for:
#: 12 of 195 executed is a ratio of 0.06.
DEFAULT_MIN_EXECUTED_RATIO = 0.8

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


class SkippedTest:
    """One skipped test, as it will appear in the end-of-run summary."""

    __slots__ = ("nodeid", "reason")

    def __init__(self, nodeid: str, reason: str) -> None:
        self.nodeid = nodeid
        self.reason = reason

    def __eq__(self, other) -> bool:
        return isinstance(other, SkippedTest) and (self.nodeid, self.reason) == (other.nodeid, other.reason)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"SkippedTest({self.nodeid!r}, {self.reason!r})"


def module_of(nodeid: str) -> str:
    """The test file part of *nodeid* -- everything before the first `::`."""
    return nodeid.split("::", 1)[0]


def skip_reason(report) -> str:
    """The human-readable reason attached to a skipped *report*.

    pytest puts it in `longrepr` as a `(path, lineno, "Skipped: <reason>")`
    triple for a plain skip. Anything else (a string, a full repr object) is
    stringified, because a reason we cannot parse is still worth printing --
    silently dropping it would leave the summary naming tests with no clue as to
    which fixture went missing, which is the whole point of collecting them.
    """
    longrepr = getattr(report, "longrepr", None)
    if isinstance(longrepr, tuple) and len(longrepr) == 3:
        text = str(longrepr[2])
    elif longrepr is None:
        return "no reason given"
    else:
        text = str(longrepr)
    prefix = "Skipped: "
    return text[len(prefix) :].strip() if text.startswith(prefix) else text.strip()


class ExecutionLedger:
    """Counts test bodies that actually ran, as opposed to being skipped.

    Beyond the session totals, it keeps per-module tallies and the id/reason of
    every skip. A leg that fails the ratio floor needs to say *which* modules
    went dark and why: "137 of 195 skipped" sends a reader grepping, whereas
    "test_actions_inputs.py: 40 skipped -- No tool with actions found" names the
    fixture to fix.
    """

    def __init__(self) -> None:
        self.executed = 0
        self.collected = 0
        self.executed_by_module = Counter()
        self.collected_by_module = Counter()
        self.skipped = []
        self._skipped_nodeids = set()

    def reset(self) -> None:
        """Clear the tallies at the start of a session.

        The conftest holds one ledger for the life of the *process*, but pytest
        can run more than one session in a process (``pytest.main()`` called
        twice, or the ``pytester`` fixture). Carrying a previous session's count
        forward would make the guard silently pass a session that ran nothing --
        a false negative in exactly the direction the guard exists to prevent.
        """
        self.executed = 0
        self.collected = 0
        self.executed_by_module.clear()
        self.collected_by_module.clear()
        self.skipped = []
        self._skipped_nodeids = set()

    def record_collected(self, items) -> None:
        """Tally the tests this session will attempt, per module.

        Called with the final item list rather than `session.testscollected` so
        the denominator matches the numerator: the conftest's `--sdk_version`
        filters and `-k`/`-m` deselection have both already pruned it, so a
        narrowed run is not measured against the items it deliberately dropped.
        """
        for item in items:
            nodeid = getattr(item, "nodeid", None)
            if not nodeid:  # pragma: no cover - defensive
                continue
            self.collected += 1
            self.collected_by_module[module_of(nodeid)] += 1

    def record(self, report) -> None:
        """Count *report* if it represents a test body that ran.

        Only the ``call`` phase counts as executed: a plain skip (whether from a
        marker or from ``pytest.skip()`` inside a fixture) is reported at
        ``setup`` and never reaches ``call`` at all, so setup/teardown reports
        say nothing about whether the body ran.

        Skips are recorded from *any* phase, because the two shapes this task
        targets land in different ones -- a fixture-level skip at ``setup``, an
        inline ``pytest.skip()`` part-way through the body at ``call``.
        """
        when = getattr(report, "when", None)
        outcome = getattr(report, "outcome", None)
        # An xfail arrives as `skipped` at call time, but the body *did* run, so
        # it counts as executed -- `wasxfail` is the marker pytest sets for it.
        was_xfail = hasattr(report, "wasxfail")

        if outcome == "skipped" and not was_xfail and when in ("setup", "call"):
            self._record_skip(report)

        if when != "call":
            return
        if outcome in ("passed", "failed") or was_xfail:
            self.executed += 1
            nodeid = getattr(report, "nodeid", "")
            if nodeid:
                self.executed_by_module[module_of(nodeid)] += 1

    def _record_skip(self, report) -> None:
        nodeid = getattr(report, "nodeid", "")
        if not nodeid:  # pragma: no cover - defensive
            return
        # A test skipped at setup emits exactly one skipped report, but a rerun
        # (pytest-rerunfailures) or a repeated session can emit the same nodeid
        # twice; the summary lists each test once.
        if nodeid in self._skipped_nodeids:
            return
        self._skipped_nodeids.add(nodeid)
        self.skipped.append(SkippedTest(nodeid, skip_reason(report)))

    def module_table(self):
        """`(module, executed, collected)` rows for the summary, module-sorted.

        `collected_by_module` is the authoritative denominator, but it is only
        filled by `record_collected`, which a pytest-xdist controller may never
        reach and which a conftest re-exporting only the report hooks does not
        wire at all. Falling back to "executed + skipped
        reports seen for this module" keeps the table populated in those cases
        instead of printing an empty section, which reads as "no modules" rather
        than "no collection data".
        """
        seen = Counter(self.executed_by_module)
        for entry in self.skipped:
            seen[module_of(entry.nodeid)] += 1

        modules = set(self.collected_by_module) | set(seen)
        return [
            (module, self.executed_by_module.get(module, 0), self.collected_by_module.get(module) or seen[module])
            for module in sorted(modules)
        ]

    def executed_ratio(self) -> float:
        """Share of collected tests whose body ran; 1.0 when nothing was collected.

        An empty collection is *not* a ratio failure: "nothing collected" is
        already the ENG-3544 guard's business, and reporting 0/0 as a shortfall
        would fail `pytest -k <no match>` for the wrong reason.
        """
        if self.collected <= 0:
            return 1.0
        return self.executed / self.collected


def guards_enabled(env=None) -> bool:
    """True if the session opted into the CI integrity guards."""
    env = os.environ if env is None else env
    return str(env.get(REQUIRE_EXECUTED_ENV, "")).lower() in _TRUTHY


def min_executed_ratio(env=None) -> float:
    """The configured execution floor, as a float in [0, 1].

    Raises:
        ValueError: If the variable is set to something that is not a number in
            [0, 1]. A typo'd floor that silently fell back to the default would
            leave the workflow claiming a threshold it does not enforce, which is
            the same class of lie the guard exists to catch -- so it is loud.
    """
    env = os.environ if env is None else env
    raw = env.get(MIN_EXECUTED_RATIO_ENV)
    if raw is None or str(raw).strip() == "":
        return DEFAULT_MIN_EXECUTED_RATIO
    try:
        ratio = float(str(raw).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{MIN_EXECUTED_RATIO_ENV}={raw!r} is not a number; expected a value in [0, 1].")
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"{MIN_EXECUTED_RATIO_ENV}={raw!r} is out of range; expected a value in [0, 1].")
    return ratio


def should_fail_for_no_executed_tests(executed: int, exitstatus: int, env=None) -> bool:
    """True if this session must be failed for having run nothing.

    Args:
        executed: Number of test bodies that ran, per :class:`ExecutionLedger`.
        exitstatus: The exit status pytest is about to report.
        env: Environment mapping to read the opt-in flag from; defaults to
            ``os.environ``.
    """
    env = os.environ if env is None else env
    if not guards_enabled(env):
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


def should_fail_for_low_execution_ratio(executed: int, collected: int, exitstatus: int, env=None) -> bool:
    """True if this session executed too small a share of what it collected.

    The ENG-3544 guard above only fires at *zero* executed, which `tests/functional/v2`
    cleared while running 12 of 195 tests: one module-scoped fixture skip took
    ~40 tests out, and 36 more inline skips took out the rest. This is the same
    check with a proportional floor.

    Args:
        executed: Number of test bodies that ran, per :class:`ExecutionLedger`.
        collected: Number of tests collected, per :class:`ExecutionLedger`.
        exitstatus: The exit status pytest is about to report.
        env: Environment mapping to read the flags from; defaults to ``os.environ``.

    Raises:
        ValueError: If ``MIN_EXECUTED_RATIO_ENV`` holds an unusable value.
    """
    env = os.environ if env is None else env
    if not guards_enabled(env):
        return False
    # Same reasoning as the zero-executed guard: a session that is already red
    # keeps its own failure. Rewriting it as a ratio shortfall would bury the
    # real error, and a leg full of failures has by definition executed bodies.
    if exitstatus not in (0, EXIT_NO_TESTS_COLLECTED):
        return False
    # "Nothing collected" belongs to the ENG-3544 guard; 0/0 is not a shortfall.
    if collected <= 0:
        return False
    ratio = min_executed_ratio(env)
    if ratio <= 0:
        return False
    return (executed / collected) < ratio


def low_execution_ratio_message(ledger: "ExecutionLedger", ratio: float, max_listed: int = 40) -> str:
    """The failure text shown when too few of the collected tests ran.

    Lists the under-executing modules and then every skipped test with its
    reason, because the fix is never "run more tests" -- it is "restore the
    backend fixture named in this reason". Truncated at *max_listed* so a
    thousand-skip session stays readable; the per-module table above it is
    complete either way.
    """
    executed, collected = ledger.executed, ledger.collected
    lines = [
        f"CI integrity failure (ENG-3684): {executed} of {collected} collected test(s) executed "
        f"({executed / collected:.0%}), below the {ratio:.0%} floor. "
        "A leg that skips most of its suite must not report success.",
        "",
        "Executed / collected per module:",
    ]
    for module, module_executed, module_collected in ledger.module_table():
        marker = "  " if module_executed == module_collected else "! "
        lines.append(f"  {marker}{module}: {module_executed}/{module_collected}")

    if ledger.skipped:
        lines.extend(["", f"Skipped ({len(ledger.skipped)}):"])
        for entry in ledger.skipped[:max_listed]:
            lines.append(f"  {entry.nodeid}: {entry.reason}")
        remaining = len(ledger.skipped) - max_listed
        if remaining > 0:
            lines.append(f"  ... and {remaining} more")

    lines.extend(
        [
            "",
            "A skip that depends on backend state hides a missing test fixture. Pin the asset "
            "the test needs and fail when it is absent, or gate the test on a credential in a "
            f"conftest fixture. Set {MIN_EXECUTED_RATIO_ENV}=0 to disable this guard, or lower "
            "the floor deliberately with a comment saying why.",
        ]
    )
    return "\n".join(lines)
