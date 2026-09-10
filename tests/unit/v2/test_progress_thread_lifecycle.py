"""Thread-lifecycle guarantees for the v2 agent progress display (BUG-943).

``AgentProgressTracker`` starts a daemon thread that repaints a spinner at
20 FPS, and the only thing that ever stopped it was ``finish()``. Three
independent holes meant ``finish()`` was routinely never called:

1. ``Agent._finish_progress_tracker`` skipped ``finish()`` when the result was
   an exception -- *and* then dropped the only reference to the tracker, so
   nothing could ever stop the thread afterwards.
2. ``RunnableResourceMixin.run`` had no exception handling at all, so
   ``sync_poll``'s ``TimeoutError`` and terminal ``APIError``s never reached
   ``after_run`` in the first place.
3. The tracker lived on the ``Agent`` instance, so two concurrent ``run()``
   calls overwrote each other: A's ``finish()`` stopped B's thread and A's span
   until process exit.

Each leaked thread then printed to stdout 20 times a second for the life of the
process -- including in non-TTY server containers, where it is pure log garbage
(hole 4: there was no ``isatty()`` check anywhere in the module).

The fix gives ``Agent.run`` / ``Agent.sync_poll`` sole ownership of the
tracker for the duration of the call, threads it down to ``on_poll`` as the
``_progress_tracker`` run kwarg, and gates only the 20 Hz repaint thread on
``isatty()`` -- the ``logs`` timeline and the completion summary are ordinary
newline-terminated output and are still written off a terminal.

Every assertion here is bounded: threads are joined with a timeout and the test
fails loudly naming the survivors, rather than sleeping and hoping.
"""

import io
import logging
import sys
import threading
import time
from unittest.mock import MagicMock

import pytest

from aixplain.v2 import agent_progress
from aixplain.v2.agent import Agent
from aixplain.v2.agent_progress import AgentProgressTracker, ProgressFormat
from aixplain.v2.exceptions import TimeoutError as AixplainTimeoutError
from aixplain.v2.session import Session, SessionMessage

JOIN_TIMEOUT = 2.0
PROGRESS_KWARGS = {"progress_format": "status"}


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_tty(monkeypatch):
    """Make the TTY gate answer True so the display thread actually starts.

    The predicate is patched rather than ``sys.stdout`` itself: pytest
    re-assigns ``sys.stdout`` when it resumes global capture for the call
    phase, so a monkeypatched stream would be silently replaced and every leak
    assertion below would pass vacuously against a thread that never started.
    """
    monkeypatch.setattr(agent_progress, "_stdout_is_tty", lambda: True)


@pytest.fixture
def trackers(monkeypatch):
    """Capture every tracker the run path builds, plus the threads it starts.

    The thread has to be recorded at ``start()`` time: teardown nulls
    ``_display_thread``, so reading it afterwards would hide a leak.
    """
    created = []
    real = agent_progress.AgentProgressTracker

    class _SpyTracker(real):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.started_threads = []
            created.append(self)

        def start(self, *args, **kwargs):
            super().start(*args, **kwargs)
            if self._display_thread is not None:
                self.started_threads.append(self._display_thread)

    monkeypatch.setattr(agent_progress, "AgentProgressTracker", _SpyTracker)
    return created


def assert_all_stopped(created, timeout: float = JOIN_TIMEOUT) -> None:
    """Join every display thread the run started; fail naming any survivor."""
    leaked = []
    for tracker in created:
        for thread in tracker.started_threads:
            thread.join(timeout=timeout)
            if thread.is_alive():
                leaked.append(thread.name)
    assert not leaked, f"leaked progress display threads: {leaked}"


def live_display_threads() -> list:
    """Every progress display thread currently alive, anywhere in the process."""
    name = AgentProgressTracker.DISPLAY_THREAD_NAME
    return [t for t in threading.enumerate() if t.name == name and t.is_alive()]


def assert_thread_count_restored(before: int, timeout: float = JOIN_TIMEOUT) -> None:
    """Wait (bounded) for the interpreter's thread count to drop back.

    Checks the named display threads first: they are the ones this module is
    about, and naming the survivor is far more useful than reporting a count.
    The count assertion then catches anything the module started that the name
    check would miss.
    """
    deadline = time.monotonic() + timeout
    while (live_display_threads() or threading.active_count() > before) and time.monotonic() < deadline:
        time.sleep(0.01)
    survivors = live_display_threads()
    assert not survivors, f"leaked progress display threads: {[t.name for t in survivors]}"
    assert threading.active_count() == before, (
        f"thread count did not return to {before} (now {threading.active_count()}); "
        f"alive: {[t.name for t in threading.enumerate()]}"
    )


