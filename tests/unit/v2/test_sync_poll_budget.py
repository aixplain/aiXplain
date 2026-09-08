"""Unit tests for ``sync_poll``'s time budget and jittered sleeps.

Two defects are pinned here:

* ``sync_poll`` checked its deadline only *between* polls, and ``poll()`` sent
  its request with no ``timeout``, so the client's own 300s read timeout
  applied.  With the 300s ``sync_poll`` default one hung poll consumed the whole
  budget -- and up to ``DEFAULT_RETRY_TOTAL`` times that, since GET is still
  retryable at the transport layer (BUG-1097, second-order item). The read
  timeout is therefore divided by ``retry_total + 1``: bounding one *request*
  is not the same as bounding the wall clock when urllib3 re-sends it
  underneath ``requests``.
* The sleep between polls was deterministic, keeping a fleet phase-locked
  (BUG-942 item 1).
"""

import time
from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest
from dataclasses_json import dataclass_json

from aixplain.v2.agent import Agent
from aixplain.v2.client import DEFAULT_RETRY_TOTAL, DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ
from aixplain.v2.exceptions import TimeoutError as AixplainTimeoutError

BACKEND_URL = "https://platform-api.aixplain.com"

IN_PROGRESS = {"status": "IN_PROGRESS", "completed": False, "data": {}}
SUCCESS = {"status": "SUCCESS", "completed": True, "data": {}}


def _create_agent(responses=None):
    """Agent with a mocked client whose ``get`` returns *responses* in order."""

    @dataclass_json
    @dataclass
    class BoundAgent(Agent):
        pass

    agent = BoundAgent(id="agent-123", name="test-agent")
    agent.context = Mock()
    agent.context.backend_url = BACKEND_URL
    # A Mock attribute is not an int, so spell the transport retry budget out
    # rather than leaning on ``_client_retry_attempts``'s fallback.
    agent.context.client.retry_total = DEFAULT_RETRY_TOTAL
    if responses is not None:
        agent.context.client.get = Mock(side_effect=list(responses))
    return agent


def _read_timeouts(client_get):
    """The read component of every ``timeout=`` the client was called with."""
    timeouts = []
    for call in client_get.call_args_list:
        timeout = call.kwargs.get("timeout")
        assert timeout is not None, "poll must bound its own request"
        timeouts.append(timeout[1])
    return timeouts


class TestPollRequestTimeout:
    """``poll`` must be able to bound a single request."""

    def test_poll_without_timeout_leaves_the_client_default(self):
        """Additive change: a bare ``poll(url)`` behaves exactly as before."""
        agent = _create_agent([SUCCESS])

        agent.poll("exec-1")

        assert "timeout" not in agent.context.client.get.call_args.kwargs

    def test_poll_with_timeout_passes_a_connect_read_tuple(self):
        """The budget is a *wall-clock* bound, so it is split across attempts."""
        agent = _create_agent([SUCCESS])

        agent.poll("exec-1", timeout=42.0)

        assert agent.context.client.get.call_args.kwargs["timeout"] == (
            DEFAULT_TIMEOUT_CONNECT,
            42.0 / (DEFAULT_RETRY_TOTAL + 1),
        )

    def test_read_timeout_is_capped_at_the_client_default(self):
        """A caller's budget must not widen the bound the deployment configured."""
        agent = _create_agent([SUCCESS])

        agent.poll("exec-1", timeout=DEFAULT_TIMEOUT_READ * 10)

        assert agent.context.client.get.call_args.kwargs["timeout"][1] == DEFAULT_TIMEOUT_READ

    @pytest.mark.parametrize("budget", [0.001, 0.5, 1.0])
    def test_read_timeout_is_floored_at_one_second(self, budget):
        """A nearly-exhausted budget must still send a real request.

        Otherwise the last poll before the deadline is guaranteed to time out.
        """
        agent = _create_agent([SUCCESS])

        agent.poll("exec-1", timeout=budget)

        assert agent.context.client.get.call_args.kwargs["timeout"][1] == 1.0


