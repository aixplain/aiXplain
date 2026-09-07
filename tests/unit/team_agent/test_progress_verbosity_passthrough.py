"""Guard: ``TeamAgent.run`` must forward ``progress_verbosity`` to ``sync_poll``.

``run`` accepts and documents ``progress_verbosity`` -- *"full" (detailed),
"compact" (brief), or None (no progress)"* -- but dropped it on the call to
``sync_poll``, which defaults it to ``"compact"``. So ``run(progress_verbosity=None)``
still printed progress to stdout (unsuppressable library output for anyone
embedding the SDK in a service) and ``"full"`` still rendered compact (BUG-946).

The sibling ``Agent.run`` has always passed it through correctly.
"""

from unittest.mock import patch

import pytest

from aixplain.modules.team_agent import TeamAgent
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData
from aixplain.enums import ResponseStatus


def _completed_response(**kwargs):
    return AgentResponse(
        status=ResponseStatus.SUCCESS,
        completed=True,
        data=AgentResponseData(input="hi", output="done"),
        **kwargs,
    )


@pytest.mark.parametrize("verbosity", [None, "full", "compact"])
def test_run_forwards_progress_verbosity_to_sync_poll(verbosity):
    """Whatever the caller passes to ``run`` must reach ``sync_poll``."""
    team_agent = TeamAgent("123", "Test Team Agent")

    with (
        patch.object(TeamAgent, "run_async", return_value={"status": ResponseStatus.IN_PROGRESS, "url": "http://poll"}),
        patch.object(TeamAgent, "sync_poll", return_value=_completed_response()) as mock_sync_poll,
    ):
        team_agent.run(query="hi", progress_verbosity=verbosity)

    assert mock_sync_poll.call_args.kwargs["progress_verbosity"] == verbosity


def test_run_defaults_to_compact():
    """The documented default must survive the passthrough."""
    team_agent = TeamAgent("123", "Test Team Agent")

    with (
        patch.object(TeamAgent, "run_async", return_value={"status": ResponseStatus.IN_PROGRESS, "url": "http://poll"}),
        patch.object(TeamAgent, "sync_poll", return_value=_completed_response()) as mock_sync_poll,
    ):
        team_agent.run(query="hi")

    assert mock_sync_poll.call_args.kwargs["progress_verbosity"] == "compact"


PROGRESS = {
    "stage": "planning",
    "message": "Breaking the task down",
    "current_step": 1,
    "total_steps": 3,
}


def _poll_sequence():
    """One in-progress poll carrying progress data, then a completed one."""
    in_progress = AgentResponse(
        status=ResponseStatus.IN_PROGRESS,
        completed=False,
        data=AgentResponseData(input="hi"),
        progress=dict(PROGRESS),
    )
    return [in_progress, _completed_response()]


def test_sync_poll_none_produces_no_stdout(capsys):
    """``progress_verbosity=None`` must suppress *all* stdout.

    That includes the completion line printed after the polling loop.
    """
    team_agent = TeamAgent("123", "Test Team Agent")

    with patch.object(TeamAgent, "poll", side_effect=_poll_sequence()):
        team_agent.sync_poll("http://poll", wait_time=0.01, progress_verbosity=None)

    assert capsys.readouterr().out == ""


def test_sync_poll_full_renders_full(capsys):
    """``"full"`` must render the detailed format, not the compact one."""
    team_agent = TeamAgent("123", "Test Team Agent")

    with patch.object(TeamAgent, "poll", side_effect=_poll_sequence()):
        team_agent.sync_poll("http://poll", wait_time=0.01, progress_verbosity="full")

    out = capsys.readouterr().out
    assert out, "'full' must produce progress output"

    full_msg = team_agent._format_team_progress(PROGRESS, "full")
    compact_msg = team_agent._format_team_progress(PROGRESS, "compact")
    assert full_msg != compact_msg, "fixture must distinguish the two formats"
    assert full_msg in out
    assert compact_msg not in out


def test_run_none_produces_no_stdout(capsys):
    """End to end: ``run(progress_verbosity=None)`` must print nothing.

    This is the acceptance criterion; it failed before the passthrough because
    ``sync_poll`` fell back to its ``"compact"`` default.
    """
    team_agent = TeamAgent("123", "Test Team Agent")

    with (
        patch.object(TeamAgent, "run_async", return_value={"status": ResponseStatus.IN_PROGRESS, "url": "http://poll"}),
        patch.object(TeamAgent, "poll", side_effect=_poll_sequence()),
    ):
        team_agent.run(query="hi", wait_time=0.01, progress_verbosity=None)

    assert capsys.readouterr().out == ""