class _FakeResult:
    """A poll/submit result shaped enough for the tracker and the run path."""

    def __init__(self, url=None, completed=True, status="SUCCESS", steps=None):
        self.url = url
        self.completed = completed
        self.status = status
        self.request_id = "req_1"
        self.session_id = "sess_1"
        self.data = None
        self._raw_data = {"data": {"steps": steps or []}}
        self._context = None


def _runnable_agent(submit_result=None):
    """An Agent whose POST is mocked out, ready for ``run(...)``."""
    agent = Agent.from_dict({"id": "a1", "name": "t"})
    agent.context = MagicMock()
    agent.status = None
    result = submit_result if submit_result is not None else _FakeResult(url="http://poll/1", completed=False)
    agent.handle_run_response = lambda response, **kwargs: result
    return agent


def _make_session_agent():
    """An Agent plus a Session whose ``add_message`` returns a request_id."""
    ctx = MagicMock(backend_url="https://platform-api.aixplain.com", api_key="k")

    class BoundAgent(Agent):
        context = ctx

    agent = BoundAgent(id="agent_99", name="A")
    agent._update_saved_state()

    session = Session(agent_id="agent_99", name="thread")
    session.id = "sess_1"
    session.context = ctx
    session.add_message = MagicMock(
        return_value=SessionMessage(
            id="msg_1",
            session_id="sess_1",
            user_id="u1",
            agent_id="agent_99",
            role="user",
            content="hi",
            sequence=1,
            request_id="req_abc",
            created_at="2025-06-01T10:01:00Z",
        )
    )
    return agent, session


# ---------------------------------------------------------------------------
# 1. The direct run path stops the thread on every failure mode
# ---------------------------------------------------------------------------