class TestPollHonoursTheClientTimeout:
    """The cap must come from the client, not from the module default.

    A deployment that narrowed ``AixplainClient(timeout=...)`` did so to bound
    its own requests; reading ``default_timeout()`` instead would silently
    widen a poll back out to the 300s module default.
    """

    @staticmethod
    def _agent_with_client_timeout(timeout):
        agent = _create_agent([SUCCESS])
        agent.context.client.timeout = timeout
        return agent

    def test_tuple_timeout_is_honoured(self):
        agent = self._agent_with_client_timeout((3.0, 20.0))

        agent.poll("exec-1", timeout=999.0)

        assert agent.context.client.get.call_args.kwargs["timeout"] == (3.0, 20.0)

    def test_scalar_timeout_is_honoured_for_both_phases(self):
        agent = self._agent_with_client_timeout(15.0)

        agent.poll("exec-1", timeout=999.0)

        assert agent.context.client.get.call_args.kwargs["timeout"] == (15.0, 15.0)

    def test_a_budget_below_the_client_bound_still_wins(self):
        agent = self._agent_with_client_timeout((3.0, 200.0))

        agent.poll("exec-1", timeout=7.0)

        assert agent.context.client.get.call_args.kwargs["timeout"] == (
            3.0,
            7.0 / (DEFAULT_RETRY_TOTAL + 1),
        )

    @pytest.mark.parametrize("configured", [None, "not-a-timeout", (1.0, 2.0, 3.0)])
    def test_unrecognisable_client_timeout_falls_back_to_the_defaults(self, configured):
        """A mock or a malformed value must still produce a bounded request."""
        agent = self._agent_with_client_timeout(configured)

        agent.poll("exec-1", timeout=999.0)

        assert agent.context.client.get.call_args.kwargs["timeout"] == (
            DEFAULT_TIMEOUT_CONNECT,
            999.0 / (DEFAULT_RETRY_TOTAL + 1),
        )

    def test_a_real_client_reports_its_own_configuration(self):
        """End-to-end through the actual client, not a mock."""
        from aixplain.v2.client import AixplainClient
        from aixplain.v2.resource import _client_timeout_bounds

        client = AixplainClient(base_url=BACKEND_URL, team_api_key="k", timeout=(2.0, 8.0))

        assert _client_timeout_bounds(client) == (2.0, 8.0)


class TestTransportRetriesDoNotMultiplyTheBudget:
    """The wall-clock budget must survive urllib3's retries (BUG-1097).

    ``GET`` is in ``RETRY_ALLOWED_METHODS``, so a ``ReadTimeoutError`` is
    re-sent up to ``retry_total`` more times *below* ``requests``. A read
    timeout equal to the whole remaining budget therefore let a hung endpoint
    block ``timeout * (retry_total + 1)`` seconds before ``sync_poll`` looked at
    its deadline again -- ~30 minutes for the 300s default.
    """

    @staticmethod
    def _agent_with_retry_total(total):
        agent = _create_agent([SUCCESS])
        agent.context.client.retry_total = total
        agent.context.client.timeout = (10.0, 10000.0)  # never the binding constraint
        return agent

    @pytest.mark.parametrize("retry_total", [0, 1, 3, 5, 10])
    def test_read_timeout_times_attempts_never_exceeds_the_budget(self, retry_total):
        agent = self._agent_with_retry_total(retry_total)

        agent.poll("exec-1", timeout=600.0)

        read = agent.context.client.get.call_args.kwargs["timeout"][1]
        assert read * (retry_total + 1) <= 600.0

    def test_a_zero_retry_client_gets_the_whole_budget(self):
        """Nothing is given away when the transport cannot re-send at all."""
        agent = self._agent_with_retry_total(0)

        agent.poll("exec-1", timeout=600.0)

        assert agent.context.client.get.call_args.kwargs["timeout"][1] == 600.0

    def test_the_default_client_budget_is_not_multiplied_by_six(self):
        """The reported symptom: ``sync_poll(timeout=300)`` blocking ~30 minutes."""
        agent = self._agent_with_retry_total(DEFAULT_RETRY_TOTAL)

        agent.poll("exec-1", timeout=300.0)

        read = agent.context.client.get.call_args.kwargs["timeout"][1]
        assert read == 50.0
        assert read * (DEFAULT_RETRY_TOTAL + 1) == 300.0

    @pytest.mark.parametrize("configured", [None, "five", -1, True])
    def test_an_unusable_retry_total_falls_back_conservatively(self, configured):
        """A mock or a nonsense value must shorten the bound, never widen it."""
        from aixplain.v2.resource import _client_retry_attempts

        agent = self._agent_with_retry_total(configured)

        assert _client_retry_attempts(agent.context.client) == DEFAULT_RETRY_TOTAL + 1

    def test_a_real_client_reports_its_own_retry_total(self):
        """End-to-end through the actual client, not a mock."""
        from aixplain.v2.client import AixplainClient
        from aixplain.v2.resource import _client_retry_attempts

        client = AixplainClient(base_url=BACKEND_URL, team_api_key="k", retry_total=2)

        assert _client_retry_attempts(client) == 3


