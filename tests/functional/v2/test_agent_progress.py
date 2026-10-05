"""Functional tests for agent progress display.

Runs a real agent once per :class:`ProgressFormat` and asserts the tracker
actually emitted output: per-step lines for ``logs``, a completion summary for
``status``, and nothing for ``none``.
"""

import time
import uuid

import pytest

from aixplain.v2.agent_progress import AgentProgressTracker, ProgressFormat


@pytest.fixture(scope="module")
def progress_agent(client, module_resource_tracker):
    agent = client.Agent(
        name=f"Progress Test Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        instructions="Think briefly, then answer the question in one short sentence.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


def test_logs_format_emits_step_and_completion_lines(progress_agent, capsys):
    progress_agent.run(query="What is the capital of France?", progress_format="logs")

    out = capsys.readouterr().out
    assert "Step  1" in out
    assert "Completed" in out


def test_status_format_emits_a_completion_summary(progress_agent, capsys):
    progress_agent.run(query="What is the capital of Spain?", progress_format="status")

    assert "Completed" in capsys.readouterr().out


def test_none_format_is_silent(progress_agent, capsys, monkeypatch):
    # An empty stdout alone would also pass if ``progress_format`` were dropped
    # before reaching the tracker, so record the format the tracker started with.
    formats = []
    start = AgentProgressTracker.start

    def spy_start(self, *args, **kwargs):
        formats.append(kwargs.get("format"))
        return start(self, *args, **kwargs)

    monkeypatch.setattr(AgentProgressTracker, "start", spy_start)

    result = progress_agent.run(query="What is the capital of Italy?", progress_format="none")

    assert result.status == "SUCCESS", result
    assert formats == [ProgressFormat.NONE]
    assert capsys.readouterr().out == ""
