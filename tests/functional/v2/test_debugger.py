"""Functional tests for the Debugger meta-agent.

The debugger is a pre-configured backend agent, so this is the one path that
actually exercises ``Debugger.run`` / ``AgentRunResult.debug`` end to end. It
needs ``meta_agents.DEBUGGER_AGENT_ID`` to exist on whichever backend the leg
runs against.
"""

import time
import uuid

import pytest

from aixplain.v2.meta_agents import Debugger


@pytest.fixture(scope="module")
def debug_agent(client, module_resource_tracker):
    agent = client.Agent(
        name=f"Debugger Test Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        instructions="Answer every question in one short sentence.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


def _assert_debug_succeeded(debug):
    assert debug.status == "SUCCESS", debug
    assert debug.analysis and str(debug.analysis).strip(), debug.data


def test_agent_result_debug_returns_an_analysis(client, debug_agent):
    run = debug_agent.run(query="What is 2 + 2?")

    _assert_debug_succeeded(run.debug())


def test_debug_sends_the_custom_prompt_to_the_debugger(client, debug_agent, monkeypatch):
    queries = []
    build_query = Debugger._build_query

    def spy_build_query(self, content=None, prompt=None):
        query = build_query(self, content=content, prompt=prompt)
        queries.append(query)
        return query

    monkeypatch.setattr(Debugger, "_build_query", spy_build_query)
    run = debug_agent.run(query="Name one primary colour.")

    debug = run.debug(prompt="Focus on whether the answer was concise.")

    _assert_debug_succeeded(debug)
    assert len(queries) == 1
    assert "Focus: Focus on whether the answer was concise." in queries[0]


def test_standalone_debugger_run(client):
    debugger = client.Debugger()

    _assert_debug_succeeded(debugger.run(content="Agent returned: 'Error 500'", prompt="Explain the failure."))