class TestSyncPollBudget:
    """A single poll must not be able to over-run the caller's ``timeout``."""

    def test_every_poll_is_bounded_by_the_remaining_budget(self):
        agent = _create_agent([IN_PROGRESS, IN_PROGRESS, SUCCESS])

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
            agent.sync_poll("exec-1", timeout=120, wait_time=0.5)

        reads = _read_timeouts(agent.context.client.get)
        assert len(reads) == 3
        # Monotonically non-increasing, and never more than the budget.
        assert reads == sorted(reads, reverse=True)
        assert max(reads) <= 120

    def test_budget_shrinks_as_time_is_consumed(self):
        """With a fake clock the read timeout tracks the remaining budget exactly."""
        agent = _create_agent([IN_PROGRESS, IN_PROGRESS, SUCCESS])
        clock = iter([0.0, 0.0, 10.0, 10.0, 10.0, 20.0, 20.0, 20.0, 30.0, 30.0, 30.0])

        with patch("aixplain.v2.resource.time.time", lambda: next(clock)):
            with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
                agent.sync_poll("exec-1", timeout=100, wait_time=0.5)

        attempts = DEFAULT_RETRY_TOTAL + 1
        reads = _read_timeouts(agent.context.client.get)
        assert reads == [100.0 / attempts, 90.0 / attempts, 80.0 / attempts]

    def test_never_exceeds_the_client_read_timeout(self):
        """Even a huge ``sync_poll`` budget stays inside the transport bound."""
        agent = _create_agent([IN_PROGRESS, SUCCESS])

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
            agent.sync_poll("exec-1", timeout=100000, wait_time=0.5)

        assert all(read <= DEFAULT_TIMEOUT_READ for read in _read_timeouts(agent.context.client.get))

    def test_wall_clock_respects_the_timeout_when_every_poll_fails(self):
        """Non-API poll errors are swallowed and retried -- but still bounded.

        ``poll`` is patched directly because the real one rewraps everything as
        ``APIError``, which ``sync_poll`` re-raises by design.
        """
        agent = _create_agent()
        polls = []

        def flaky(poll_url, timeout=None):
            polls.append(timeout)
            raise ValueError("transient")

        started = time.monotonic()
        with patch.object(type(agent), "poll", side_effect=flaky):
            with pytest.raises(AixplainTimeoutError):
                agent.sync_poll("exec-1", timeout=0.4, wait_time=0.05)
        elapsed = time.monotonic() - started

        assert len(polls) >= 2, polls
        assert all(t is not None and t <= 0.4 for t in polls), polls
        # The loop must not overshoot its own budget by a whole sleep interval.
        assert elapsed < 1.0, elapsed

    def test_zero_budget_polls_nothing_and_times_out(self):
        """A caller with no budget left must not issue a request at all."""
        agent = _create_agent([SUCCESS])

        with pytest.raises(AixplainTimeoutError):
            agent.sync_poll("exec-1", timeout=0)

        agent.context.client.get.assert_not_called()

    def test_does_not_sleep_past_the_deadline(self):
        """The sleep is clamped, so an exhausted budget never adds a sleep.

        Before the fix the loop slept the full ``wait_time`` after its last
        poll, overshooting ``timeout`` by up to 60s.
        """
        agent = _create_agent([IN_PROGRESS, IN_PROGRESS, SUCCESS])
        recorded = []

        def record(wait_time, *args, **kwargs):
            recorded.append((wait_time, kwargs.get("max_sleep")))
            return 0.0

        with patch("aixplain.v2.resource.sleep_with_jitter", side_effect=record):
            agent.sync_poll("exec-1", timeout=50, wait_time=1.0)

        assert recorded, "expected sleeps between polls"
        for wait_time, max_sleep in recorded:
            assert max_sleep is not None
            assert max_sleep <= 50


