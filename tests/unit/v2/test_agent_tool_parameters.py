"""Unit tests for object-based per-tool parameter overrides (PROD-2481).

Per-tool parameters are configured by mutating a tool object's typed action
inputs and attaching it to the agent::

    tool = aix.Tool.get("aixplain/aixplain-web-search")
    tool.actions.search.inputs.num_results = 2
    agent = aix.Agent(name="my-agent", tools=[tool])
    agent.save()                                  # persists num_results=2

    agent.tools[0].actions.search.inputs.num_results = 5
    agent.run("query")                            # ephemeral run-time override

These tests cover:

* Hydration — a tool dict from a get()/create response becomes a mutable
  ``Tool``/``Model`` object, offline (no network).
* Save payload picks up the current input values.
* Run payload forwards the current values as an ephemeral override.
* Mutating a tool input does not mark the agent modified (so an onboarded
  agent's run is not blocked); adding/removing a whole tool does.
* Attach-only shapes (string id, ``as_tool()`` snapshot dict) still serialize.
"""

from typing import Any, Dict, List
from unittest.mock import Mock, patch

from aixplain.v2.agent import Agent
from aixplain.v2.model import Model, Parameter
from aixplain.v2.tool import Tool


def _params_as_dict(parameters: List[dict]) -> Dict[str, Any]:
    """Flatten ``[{name, value}]`` to ``{name: value}`` for ergonomic assertions."""
    return {item["name"]: item["value"] for item in parameters}


def _tool_by_id(tools: List[dict], tool_id: str) -> dict:
    return next(t for t in tools if t.get("id") == tool_id or t.get("assetId") == tool_id)


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


def _model_tool(temperature: Any = None) -> Model:
    model = Model(id="m2", name="translate", params=[Parameter(name="temperature", data_type="number")])
    if temperature is not None:
        model.inputs.temperature = temperature
    return model


# ---------------------------------------------------------------------------
# Hydration: response tool dicts become mutable objects, offline.
# ---------------------------------------------------------------------------


class TestHydration:
    def test_model_tool_dict_hydrated_offline(self):
        ctx = _ctx()
        tool_dict = {
            "id": "m2",
            "type": "model",
            "name": "translate",
            "parameters": [{"name": "temperature", "value": 0.5, "datatype": "number", "required": False}],
        }
        agent = _bound_agent(ctx).from_dict({"name": "n", "description": "d", "tools": [tool_dict]})

        assert isinstance(agent.tools[0], Model)
        assert agent.tools[0].inputs.temperature.value == 0.5
        # Hydration must not hit the network.
        ctx.client.get.assert_not_called()
        ctx.client.request.assert_not_called()

    def test_action_tool_dict_hydrated_with_dot_access(self):
        ctx = _ctx()
        tool_dict = {
            "id": "t-web",
            "type": "tool",
            "name": "web-search",
            "parameters": [
                {
                    "code": "SEARCH",
                    "name": "search",
                    "description": "",
                    "inputs": {"num_results": {"name": "num_results", "value": 2, "datatype": "integer"}},
                }
            ],
        }
        agent = _bound_agent(ctx).from_dict({"name": "n", "description": "d", "tools": [tool_dict]})

        assert isinstance(agent.tools[0], Tool)
        assert agent.tools[0].actions.search.inputs.num_results.value == 2
        ctx.client.request.assert_not_called()

    def test_object_tool_passed_through_unchanged(self):
        ctx = _ctx()
        model = _model_tool()
        agent = _bound_agent(ctx)(name="n", description="d", tools=[model])
        assert agent.tools[0] is model

    def test_string_id_kept_as_is(self):
        ctx = _ctx()
        agent = _bound_agent(ctx)(name="n", description="d", tools=["tool-1"])
        assert agent.tools[0] == "tool-1"


# ---------------------------------------------------------------------------
# Save payload reflects the tool object's current input values.
# ---------------------------------------------------------------------------


class TestSavePayload:
    def test_save_reflects_mutated_model_input(self):
        agent = Agent(name="n", description="d", tools=[_model_tool(temperature=0.7)])
        agent.context = Mock()
        tool = _tool_by_id(agent.build_save_payload()["tools"], "m2")
        assert _params_as_dict(tool["parameters"]) == {"temperature": 0.7}

    def test_save_persists_latest_value(self):
        model = _model_tool(temperature=0.3)
        agent = Agent(name="n", description="d", tools=[model])
        agent.context = Mock()
        first = _tool_by_id(agent.build_save_payload()["tools"], "m2")
        assert _params_as_dict(first["parameters"]) == {"temperature": 0.3}

        model.inputs.temperature = 0.9
        second = _tool_by_id(agent.build_save_payload()["tools"], "m2")
        assert _params_as_dict(second["parameters"]) == {"temperature": 0.9}

    def test_save_does_not_crash_on_object_tools(self):
        # Regression: to_dict() used to recurse into Model/Tool objects and raise.
        agent = Agent(name="n", description="d", tools=[_model_tool()])
        agent.context = Mock()
        payload = agent.build_save_payload()
        assert _tool_by_id(payload["tools"], "m2")["id"] == "m2"


