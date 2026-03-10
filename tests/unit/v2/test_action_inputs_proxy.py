"""Unit tests for ActionInputsProxy default value extraction and type coercion.

This module tests the fix for the bug where optional tool parameters with
backend defaults (e.g. ``num_results`` for Tavily search) were stored as raw
dicts instead of extracted primitive values, causing the run payload to send
malformed data to the backend.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from aixplain.v2.integration import ActionInputsProxy, Input, Action


# =============================================================================
# Helper factories
# =============================================================================


def _make_input(name, code, datatype, default_value=None, required=False):
    """Create an Input instance with an optional default value dict."""
    default_list = []
    if default_value is not None:
        default_list = [default_value]
    return Input(
        name=name,
        code=code,
        datatype=datatype,
        default_value=default_list,
        required=required,
    )


def _make_default(label, value, provider_value=None):
    """Create a backend-style default value dict."""
    return {
        "label": label,
        "value": value,
        "providerValue": provider_value or value,
        "isUrl": False,
    }


# =============================================================================
# _coerce_value Tests
# =============================================================================


class TestCoerceValue:
    """Tests for ActionInputsProxy._coerce_value static method."""

    def test_coerce_integer_from_string(self):
        """String '10' with datatype 'number' should become int 10."""
        assert ActionInputsProxy._coerce_value("10", "number") == 10
        assert isinstance(ActionInputsProxy._coerce_value("10", "number"), int)

    def test_coerce_float_from_string(self):
        """String '3.14' with datatype 'number' should become float 3.14."""
        assert ActionInputsProxy._coerce_value("3.14", "number") == 3.14
        assert isinstance(ActionInputsProxy._coerce_value("3.14", "number"), float)

    def test_coerce_integer_datatype(self):
        """String '5' with datatype 'integer' should become int 5."""
        assert ActionInputsProxy._coerce_value("5", "integer") == 5
        assert isinstance(ActionInputsProxy._coerce_value("5", "integer"), int)

    def test_coerce_boolean_true(self):
        """String 'true' with datatype 'boolean' should become True."""
        assert ActionInputsProxy._coerce_value("true", "boolean") is True

    def test_coerce_boolean_false(self):
        """String 'false' with datatype 'boolean' should become False."""
        assert ActionInputsProxy._coerce_value("false", "boolean") is False

    def test_coerce_boolean_yes(self):
        """String 'yes' with datatype 'boolean' should become True."""
        assert ActionInputsProxy._coerce_value("yes", "boolean") is True

    def test_coerce_boolean_one(self):
        """String '1' with datatype 'boolean' should become True."""
        assert ActionInputsProxy._coerce_value("1", "boolean") is True

    def test_coerce_boolean_zero(self):
        """String '0' with datatype 'boolean' should become False."""
        assert ActionInputsProxy._coerce_value("0", "boolean") is False

    def test_coerce_string_passthrough(self):
        """String datatype should pass through unchanged."""
        assert ActionInputsProxy._coerce_value("basic", "string") == "basic"

    def test_coerce_none_returns_none(self):
        """None value should return None regardless of datatype."""
        assert ActionInputsProxy._coerce_value(None, "number") is None
        assert ActionInputsProxy._coerce_value(None, "boolean") is None
        assert ActionInputsProxy._coerce_value(None, "string") is None

    def test_coerce_invalid_number_falls_back(self):
        """Non-numeric string with datatype 'number' should return original string."""
        assert ActionInputsProxy._coerce_value("not_a_number", "number") == "not_a_number"

    def test_coerce_unknown_datatype_passthrough(self):
        """Unknown datatype should pass through the value unchanged."""
        assert ActionInputsProxy._coerce_value("hello", "unknown_type") == "hello"


# =============================================================================
# _extract_default_value Tests
# =============================================================================


class TestExtractDefaultValue:
    """Tests for ActionInputsProxy._extract_default_value static method."""

    def test_extract_number_default(self):
        """Number default should be extracted and coerced to int."""
        inp = _make_input("Num Results", "num_results", "number", _make_default("Num Results", "10"))
        result = ActionInputsProxy._extract_default_value(inp)
        assert result == 10
        assert isinstance(result, int)

    def test_extract_float_default(self):
        """Float default should be extracted and coerced to float."""
        inp = _make_input("Score", "score", "number", _make_default("Score", "0.75"))
        result = ActionInputsProxy._extract_default_value(inp)
        assert result == 0.75
        assert isinstance(result, float)

    def test_extract_string_default(self):
        """String default should be extracted as-is."""
        inp = _make_input(
            "Search Depth",
            "search_depth",
            "string",
            _make_default("Search Depth", "basic"),
        )
        result = ActionInputsProxy._extract_default_value(inp)
        assert result == "basic"

    def test_extract_boolean_default_false(self):
        """Boolean 'false' default should be extracted as False."""
        inp = _make_input(
            "Include Answer",
            "include_answer",
            "boolean",
            _make_default("Include Answer", "false"),
        )
        result = ActionInputsProxy._extract_default_value(inp)
        assert result is False

    def test_extract_boolean_default_true(self):
        """Boolean 'true' default should be extracted as True."""
        inp = _make_input(
            "Include Images",
            "include_images",
            "boolean",
            _make_default("Include Images", "true"),
        )
        result = ActionInputsProxy._extract_default_value(inp)
        assert result is True

    def test_extract_empty_default_returns_none(self):
        """Empty defaultValue list should return None."""
        inp = _make_input("Query", "query", "string")
        result = ActionInputsProxy._extract_default_value(inp)
        assert result is None

    def test_extract_non_dict_default_passthrough(self):
        """Non-dict default value should be returned as-is."""
        inp = Input(name="Raw", code="raw", datatype="string", default_value=["literal_value"])
        result = ActionInputsProxy._extract_default_value(inp)
        assert result == "literal_value"

    def test_extract_default_with_none_value_key(self):
        """Default dict with value=None should return None."""
        inp = _make_input("Optional", "optional", "string", {"label": "Optional", "value": None})
        result = ActionInputsProxy._extract_default_value(inp)
        assert result is None


# =============================================================================
# ActionInputsProxy Integration Tests (with mocked backend)
# =============================================================================


class TestActionInputsProxyDefaults:
    """Tests for ActionInputsProxy storing extracted defaults after fetch."""

    @staticmethod
    def _create_proxy_with_inputs(inputs):
        """Create an ActionInputsProxy with mocked list_inputs returning given inputs."""
        container = Mock()
        action = Action(name="search", inputs=inputs)
        container.list_inputs = Mock(return_value=[action])

        proxy = ActionInputsProxy(container, "search")
        return proxy

    def test_fetched_defaults_are_primitives_not_dicts(self):
        """After fetching, default values should be primitives, not raw backend dicts."""
        inputs = [
            _make_input("Query", "query", "string"),
            _make_input(
                "Num Results",
                "num_results",
                "number",
                _make_default("Num Results", "10"),
            ),
            _make_input(
                "Search Depth",
                "search_depth",
                "string",
                _make_default("Search Depth", "basic"),
            ),
            _make_input(
                "Include Answer",
                "include_answer",
                "boolean",
                _make_default("Include Answer", "false"),
            ),
        ]
        proxy = self._create_proxy_with_inputs(inputs)

        assert proxy["query"] is None
        assert proxy["num_results"] == 10
        assert isinstance(proxy["num_results"], int)
        assert proxy["search_depth"] == "basic"
        assert proxy["include_answer"] is False

    def test_default_values_not_stored_as_dicts(self):
        """Regression: default values must never be dicts (the original bug)."""
        inputs = [
            _make_input(
                "Num Results",
                "num_results",
                "number",
                _make_default("Num Results", "10"),
            ),
        ]
        proxy = self._create_proxy_with_inputs(inputs)
        value = proxy["num_results"]
        assert not isinstance(value, dict), f"Default should be a primitive, got dict: {value}"

    def test_user_override_replaces_default(self):
        """Explicitly setting a value should override the extracted default."""
        inputs = [
            _make_input(
                "Num Results",
                "num_results",
                "number",
                _make_default("Num Results", "10"),
            ),
        ]
        proxy = self._create_proxy_with_inputs(inputs)
        assert proxy["num_results"] == 10

        proxy["num_results"] = 5
        assert proxy["num_results"] == 5

    def test_reset_restores_extracted_default(self):
        """reset_input should restore the extracted primitive default, not the raw dict."""
        inputs = [
            _make_input(
                "Num Results",
                "num_results",
                "number",
                _make_default("Num Results", "10"),
            ),
        ]
        proxy = self._create_proxy_with_inputs(inputs)

        proxy["num_results"] = 99
        assert proxy["num_results"] == 99

        proxy.reset_input("num_results")
        assert proxy["num_results"] == 10
        assert isinstance(proxy["num_results"], int)

    def test_none_defaults_excluded_from_items(self):
        """Parameters with None defaults should appear in keys but have None values."""
        inputs = [
            _make_input("Query", "query", "string"),
            _make_input(
                "Num Results",
                "num_results",
                "number",
                _make_default("Num Results", "10"),
            ),
        ]
        proxy = self._create_proxy_with_inputs(inputs)

        items = dict(proxy.items())
        assert "query" in items
        assert items["query"] is None
        assert items["num_results"] == 10


# =============================================================================
# Tool._merge_with_dynamic_attrs payload Tests
# =============================================================================


class TestToolMergePayloadDefaults:
    """Tests verifying that _merge_with_dynamic_attrs produces clean payloads."""

    @staticmethod
    def _create_tool_with_action_proxy(inputs):
        """Create a minimal Tool-like object with a mocked actions proxy."""
        from aixplain.v2.tool import Tool

        tool = Tool.__new__(Tool)
        tool.id = "test-tool-id"
        tool.name = "Test Tool"
        tool.allowed_actions = ["search"]
        tool._dynamic_attrs = {}

        action = Action(name="search", inputs=inputs)
        container = Mock()
        container.list_inputs = Mock(return_value=[action])
        proxy = ActionInputsProxy(container, "search")

        actions_mock = MagicMock()
        actions_mock.__getitem__ = Mock(return_value=proxy)
        tool.__dict__["actions"] = actions_mock

        return tool

    def test_payload_contains_primitive_defaults(self):
        """Run payload should contain primitive values, not backend default dicts."""
        inputs = [
            _make_input("Query", "query", "string"),
            _make_input(
                "Num Results",
                "num_results",
                "number",
                _make_default("Num Results", "10"),
            ),
            _make_input(
                "Search Depth",
                "search_depth",
                "string",
                _make_default("Search Depth", "basic"),
            ),
            _make_input(
                "Include Answer",
                "include_answer",
                "boolean",
                _make_default("Include Answer", "false"),
            ),
        ]
        tool = self._create_tool_with_action_proxy(inputs)

        result = tool._merge_with_dynamic_attrs(action="search", data={"query": "friendship paradox"})

        assert result["action"] == "search"
        data = result["data"]
        assert data["query"] == "friendship paradox"
        assert data["num_results"] == 10
        assert data["search_depth"] == "basic"
        assert data["include_answer"] is False
        for key, value in data.items():
            assert not isinstance(value, dict), f"Payload key '{key}' should not be a dict, got: {value}"

    def test_payload_user_data_overrides_defaults(self):
        """User-provided data should override extracted defaults in the payload."""
        inputs = [
            _make_input("Query", "query", "string"),
            _make_input(
                "Num Results",
                "num_results",
                "number",
                _make_default("Num Results", "10"),
            ),
        ]
        tool = self._create_tool_with_action_proxy(inputs)

        result = tool._merge_with_dynamic_attrs(action="search", data={"query": "test", "num_results": 3})

        assert result["data"]["num_results"] == 3

    def test_payload_excludes_none_defaults(self):
        """Parameters with None defaults should not appear in the payload."""
        inputs = [
            _make_input("Query", "query", "string"),
            _make_input("Domains", "domains", "string"),
        ]
        tool = self._create_tool_with_action_proxy(inputs)

        result = tool._merge_with_dynamic_attrs(action="search", data={"query": "test"})

        assert "domains" not in result["data"]