class TestDirectPathFailuresStopTheThread:
    """``run()`` had no ``try/finally``, so teardown was simply never reached."""

    @pytest.mark.parametrize(
        "error",
        [
            RuntimeError("backend blew up"),
            TimeoutError("Operation timed out after 300 seconds"),
        ],
        ids=["raise", "timeout"],
    )
    def test_failed_run_leaves_no_display_thread(self, fake_tty, trackers, error):
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(side_effect=error)
        before = threading.active_count()

        with pytest.raises(type(error)):
            agent.run(query="hi", **PROGRESS_KWARGS)

        assert trackers, "the run never built a progress tracker"
        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_failure_before_polling_leaves_no_display_thread(self, fake_tty, trackers):
        """The submit can fail too -- the tracker is already running by then."""
        agent = _runnable_agent()
        agent._submit_with_retries = MagicMock(side_effect=RuntimeError("POST failed"))
        before = threading.active_count()

        with pytest.raises(RuntimeError):
            agent.run(query="hi", **PROGRESS_KWARGS)

        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_successful_run_still_stops_the_thread(self, fake_tty, trackers):
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(return_value=_FakeResult(completed=True))
        before = threading.active_count()

        agent.run(query="hi", **PROGRESS_KWARGS)

        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_run_async_starts_no_tracker_and_warns(self, fake_tty, trackers, caplog):
        """``run_async`` returns at submission: it cannot drive a display.

        It used to start a tracker in ``before_run`` that nothing ever fed or
        stopped. Now it starts none and says so, pointing at ``sync_poll``.
        """
        agent = _runnable_agent(submit_result=_FakeResult(url="http://poll/1", completed=False))
        before = threading.active_count()

        with caplog.at_level(logging.WARNING, logger="aixplain.v2.agent"):
            result = agent.run_async(query="hi", **PROGRESS_KWARGS)

        assert result.url == "http://poll/1"
        assert trackers == [], "run_async must not build a tracker it cannot drive"
        assert threading.active_count() == before
        assert any("sync_poll" in record.getMessage() for record in caplog.records), (
            "run_async accepted progress_format silently"
        )

    def test_failed_run_async_leaves_no_thread(self, fake_tty, trackers):
        agent = _runnable_agent()
        agent._submit_with_retries = MagicMock(side_effect=RuntimeError("POST failed"))
        before = threading.active_count()

        with pytest.raises(RuntimeError, match="POST failed"):
            agent.run_async(query="hi", **PROGRESS_KWARGS)

        assert trackers == []
        assert threading.active_count() == before

    def test_run_async_then_sync_poll_with_progress_renders_and_stops(self, fake_tty, trackers, capsys):
        """The documented pairing: submit with ``run_async``, watch with ``sync_poll``.

        ``sync_poll`` owns a tracker of its own when handed the progress kwargs
        and no enclosing ``run()`` is driving it.
        """
        agent = _runnable_agent(submit_result=_FakeResult(url="http://poll/1", completed=False))
        steps = [{"agent": {"name": "Responder"}, "api_calls": 1}]
        agent.poll = MagicMock(
            side_effect=[
                _FakeResult(completed=False, status="IN_PROGRESS", steps=steps),
                _FakeResult(completed=True, status="SUCCESS", steps=steps),
            ]
        )
        before = threading.active_count()

        submitted = agent.run_async(query="hi")
        result = agent.sync_poll(submitted.url, wait_time=0.2, **PROGRESS_KWARGS)

        assert result.completed
        assert len(trackers) == 1, "sync_poll should own exactly one tracker"
        assert trackers[0]._poll_count == 2, "on_poll never reached sync_poll's tracker"
        assert trackers[0].started_threads, "a TTY poll should have animated"
        assert "✓ Completed" in capsys.readouterr().out
        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_a_failing_standalone_sync_poll_stops_the_thread(self, fake_tty, trackers):
        agent = _runnable_agent()
        before = threading.active_count()

        with pytest.raises(AixplainTimeoutError):
            agent.sync_poll("http://poll/1", timeout=0, **PROGRESS_KWARGS)

        assert trackers, "sync_poll never built a progress tracker"
        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_sync_poll_inside_run_does_not_start_a_second_tracker(self, fake_tty, trackers):
        """``run()`` calls ``sync_poll`` with the progress kwargs still present."""
        agent = _runnable_agent()
        agent.poll = MagicMock(return_value=_FakeResult(completed=True))

        agent.run(query="hi", **PROGRESS_KWARGS)

        assert len(trackers) == 1, "the enclosing run() owns the display; sync_poll must not add one"
        assert_all_stopped(trackers)

    def test_an_after_run_override_that_skips_super_cannot_leak(self, fake_tty, trackers):
        """Teardown belongs to ``run()``, not to a hook a subclass may replace."""
        agent = _runnable_agent()
        agent.after_run = lambda result, *args, **kwargs: None
        agent.sync_poll = MagicMock(side_effect=[_FakeResult(completed=True), RuntimeError("second run fails")])
        before = threading.active_count()

        agent.run(query="hi", **PROGRESS_KWARGS)
        with pytest.raises(RuntimeError):
            agent.run(query="hi", **PROGRESS_KWARGS)

        assert len(trackers) == 2
        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_a_nested_progress_less_run_cannot_touch_the_outer_display(self, fake_tty, trackers):
        """Nothing is shared between runs, so a hook that starts another run is harmless.

        With a context-wide slot, a nested ``run_async()`` without progress
        adopted and stopped the *outer* run's tracker on its way out.
        """
        outer = _runnable_agent()
        inner = _runnable_agent(submit_result=_FakeResult(url="http://poll/2", completed=False))
        steps = [{"agent": {"name": "Responder"}, "api_calls": 1}]
        seen_alive = []

        def poll(url, timeout=None):
            if not seen_alive:
                inner.run_async(query="nested")
                seen_alive.append(trackers[0].started_threads[0].is_alive())
                return _FakeResult(completed=False, status="IN_PROGRESS", steps=steps)
            return _FakeResult(completed=True, status="SUCCESS", steps=steps)

        outer.poll = poll
        before = threading.active_count()

        outer.run(query="hi", wait_time=0.2, **PROGRESS_KWARGS)

        assert len(trackers) == 1, "the nested progress-less run must not build a tracker"
        assert seen_alive == [True], "the nested run stopped the outer display"
        assert trackers[0]._poll_count == 2
        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_the_run_owned_tracker_still_receives_poll_updates(self, fake_tty, trackers, capsys):
        """Moving the tracker off ``self`` must not unhook ``on_poll``.

        ``on_poll`` is the only thing that feeds the display, and it now
        receives the tracker as a run kwarg rather than reading the instance.
        Without this, every other assertion in the module would still pass
        against a tracker that was simply never fed.
        """
        agent = _runnable_agent()
        steps = [{"agent": {"name": "Responder"}, "api_calls": 1}]
        agent.poll = MagicMock(
            side_effect=[
                _FakeResult(completed=False, status="IN_PROGRESS", steps=steps),
                _FakeResult(completed=True, status="SUCCESS", steps=steps),
            ]
        )

        agent.run(query="hi", wait_time=0.2, **PROGRESS_KWARGS)

        assert len(trackers) == 1
        tracker = trackers[0]
        assert tracker._poll_count == 2, "on_poll never reached the run's tracker"
        assert tracker._total_api_calls == 1
        assert capsys.readouterr().out != "", "a TTY run rendered nothing at all"


# ---------------------------------------------------------------------------
# 2. The session run path
# ---------------------------------------------------------------------------


