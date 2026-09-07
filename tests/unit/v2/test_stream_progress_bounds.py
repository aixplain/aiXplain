"""Unit tests for ``stream_progress`` termination guarantees (BUG-942 item 2).

``stream_progress`` was a ``while True`` at ``poll_interval=0.05`` -- 20
requests/second per job -- with no ``timeout`` parameter at all. Worse,
``self._poll_count += 1`` sat *inside* ``if steps:``, so a backend returning a
valid non-terminal response with no ``steps`` array never advanced the counter
and ``max_polls`` was unreachable: the loop ran forever.

Every test below drives a poll function that returns ``IN_PROGRESS`` and **no
steps**, which is precisely the shape that used to hang.
"""

from unittest.mock import patch

import pytest

from aixplain.v2.agent_progress import AgentProgressTracker, ProgressFormat


class _Response:
    """Minimal poll response: a status and an optional steps payload."""

    def __init__(self, status="IN_PROGRESS", steps=None):
        self.status = status
        self.data = {"intermediate_steps": steps or []}


def _tracker(responses=None, **kwargs):
    """Tracker whose poll returns *responses* in order, then repeats the last."""
    responses = list(responses or [_Response()])
    calls = []

    def poll(url):
        calls.append(url)
        index = min(len(calls) - 1, len(responses) - 1)
        return responses[index]

    tracker = AgentProgressTracker(poll_func=poll, **kwargs)
    tracker._poll_calls = calls
    return tracker


class TestDefaults:
    """The 20 req/s default is the load defect; pin the new one."""

    def test_default_poll_interval_is_at_least_half_a_second(self):
        tracker = _tracker()

        assert tracker.poll_interval >= 0.5
        assert AgentProgressTracker.DEFAULT_POLL_INTERVAL >= 0.5

    def test_default_poll_interval_is_not_the_display_refresh_rate(self):
        """0.05s is the local spinner's cadence, never a network cadence."""
        assert AgentProgressTracker.DEFAULT_POLL_INTERVAL != AgentProgressTracker.DISPLAY_REFRESH_RATE

    def test_stream_progress_has_a_default_timeout(self):
        """Unlike before, the method is bounded even if the caller says nothing."""
        import inspect

        default = inspect.signature(AgentProgressTracker.stream_progress).parameters["timeout"].default

        assert default is not None
        assert default > 0


class TestUnconditionalPollCount:
    """``max_polls`` must terminate the loop even with no ``steps``."""

    def test_max_polls_fires_without_any_steps(self):
        """The regression test: this looped forever before the fix."""
        tracker = _tracker(max_polls=3, poll_interval=0.0)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
            result = tracker.stream_progress("http://poll", format=ProgressFormat.NONE)

        assert tracker._poll_count == 3
        assert len(tracker._poll_calls) == 3
        assert result.status == "IN_PROGRESS"

    @pytest.mark.parametrize("max_polls", [1, 2, 5])
    def test_poll_count_matches_max_polls_exactly(self, max_polls):
        tracker = _tracker(max_polls=max_polls, poll_interval=0.0)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
            tracker.stream_progress("http://poll", format=ProgressFormat.NONE)

        assert len(tracker._poll_calls) == max_polls

    def test_counter_matches_the_sibling_update_method(self):
        """``update()`` always incremented; the inconsistency *was* the bug."""
        tracker = _tracker()
        tracker.start(format=ProgressFormat.LOGS)

        tracker.update(_Response())
        tracker.update(_Response())

        assert tracker._poll_count == 2

    def test_steps_bearing_responses_still_count_once_each(self):
        """Moving the increment must not double-count a response with steps."""
        steps = [{"agent": "a", "tool": "t", "input": "i", "output": "o"}]
        tracker = _tracker([_Response(steps=steps)], max_polls=4, poll_interval=0.0)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
            tracker.stream_progress("http://poll", format=ProgressFormat.NONE)

        assert tracker._poll_count == 4
        assert len(tracker._poll_calls) == 4


