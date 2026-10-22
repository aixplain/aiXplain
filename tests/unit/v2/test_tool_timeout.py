"""Unit tests for the per-tool ``timeout`` override (ENG-3817).

The platform limits each agent call to a tool to a default it owns (per
model/integration definition, else the agent runtime's own). A user overrides it
per tool by setting ``timeout`` on the tool object before attaching it::

    tool = aix.Tool.get("...")
    tool.timeout = 30
    agent = aix.Agent(name="my-agent", tools=[tool])
    agent.save()                                  # persists timeout=30
"""

from fractions import Fraction
from unittest.mock import Mock

import pytest

from aixplain import Agent, Integration, Model, Tool, ValidationError


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


def _fetched_agent(tool_dict: dict) -> Agent:
    """An onboarded agent as ``Agent.get()`` leaves it: hydrated, with a saved-state baseline."""
    agent = _bound_agent(_ctx()).from_dict(
        {"name": "n", "description": "d", "tools": [tool_dict], "status": "onboarded"}
    )
    agent._update_saved_state()
    return agent


class TestAsTool:
    def test_unset_timeout_is_omitted(self):
        assert "timeout" not in Model(id="m1", name="translate").as_tool()

    def test_model_timeout_serialized_as_float_seconds(self):
        timeout = Model(id="m1", name="translate", timeout=10).as_tool()["timeout"]
        assert timeout == 10.0
        assert isinstance(timeout, float)

    def test_tool_inherits_timeout(self):
        tool = Tool(id="t1", name="air", timeout=2.5)
        tool.context = Mock()
        assert tool.as_tool()["timeout"] == 2.5

    def test_integration_inherits_timeout(self):
        assert Integration(id="i1", name="air", timeout=10).as_tool()["timeout"] == 10.0

    def test_any_real_number_accepted(self):
        assert Model(id="m1", name="translate", timeout=Fraction(5, 2)).as_tool()["timeout"] == 2.5

    @pytest.mark.parametrize(
        "value",
        [0, -1, True, "10", float("inf"), float("nan"), 10**400],
        ids=["zero", "negative", "bool", "str", "inf", "nan", "overflow"],
    )
    def test_invalid_timeout_raises(self, value):
        with pytest.raises(ValidationError, match="positive number of seconds"):
            Model(id="m1", name="translate", timeout=value).as_tool()

    def test_timeout_not_sent_when_saving_the_model_itself(self):
        # Only the agent's tool entry carries it, not the asset's own payload.
        assert "timeout" not in Model(id="m1", name="translate", timeout=10).to_dict()


class TestBackendRecords:
    @pytest.mark.parametrize("raw", [10, "10s", {"value": 10}, 0], ids=["number", "text", "dict", "zero"])
    def test_backend_timeout_key_is_not_decoded(self, raw):
        # A platform default on the model record must not come back as the
        # user's override, and an unexpected shape must not break Model.get().
        model = Model.from_dict({"id": "m1", "name": "translate", "timeout": raw})
        assert model.timeout is None
        assert "timeout" not in model.as_tool()


class TestAgentSave:
    def test_save_payload_carries_tool_timeout(self):
        model = Model(id="m1", name="translate", timeout=10)
        agent = Agent(name="n", description="d", tools=[model])
        assert _saved_tools(agent)[0]["timeout"] == 10.0

    def test_save_payload_omits_unset_timeout(self):
        agent = Agent(name="n", description="d", tools=[Model(id="m1", name="translate")])
        assert "timeout" not in _saved_tools(agent)[0]

    def test_dict_tool_entry_is_validated(self):
        agent = Agent(name="n", description="d", tools=[{"id": "m1", "type": "model", "timeout": -5}])
        with pytest.raises(ValidationError, match="positive number of seconds"):
            _saved_tools(agent)

    def test_dict_tool_entry_timeout_sent_as_float(self):
        agent = Agent(name="n", description="d", tools=[{"id": "m1", "type": "model", "timeout": 10}])
        assert _saved_tools(agent)[0]["timeout"] == 10.0

    @pytest.mark.parametrize("tool_type", ["model", "tool"])
    def test_fetched_agent_keeps_timeout_on_resave(self, tool_type):
        agent = _fetched_agent({"id": "x1", "type": tool_type, "name": "air", "timeout": 10})

        assert agent.tools[0].timeout == 10
        agent.tools[0].timeout = 30
        assert _saved_tools(agent)[0]["timeout"] == 30.0

    def test_stored_numeric_string_is_coerced(self):
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": "10"})
        assert agent.tools[0].timeout == 10.0

    @pytest.mark.parametrize("raw", [0, "soon", True], ids=["zero", "text", "bool"])
    def test_invalid_stored_timeout_is_dropped_so_the_agent_still_saves(self, raw):
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": raw})
        assert agent.tools[0].timeout is None
        assert "timeout" not in _saved_tools(agent)[0]


class TestIsModified:
    def test_timeout_change_marks_agent_modified(self):
        # Unlike input values there is no run-time override for it, so an
        # unsaved change must not be silently ignored by run().
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": 10})
        assert agent.is_modified is False
        agent.tools[0].timeout = 30
        assert agent.is_modified is True