class TestSessionPathFailuresStopTheThread:
    """The session path already had an ``except``; it leaked anyway (hole 1)."""

    @pytest.mark.parametrize(
        "error",
        [
            RuntimeError("backend blew up"),
            TimeoutError("Operation timed out after 300 seconds"),
        ],
        ids=["raise", "timeout"],
    )
    def test_failed_session_run_leaves_no_display_thread(self, fake_tty, trackers, error):
        agent, session = _make_session_agent()
        agent.sync_poll = MagicMock(side_effect=error)
        before = threading.active_count()

        with pytest.raises(type(error)):
            agent.run("hi", session=session, **PROGRESS_KWARGS)

        assert trackers, "the session run never built a progress tracker"
        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_successful_session_run_leaves_no_display_thread(self, fake_tty, trackers):
        agent, session = _make_session_agent()
        agent.sync_poll = MagicMock(return_value=_FakeResult(completed=True))
        before = threading.active_count()

        agent.run("hi", session=session, **PROGRESS_KWARGS)

        assert_all_stopped(trackers)
        assert_thread_count_restored(before)


# ---------------------------------------------------------------------------
# 3. Concurrency: one Agent, two runs
# ---------------------------------------------------------------------------


def test_concurrent_runs_on_one_agent_leave_no_thread(fake_tty, trackers):
    """Two runs must own two independent trackers and stop both.

    With the tracker on ``self``, B overwrote A; A's ``finish()`` then stopped
    B's thread while A's spun forever. The barrier guarantees both trackers are
    live simultaneously, which is exactly the overwrite window.
    """
    agent = _runnable_agent()
    barrier = threading.Barrier(2, timeout=JOIN_TIMEOUT)
    outcomes = {}

    def sync_poll(url, **kwargs):
        barrier.wait()
        if threading.current_thread().name == "run-fails":
            raise RuntimeError("this one fails")
        return _FakeResult(completed=True)

    agent.sync_poll = sync_poll

    def worker(name):
        try:
            agent.run(query="hi", **PROGRESS_KWARGS)
            outcomes[name] = "ok"
        except RuntimeError:
            outcomes[name] = "raised"

    before = threading.active_count()
    workers = [
        threading.Thread(target=worker, args=("run-ok",), name="run-ok"),
        threading.Thread(target=worker, args=("run-fails",), name="run-fails"),
    ]
    for thread in workers:
        thread.start()
    for thread in workers:
        thread.join(timeout=JOIN_TIMEOUT * 2)
        assert not thread.is_alive(), f"{thread.name} never finished"

    assert outcomes == {"run-ok": "ok", "run-fails": "raised"}
    assert len(trackers) == 2, f"expected one tracker per run, got {len(trackers)}"
    assert trackers[0] is not trackers[1]
    assert_all_stopped(trackers)
    assert_thread_count_restored(before)


# ---------------------------------------------------------------------------
# 4. The TTY gate
# ---------------------------------------------------------------------------


