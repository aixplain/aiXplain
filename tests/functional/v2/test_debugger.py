"""Functional tests for the Debugger meta-agent.

The debugger is a pre-configured backend agent, so this is the one path that
actually exercises ``Debugger.run`` / ``AgentRunResult.debug`` end to end. The
SDK hard-codes one debugger agent id (``meta_agents.DEBUGGER_AGENT_ID``), which
exists on dev only, so every test here patches it with this backend's
``DEBUGGER_AGENT`` from ``tests/functional/_assets.py``.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
import uuid

import pytest

from aixplain.v2 import meta_agents
from aixplain.v2.meta_agents import Debugger


@pytest.fixture(autouse=True)
def _debugger_agent_for_this_backend(assets, monkeypatch):
    """Point the SDK's hard-coded debugger agent id at this backend's debugger.

    ``Debugger._get_debugger_agent`` reads the module global at call time, so
    patching it is enough; reading ``assets.DEBUGGER_AGENT`` also fails the test
    by name if the debugger agent does not resolve on this backend.
    """
    monkeypatch.setattr(meta_agents, "DEBUGGER_AGENT_ID", assets.DEBUGGER_AGENT)


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
