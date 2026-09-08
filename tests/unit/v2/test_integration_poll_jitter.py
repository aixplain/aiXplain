"""Unit tests for ``ActionMixin._poll_for_data`` (BUG-942 item 1).

This loop was the worst of the four v2 sites: a *fixed* 1s tick with no backoff
at all, so a batch of clients not only stayed phase-locked, they polled at a
constant 1 req/s each for the whole 30s budget.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain.v2.integration import ActionMixin

POLL_URL = "https://platform-api.aixplain.com/sdk/actions/exec-1"
PENDING = {"completed": False, "status": "IN_PROGRESS"}
DONE = {"completed": True, "status": "SUCCESS", "data": {"rows": 1}}


class _Poller(ActionMixin):
    """ActionMixin bound to a mock client returning *responses* in order."""

    def __init__(self, responses):
        self.actions_available = True
        self.context = Mock()
        self.context.client.request = Mock(side_effect=list(responses))


class TestShortCircuits:
    """Unchanged behaviour for anything that isn't an async poll URL."""

    @pytest.mark.parametrize(
        "response",
        [
            {"completed": True, "data": {"x": 1}},
            {"completed": False, "data": {"x": 1}},
            {"completed": False, "data": "not-a-url"},
            {"completed": False, "data": None},
        ],
    )
    def test_returns_data_without_polling(self, response):
        poller = _Poller([])

        assert poller._poll_for_data(response) == response["data"]
        poller.context.client.request.assert_not_called()


class TestJitteredBackoff:
    """The sleep must be jittered, backed off, and deadline-clamped."""

    def test_uses_the_jittered_sleep_helper(self):
        poller = _Poller([DONE])

        with patch("aixplain.v2.integration.sleep_with_jitter", return_value=0.0) as sleeper:
            with patch("aixplain.v2.integration.time.sleep") as bare_sleep:
                data = poller._poll_for_data({"completed": False, "data": POLL_URL})

        assert data == {"rows": 1}
        assert sleeper.call_count == 1
        bare_sleep.assert_not_called()

    def test_interval_now_backs_off(self):
        """It used to be a flat 1s tick with no growth whatsoever."""
        poller = _Poller([PENDING, PENDING, DONE])
        waits = []

        with patch(
            "aixplain.v2.integration.sleep_with_jitter",
            side_effect=lambda w, **k: waits.append(w) or 0.0,
        ):
            poller._poll_for_data({"completed": False, "data": POLL_URL}, timeout=600)

        assert waits == sorted(waits)
        assert waits[0] == pytest.approx(1.0)
        assert waits[1] == pytest.approx(1.1)
        assert waits[2] == pytest.approx(1.21)

    def test_sleep_is_clamped_to_the_remaining_budget(self):
        poller = _Poller([PENDING] * 20 + [DONE])
        clamps = []

        with patch(
            "aixplain.v2.integration.sleep_with_jitter",
            side_effect=lambda w, **k: clamps.append(k.get("max_sleep")) or 0.0,
        ):
            poller._poll_for_data({"completed": False, "data": POLL_URL}, timeout=5, wait_time=30)

        assert clamps
        assert all(c is not None and c <= 5 for c in clamps)

    def test_real_delays_are_spread_across_clients(self):
        observed = []

        for _ in range(2):
            poller = _Poller([PENDING, PENDING, DONE])
            delays = []
            with patch("aixplain.v2._backoff.time.sleep", side_effect=delays.append):
                poller._poll_for_data({"completed": False, "data": POLL_URL}, timeout=600)
            observed.append(delays)

        assert observed[0] != observed[1]


class TestBudget:
    """The loop must still honour its ``timeout``."""

    def test_exhausted_budget_returns_none_without_polling(self):
        poller = _Poller([DONE])

        assert poller._poll_for_data({"completed": False, "data": POLL_URL}, timeout=0) is None
        poller.context.client.request.assert_not_called()

    def test_returns_none_when_the_budget_expires(self):
        poller = _Poller([PENDING] * 50)

        with patch("aixplain.v2.integration.sleep_with_jitter", return_value=0.0):
            clock = {"t": 0.0}
            with patch("aixplain.v2.integration.time.time", lambda: clock["t"]):

                def advance(*_args, **_kwargs):
                    clock["t"] += 5.0
                    return PENDING

                poller.context.client.request = Mock(side_effect=advance)
                assert poller._poll_for_data({"completed": False, "data": POLL_URL}, timeout=30) is None

        assert poller.context.client.request.call_count == 6

    @pytest.mark.parametrize("terminal", [{"completed": True, "data": "d"}, {"status": "SUCCESS", "data": "d"}])
    def test_both_terminal_shapes_still_return_data(self, terminal):
        poller = _Poller([terminal])

        with patch("aixplain.v2.integration.sleep_with_jitter", return_value=0.0):
            assert poller._poll_for_data({"completed": False, "data": POLL_URL}) == "d"