class TestTtyGate:
    """A pipe is not a human: off a terminal, no repaint thread.

    Only the 20 Hz carriage-return animation is gated. The ``logs`` timeline and the
    completion summary are written from the caller's thread with ordinary
    newlines, and a CI log or a ``tee`` must still get them in full.
    """

    def test_non_tty_run_starts_no_thread_but_still_prints_the_summary(self, trackers, capsys):
        assert not agent_progress._stdout_is_tty(), "capsys should not look like a terminal"
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(return_value=_FakeResult(completed=True, steps=[{"agent": {"name": "A"}}]))
        before = threading.active_count()

        agent.run(query="hi", **PROGRESS_KWARGS)

        assert trackers, "the run never built a progress tracker"
        assert all(tracker.started_threads == [] for tracker in trackers)
        out = capsys.readouterr().out
        assert "✓ Completed 1 steps" in out
        assert out.endswith("\n")
        assert threading.active_count() == before

    def test_logs_format_under_a_pipe_prints_the_full_timeline(self, trackers, capsys):
        """A run piped through ``tee`` or into a CI log keeps its step timeline."""
        assert not agent_progress._stdout_is_tty()
        agent = _runnable_agent()
        running = [{"agent": {"name": "Researcher"}, "api_calls": 1}]
        done = [{"agent": {"name": "Researcher"}, "api_calls": 1, "output": "found it", "used_credits": 0.5}]
        agent.poll = MagicMock(
            side_effect=[
                _FakeResult(completed=False, status="IN_PROGRESS", steps=running),
                _FakeResult(completed=True, status="SUCCESS", steps=done),
            ]
        )
        before = threading.active_count()

        agent.run(query="hi", wait_time=0.2, progress_format="logs")

        assert all(tracker.started_threads == [] for tracker in trackers)
        out = capsys.readouterr().out
        assert "Researcher" in out, "the logs timeline was suppressed off a terminal"
        assert "✓ Completed 1 steps" in out
        assert "$0.5" in out, "the credits summary was suppressed off a terminal"
        assert threading.active_count() == before

    def test_non_tty_logs_tracker_prints_the_timeline_and_summary_without_a_thread(self, capsys):
        assert not agent_progress._stdout_is_tty()
        tracker = AgentProgressTracker(poll_func=lambda _: None)
        response = _FakeResult(steps=[{"agent": {"name": "A"}, "output": "done"}])

        tracker.start(format=ProgressFormat.LOGS)
        tracker.update(response)
        tracker.finish(response)

        assert tracker._display_thread is None
        out = capsys.readouterr().out
        assert "A" in out
        assert "✓ Completed 1 steps" in out
        assert out.endswith("\n")

    def test_non_tty_status_tracker_prints_only_the_summary(self, capsys):
        """Status mode paints from the thread; with no thread only the summary is left."""
        assert not agent_progress._stdout_is_tty()
        tracker = AgentProgressTracker(poll_func=lambda _: None)
        response = _FakeResult(steps=[{"agent": {"name": "A"}, "output": "done"}])

        tracker.start(format=ProgressFormat.STATUS)
        tracker.update(response)
        assert capsys.readouterr().out == "", "status mode must not paint from the caller thread"
        tracker.finish(response)

        assert tracker._display_thread is None
        out = capsys.readouterr().out
        assert out.startswith("\n✓ Completed 1 steps")
        assert out.endswith("\n")

    def test_bookkeeping_still_runs_with_the_animation_off(self, fake_tty):
        """The poll counter and metrics are not display state (BUG-942)."""
        tracker = AgentProgressTracker(poll_func=lambda _: None, force_display=False)
        response = _FakeResult(steps=[{"agent": {"name": "A"}, "api_calls": 2}])

        tracker.start(format=ProgressFormat.LOGS)
        tracker.update(response)
        tracker.update(response)

        assert tracker._display_thread is None
        assert tracker._poll_count == 2
        assert tracker._total_api_calls == 2

    def test_force_display_kwarg_animates_a_non_tty_stdout(self, capsys):
        tracker = AgentProgressTracker(poll_func=lambda _: None, force_display=True)
        response = _FakeResult(steps=[{"agent": {"name": "A"}, "output": "done"}])

        tracker.start(format=ProgressFormat.LOGS)
        try:
            assert tracker._display_thread is not None and tracker._display_thread.is_alive()
            tracker.update(response)
        finally:
            tracker.stop()

        assert capsys.readouterr().out != ""

    @pytest.mark.parametrize("value", ["1", "true", "YES", " on "])
    def test_a_truthy_force_display_env_var_animates_a_non_tty_stdout(self, monkeypatch, value):
        monkeypatch.setenv("AIXPLAIN_PROGRESS_FORCE_DISPLAY", value)
        tracker = AgentProgressTracker(poll_func=lambda _: None)

        tracker.start(format=ProgressFormat.STATUS)
        try:
            assert tracker._display_thread is not None, f"{value!r} should opt in to the animation"
        finally:
            tracker.stop()

    @pytest.mark.parametrize("value", ["false", "0", "no", "off", "", "maybe"])
    def test_a_non_truthy_force_display_env_var_leaves_a_real_tty_animated(self, monkeypatch, fake_tty, value):
        """The variable is an opt-in only: ``false`` is no opinion, not a veto."""
        monkeypatch.setenv("AIXPLAIN_PROGRESS_FORCE_DISPLAY", value)
        tracker = AgentProgressTracker(poll_func=lambda _: None)

        tracker.start(format=ProgressFormat.STATUS)
        try:
            assert tracker._display_thread is not None, f"{value!r} disabled the animation on a real TTY"
        finally:
            tracker.stop()

    @pytest.mark.parametrize("value", ["false", "0"])
    def test_a_non_truthy_force_display_env_var_does_not_animate_a_pipe(self, monkeypatch, value):
        monkeypatch.setenv("AIXPLAIN_PROGRESS_FORCE_DISPLAY", value)
        tracker = AgentProgressTracker(poll_func=lambda _: None)

        tracker.start(format=ProgressFormat.STATUS)
        tracker.stop()

        assert tracker._display_thread is None

    def test_force_display_false_stops_the_animation_on_a_real_tty(self, fake_tty, capsys):
        tracker = AgentProgressTracker(poll_func=lambda _: None, force_display=False)

        tracker.start(format=ProgressFormat.STATUS)
        tracker.update(_FakeResult(steps=[{"agent": {"name": "A"}, "output": "done"}]))

        assert tracker._display_thread is None
        assert capsys.readouterr().out == ""

    def test_notebook_path_still_renders_without_a_tty(self, monkeypatch, capsys):
        """ipykernel's stdout is not a tty but is very much a display."""
        monkeypatch.setattr(agent_progress, "_is_notebook_environment", lambda: True)
        tracker = AgentProgressTracker(poll_func=lambda _: None)
        assert tracker._is_notebook

        tracker.start(format=ProgressFormat.STATUS)
        tracker.update(_FakeResult(steps=[{"agent": {"name": "A"}}]))

        # Notebooks never used the background thread; they repaint synchronously.
        assert tracker._display_thread is None
        assert capsys.readouterr().out != ""

    def test_a_closed_stdout_is_not_a_tty(self, monkeypatch):
        """A detached or replaced stream must answer False, never raise."""
        stream = io.StringIO()
        stream.close()
        monkeypatch.setattr(sys, "stdout", stream)

        assert agent_progress._stdout_is_tty() is False

        monkeypatch.setattr(sys, "stdout", None)
        assert agent_progress._stdout_is_tty() is False


