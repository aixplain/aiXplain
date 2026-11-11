"""Integration action polling honours its wall-clock budget (BUG-1453).

``ActionMixin._poll_for_data`` checked its 30s budget only *between* polls; each
poll ran with the client default ``(10, 300)`` timeout and urllib3 re-sent a
timed-out GET up to 5 more times, so one hung endpoint could block ~30 minutes.
On expiry it returned ``None``, which ``list_actions`` turned into ``[]``.
"""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from aixplain.v2.exceptions import TimeoutError as AixTimeoutError
from aixplain.v2.integration import ActionMixin, ActionSpec
from aixplain.v2.tool import Tool

POLL_URL = "https://platform-api.aixplain.com/sdk/actions/exec-1"
ASYNC = {"completed": False, "data": POLL_URL}
PENDING = {"completed": False, "status": "IN_PROGRESS"}


class _Poller(ActionMixin):
    def __init__(self, request=None, timeout=(10, 300), retry_total=5):
        self.actions_available = True
        self.context = Mock()
        self.context.client.timeout = timeout
        self.context.client.retry_total = retry_total
        self.context.client.request = request or Mock()

    def build_run_url(self):
        return "https://models.aixplain.com/api/v2/execute/x"


@pytest.fixture(autouse=True)
def _no_sleep():
    with patch("aixplain.v2.integration.sleep_with_jitter", return_value=0.0):
        yield


class TestPerRequestTimeout:
    def test_every_poll_carries_a_budget_bounded_timeout(self):
        seen = []

        def request(method, url, **kwargs):
            seen.append(kwargs.get("timeout"))
            return PENDING if len(seen) < 3 else {"completed": True, "data": "d"}

        poller = _Poller(Mock(side_effect=request))
        assert poller._poll_for_data(ASYNC, timeout=30) == "d"

        assert len(seen) == 3
        for connect, read in seen:
            assert connect == 10.0
            # remaining / (retry_total + 1), floored at 1s.
            assert 1.0 <= read <= 30 / 6

    def test_narrower_client_read_timeout_wins(self):
        seen = []

        def request(method, url, **kwargs):
            seen.append(kwargs["timeout"])
            return {"completed": True, "data": "d"}

        poller = _Poller(Mock(side_effect=request), timeout=(2, 4), retry_total=1)
        poller._poll_for_data(ASYNC, timeout=600)

        assert seen == [(2.0, 4.0)]


class TestExpiry:
    def test_hung_poll_raises_within_budget(self):
        def request(method, url, **kwargs):
            time.sleep(min(kwargs["timeout"][1], 0.2))
            if time.time() - started >= 0.5:
                raise requests.exceptions.ReadTimeout("read timed out")
            return PENDING

        poller = _Poller(Mock(side_effect=request))
        started = time.time()
        with pytest.raises(AixTimeoutError):
            poller._poll_for_data(ASYNC, timeout=0.5)
        assert time.time() - started < 0.5 + 1.0

    def test_transport_error_with_budget_left_propagates(self):
        poller = _Poller(Mock(side_effect=requests.exceptions.ConnectionError("refused")))

        with pytest.raises(requests.exceptions.ConnectionError) as info:
            poller._poll_for_data(ASYNC, timeout=30)
        assert not isinstance(info.value, AixTimeoutError)
        assert poller.context.client.request.call_count == 1

    def test_timeout_is_also_a_builtin_timeout_error(self):
        poller = _Poller()
        with pytest.raises(TimeoutError):
            poller._poll_for_data(ASYNC, timeout=0)


class TestCallersSurfaceTheTimeout:
    def _timing_out(self):
        poller = _Poller()
        poller.context.client.request = Mock(return_value=ASYNC)
        return poller

    def test_list_actions_raises_instead_of_returning_empty(self):
        poller = self._timing_out()
        with patch.object(ActionMixin, "_poll_for_data", side_effect=AixTimeoutError("t")):
            with pytest.raises(AixTimeoutError):
                poller.list_actions()

    def test_list_inputs_raises_instead_of_returning_empty(self):
        poller = self._timing_out()
        with patch.object(ActionMixin, "_poll_for_data", side_effect=AixTimeoutError("t")):
            with pytest.raises(AixTimeoutError):
                poller._list_inputs("SEND")


def _bare_tool(integration=None):
    tool = Tool.__new__(Tool)
    tool.id = "tool-id"
    tool.name = "Tool"
    tool.integration = integration
    return tool


SPEC = ActionSpec(name="SEND")


class TestToolFallback:
    def test_list_actions_reraises_timeout_without_fallback(self):
        tool = _bare_tool()
        with patch.object(ActionMixin, "list_actions", side_effect=AixTimeoutError("t")):
            with patch.object(Tool, "_ensure_integration", return_value=False):
                with pytest.warns(UserWarning), pytest.raises(AixTimeoutError):
                    tool.list_actions()

    def test_list_actions_uses_fallback_after_timeout(self):
        integration = Mock()
        integration.list_actions.return_value = [SPEC]
        tool = _bare_tool(integration)
        with patch.object(ActionMixin, "list_actions", side_effect=AixTimeoutError("t")):
            with patch.object(Tool, "_ensure_integration", return_value=True):
                with pytest.warns(UserWarning):
                    assert tool.list_actions() == [SPEC]

    def test_list_actions_raises_when_fallback_also_times_out(self):
        integration = Mock()
        integration.list_actions.side_effect = AixTimeoutError("fallback")
        tool = _bare_tool(integration)
        with patch.object(ActionMixin, "list_actions", side_effect=AixTimeoutError("t")):
            with patch.object(Tool, "_ensure_integration", return_value=True):
                with pytest.warns(UserWarning), pytest.raises(AixTimeoutError, match="fallback"):
                    tool.list_actions()

    def test_list_actions_non_timeout_error_still_returns_empty(self):
        tool = _bare_tool()
        with patch.object(ActionMixin, "list_actions", side_effect=RuntimeError("boom")):
            with patch.object(Tool, "_ensure_integration", return_value=False):
                with pytest.warns(UserWarning):
                    assert tool.list_actions() == []

    def test_list_inputs_reraises_timeout_without_fallback(self):
        tool = _bare_tool()
        with patch.object(ActionMixin, "_list_inputs", side_effect=AixTimeoutError("t")):
            with patch.object(Tool, "_ensure_integration", return_value=False):
                with pytest.warns(UserWarning), pytest.raises(AixTimeoutError):
                    tool._list_inputs("SEND")

    def test_list_inputs_raises_fallback_timeout(self):
        integration = Mock()
        integration._list_inputs.side_effect = AixTimeoutError("fallback")
        tool = _bare_tool(integration)
        with patch.object(ActionMixin, "_list_inputs", side_effect=RuntimeError("boom")):
            with patch.object(Tool, "_ensure_integration", return_value=True):
                with pytest.warns(UserWarning), pytest.raises(AixTimeoutError, match="fallback"):
                    tool._list_inputs("SEND")

    def test_list_inputs_uses_fallback_after_timeout(self):
        integration = Mock()
        integration._list_inputs.return_value = [SPEC]
        tool = _bare_tool(integration)
        with patch.object(ActionMixin, "_list_inputs", side_effect=AixTimeoutError("t")):
            with patch.object(Tool, "_ensure_integration", return_value=True):
                with pytest.warns(UserWarning):
                    assert tool._list_inputs("SEND") == [SPEC]
