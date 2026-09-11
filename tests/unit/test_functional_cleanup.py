"""Unit tests for the functional suite's cleanup tracker (BUG-947).

The tracker itself only ever runs against a live backend, so these tests are the
only ones that can run locally. They exercise the whole contract in-process with
fake resources: deletion order, the list-compatible call shape the existing ~71
``resource_tracker.append(...)`` sites rely on, tolerance of resources the test
already deleted, and -- the point of the ticket -- that a failed delete is
*reported* rather than swallowed.
"""

import logging

import pytest

from tests.cleanup_guards import (
    LEAK_LEDGER,
    STRICT_ENV,
    CleanupError,
    CleanupFailure,
    ResourceTracker,
    cleanup_failure_message,
    confirm_leaked,
    describe,
    finish_cleanup,
    is_already_gone,
    strict_cleanup,
)


class FakeResource:
    """A resource whose ``delete()`` records itself, or raises on demand."""

    def __init__(self, name, deleted, error=None, id=None):
        self.name = name
        self.id = id
        self._deleted = deleted
        self._error = error

    def delete(self):
        self._deleted.append(self.name)
        if self._error is not None:
            raise self._error


# ---------------------------------------------------------------------------
# Deletion order and the existing call shape
# ---------------------------------------------------------------------------


def test_cleanup_deletes_newest_first():
    """Reverse order, so a resource is deleted before whatever it depends on."""
    deleted = []
    tracker = ResourceTracker()
    tracker.append(FakeResource("agent", deleted))
    tracker.append(FakeResource("team_agent", deleted))

    assert tracker.cleanup("nodeid") == []
    assert deleted == ["team_agent", "agent"]


def test_tracker_is_a_list():
    """The four fixtures being replaced yielded a plain list; 71 call sites use it."""
    tracker = ResourceTracker()
    resource = FakeResource("agent", [])
    tracker.append(resource)

    assert isinstance(tracker, list)
    assert list(tracker) == [resource]
    assert len(tracker) == 1


def test_tracker_accepts_initial_resources():
    """``ResourceTracker([a, b])`` is how the apikey leak check adopts strays."""
    deleted = []
    tracker = ResourceTracker([FakeResource("first", deleted), FakeResource("second", deleted)])

    assert tracker.cleanup() == []
    assert deleted == ["second", "first"]


# ---------------------------------------------------------------------------
# Callbacks, for factories that return a dict rather than a deletable object
# ---------------------------------------------------------------------------


def test_add_callback_is_invoked_on_cleanup():
    calls = []
    tracker = ResourceTracker()
    tracker.add_callback("Dataset id=abc", lambda: calls.append("deleted"))

    assert tracker.cleanup() == []
    assert calls == ["deleted"]


def test_add_callback_failure_is_reported_under_its_label():
    def boom():
        raise RuntimeError("backend said no")

    tracker = ResourceTracker()
    tracker.add_callback("Dataset id=abc", boom)

    failures = tracker.cleanup("tests/functional/x.py::test_y")
    assert len(failures) == 1
    assert failures[0].label == "Dataset id=abc"
    assert failures[0].nodeid == "tests/functional/x.py::test_y"
    assert "RuntimeError: backend said no" == failures[0].error


def test_add_callback_survives_a_partial():
    """``functools.partial`` rejects attribute assignment; the label must not rely on it."""
    from functools import partial

    calls = []
    tracker = ResourceTracker()
    tracker.add_callback("Corpus id=abc", partial(calls.append, "deleted"))

    assert tracker.cleanup() == []
    assert calls == ["deleted"]


def test_add_callback_returns_the_entry_for_deregistration():
    calls = []
    tracker = ResourceTracker()
    entry = tracker.add_callback("Dataset id=abc", lambda: calls.append("deleted"))

    tracker.mark_cleaned(entry)

    assert tracker.cleanup() == []
    assert calls == []


# ---------------------------------------------------------------------------
# mark_cleaned: the test deleted it itself
# ---------------------------------------------------------------------------


def test_mark_cleaned_stops_teardown_deleting_again():
    """A double delete is not detectable from most v1 error messages."""
    deleted = []
    resource = FakeResource("dataset", deleted)
    tracker = ResourceTracker([resource])

    resource.delete()  # what the test under test does
    tracker.mark_cleaned(resource)

    assert tracker.cleanup() == []
    assert deleted == ["dataset"]


