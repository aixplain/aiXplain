"""Functional tests for the Debugger meta-agent.

The debugger is a pre-configured backend agent, so this is the one path that
actually exercises ``Debugger.run`` / ``AgentRunResult.debug`` end to end.
"""

import time
import uuid

import pytest

from aixplain.v2.meta_agents import DebugResult


@pytest.fixture(scope="module")
def debug_agent(client, module_resource_tracker):
    agent = client.Agent(
        name=f"Debugger Test Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        instructions="Answer every question in one short sentence.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


def test_agent_result_debug_returns_debug_result(client, debug_agent):
    run = debug_agent.run(query="What is 2 + 2?")

    debug = run.debug()

    assert isinstance(debug, DebugResult)
    assert debug.status == "SUCCESS", debug
    assert debug.analysis


def test_debug_response_accepts_a_custom_prompt(client, debug_agent):
    run = debug_agent.run(query="Name one primary colour.")

    debug = run.debug(prompt="Focus on whether the answer was concise.")

    assert isinstance(debug, DebugResult)
    assert debug.analysis


def test_standalone_debugger_run(client):
    debugger = client.Debugger()

    debug = debugger.run(content="Agent returned: 'Error 500'", prompt="Explain the failure.")

    assert isinstance(debug, DebugResult)
    assert debug.analysis
