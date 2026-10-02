"""Functional tests for agent progress display.

Runs a real agent once per :class:`ProgressFormat` and asserts the tracker
actually emitted output: per-step lines for ``logs``, a completion summary for
``status``, and nothing for ``none``.
"""

import time
import uuid

import pytest


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
    assert "Step" in out
    assert "Completed" in out


def test_status_format_emits_a_completion_summary(progress_agent, capsys):
    progress_agent.run(query="What is the capital of Spain?", progress_format="status")

    assert "Completed" in capsys.readouterr().out


def test_none_format_is_silent(progress_agent, capsys):
    progress_agent.run(query="What is the capital of Italy?", progress_format="none")

    assert capsys.readouterr().out == ""