def test_mark_cleaned_leaves_the_other_resources_registered():
    deleted = []
    first = FakeResource("first", deleted)
    second = FakeResource("second", deleted)
    tracker = ResourceTracker([first, second])

    tracker.mark_cleaned(second)

    assert tracker.cleanup() == []
    assert deleted == ["first"]


def test_mark_cleaned_matches_on_identity_not_equality():
    """Two distinct resources can compare equal; removing the wrong one leaks it."""

    class EqualToAnything(FakeResource):
        def __eq__(self, other):
            return True

        __hash__ = None

    deleted = []
    keep = EqualToAnything("keep", deleted)
    drop = EqualToAnything("drop", deleted)
    tracker = ResourceTracker([keep, drop])

    tracker.mark_cleaned(drop)

    assert tracker.cleanup() == []
    assert deleted == ["keep"]


def test_mark_cleaned_ignores_an_unregistered_target():
    """So a test can call it unconditionally without tracking what it registered."""
    deleted = []
    tracker = ResourceTracker([FakeResource("registered", deleted)])

    tracker.mark_cleaned(FakeResource("never-registered", deleted))

    assert tracker.cleanup() == []
    assert deleted == ["registered"]


def test_a_bare_callable_appended_directly_is_still_called():
    calls = []
    tracker = ResourceTracker()
    tracker.append(lambda: calls.append("deleted"))

    assert tracker.cleanup() == []
    assert calls == ["deleted"]


def test_delete_is_preferred_over_calling_a_callable_resource():
    """A resource that happens to define ``__call__`` must still be deleted, not run."""

    class CallableResource(FakeResource):
        def __call__(self):
            raise AssertionError("the tracker invoked the resource instead of deleting it")

    deleted = []
    tracker = ResourceTracker([CallableResource("agent", deleted)])

    assert tracker.cleanup() == []
    assert deleted == ["agent"]


def test_an_entry_that_can_neither_be_deleted_nor_called_is_reported():
    tracker = ResourceTracker(["not-a-resource"])

    failures = tracker.cleanup()
    assert len(failures) == 1
    assert "cannot be cleaned up" in failures[0].error


# ---------------------------------------------------------------------------
# Already-gone tolerance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "404 Client Error: Not Found",
        "Agent Deletion Error: Not Found",
        "asset does not exist",
        "No such dataset",
    ],
)
def test_a_resource_that_is_already_gone_is_a_successful_cleanup(message):
    """Tests that delete explicitly *and* register must not go red for it."""
    deleted = []
    tracker = ResourceTracker([FakeResource("agent", deleted, error=Exception(message))])

    assert tracker.cleanup() == []


def test_is_already_gone_does_not_swallow_a_real_error():
    assert not is_already_gone(Exception("500 Internal Server Error"))
    assert not is_already_gone(Exception("connection reset by peer"))


#: The two messages review asked whether to tolerate. Both are pinned as *not*
#: already-gone: the first says the resource still exists and the delete was
#: refused, and the second is the string `APIKey.delete` reports for every
#: failure alike, outage included. See the note on `_ALREADY_GONE`.
NOT_ALREADY_GONE = [
    (
        "Error: Agent cannot be deleted.\nReason: This agent is currently used by one or more "
        "team agents.\n\nteam_agent_id: t1. To proceed, remove the agent from all team agents "
        "before deletion."
    ),
    "API Key Deletion Error: Make sure the API Key exists and you are the owner.",
]


@pytest.mark.parametrize("message", NOT_ALREADY_GONE, ids=["agent-in-use", "generic-api-key"])
def test_an_ambiguous_delete_failure_is_reported_not_tolerated(message):
    """Widening the patterns for these would re-hide the leaks (BUG-947)."""
    assert not is_already_gone(Exception(message))

    tracker = ResourceTracker([FakeResource("resource", [], error=Exception(message))])
    assert len(tracker.cleanup("nodeid")) == 1


# ---------------------------------------------------------------------------
# Failure aggregation: cleanup never raises, and never stops early
# ---------------------------------------------------------------------------


