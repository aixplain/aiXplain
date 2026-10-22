"""Unit tests for the per-tool ``timeout`` override (ENG-3817).

An agent's call to a tool is limited to the model/integration definition's
default (e.g. 10s for AiR), else the agent runtime's 300s. A user overrides it
per tool by setting ``timeout`` on the tool object before attaching it::

    tool = aix.Tool.get("...")
    tool.timeout = 30
    agent = aix.Agent(name="my-agent", tools=[tool])
    agent.save()                                  # persists timeout=30
"""

from unittest.mock import Mock

import pytest

from aixplain import Agent, Model, Tool, ValidationError


def _ctx() -> Mock:
    """A mock client context that exposes the real Tool/Model resource classes."""
    ctx = Mock(client=Mock(), backend_url="https://platform-api.aixplain.com", api_key="k")
    ctx.Model = Model
    ctx.Tool = Tool
    return ctx


def _bound_agent(ctx: Mock):
    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


def _saved_tools(agent: Agent) -> list:
    agent.context = agent.context or Mock()
    return agent.build_save_payload()["tools"]


class TestAsTool:
    def test_unset_timeout_is_omitted(self):
        assert "timeout" not in Model(id="m1", name="translate").as_tool()

    def test_model_timeout_serialized_as_float_seconds(self):
        assert Model(id="m1", name="translate", timeout=10).as_tool()["timeout"] == 10.0

    def test_tool_inherits_timeout(self):
        tool = Tool(id="t1", name="air", timeout=2.5)
        tool.context = Mock()
        assert tool.as_tool()["timeout"] == 2.5

    @pytest.mark.parametrize("value", [0, -1, True, "10", float("inf"), float("nan")])
    def test_invalid_timeout_raises(self, value):
        with pytest.raises(ValidationError, match="positive number of seconds"):
            Model(id="m1", name="translate", timeout=value).as_tool()

    def test_timeout_not_sent_when_saving_the_model_itself(self):
        # Only the agent's tool entry carries it, not the asset's own payload.
        assert "timeout" not in Model(id="m1", name="translate", timeout=10).to_dict()


class TestAgentSave:
    def test_save_payload_carries_tool_timeout(self):
        model = Model(id="m1", name="translate", timeout=10)
        agent = Agent(name="n", description="d", tools=[model])
        assert _saved_tools(agent)[0]["timeout"] == 10.0

    def test_save_payload_omits_unset_timeout(self):
        agent = Agent(name="n", description="d", tools=[Model(id="m1", name="translate")])
        assert "timeout" not in _saved_tools(agent)[0]

    @pytest.mark.parametrize("tool_type", ["model", "tool"])
    def test_fetched_agent_keeps_timeout_on_resave(self, tool_type):
        ctx = _ctx()
        tool_dict = {"id": "x1", "type": tool_type, "name": "air", "timeout": 10}
        agent = _bound_agent(ctx).from_dict({"name": "n", "description": "d", "tools": [tool_dict]})

        assert agent.tools[0].timeout == 10
        agent.tools[0].timeout = 30
        assert _saved_tools(agent)[0]["timeout"] == 30.0