class TestDeadlineWinsOverTheErrorItCauses:
    """The bound must not change which exception a timed-out run reports.

    Each poll is now bounded by the remaining budget, so the last poll before
    the deadline can fail *because* the deadline arrived. That must still
    surface as the documented ``TimeoutError``, not as an ``APIError`` about a
    read timeout.
    """

    def test_read_timeout_at_the_deadline_raises_timeout_error(self):
        import requests

        from aixplain.v2.exceptions import APIError

        agent = _create_agent()
        # Budget gone by the time the (bounded) request gives up.
        clock = {"t": 0.0}

        def hang(path, **kwargs):
            clock["t"] += 40.0
            raise requests.exceptions.ReadTimeout("read timed out")

        agent.context.client.get = Mock(side_effect=hang)

        with patch("aixplain.v2.resource.time.time", lambda: clock["t"]):
            with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
                with pytest.raises(AixplainTimeoutError):
                    agent.sync_poll("exec-1", timeout=30, wait_time=0.5)

        assert agent.context.client.get.call_count == 1
        # Sanity: the underlying failure really is an APIError from ``poll``.
        with pytest.raises(APIError):
            agent.poll("exec-1", timeout=5.0)

    def test_an_api_error_inside_the_budget_still_propagates(self):
        """Only budget exhaustion softens the error; a live failure must not."""
        from aixplain.v2.exceptions import APIError

        agent = _create_agent([APIError("upstream exploded", 500, {})])

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
            with pytest.raises(APIError):
                agent.sync_poll("exec-1", timeout=300, wait_time=0.5)

    def test_the_final_failure_is_chained_onto_the_timeout(self):
        """A 401 on the last poll must stay visible, not become "timed out"."""
        from aixplain.v2.exceptions import APIError

        agent = _create_agent()
        clock = {"t": 0.0}

        def expire(poll_url, timeout=None):
            clock["t"] += 40.0
            raise APIError("Unauthorized", 401, {})

        with patch("aixplain.v2.resource.time.time", lambda: clock["t"]):
            with patch.object(type(agent), "poll", side_effect=expire):
                with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
                    with pytest.raises(AixplainTimeoutError) as excinfo:
                        agent.sync_poll("exec-1", timeout=30, wait_time=0.5)

        cause = excinfo.value.__cause__
        assert isinstance(cause, APIError)
        assert cause.status_code == 401
        assert "Unauthorized" in str(cause)

    def test_a_plain_timeout_has_no_spurious_cause(self):
        """Nothing failed, so nothing is chained."""
        agent = _create_agent([SUCCESS])

        with pytest.raises(AixplainTimeoutError) as excinfo:
            agent.sync_poll("exec-1", timeout=0)

        assert excinfo.value.__cause__ is None

    def test_untrusted_url_is_never_softened_into_a_timeout(self):
        """A refused credential leak must stay a security error, budget or not."""
        from aixplain.v2.exceptions import UntrustedURLError

        agent = _create_agent()
        agent.context.client.ensure_trusted_url = Mock(side_effect=UntrustedURLError("nope"))

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
            with pytest.raises(UntrustedURLError):
                agent.sync_poll("exec-1", timeout=30, wait_time=0.5)


class TestSyncPollJitter:
    """The poll sleep must be jittered, not a bare ``time.sleep``."""

    def test_uses_the_jittered_sleep_helper(self):
        agent = _create_agent([IN_PROGRESS, IN_PROGRESS, SUCCESS])

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0) as sleeper:
            with patch("aixplain.v2.resource.time.sleep") as bare_sleep:
                agent.sync_poll("exec-1", timeout=60, wait_time=0.5)

        assert sleeper.call_count == 2
        bare_sleep.assert_not_called()

    def test_backoff_ladder_is_preserved(self):
        """Jitter replaces the constant, it does not remove the growth."""
        agent = _create_agent([IN_PROGRESS] * 4 + [SUCCESS])
        waits = []

        with patch("aixplain.v2.resource.sleep_with_jitter", side_effect=lambda w, **k: waits.append(w) or 0.0):
            agent.sync_poll("exec-1", timeout=600, wait_time=0.5)

        assert waits == sorted(waits)
        assert waits[0] == pytest.approx(0.5)
        assert waits[-1] > waits[0]

    def test_real_sleeps_are_spread(self):
        """End-to-end: the actual delays differ from run to run."""
        observed = []

        for _ in range(2):
            agent = _create_agent([IN_PROGRESS] * 3 + [SUCCESS])
            delays = []
            with patch("aixplain.v2._backoff.time.sleep", side_effect=delays.append):
                agent.sync_poll("exec-1", timeout=600, wait_time=0.5)
            observed.append(delays)

        assert observed[0] != observed[1]