# ---------------------------------------------------------------------------
# Run payload forwards the current values as an ephemeral override.
# ---------------------------------------------------------------------------


class TestRunPayload:
    def test_run_sends_current_model_params(self):
        agent = Agent(name="n", description="d", tools=[_model_tool(temperature=0.7)])
        agent.context = Mock()
        agent.id = "agent-1"
        payload = agent.build_run_payload(query="hi")
        assert _params_as_dict(_tool_by_id(payload["tools"], "m2")["parameters"]) == {"temperature": 0.7}

    def test_run_sends_action_tool_params(self):
        ctx = _ctx()
        tool_dict = {
            "id": "t-web",
            "type": "tool",
            "name": "web-search",
            "parameters": [
                {"code": "SEARCH", "name": "search", "inputs": {"num_results": {"name": "num_results", "value": 2}}}
            ],
        }
        agent = _bound_agent(ctx).from_dict({"name": "n", "description": "d", "tools": [tool_dict]})
        agent.id = "agent-1"
        agent.tools[0].actions.search.inputs.num_results = 5
        payload = agent.build_run_payload(query="hi")
        assert _params_as_dict(_tool_by_id(payload["tools"], "t-web")["parameters"]) == {"num_results": 5}

    def test_run_without_values_omits_tools_key(self):
        agent = Agent(name="n", description="d", tools=[_model_tool()])  # no value set
        agent.context = Mock()
        agent.id = "agent-1"
        assert "tools" not in agent.build_run_payload(query="hi")

    def test_run_no_tools_omits_key(self):
        agent = Agent(name="n", description="d")
        agent.context = Mock()
        agent.id = "agent-1"
        assert "tools" not in agent.build_run_payload(query="hi")


# ---------------------------------------------------------------------------
# is_modified: input mutation is ephemeral; tool add/remove is a change.
# ---------------------------------------------------------------------------


class TestIsModified:
    def _onboarded_agent_with_model_tool(self, ctx):
        tool_dict = {
            "id": "m2",
            "type": "model",
            "name": "translate",
            "parameters": [{"name": "temperature", "value": 0.5, "datatype": "number"}],
        }
        agent = _bound_agent(ctx).from_dict(
            {"name": "n", "description": "d", "tools": [tool_dict], "status": "onboarded"}
        )
        agent._update_saved_state()
        return agent

    def test_input_mutation_not_modified(self):
        agent = self._onboarded_agent_with_model_tool(_ctx())
        assert agent.is_modified is False
        agent.tools[0].inputs.temperature = 0.9
        assert agent.is_modified is False

    def test_adding_a_tool_is_modified(self):
        agent = self._onboarded_agent_with_model_tool(_ctx())
        agent.tools = agent.tools + [_model_tool()]
        assert agent.is_modified is True

    def test_not_modified_after_save_so_onboarded_run_is_allowed(self):
        # Regression: save() restored the caller's tool objects but did not
        # re-baseline the saved state, so is_modified read True and a following
        # run() on an onboarded agent wrongly raised.
        ctx = _ctx()

        def fake_request(method, path, **kw):
            if method == "post":
                return {
                    "id": "agent-1",
                    "name": "a",
                    "description": "d",
                    "status": "onboarded",
                    "tools": [{"id": "m2", "type": "model", "name": "translate"}],
                }
            return {}

        ctx.client.request.side_effect = fake_request
        ctx.client.get.side_effect = lambda *a, **k: {}

        agent = _bound_agent(ctx)(name="a", description="d", tools=[_model_tool(temperature=2)])
        agent.save()

        assert agent.is_modified is False


# ---------------------------------------------------------------------------
# Attach-only shapes (no per-tool override) still serialize for create.
# ---------------------------------------------------------------------------


class TestAttachShapes:
    def test_string_id_resolves_type(self):
        snap = {"id": "model-1", "type": "model", "name": "Translate"}
        with patch.object(Agent, "_resolve_tool_snapshot", return_value=snap):
            entry = Agent._normalize_tool_for_api("model-1")
        assert entry["type"] == "model"
        assert entry["id"] == "model-1"

    def test_unresolvable_string_id_falls_back_to_bare_entry(self):
        with patch.object(Agent, "_resolve_tool_snapshot", return_value=None):
            entry = Agent._normalize_tool_for_api("tool-x")
        assert entry == {"id": "tool-x"}

    def test_as_tool_snapshot_dict_passthrough(self):
        as_tool_dict = {
            "id": "tool-1",
            "asset_id": "tool-1",
            "type": "model",
            "parameters": [
                {"name": "temperature", "value": "0.5", "allow_multi": False, "supports_variables": True}
            ],
        }
        # A dict that already carries a type must not trigger asset resolution.
        with patch.object(Agent, "_resolve_tool_snapshot", side_effect=AssertionError("must not resolve")):
            agent = Agent(name="n", description="d", tools=[as_tool_dict])
            agent.context = Mock()
            entry = _tool_by_id(agent.build_save_payload()["tools"], "tool-1")
        assert entry["assetId"] == "tool-1"
        param = entry["parameters"][0]
        assert param["name"] == "temperature"
        assert param["value"] == "0.5"
        assert param["allowMulti"] is False
        assert param["supportsVariables"] is True
