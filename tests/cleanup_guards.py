"""Guaranteed, visible cleanup of resources created by functional tests (BUG-947).

The functional suite runs against the production tenant on every push to `main`,
and four copies of a `resource_tracker` fixture ended their teardown with
``except Exception: pass``. A delete that failed therefore left an orphaned
production asset behind with no trace anywhere, so leakage was invisible rather
than merely tolerated.

This module holds the tracker and its reporting; `tests/functional/conftest.py`
does nothing but wire it into a fixture. Splitting it that way is what makes it
testable: the tracker can only ever *run* against a live backend, but its
contract -- deletion order, already-gone tolerance, failure aggregation -- is
pure, so `tests/unit/test_functional_cleanup.py` covers all of it in-process.
Kept beside `tests/ci_guards.py` for the same two reasons that module lives
there: `tests/` is a package so `tests/unit/` can import it, and the name matches
neither `test_*.py` nor `*_test.py`, so pytest does not collect it.
"""

import logging
import os
import time
from typing import Any, Callable, Iterable, List, NamedTuple, Optional

#: Set to a falsy value to downgrade cleanup failures to warnings. Strict by
#: default -- the whole point of BUG-947 is that a swallowed teardown made
#: orphaned production assets invisible. This is the inverse of
#: `REQUIRE_EXECUTED_ENV` in tests/ci_guards.py, which is opt-*in* because it
#: must not affect laptops; here the fail-closed default is the requirement, and
#: a laptop that cannot reach the backend never creates a resource to leak.
STRICT_ENV = "AIXPLAIN_FUNCTIONAL_CLEANUP_STRICT"

_TRUTHY = frozenset({"1", "true", "yes", "on"})

#: Substrings that mean "the backend already deleted it", which is a successful
#: cleanup rather than a failure. Registering with the tracker *and* deleting
#: explicitly is the common case -- the tracker is the net under an assertion
#: that might fail early -- and it must not turn a green test red.
#:
#: Kept narrow, and *not* the primary mechanism for that case: many v1 deletes
#: collapse every failure into one generic string with no status code (e.g.
#: ``"API Key Deletion Error: Make sure the API Key exists and you are the
#: owner."``), so a second delete is indistinguishable from a backend outage.
#: Widening the list to match those would swallow real failures -- exactly the
#: invisibility BUG-947 is about. A test that deletes explicitly should call
#: :meth:`ResourceTracker.mark_cleaned` instead; this list only covers the
#: deletes that do report a status (agent, team agent, the factory GETs).
#:
#: Deliberately excluded, though both were raised in review: "This agent is
#: currently used by one or more team agents" and the generic API-key string
#: above. The first is the *opposite* of already-gone -- the agent still exists
#: and the delete was refused -- so matching it would silently orphan every
#: agent still attached to a team; the fix is to register the team's members
#: before the team so newest-first teardown deletes the team first. The second
#: names no status code at all, so it covers a backend outage and a revoked
#: token as readily as a second delete, and API keys are the suite's most
#: frequently deleted resource. Widening for either would restore exactly the
#: invisibility BUG-947 is about.
_ALREADY_GONE = ("404", "not found", "does not exist", "no such")

#: Attributes worth naming in a failure message, in the order they read best.
_DESCRIBE_ATTRIBUTES = ("id", "name")

#: How many times :func:`confirm_leaked` lists before believing what it sees,
#: and how long it waits between listings. A backend listing is not immediately
#: consistent -- the code the apikey leak check replaced waited an explicit
#: ``time.sleep(0.5)`` after every delete for exactly this reason -- so a key
#: deleted in the previous test's teardown can still be returned. Deciding on
#: the first listing therefore reports a phantom leak on a clean run, which is
#: a red build that names an innocent test. Only paid when something *is*
#: listed, so a clean run adds no delay at all.
LEAK_SETTLE_ATTEMPTS = 3
LEAK_SETTLE_SECONDS = 2.0

logger = logging.getLogger("aixplain.tests.cleanup")


class CleanupFailure(NamedTuple):
    """One resource the tracker could not delete.

    Attributes:
        nodeid: The pytest node whose teardown failed, for the session summary.
        label: Human-readable identification of the resource, from
            :func:`describe` or the label passed to
            :meth:`ResourceTracker.add_callback`.
        error: ``"<ExceptionType>: <message>"`` for the failing delete.
    """

    nodeid: str
    label: str
    error: str


class CleanupError(AssertionError):
    """Raised in teardown when a tracked resource could not be deleted.

    An ``AssertionError`` rather than a bare ``Exception`` so pytest reports it
    as a teardown *failure* of the owning test instead of an internal error, and
    so it is attributable to the test that leaked.
    """