def test_cleanup_never_raises_and_continues_past_a_failure():
    deleted = []
    tracker = ResourceTracker()
    tracker.append(FakeResource("first", deleted))
    tracker.append(FakeResource("second", deleted, error=RuntimeError("nope")))
    tracker.append(FakeResource("third", deleted))

    failures = tracker.cleanup("nodeid")

    # Every resource was attempted, newest first, despite the middle failure.
    assert deleted == ["third", "second", "first"]
    assert [failure.label for failure in failures] == ["FakeResource name='second'"]


def test_cleanup_reports_every_failure():
    tracker = ResourceTracker(
        [
            FakeResource("a", [], error=RuntimeError("one")),
            FakeResource("b", [], error=RuntimeError("two")),
        ]
    )

    failures = tracker.cleanup("nodeid")
    assert len(failures) == 2
    assert {failure.error for failure in failures} == {"RuntimeError: one", "RuntimeError: two"}


def test_cleanup_logs_failures_at_error_level(caplog):
    """A swallowed teardown is what made the orphans invisible; log every one."""
    tracker = ResourceTracker([FakeResource("agent", [], error=RuntimeError("nope"))])

    with caplog.at_level(logging.ERROR, logger="aixplain.tests.cleanup"):
        tracker.cleanup("nodeid")

    messages = [record.getMessage() for record in caplog.records]
    assert any("cleanup FAILED" in message and "FakeResource name='agent'" in message for message in messages)


def test_cleanup_clears_the_tracker_so_a_second_call_is_a_no_op():
    """Guards against a resource being deleted twice if cleanup is retried."""
    deleted = []
    tracker = ResourceTracker([FakeResource("agent", deleted)])

    tracker.cleanup()
    tracker.cleanup()

    assert deleted == ["agent"]
    assert tracker == []


# ---------------------------------------------------------------------------
# describe()
# ---------------------------------------------------------------------------


def test_describe_names_the_type_id_and_name():
    assert describe(FakeResource("my-agent", [], id="abc123")) == "FakeResource id='abc123' name='my-agent'"


def test_describe_omits_missing_attributes():
    assert describe(object()) == "object"


def test_describe_tolerates_an_attribute_that_raises():
    class Awkward:
        @property
        def id(self):
            raise RuntimeError("not loaded")

    assert describe(Awkward()) == "Awkward"


# ---------------------------------------------------------------------------
# The strict flag
# ---------------------------------------------------------------------------


def test_strict_cleanup_defaults_to_strict():
    """Fail-closed: the ticket exists because a warning was ignorable."""
    assert strict_cleanup(env={}) is True


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_strict_cleanup_honours_truthy_values(value):
    assert strict_cleanup(env={STRICT_ENV: value}) is True


@pytest.mark.parametrize("value", ["0", "false", "False", "no", "off", ""])
def test_strict_cleanup_honours_falsy_values(value):
    assert strict_cleanup(env={STRICT_ENV: value}) is False


def test_strict_cleanup_reads_os_environ_by_default(monkeypatch):
    monkeypatch.setenv(STRICT_ENV, "0")
    assert strict_cleanup() is False


# ---------------------------------------------------------------------------
# The failure message
# ---------------------------------------------------------------------------


def test_cleanup_failure_message_names_every_orphan_and_the_escape_hatch():
    failures = [
        CleanupFailure("nodeid", "Agent id='a1'", "RuntimeError: one"),
        CleanupFailure("nodeid", "Dataset id='d1'", "RuntimeError: two"),
    ]

    message = cleanup_failure_message(failures)

    assert "BUG-947" in message
    assert "2 resource(s)" in message
    assert "Agent id='a1'" in message
    assert "Dataset id='d1'" in message
    assert "RuntimeError: one" in message
    assert STRICT_ENV in message


def test_cleanup_error_is_an_assertion_error():
    """So a strict teardown reads as a test failure rather than a suite error."""
    assert issubclass(CleanupError, AssertionError)


# ---------------------------------------------------------------------------
# finish_cleanup: the whole `resource_tracker` teardown
# ---------------------------------------------------------------------------


def test_finish_cleanup_deletes_and_reports_nothing_when_everything_goes():
    deleted = []
    tracker = ResourceTracker([FakeResource("agent", deleted)])
    ledger = []

    assert finish_cleanup(tracker, "nodeid", ledger=ledger) == []
    assert deleted == ["agent"]
    assert ledger == []