class TestDeadline:
    """The ``timeout`` parameter, enforced as a wall-clock deadline."""

    def test_timeout_terminates_the_loop(self):
        tracker = _tracker(poll_interval=0.01)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
            result = tracker.stream_progress("http://poll", format=ProgressFormat.NONE, timeout=0.05)

        assert result.status == "IN_PROGRESS"
        assert tracker._poll_count >= 1

    def test_timeout_logs_a_warning_rather_than_raising(self, caplog):
        """A documented public method that has never raised still doesn't."""
        tracker = _tracker(poll_interval=0.01)

        with caplog.at_level("WARNING", logger="aixplain.v2.agent_progress"):
            with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
                tracker.stream_progress("http://poll", format=ProgressFormat.NONE, timeout=0.01)

        assert any("timed out" in record.message for record in caplog.records)

    def test_deadline_is_measured_from_the_start_with_a_fake_clock(self):
        """Exactly two polls fit a 10s budget when each poll advances the clock 6s."""
        clock = {"t": 0.0}
        responses = [_Response()]

        def poll(url):
            clock["t"] += 6.0
            return responses[0]

        tracker = AgentProgressTracker(poll_func=poll, poll_interval=1.0)

        with patch.object(type(tracker), "_now", lambda self: clock["t"]):
            with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
                tracker.stream_progress("http://poll", format=ProgressFormat.NONE, timeout=10.0)

        # Poll 1 at t=6 (4s left), poll 2 at t=12 -> budget exhausted, return.
        assert tracker._poll_count == 2

    def test_timeout_none_preserves_unbounded_behaviour(self):
        """Opt-out escape hatch; ``max_polls`` is then the only bound."""
        tracker = _tracker(max_polls=4, poll_interval=0.0)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
            tracker.stream_progress("http://poll", format=ProgressFormat.NONE, timeout=None)

        assert tracker._poll_count == 4

    def test_terminal_status_still_wins_over_the_deadline(self):
        tracker = _tracker([_Response(status="SUCCESS")], poll_interval=0.0)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
            result = tracker.stream_progress("http://poll", format=ProgressFormat.NONE, timeout=60)

        assert result.status == "SUCCESS"
        assert tracker._poll_count == 1

    @pytest.mark.parametrize("status", ["FAILED", "ABORTED", "CANCELLED", "ERROR"])
    def test_terminal_failures_still_return_immediately(self, status):
        tracker = _tracker([_Response(status=status)], poll_interval=0.0)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0):
            result = tracker.stream_progress("http://poll", format=ProgressFormat.NONE, timeout=60)

        assert result.status == status
        assert tracker._poll_count == 1


class TestSleepBehaviour:
    """The sleep must be jittered, backed off, and deadline-clamped."""

    def test_sleep_is_jittered_not_a_bare_time_sleep(self):
        tracker = _tracker(max_polls=3, poll_interval=0.5)

        with patch("aixplain.v2.agent_progress.sleep_with_jitter", return_value=0.0) as sleeper:
            with patch("aixplain.v2.agent_progress.time.sleep") as bare_sleep:
                tracker.stream_progress("http://poll", format=ProgressFormat.NONE)

        # One sleep per poll except the last, which returns instead.
        assert sleeper.call_count == 2
        bare_sleep.assert_not_called()

    def test_interval_backs_off_and_is_capped(self):
        tracker = _tracker(max_polls=6, poll_interval=0.5)
        waits = []

        with patch(
            "aixplain.v2.agent_progress.sleep_with_jitter",
            side_effect=lambda w, **k: waits.append(w) or 0.0,
        ):
            tracker.stream_progress("http://poll", format=ProgressFormat.NONE)

        assert waits == sorted(waits)
        assert waits[0] == pytest.approx(0.5)
        assert waits[1] == pytest.approx(0.55)
        assert all(w <= 60.0 for w in waits)

    def test_sleep_is_clamped_to_the_remaining_budget(self):
        tracker = _tracker(max_polls=3, poll_interval=30.0)
        clamps = []

        with patch(
            "aixplain.v2.agent_progress.sleep_with_jitter",
            side_effect=lambda w, **k: clamps.append(k.get("max_sleep")) or 0.0,
        ):
            tracker.stream_progress("http://poll", format=ProgressFormat.NONE, timeout=5.0)

        assert clamps
        assert all(c is not None and c <= 5.0 for c in clamps)

    def test_a_sub_refresh_rate_interval_is_floored(self):
        """A caller asking for 0.001s must not reinstate a 1,000 req/s loop."""
        tracker = _tracker(max_polls=2, poll_interval=0.001)
        waits = []

        with patch(
            "aixplain.v2.agent_progress.sleep_with_jitter",
            side_effect=lambda w, **k: waits.append(w) or 0.0,
        ):
            tracker.stream_progress("http://poll", format=ProgressFormat.NONE)

        assert waits[0] >= AgentProgressTracker.DISPLAY_REFRESH_RATE
