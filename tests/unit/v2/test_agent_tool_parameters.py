"""Unit tests for per-tool parameter override in Agent save/run payloads.

Issue #966 / PROD-2481. Tools attached to an agent may now carry their own
``parameters`` in the user-facing ``{id, parameters: {...}}`` shape — the same
shape role models already accept. On the wire, per-tool ``parameters`` are
normalized into the platform's ``[{name, value}]`` ``NameValue`` list, both in
the create (``build_save_payload``) and run (``build_run_payload``) payloads.

Backward compatibility: plain string tool ids and existing ``as_tool()`` dicts
(whose ``parameters`` is already a list of full parameter definitions) must
continue to serialize unchanged.
"""

from typing import Any, Dict, List

from unittest.mock import Mock

from aixplain.v2.agent import Agent


def _agent(**kwargs: Any) -> Agent:
    """Build an :class:`Agent` that can run payload builders without a real client."""
    agent = Agent(**kwargs)
    agent.context = Mock()
    return agent


def _params_as_dict(parameters: List[dict]) -> Dict[str, Any]:
    """Flatten ``[{name, value}]`` to ``{name: value}`` for ergonomic assertions."""
    return {item["name"]: item["value"] for item in parameters}


def _tool_by_id(tools: List[dict], tool_id: str) -> dict:
    return next(t for t in tools if t.get("id") == tool_id or t.get("assetId") == tool_id)


class TestSavePayloadToolParameters:
    """``build_save_payload`` carries per-tool params in the NameValue shape."""

    def test_tool_dict_with_param_dict_normalized_to_namevalue(self):
        agent = _agent(
            name="n",
            description="d",
            tools=[{"id": "tool-1", "parameters": {"top_k": 5, "language": "es"}}],
        )
        payload = agent.build_save_payload()

        tool = _tool_by_id(payload["tools"], "tool-1")
        assert tool["id"] == "tool-1"
        assert _params_as_dict(tool["parameters"]) == {"top_k": 5, "language": "es"}

    def test_multiple_tools_each_keep_their_own_params(self):
        agent = _agent(
            name="n",
            description="d",
            tools=[
                {"id": "tool-1", "parameters": {"top_k": 5}},
                {"id": "tool-2", "parameters": {"language": "es"}},
            ],
        )
        payload = agent.build_save_payload()

        assert _params_as_dict(_tool_by_id(payload["tools"], "tool-1")["parameters"]) == {"top_k": 5}
        assert _params_as_dict(_tool_by_id(payload["tools"], "tool-2")["parameters"]) == {"language": "es"}

    def test_empty_param_dict_becomes_empty_list(self):
        agent = _agent(name="n", description="d", tools=[{"id": "tool-1", "parameters": {}}])
        payload = agent.build_save_payload()
        assert _tool_by_id(payload["tools"], "tool-1")["parameters"] == []

    def test_nested_filter_value_is_preserved(self):
        filters = {"field": "category", "op": "in", "values": ["a", "b"]}
        agent = _agent(
            name="n",
            description="d",
            tools=[{"id": "tool-1", "parameters": {"filters": filters}}],
        )
        payload = agent.build_save_payload()
        params = _params_as_dict(_tool_by_id(payload["tools"], "tool-1")["parameters"])
        assert params["filters"] == filters


class TestSavePayloadBackwardCompat:
    """Existing string-id / as_tool()-list shapes serialize unchanged."""

    def test_plain_string_tool_id(self):
        agent = _agent(name="n", description="d", tools=["tool-1"])
        payload = agent.build_save_payload()
        assert payload["tools"] == [{"id": "tool-1"}]

    def test_tool_dict_without_parameters(self):
        agent = _agent(name="n", description="d", tools=[{"id": "tool-1"}])
        payload = agent.build_save_payload()
        assert _tool_by_id(payload["tools"], "tool-1") == {"id": "tool-1"}

    def test_as_tool_list_parameters_still_normalized(self):
        """A dict whose ``parameters`` is a list of definitions keeps the legacy path."""
        as_tool_dict = {
            "id": "tool-1",
            "asset_id": "tool-1",
            "type": "model",
            "parameters": [
                {
                    "name": "temperature",
                    "value": "0.5",
                    "allow_multi": False,
                    "supports_variables": True,
                }
            ],
        }
        agent = _agent(name="n", description="d", tools=[as_tool_dict])
        payload = agent.build_save_payload()
        tool = _tool_by_id(payload["tools"], "tool-1")
        assert tool["assetId"] == "tool-1"
        # snake_case keys inside the parameter definition map to camelCase.
        param = tool["parameters"][0]
        assert param["name"] == "temperature"
        assert param["value"] == "0.5"
        assert param["allowMulti"] is False
        assert param["supportsVariables"] is True


class TestRunPayloadToolParameters:
    """``build_run_payload`` forwards run-time per-tool overrides."""

    def test_run_tools_param_dict_normalized(self):
        agent = _agent(name="n", description="d")
        agent.id = "agent-1"
        payload = agent.build_run_payload(
            query="hi",
            tools=[{"id": "tool-1", "parameters": {"top_k": 8}}],
        )
        tool = _tool_by_id(payload["tools"], "tool-1")
        assert _params_as_dict(tool["parameters"]) == {"top_k": 8}

    def test_run_without_tools_omits_tools_key(self):
        agent = _agent(name="n", description="d")
        agent.id = "agent-1"
        payload = agent.build_run_payload(query="hi")
        assert "tools" not in payload

    def test_run_multiple_tools_keyed_by_id(self):
        agent = _agent(name="n", description="d")
        agent.id = "agent-1"
        payload = agent.build_run_payload(
            query="hi",
            tools=[
                {"id": "tool-1", "parameters": {"top_k": 8}},
                {"id": "tool-2", "parameters": {"language": "fr"}},
            ],
        )
        assert _params_as_dict(_tool_by_id(payload["tools"], "tool-1")["parameters"]) == {"top_k": 8}
        assert _params_as_dict(_tool_by_id(payload["tools"], "tool-2")["parameters"]) == {"language": "fr"}

    def test_run_string_tool_id(self):
        agent = _agent(name="n", description="d")
        agent.id = "agent-1"
        payload = agent.build_run_payload(query="hi", tools=["tool-1"])
        assert payload["tools"] == [{"id": "tool-1"}]
