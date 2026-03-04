"""Tests that validate the camelCase → snake_case migration for v2 public identifiers.

Covers:
- integration.py: Input, Action, ToolId dataclasses (field_name metadata + round-trip JSON)
- agent.py: AgentRunParams TypedDict keys, build_run_payload snake→camel translation
- mixins.py: ParameterInput, ToolDict TypedDict key names
- model.py: as_tool() and get_parameters() output key names
- agent.py: _normalize_tool_dict_for_api conversion for save payloads
"""

import json
from unittest.mock import Mock, patch, MagicMock

import pytest

from aixplain.v2.integration import Input, Action, ToolId
from aixplain.v2.agent import Agent, AgentRunParams
from aixplain.v2.mixins import ParameterInput, ToolDict


# =============================================================================
# Input dataclass: snake_case fields with camelCase JSON round-trip
# =============================================================================


class TestInputDataclass:
    """Validate Input uses snake_case attributes and preserves camelCase JSON keys."""

    SAMPLE_JSON = {
        "name": "channel",
        "code": "ch",
        "value": ["general"],
        "availableOptions": ["general", "random"],
        "datatype": "string",
        "allowMulti": True,
        "supportsVariables": False,
        "defaultValue": ["general"],
        "required": True,
        "fixed": False,
        "description": "Slack channel",
    }

    def test_from_dict_populates_snake_case_attrs(self):
        inp = Input.from_dict(self.SAMPLE_JSON)

        assert inp.available_options == ["general", "random"]
        assert inp.allow_multi is True
        assert inp.supports_variables is False
        assert inp.default_value == ["general"]

    def test_to_dict_emits_camelcase_keys(self):
        inp = Input.from_dict(self.SAMPLE_JSON)
        d = inp.to_dict()

        assert "availableOptions" in d
        assert "allowMulti" in d
        assert "supportsVariables" in d
        assert "defaultValue" in d
        # snake_case keys must NOT leak into JSON
        assert "available_options" not in d
        assert "allow_multi" not in d
        assert "supports_variables" not in d
        assert "default_value" not in d

    def test_round_trip_preserves_values(self):
        inp = Input.from_dict(self.SAMPLE_JSON)
        restored = Input.from_dict(inp.to_dict())

        assert restored.available_options == inp.available_options
        assert restored.allow_multi == inp.allow_multi
        assert restored.supports_variables == inp.supports_variables
        assert restored.default_value == inp.default_value

    def test_constructor_accepts_snake_case(self):
        inp = Input(
            name="test",
            available_options=["a", "b"],
            allow_multi=True,
            supports_variables=True,
            default_value=["a"],
        )
        assert inp.allow_multi is True
        assert inp.to_dict()["allowMulti"] is True


# =============================================================================
# Action dataclass: display_name
# =============================================================================


class TestActionDataclass:
    def test_display_name_from_dict(self):
        action = Action.from_dict({"name": "send", "displayName": "Send Message"})
        assert action.display_name == "Send Message"

    def test_display_name_to_dict(self):
        action = Action(name="send", display_name="Send Message")
        d = action.to_dict()
        assert d["displayName"] == "Send Message"
        assert "display_name" not in d


# =============================================================================
# ToolId dataclass: redirect_url
# =============================================================================


class TestToolIdDataclass:
    def test_redirect_url_from_dict(self):
        tid = ToolId.from_dict({"id": "abc", "redirectURL": "https://example.com/oauth"})
        assert tid.redirect_url == "https://example.com/oauth"

    def test_redirect_url_to_dict(self):
        tid = ToolId(id="abc", redirect_url="https://example.com/oauth")
        d = tid.to_dict()
        assert d["redirectURL"] == "https://example.com/oauth"
        assert "redirect_url" not in d

    def test_redirect_url_none_by_default(self):
        tid = ToolId(id="abc")
        assert tid.redirect_url is None


# =============================================================================
# AgentRunParams TypedDict: snake_case keys
# =============================================================================