#: Session-wide ledger of everything that could not be deleted, drained by
#: `pytest_terminal_summary` in tests/conftest.py. A strict teardown already
#: fails the individual test; this is what makes the total legible at the end of
#: a 400-test run instead of buried in one traceback among many.
LEAK_LEDGER: List[CleanupFailure] = []


def strict_cleanup(env=None) -> bool:
    """Return True when a cleanup failure must fail the test's teardown.

    Args:
        env: Environment mapping to read :data:`STRICT_ENV` from; defaults to
            ``os.environ``.
    """
    env = os.environ if env is None else env
    return str(env.get(STRICT_ENV, "1")).lower() in _TRUTHY


def is_already_gone(exc: BaseException) -> bool:
    """Return True when *exc* says the resource no longer exists.

    Args:
        exc: The exception raised by the failed delete.
    """
    text = str(exc).lower()
    return any(marker in text for marker in _ALREADY_GONE)


def describe(resource: Any) -> str:
    """Return a human-readable label for *resource*: type, id and name.

    Args:
        resource: The tracked object. Any attribute may be missing, and a lazy
            resource's property may raise, so both are tolerated -- a label is
            diagnostic output and must never be the reason cleanup fails.
    """
    parts = [type(resource).__name__]
    for attribute in _DESCRIBE_ATTRIBUTES:
        try:
            value = getattr(resource, attribute, None)
        except Exception:  # noqa: BLE001 - a label must not raise
            continue
        if value:
            parts.append(f"{attribute}={value!r}")
    return " ".join(parts)


def confirm_leaked(
    list_matches: Callable[[], Iterable[Any]],
    attempts: int = LEAK_SETTLE_ATTEMPTS,
    delay: float = LEAK_SETTLE_SECONDS,
    sleep: Callable[[float], Any] = time.sleep,
) -> List[Any]:
    """Return the resources still listed once the backend has settled.

    A leak check asks "did anything this run created outlive its test?", and the
    only honest answer comes from a listing that has caught up with the deletes
    that just happened. Re-listing rather than sleeping unconditionally keeps a
    clean run fast, and keeps genuine detection intact: a resource nobody
    deleted survives every attempt.

    Args:
        list_matches: Zero-argument callable returning the resources that look
            leaked right now.
        attempts: How many listings to take before believing a non-empty one.
        delay: Seconds to wait between listings.
        sleep: Injected so tests need not actually wait.

    Returns:
        Empty as soon as any listing comes back clean, otherwise the resources
        returned by the final attempt.

    Raises:
        Exception: Whatever *list_matches* raises. An unreachable backend is
            not evidence of a leak, so the caller decides what it means.
    """
    leaked: List[Any] = []
    for attempt in range(max(1, attempts)):
        leaked = list(list_matches())
        if not leaked:
            return []
        if attempt < attempts - 1:
            sleep(delay)
    return leaked


class _LabelledCallback:
    """A zero-argument cleanup callable carrying its own label.

    A wrapper rather than an attribute set on the callable itself, because
    ``functools.partial`` and built-in methods reject attribute assignment --
    and both are natural things to hand to :meth:`ResourceTracker.add_callback`.
    """

    def __init__(self, label: str, delete: Callable[[], Any]) -> None:
        self.cleanup_label = label
        self._delete = delete

    def __call__(self) -> Any:
        """Run the wrapped delete."""
        return self._delete()


def _delete_entry(entry: Any) -> None:
    """Delete one tracked entry, dispatching on what it offers.

    ``delete()`` is preferred over ``__call__`` so that a resource which happens
    to be callable is deleted rather than *invoked* -- invoking an agent instead
    of deleting it would cost credits and leak the agent anyway.

    Args:
        entry: A registered callback, an object exposing ``delete()``, or a bare
            zero-argument callable.

    Raises:
        TypeError: If *entry* offers neither.
    """
    if isinstance(entry, _LabelledCallback):
        entry()
        return
    delete = getattr(entry, "delete", None)
    if callable(delete):
        delete()
        return
    if callable(entry):
        entry()
        return
    raise TypeError(f"{describe(entry)} cannot be cleaned up: it has no delete() and is not callable")


