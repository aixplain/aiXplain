"""Unit tests for the v2 agent progress formatter."""

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