# ---------------------------------------------------------------------------
# 5. The refresh loop: lock released before waiting, immediate shutdown
# ---------------------------------------------------------------------------


class TestRefreshLoop:
    """``update()`` takes ``_display_lock`` too -- holding it across the sleep
    made every leaked tracker throttle the live run that followed it."""

    @staticmethod
    def _slow_tracker():
        """A started tracker whose refresh interval is far longer than any bound."""
        tracker = AgentProgressTracker(poll_func=lambda _: None, force_display=True)
        tracker.DISPLAY_REFRESH_RATE = 5.0
        tracker.start(format=ProgressFormat.STATUS)
        return tracker

    def test_display_lock_is_free_during_a_refresh_cycle(self):
        tracker = self._slow_tracker()
        try:
            # Repeated so the check cannot slip through the microsecond gap
            # between two iterations of a lock-holding loop.
            for attempt in range(5):
                acquired = tracker._display_lock.acquire(timeout=0.5)
                assert acquired, f"_display_lock was held across the refresh interval (attempt {attempt})"
                tracker._display_lock.release()
        finally:
            tracker.stop()

    def test_stop_returns_immediately_at_a_long_refresh_rate(self):
        tracker = self._slow_tracker()
        thread = tracker._display_thread
        assert thread is not None

        started = time.monotonic()
        tracker.stop()
        elapsed = time.monotonic() - started

        assert not thread.is_alive(), "the display thread outlived stop()"
        assert elapsed < 1.0, f"stop() waited {elapsed:.2f}s; Event.wait should be immediate"

    @pytest.mark.parametrize("fmt", [ProgressFormat.STATUS, ProgressFormat.LOGS], ids=["status", "logs"])
    def test_the_thread_renders_a_frame_and_still_exits_promptly(self, fake_tty, capsys, fmt):
        """The rewritten loop must keep repainting -- and keep the lock free.

        This is the 20 Hz printer itself: with data present it renders outside
        the lock, so ``update()`` and ``stop()`` are never blocked by a frame.
        """
        painted = threading.Event()
        tracker = AgentProgressTracker(poll_func=lambda _: None, force_display=True)
        real_status = tracker._refresh_status_display
        real_logs = tracker._refresh_logs_display

        def spy_status(steps):
            real_status(steps)
            painted.set()

        def spy_logs(steps):
            real_logs(steps)
            painted.set()

        tracker._refresh_status_display = spy_status
        tracker._refresh_logs_display = spy_logs

        tracker.start(format=fmt)
        try:
            tracker.update(_FakeResult(steps=[{"agent": {"name": "Responder"}, "api_calls": 1}]))
            assert painted.wait(timeout=JOIN_TIMEOUT), "the display thread never rendered a frame"
            assert tracker._display_lock.acquire(timeout=0.5), "_display_lock was held across a render"
            tracker._display_lock.release()
        finally:
            thread = tracker._display_thread
            tracker.stop()

        assert thread is not None and not thread.is_alive()
        assert capsys.readouterr().out != ""

    def test_a_second_start_does_not_orphan_the_first_thread(self, fake_tty):
        """``stream_progress`` calls ``start()``; a tracker may already have one.

        The second ``start()`` used to clear the shared stop event and overwrite
        ``_display_thread``, dropping the only reference to a thread that kept
        printing -- two spinners interleaving on one fd.
        """
        tracker = AgentProgressTracker(poll_func=lambda _: None)
        tracker.start(format=ProgressFormat.STATUS)
        first = tracker._display_thread
        assert first is not None

        tracker.start(format=ProgressFormat.STATUS)
        second = tracker._display_thread
        try:
            assert second is not None and second is not first
            first.join(timeout=JOIN_TIMEOUT)
            assert not first.is_alive(), "the first display thread outlived the second start()"
            assert second.is_alive(), "the second start() must leave a live thread"
        finally:
            tracker.stop()

        assert not second.is_alive()
        assert live_display_threads() == []

    def test_a_thread_that_outlives_its_join_is_not_re_armed_by_the_next_start(self, caplog):
        """A painter blocked in ``print()`` (full pipe, paused pager) survives ``stop()``.

        ``start()`` used to ``clear()`` the one shared stop event, which
        re-armed that survivor alongside the new thread: two painters on one
        fd and no reference left to join the first. Each ``start()`` now binds
        a fresh event, so the survivor's own event stays set and it exits the
        moment ``print()`` returns.
        """
        tracker = AgentProgressTracker(poll_func=lambda _: None, force_display=True)
        tracker.DISPLAY_JOIN_TIMEOUT = 0.05
        entered = threading.Event()
        release = threading.Event()

        def stuck_render(steps):
            entered.set()
            assert release.wait(timeout=JOIN_TIMEOUT), "test never released the stuck painter"

        tracker._refresh_status_display = stuck_render
        tracker.start(format=ProgressFormat.STATUS)
        first = tracker._display_thread
        assert first is not None
        tracker.update(_FakeResult(steps=[{"agent": {"name": "A"}}]))
        assert entered.wait(timeout=JOIN_TIMEOUT), "the painter never reached the render"

        with caplog.at_level(logging.WARNING, logger="aixplain.v2.agent_progress"):
            tracker.stop()
        assert first.is_alive(), "precondition: the painter must survive the bounded join"
        assert any("did not exit" in record.getMessage() for record in caplog.records)

        tracker.start(format=ProgressFormat.STATUS)
        second = tracker._display_thread
        assert second is not None and second is not first
        try:
            release.set()
            first.join(timeout=JOIN_TIMEOUT)
            assert not first.is_alive(), "the surviving painter was re-armed by the next start()"
            assert second.is_alive()
        finally:
            tracker.stop()

        second.join(timeout=JOIN_TIMEOUT)
        assert not second.is_alive()
        assert live_display_threads() == []

    def test_stop_is_idempotent_and_safe_when_never_started(self):
        never_started = AgentProgressTracker(poll_func=lambda _: None)
        never_started.stop()
        never_started.stop()

        disabled = AgentProgressTracker(poll_func=lambda _: None, force_display=True)
        disabled.start(format=ProgressFormat.NONE)
        disabled.stop()
        disabled.stop()

        assert disabled._display_thread is None

    def test_finish_after_an_error_renders_nothing_but_still_stops(self, fake_tty, capsys):
        """An errored run stops cleanly; it does not print a completion summary."""
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(side_effect=RuntimeError("nope"))

        with pytest.raises(RuntimeError):
            agent.run(query="hi", **PROGRESS_KWARGS)

        assert "Completed" not in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 6. stream_progress: the standalone loop is gated and torn down the same way