def test_finish_cleanup_raises_and_records_when_a_delete_fails(monkeypatch):
    """Strict by default: the leak fails the test *and* reaches the ledger."""
    monkeypatch.delenv(STRICT_ENV, raising=False)
    tracker = ResourceTracker([FakeResource("agent", [], error=RuntimeError("nope"))])
    ledger = []

    with pytest.raises(CleanupError) as excinfo:
        finish_cleanup(tracker, "tests/functional/x.py::test_y", ledger=ledger)

    assert "FakeResource name='agent'" in str(excinfo.value)
    assert [failure.nodeid for failure in ledger] == ["tests/functional/x.py::test_y"]


def test_finish_cleanup_records_without_raising_when_not_strict(monkeypatch):
    """The escape hatch must still leave the orphan visible in the summary."""
    monkeypatch.setenv(STRICT_ENV, "0")
    tracker = ResourceTracker([FakeResource("agent", [], error=RuntimeError("nope"))])
    ledger = []

    failures = finish_cleanup(tracker, "nodeid", ledger=ledger)

    assert len(failures) == 1
    assert ledger == failures


def test_finish_cleanup_attempts_every_resource_before_raising(monkeypatch):
    """A failure must not abandon the resources the tracker had not reached."""
    monkeypatch.delenv(STRICT_ENV, raising=False)
    deleted = []
    tracker = ResourceTracker(
        [
            FakeResource("first", deleted),
            FakeResource("second", deleted, error=RuntimeError("nope")),
        ]
    )

    with pytest.raises(CleanupError):
        finish_cleanup(tracker, "nodeid", ledger=[])

    assert deleted == ["second", "first"]


def test_finish_cleanup_defaults_to_the_session_ledger(monkeypatch):
    monkeypatch.setenv(STRICT_ENV, "0")
    LEAK_LEDGER.clear()
    tracker = ResourceTracker([FakeResource("agent", [], error=RuntimeError("nope"))])
    try:
        finish_cleanup(tracker, "nodeid")
        assert [failure.label for failure in LEAK_LEDGER] == ["FakeResource name='agent'"]
    finally:
        LEAK_LEDGER.clear()


# ---------------------------------------------------------------------------
# confirm_leaked(): a stale listing must not be reported as a leak
# ---------------------------------------------------------------------------


def _listings(*results):
    """Return a callable yielding *results* in order, one per call, plus a log."""
    calls = []
    remaining = list(results)

    def list_matches():
        calls.append(len(calls))
        return remaining.pop(0) if remaining else []

    return list_matches, calls


def test_confirm_leaked_returns_nothing_when_the_first_listing_is_clean():
    list_matches, calls = _listings([])
    slept = []

    assert confirm_leaked(list_matches, sleep=slept.append) == []
    assert len(calls) == 1
    assert slept == [], "a clean run must not pay the settle delay"


def test_confirm_leaked_re_lists_a_resource_the_backend_has_not_caught_up_with():
    """The false-leak case: the key was deleted, the listing is just stale."""
    list_matches, calls = _listings(["stale"], [])
    slept = []

    assert confirm_leaked(list_matches, delay=7.0, sleep=slept.append) == []
    assert len(calls) == 2
    assert slept == [7.0]


def test_confirm_leaked_reports_a_resource_that_survives_every_attempt():
    """The genuine leak this check exists for is still detected."""
    list_matches, calls = _listings(["orphan"], ["orphan"], ["orphan"])
    slept = []

    assert confirm_leaked(list_matches, attempts=3, sleep=slept.append) == ["orphan"]
    assert len(calls) == 3
    assert len(slept) == 2, "no delay after the final listing"


def test_confirm_leaked_believes_a_single_attempt():
    list_matches, calls = _listings(["orphan"])
    slept = []

    assert confirm_leaked(list_matches, attempts=1, sleep=slept.append) == ["orphan"]
    assert len(calls) == 1
    assert slept == []


def test_confirm_leaked_propagates_a_listing_failure():
    """An unreachable backend is not evidence of a leak."""

    def list_matches():
        raise RuntimeError("backend down")

    with pytest.raises(RuntimeError, match="backend down"):
        confirm_leaked(list_matches, sleep=lambda _: None)


def test_confirm_leaked_materialises_a_lazy_listing():
    """The result is a list, so the caller can count and re-read it."""
    assert confirm_leaked(lambda: iter(["orphan"]), attempts=1, sleep=lambda _: None) == ["orphan"]