class ResourceTracker(list):
    """Tracks resources created during a test for guaranteed, visible cleanup.

    Subclasses ``list`` so that every existing ``resource_tracker.append(agent)``
    call site keeps working unchanged -- the four fixtures this replaces yielded
    a plain list, and there are ~71 append sites across the functional suite.
    The only behavioural difference is that a failed delete is now reported.

    Entries may be an object exposing ``delete()``, a callback registered with
    :meth:`add_callback` (for factories such as ``DatasetFactory.create`` that
    return a dict rather than a deletable object), or a bare zero-argument
    callable.
    """

    def add_callback(self, label: str, delete: Callable[[], Any]) -> "_LabelledCallback":
        """Register an arbitrary cleanup callable under *label*.

        Args:
            label: How the resource is named if the cleanup fails, e.g.
                ``"Dataset id=abc123"``.
            delete: Zero-argument callable that deletes the resource.

        Returns:
            The registered entry, to hand to :meth:`mark_cleaned` if the test
            goes on to delete the resource itself.
        """
        entry = _LabelledCallback(label, delete)
        self.append(entry)
        return entry

    def mark_cleaned(self, target: Any) -> None:
        """Deregister *target*: the test deleted it, so teardown must not retry.

        This is how a test whose *subject* is the delete -- ``dataset.delete()``
        followed by asserting the GET now fails -- keeps the tracker as a net
        without a second delete failing teardown. Precise deregistration rather
        than string-matching the second delete's error, because most v1 deletes
        report "make sure it exists and you are the owner" for every failure
        alike, so a genuine outage and an already-deleted resource are the same
        message (BUG-947).

        Matches on identity, not equality: two distinct resources can compare
        equal, and removing the wrong one would silently leak it. Unregistered
        targets are ignored, so this is safe to call unconditionally.

        Args:
            target: The resource object, or the entry
                :meth:`add_callback` returned.
        """
        for index, entry in enumerate(self):
            if entry is target:
                del self[index]
                return

    def cleanup(self, nodeid: str = "") -> List[CleanupFailure]:
        """Delete every tracked resource, newest first, and report what failed.

        Newest-first because a resource is usually created after the things it
        depends on, so the reverse order is the one in which deletes are
        accepted. One failure never stops the rest: the remaining resources are
        still attempted, since abandoning them would leak more than the one that
        failed.

        Never raises -- the caller decides whether a failure should fail the
        test, and a tracker that raised mid-teardown would skip the resources it
        had not reached yet. The tracker is emptied either way, so a retried
        cleanup cannot delete anything twice.

        Args:
            nodeid: The pytest nodeid to attribute failures to.

        Returns:
            One :class:`CleanupFailure` per resource that could not be deleted.
        """
        failures = []
        entries = list(self)
        self.clear()
        for entry in reversed(entries):
            label = getattr(entry, "cleanup_label", None) or describe(entry)
            try:
                _delete_entry(entry)
            except Exception as exc:  # noqa: BLE001 - reported below, never swallowed
                if is_already_gone(exc):
                    logger.debug("cleanup: %s was already gone", label)
                    continue
                logger.error("cleanup FAILED for %s: %s", label, exc)
                failures.append(CleanupFailure(nodeid, label, f"{type(exc).__name__}: {exc}"))
        return failures


def cleanup_failure_message(failures: List[CleanupFailure]) -> str:
    """Return the teardown failure text, naming every resource left behind.

    Args:
        failures: The failures returned by :meth:`ResourceTracker.cleanup`.
    """
    lines = "\n".join(f"  - {failure.label}: {failure.error}" for failure in failures)
    return (
        f"BUG-947: {len(failures)} resource(s) could not be deleted and are now orphaned in the "
        f"target tenant:\n{lines}\n\n"
        f"Set {STRICT_ENV}=0 to downgrade this to a warning."
    )


def finish_cleanup(
    tracker: ResourceTracker, nodeid: str = "", ledger: Optional[List[CleanupFailure]] = None
) -> List[CleanupFailure]:
    """Run *tracker*'s cleanup, record what leaked, and raise if strict.

    The whole body of the `resource_tracker` teardown, kept here rather than in
    `tests/functional/conftest.py` so it is reachable from a unit test. A fixture
    body can only be exercised by a live pytest session, and this is the part of
    BUG-947 that must not silently regress: a delete that failed has to reach
    both the session ledger and the failing test.

    Args:
        tracker: The tracker to drain.
        nodeid: The pytest nodeid to attribute failures to.
        ledger: Where to record failures; defaults to :data:`LEAK_LEDGER`.

    Returns:
        One :class:`CleanupFailure` per resource that could not be deleted.

    Raises:
        CleanupError: If anything could not be deleted and :func:`strict_cleanup`
            is on.
    """
    ledger = LEAK_LEDGER if ledger is None else ledger
    failures = tracker.cleanup(nodeid)
    ledger.extend(failures)
    if failures and strict_cleanup():
        raise CleanupError(cleanup_failure_message(failures))
    return failures