# ---------------------------------------------------------------------------


class _StreamResponse:
    """A poll response for ``stream_progress``: a status and optional steps."""

    def __init__(self, status="IN_PROGRESS", steps=None):
        self.status = status
        self._raw_data = {"data": {"steps": steps or []}}


def _stream_tracker(responses, **kwargs):
    """A tracker whose poll returns *responses* in order, then repeats the last."""
    calls = []

    def poll(url):
        calls.append(url)
        return responses[min(len(calls) - 1, len(responses) - 1)]

    tracker = AgentProgressTracker(poll_func=poll, poll_interval=0.0, **kwargs)
    return tracker


class TestStreamProgressDisplayGate:
    """``stream_progress`` owns its own loop; it must obey the same gate."""

    STEPS = [{"agent": {"name": "A"}, "output": "done", "api_calls": 1}]

    @pytest.mark.parametrize(
        ("status", "expected"),
        [("SUCCESS", "✓ Completed"), ("FAILED", "✗ Agent failed")],
        ids=["success", "failure"],
    )
    def test_terminal_status_prints_a_summary_when_display_is_on(self, capsys, status, expected):
        tracker = _stream_tracker([_StreamResponse(status, self.STEPS)], force_display=True)

        tracker.stream_progress("http://poll", format=ProgressFormat.LOGS)

        assert expected in capsys.readouterr().out
        assert tracker._display_thread is None

    def test_max_polls_prints_a_summary_when_display_is_on(self, capsys):
        tracker = _stream_tracker([_StreamResponse(steps=self.STEPS)], max_polls=2, force_display=True)

        tracker.stream_progress("http://poll", format=ProgressFormat.LOGS)

        assert "reached max polling limit" in capsys.readouterr().out
        assert tracker._poll_count == 2

    def test_timeout_prints_a_summary_and_still_raises(self, capsys):
        tracker = _stream_tracker([_StreamResponse(steps=self.STEPS)], force_display=True)

        with pytest.raises(TimeoutError):
            tracker.stream_progress("http://poll", format=ProgressFormat.LOGS, timeout=0.0)

        assert "progress stream timed out" in capsys.readouterr().out

    @pytest.mark.parametrize(
        ("status", "expected"),
        [("SUCCESS", "✓ Completed"), ("FAILED", "✗ Agent failed")],
        ids=["success", "failure"],
    )
    def test_off_a_terminal_the_timeline_and_summary_print_without_a_thread(self, capsys, status, expected):
        assert not agent_progress._stdout_is_tty()
        tracker = _stream_tracker([_StreamResponse(status, self.STEPS)])
        started = []
        real_start = tracker.start

        def spy_start(*args, **kwargs):
            real_start(*args, **kwargs)
            started.append(tracker._display_thread)

        tracker.start = spy_start

        tracker.stream_progress("http://poll", format=ProgressFormat.LOGS)

        assert started == [None], "stream_progress started a repaint thread off a terminal"
        out = capsys.readouterr().out
        assert "A" in out
        assert expected in out

    def test_the_display_thread_is_stopped_even_when_the_loop_raises(self, fake_tty):
        tracker = _stream_tracker([_StreamResponse(steps=self.STEPS)])
        tracker.start(format=ProgressFormat.STATUS)
        thread = tracker._display_thread
        assert thread is not None, "the tty gate should have started a display thread"

        def exploding_poll(url):
            raise RuntimeError("poll died")

        tracker.poll = exploding_poll
        with pytest.raises(RuntimeError, match="poll died"):
            tracker.stream_progress("http://poll", format=ProgressFormat.STATUS)

        thread.join(timeout=JOIN_TIMEOUT)
        assert not thread.is_alive()
        assert tracker._display_thread is None