class TestSubmitRetryJitter:
    """``_submit_with_retries`` sleeps between submissions -- also jittered."""

    def test_submission_retry_sleep_is_jittered(self):
        from aixplain.v2.exceptions import APIError
        from aixplain.v2.resource import RunnableResourceMixin

        agent = _create_agent()
        attempts = []

        def fail(**kwargs):
            attempts.append(kwargs)
            raise APIError("upstream unavailable", 503, {})

        with patch.object(RunnableResourceMixin, "_post_and_handle_run", side_effect=fail):
            with patch.object(RunnableResourceMixin, "_is_retryable_run_error", return_value=True):
                with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0) as sleeper:
                    with patch("aixplain.v2.resource.time.sleep") as bare_sleep:
                        with pytest.raises(APIError):
                            agent._submit_with_retries(run_retries=2, run_retry_wait=1.0)

        assert len(attempts) == 3
        assert sleeper.call_count == 2
        bare_sleep.assert_not_called()


class TestLegacyPollOverrideCompatibility:
    """``poll`` gained ``timeout`` additively, so old overrides must keep working.

    A third-party subclass may still define ``poll(self, poll_url)``. Passing
    the remaining budget to it would raise ``TypeError``; such an override
    should simply lose the bound instead.
    """

    @staticmethod
    def _agent_with_poll(poll_impl):
        @dataclass_json
        @dataclass
        class BoundAgent(Agent):
            pass

        BoundAgent.poll = poll_impl
        agent = BoundAgent(id="agent-123", name="test-agent")
        agent.context = Mock()
        agent.context.backend_url = BACKEND_URL
        return agent

    def test_old_signature_override_does_not_raise(self):
        calls = []

        def legacy_poll(self, poll_url):
            calls.append(poll_url)
            return Mock(completed=True, status="SUCCESS")

        agent = self._agent_with_poll(legacy_poll)

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
            agent.sync_poll("exec-1", timeout=30)

        # Agent.sync_poll resolves the execution ID before delegating.
        assert calls == [f"{BACKEND_URL}/sdk/agents/exec-1/result"]

    def test_new_signature_override_still_receives_the_budget(self):
        seen = []

        def modern_poll(self, poll_url, timeout=None):
            seen.append(timeout)
            return Mock(completed=True, status="SUCCESS")

        agent = self._agent_with_poll(modern_poll)

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
            agent.sync_poll("exec-1", timeout=30)

        assert seen and seen[0] is not None
        assert seen[0] <= 30

    def test_kwargs_only_override_receives_the_budget(self):
        """``poll(self, poll_url, **kwargs)`` can absorb it, so it should."""
        seen = []

        def kwargs_poll(self, poll_url, **kwargs):
            seen.append(kwargs.get("timeout"))
            return Mock(completed=True, status="SUCCESS")

        agent = self._agent_with_poll(kwargs_poll)

        with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
            agent.sync_poll("exec-1", timeout=30)

        assert seen and seen[0] is not None

    def test_the_shipped_poll_is_detected_as_supporting_timeout(self):
        agent = _create_agent([SUCCESS])

        assert agent._poll_accepts_timeout() is True

    def test_support_is_cached_per_callable(self):
        """The introspection must not run once per poll."""
        import aixplain.v2.resource as resource_module

        agent = _create_agent([IN_PROGRESS, IN_PROGRESS, SUCCESS])
        agent._poll_accepts_timeout()  # warm the cache

        with patch.object(resource_module, "inspect", wraps=resource_module.inspect) as inspect_module:
            with patch("aixplain.v2.resource.sleep_with_jitter", return_value=0.0):
                agent.sync_poll("exec-1", timeout=30)

        inspect_module.signature.assert_not_called()
        assert agent.context.client.get.call_count == 3
