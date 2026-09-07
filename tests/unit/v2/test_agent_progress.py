"""Unit tests for the v2 agent progress formatter."""

from unittest.mock import MagicMock

from aixplain.v2.agent import Agent
from aixplain.v2.agent_progress import AgentProgressTracker


def _tracker() -> AgentProgressTracker:
    """Create a tracker with a no-op poll function."""
    return AgentProgressTracker(poll_func=lambda _: None)


def test_format_token_usage_inline_uses_arrow_style():
    """Token usage should render with input/output arrows and total in parentheses."""
    tracker = _tracker()

    text = tracker._format_token_usage_inline(
        {
            "input_tokens": 510,
            "output_tokens": 536,
            "total_tokens": 1046,
        }
    )

    assert text == "↓510 ↑536 (1046)"


def test_format_step_line_includes_arrow_style_tokens():
    """Step lines should include the compact token summary in logs/status output."""
    tracker = _tracker()

    line = tracker._format_step_line(
        {
            "agent": {"name": "Responder"},
            "unit": {"name": "Final Answer", "type": "llm"},
            "api_calls": 1,
            "used_credits": 0.123456,
            "input_tokens": 510,
            "output_tokens": 536,
            "total_tokens": 1046,
        },
        step_idx=0,
        icon="✓",
        step_elapsed=1.23,
        show_timing=True,
        is_complete=True,
    )

    assert "· ↓510 ↑536 (1046) ·" in line


def test_completion_message_includes_arrow_style_totals(capsys):
    """Completion summaries should use the same token formatting."""
    tracker = _tracker()
    tracker._format = "logs"
    tracker._total_start_time = tracker._now()
    tracker._total_api_calls = 3
    tracker._total_credits = 0.654321
    tracker._total_input_tokens = 510
    tracker._total_output_tokens = 536

    tracker._print_completion_message("SUCCESS", [{}, {}])

    captured = capsys.readouterr().out
    assert "↓510 ↑536 (1046)" in captured


class TestProgressKwargsStayOffTheWire:
    """``progress_*`` configure the client-side display, never the run body.

    They were in no filter, so ``build_run_payload``'s catch-all snake_case →
    camelCase forwarder put them in the run POST — coupling the SDK's display
    options to the backend's input contract (BUG-1091). The tracker must keep
    receiving them: ``before_run`` sees the *unfiltered* kwargs.
    """

    PROGRESS_KWARGS = {"progress_format": "logs", "progress_verbosity": 2, "progress_truncate": False}

    @staticmethod
    def _runnable_agent():
        agent = Agent.from_dict({"id": "a1", "name": "t"})
        agent.context = MagicMock()
        agent.status = None
        fake_result = MagicMock()
        fake_result.url = None
        fake_result.completed = True
        agent.handle_run_response = lambda response, **kw: fake_result
        return agent

    def test_progress_kwargs_absent_from_build_run_payload(self):
        agent = self._runnable_agent()
        payload = agent.build_run_payload(query="hi", **self.PROGRESS_KWARGS)

        for key in self.PROGRESS_KWARGS:
            assert key not in payload

    def test_progress_kwargs_absent_from_the_posted_body(self):
        agent = self._runnable_agent()
        agent.run(query="hi", **self.PROGRESS_KWARGS)

        body = agent.context.client.request.call_args.kwargs["json"]
        for key in self.PROGRESS_KWARGS:
            assert key not in body
        assert body["query"] == {"input": "hi"}

    def test_tracker_still_receives_the_progress_kwargs(self):
        agent = self._runnable_agent()
        observed = {}

        def capture(kwargs):
            observed.update({k: kwargs.get(k) for k in self.PROGRESS_KWARGS})

        agent._start_progress_tracker = capture
        agent.run(query="hi", **self.PROGRESS_KWARGS)

        assert observed == self.PROGRESS_KWARGS


class TestSdkRequestKwargsStayOffTheAgentWire:
    """``api_key`` / ``resource_path`` are dispatch params, never model input."""

    @staticmethod
    def _runnable_agent():
        return TestProgressKwargsStayOffTheWire._runnable_agent()

    def test_api_key_never_reaches_the_agent_run_body(self):
        agent = self._runnable_agent()
        agent.run(query="hi", api_key="SECRET", resource_path="sdk/agents")

        body = agent.context.client.request.call_args.kwargs["json"]
        assert "api_key" not in body
        assert "resource_path" not in body
        assert "SECRET" not in str(body)