# ---------------------------------------------------------------------------
# 7. The run() teardown must not change what run() returns or raises
# ---------------------------------------------------------------------------


class TestRunSemanticsArePreserved:
    """Teardown is additive: it may not swallow, substitute, or reorder."""

    def test_run_returns_the_after_run_result_unchanged(self):
        agent = _runnable_agent()
        expected = _FakeResult(completed=True)
        agent.sync_poll = MagicMock(return_value=expected)

        assert agent.run(query="hi") is expected

    def test_after_run_may_still_substitute_the_result_on_success(self):
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(return_value=_FakeResult(completed=True))
        substitute = _FakeResult(completed=True)
        agent.after_run = lambda result, *args, **kwargs: substitute

        assert agent.run(query="hi") is substitute

    def test_after_run_cannot_turn_a_raise_into_a_return(self):
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(side_effect=RuntimeError("boom"))
        agent.after_run = lambda result, *args, **kwargs: _FakeResult(completed=True)

        with pytest.raises(RuntimeError, match="boom"):
            agent.run(query="hi")

    def test_a_raising_after_run_hook_cannot_mask_the_original_exception(self):
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(side_effect=RuntimeError("original"))

        def exploding_after_run(result, *args, **kwargs):
            raise ValueError("teardown blew up")

        agent.after_run = exploding_after_run

        with pytest.raises(RuntimeError, match="original"):
            agent.run(query="hi")

    def test_a_render_error_in_finish_does_not_discard_the_result(self, fake_tty, trackers, monkeypatch, caplog):
        """The run is complete and billed; a console that cannot print ``✓`` must not lose it.

        ``finish`` here raises *before* stopping the thread, so the test also
        pins that the owner's teardown still runs after a failed render.
        """
        agent = _runnable_agent()
        expected = _FakeResult(completed=True)
        agent.sync_poll = MagicMock(return_value=expected)

        def exploding_finish(self, response):
            raise UnicodeEncodeError("ascii", "✓", 0, 1, "ordinal not in range(128)")

        monkeypatch.setattr(AgentProgressTracker, "finish", exploding_finish)
        before = threading.active_count()

        with caplog.at_level(logging.WARNING, logger="aixplain.v2.agent"):
            result = agent.run(query="hi", **PROGRESS_KWARGS)

        assert result is expected
        assert any("completion summary" in record.getMessage() for record in caplog.records)
        assert_all_stopped(trackers)
        assert_thread_count_restored(before)

    def test_keyboard_interrupt_also_stops_the_thread(self, fake_tty, trackers):
        """A Ctrl-C in a notebook leaves the kernel -- and the leak -- alive."""
        agent = _runnable_agent()
        agent.sync_poll = MagicMock(side_effect=KeyboardInterrupt())
        before = threading.active_count()

        with pytest.raises(KeyboardInterrupt):
            agent.run(query="hi", **PROGRESS_KWARGS)

        assert_all_stopped(trackers)
        assert_thread_count_restored(before)


# ---------------------------------------------------------------------------
# 8. Structural guarantees
# ---------------------------------------------------------------------------


def test_the_agent_holds_no_progress_tracker_state():
    """A per-instance slot is what caused hole 3; the tracker now lives in the run's kwargs only."""
    agent = _runnable_agent()

    assert not hasattr(agent, "_progress_tracker")
    assert "_progress_tracker" in Agent._RUN_CONTROL_KEYS
    assert "_progress_tracker" not in agent.build_run_payload(query="hi", _progress_tracker=object())