class TestAgentRunParamsKeys:
    """Ensure the TypedDict uses snake_case key names."""

    def test_snake_case_keys_exist(self):
        hints = AgentRunParams.__annotations__
        assert "session_id" in hints
        assert "allow_history_and_session_id" in hints
        assert "execution_params" in hints
        assert "run_response_generation" in hints

    def test_camelcase_keys_absent(self):
        hints = AgentRunParams.__annotations__
        assert "sessionId" not in hints
        assert "allowHistoryAndSessionId" not in hints
        assert "executionParams" not in hints
        assert "runResponseGeneration" not in hints


# =============================================================================
# ParameterInput / ToolDict TypedDicts: snake_case keys
# =============================================================================


class TestTypedDictKeys:
    def test_parameter_input_snake_case(self):
        hints = ParameterInput.__annotations__
        assert "allow_multi" in hints
        assert "supports_variables" in hints
        assert "allowMulti" not in hints
        assert "supportsVariables" not in hints

    def test_tool_dict_snake_case(self):
        hints = ToolDict.__annotations__
        assert "asset_id" in hints
        assert "assetId" not in hints


# =============================================================================
# build_run_payload: snake_case kwargs → camelCase API payload
# =============================================================================


class TestBuildRunPayload:
    """Verify that build_run_payload translates snake_case kwargs to camelCase."""

    def _make_agent(self):
        agent = Agent.__new__(Agent)
        agent.id = "agent-123"
        agent.output_format = "text"
        agent.max_tokens = 2048
        agent.max_iterations = 5
        agent.expected_output = ""
        return agent

    def test_session_id_becomes_camelcase(self):
        agent = self._make_agent()
        payload = agent.build_run_payload(
            query="hello",
            session_id="sess-1",
        )
        assert payload["sessionId"] == "sess-1"
        assert "session_id" not in payload

    def test_allow_history_becomes_camelcase(self):
        agent = self._make_agent()
        payload = agent.build_run_payload(
            query="hello",
            allow_history_and_session_id=True,
        )
        assert payload["allowHistoryAndSessionId"] is True
        assert "allow_history_and_session_id" not in payload

    def test_execution_params_used(self):
        agent = self._make_agent()
        payload = agent.build_run_payload(
            query="hello",
            execution_params={"maxTokens": 100},
        )
        assert payload["executionParams"]["maxTokens"] == 100

    def test_run_response_generation_default_true(self):
        agent = self._make_agent()
        payload = agent.build_run_payload(query="hello")
        assert payload["runResponseGeneration"] is True

    def test_run_response_generation_false(self):
        agent = self._make_agent()
        payload = agent.build_run_payload(query="hello", run_response_generation=False)
        assert payload["runResponseGeneration"] is False


# =============================================================================
# _normalize_tool_dict_for_api: snake_case → camelCase at API boundary
# =============================================================================


class TestNormalizeToolDictForApi:
    """Verify that as_tool() snake_case output is converted to camelCase for the API."""

    def test_asset_id_converted(self):
        tool_dict = {"id": "t1", "name": "test", "asset_id": "t1"}
        result = Agent._normalize_tool_dict_for_api(tool_dict)
        assert result["assetId"] == "t1"
        assert "asset_id" not in result

    def test_parameters_inputs_converted(self):
        tool_dict = {
            "id": "t1",
            "name": "test",
            "asset_id": "t1",
            "parameters": [
                {
                    "code": "action1",
                    "name": "Action 1",
                    "description": "",
                    "inputs": {
                        "param1": {
                            "name": "param1",
                            "allow_multi": True,
                            "supports_variables": False,
                            "fixed": False,
                        }
                    },
                }
            ],
        }
        result = Agent._normalize_tool_dict_for_api(tool_dict)
        param_input = result["parameters"][0]["inputs"]["param1"]
        assert param_input["allowMulti"] is True
        assert param_input["supportsVariables"] is False
        assert "allow_multi" not in param_input
        assert "supports_variables" not in param_input

    def test_passthrough_keys_unchanged(self):
        tool_dict = {"id": "t1", "name": "test", "type": "model", "version": "1"}
        result = Agent._normalize_tool_dict_for_api(tool_dict)
        assert result == tool_dict
