"""Unit tests for Input/Inputs default value handling and type validation.

This module tests the unified actions/inputs hierarchy (Input, Inputs, Action)
that replaced the legacy ActionInputsProxy. It verifies that:
- Input.from_action_input_spec() correctly extracts default values
- Input validators enforce type constraints
- Inputs collection provides correct dict-like access, reset, and iteration
- Tool._merge_with_dynamic_attrs produces clean payloads with primitive defaults
"""

import pytest

from aixplain.v2.actions import Action, Input, Inputs
from aixplain.v2.integration import ActionInputSpec


# =============================================================================
# Helper factories
# =============================================================================


def _make_spec(name, code, datatype, default_value=None, required=False, description=""):
    """Create an ActionInputSpec with an optional default value."""
    default_list = []
    if default_value is not None:
        default_list = [default_value]
    return ActionInputSpec(
        name=name,
        code=code,
        datatype=datatype,
        default_value=default_list,
        required=required,
        description=description,
    )


def _build_inputs(specs):
    """Build an Inputs collection from a list of ActionInputSpec objects."""
    return Inputs.from_action_input_specs(specs)


# =============================================================================
# Input Validator Tests
# =============================================================================


class TestInputValidator:
    """Tests for Input type validation via from_action_input_spec."""

    def test_validate_number_accepts_int(self):
        """Number datatype should accept int values."""
        spec = _make_spec("Count", "count", "number", 10)
        inp = Input.from_action_input_spec(spec)
        inp.value = 42
        assert inp.value == 42

    def test_validate_number_accepts_float(self):
        """Number datatype should accept float values."""
        spec = _make_spec("Score", "score", "number", 0.75)
        inp = Input.from_action_input_spec(spec)
        inp.value = 3.14
        assert inp.value == 3.14

    def test_validate_number_rejects_string(self):
        """Number datatype should reject string values."""
        spec = _make_spec("Count", "count", "number", 10)
        inp = Input.from_action_input_spec(spec)
        with pytest.raises(ValueError):
            inp.value = "not_a_number"

    def test_validate_integer_accepts_int(self):
        """Integer datatype should accept int values."""
        spec = _make_spec("Count", "count", "integer", 5)
        inp = Input.from_action_input_spec(spec)
        inp.value = 7
        assert inp.value == 7

    def test_validate_boolean_accepts_bool(self):
        """Boolean datatype should accept bool values."""
        spec = _make_spec("Flag", "flag", "boolean", True)
        inp = Input.from_action_input_spec(spec)
        inp.value = False
        assert inp.value is False

    def test_validate_boolean_rejects_string(self):
        """Boolean datatype should reject string values."""
        spec = _make_spec("Flag", "flag", "boolean", True)
        inp = Input.from_action_input_spec(spec)
        with pytest.raises(ValueError):
            inp.value = "true"

    def test_validate_string_accepts_string(self):
        """String datatype should accept string values."""
        spec = _make_spec("Query", "query", "string", "default")
        inp = Input.from_action_input_spec(spec)
        inp.value = "hello"
        assert inp.value == "hello"

    def test_validate_none_always_accepted(self):
        """None value should be accepted regardless of datatype."""
        spec = _make_spec("Count", "count", "number", 10)
        inp = Input.from_action_input_spec(spec)
        inp.value = None
        assert inp.value is None

    def test_validate_unknown_datatype_accepts_anything(self):
        """Unknown datatype should accept any value."""
        spec = _make_spec("Custom", "custom", "unknown_type", "hello")
        inp = Input.from_action_input_spec(spec)
        inp.value = 42
        assert inp.value == 42


# =============================================================================
# Input.from_action_input_spec Default Extraction Tests
# =============================================================================


class TestInputFromActionInputSpec:
    """Tests for Input.from_action_input_spec() default value extraction."""

    def test_extract_number_default(self):
        """Number default should be stored correctly."""
        spec = _make_spec("Num Results", "num_results", "number", 10)
        inp = Input.from_action_input_spec(spec)
        assert inp.value == 10
        assert isinstance(inp.value, int)

    def test_extract_float_default(self):
        """Float default should be stored correctly."""
        spec = _make_spec("Score", "score", "number", 0.75)
        inp = Input.from_action_input_spec(spec)
        assert inp.value == 0.75
        assert isinstance(inp.value, float)

    def test_extract_string_default(self):
        """String default should be stored as-is."""
        spec = _make_spec("Search Depth", "search_depth", "string", "basic")
        inp = Input.from_action_input_spec(spec)
        assert inp.value == "basic"

    def test_extract_boolean_default_false(self):
        """Boolean False default should be stored correctly."""
        spec = _make_spec("Include Answer", "include_answer", "boolean", False)
        inp = Input.from_action_input_spec(spec)
        assert inp.value is False

    def test_extract_boolean_default_true(self):
        """Boolean True default should be stored correctly."""
        spec = _make_spec("Include Images", "include_images", "boolean", True)
        inp = Input.from_action_input_spec(spec)
        assert inp.value is True

    def test_extract_empty_default_returns_none(self):
        """Empty defaultValue list should result in None value."""
        spec = _make_spec("Query", "query", "string")
        inp = Input.from_action_input_spec(spec)
        assert inp.value is None

    def test_extract_uses_code_as_name(self):
        """Input name should come from ActionInputSpec.code."""
        spec = _make_spec("Num Results", "num_results", "number", 10)
        inp = Input.from_action_input_spec(spec)
        assert inp.name == "num_results"

    def test_extract_derives_code_from_name(self):
        """When code is None, name should be derived from display name."""
        spec = ActionInputSpec(
            name="Num Results",
            code=None,
            datatype="number",
            default_value=[10],
        )
        inp = Input.from_action_input_spec(spec)
        assert inp.name == "num_results"

    def test_extract_preserves_required_flag(self):
        """Required flag should be preserved."""
        spec = _make_spec("Query", "query", "string", required=True)
        inp = Input.from_action_input_spec(spec)
        assert inp.required is True

    def test_extract_preserves_datatype(self):
        """Datatype should be stored as the input type."""
        spec = _make_spec("Count", "count", "number", 10)
        inp = Input.from_action_input_spec(spec)
        assert inp.type == "number"


# =============================================================================
# Inputs Collection Tests
# =============================================================================


class TestInputsCollection:
    """Tests for Inputs collection dict-like behavior."""

    def test_getitem_returns_input_object(self):
        """Bracket access should return the Input object."""
        specs = [_make_spec("Query", "query", "string")]
        inputs = _build_inputs(specs)
        result = inputs["query"]
        assert isinstance(result, Input)

    def test_getitem_value_equality(self):
        """Input objects should compare equal to their value."""
        specs = [_make_spec("Num Results", "num_results", "number", 10)]
        inputs = _build_inputs(specs)
        assert inputs["num_results"] == 10

    def test_setitem_updates_value(self):
        """Setting a value via bracket notation should update the input."""
        specs = [_make_spec("Num Results", "num_results", "number", 10)]
        inputs = _build_inputs(specs)
        assert inputs["num_results"] == 10

        inputs["num_results"] = 5
        assert inputs["num_results"] == 5

    def test_setitem_unknown_key_raises(self):
        """Setting an unknown key should raise KeyError."""
        specs = [_make_spec("Query", "query", "string")]
        inputs = _build_inputs(specs)
        with pytest.raises(KeyError):
            inputs["nonexistent"] = "value"

    def test_contains(self):
        """Membership test should work correctly."""
        specs = [_make_spec("Query", "query", "string")]
        inputs = _build_inputs(specs)
        assert "query" in inputs
        assert "nonexistent" not in inputs

    def test_len(self):
        """Length should match number of inputs."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Count", "count", "number", 10),
        ]
        inputs = _build_inputs(specs)
        assert len(inputs) == 2

    def test_keys_returns_all_names(self):
        """keys() should return all input names."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Count", "count", "number", 10),
        ]
        inputs = _build_inputs(specs)
        assert inputs.keys() == ["query", "count"]

    def test_values_returns_raw_values(self):
        """values() should return raw values, not Input objects."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Count", "count", "number", 10),
        ]
        inputs = _build_inputs(specs)
        values = inputs.values()
        assert values == [None, 10]
        assert not isinstance(values[1], Input)

    def test_items_returns_name_value_pairs(self):
        """items() should return (name, raw_value) pairs."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Count", "count", "number", 10),
        ]
        inputs = _build_inputs(specs)
        items = dict(inputs.items())
        assert "query" in items
        assert items["query"] is None
        assert items["count"] == 10

    def test_defaults_are_primitives_not_dicts(self):
        """After construction, default values should be primitives, not raw backend dicts."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Num Results", "num_results", "number", 10),
            _make_spec("Search Depth", "search_depth", "string", "basic"),
            _make_spec("Include Answer", "include_answer", "boolean", False),
        ]
        inputs = _build_inputs(specs)

        assert inputs["query"].value is None
        assert inputs["num_results"] == 10
        assert isinstance(inputs["num_results"].value, int)
        assert inputs["search_depth"] == "basic"
        assert inputs["include_answer"] == False

    def test_default_values_not_stored_as_dicts(self):
        """Regression: default values must never be dicts (the original bug)."""
        specs = [_make_spec("Num Results", "num_results", "number", 10)]
        inputs = _build_inputs(specs)
        value = inputs["num_results"].value
        assert not isinstance(value, dict), f"Default should be a primitive, got dict: {value}"

    def test_user_override_replaces_default(self):
        """Explicitly setting a value should override the extracted default."""
        specs = [_make_spec("Num Results", "num_results", "number", 10)]
        inputs = _build_inputs(specs)
        assert inputs["num_results"] == 10

        inputs["num_results"] = 5
        assert inputs["num_results"] == 5

    def test_reset_restores_default(self):
        """reset() should restore the default value."""
        specs = [_make_spec("Num Results", "num_results", "number", 10)]
        inputs = _build_inputs(specs)

        inputs["num_results"] = 99
        assert inputs["num_results"] == 99

        inputs.reset("num_results")
        assert inputs["num_results"] == 10
        assert isinstance(inputs["num_results"].value, int)

    def test_reset_all(self):
        """reset() with no arguments should restore all defaults."""
        specs = [
            _make_spec("Count", "count", "number", 10),
            _make_spec("Depth", "depth", "string", "basic"),
        ]
        inputs = _build_inputs(specs)

        inputs["count"] = 99
        inputs["depth"] = "advanced"
        inputs.reset()
        assert inputs["count"] == 10
        assert inputs["depth"] == "basic"

    def test_none_defaults_in_items(self):
        """Parameters with None defaults should appear in keys with None values."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Num Results", "num_results", "number", 10),
        ]
        inputs = _build_inputs(specs)

        items = dict(inputs.items())
        assert "query" in items
        assert items["query"] is None
        assert items["num_results"] == 10

    def test_dot_notation_read(self):
        """Dot notation should work for reading inputs."""
        specs = [_make_spec("Count", "count", "number", 10)]
        inputs = _build_inputs(specs)
        assert inputs.count == 10

    def test_dot_notation_write(self):
        """Dot notation should work for writing inputs."""
        specs = [_make_spec("Count", "count", "number", 10)]
        inputs = _build_inputs(specs)
        inputs.count = 20
        assert inputs.count == 20


# =============================================================================
# Tool._merge_with_dynamic_attrs payload Tests
# =============================================================================


class TestToolMergePayloadDefaults:
    """Tests verifying that _merge_with_dynamic_attrs produces clean payloads."""

    @staticmethod
    def _create_tool_with_inputs(specs):
        """Create a minimal Tool with an Action containing the given input specs."""
        from aixplain.v2.tool import Tool

        tool = Tool.__new__(Tool)
        tool.id = "test-tool-id"
        tool.name = "Test Tool"
        tool.allowed_actions = ["search"]
        tool._dynamic_attrs = {}

        inputs_obj = _build_inputs(specs)
        action_obj = Action(name="search", inputs=inputs_obj)

        from aixplain.v2.actions import Actions

        actions = Actions(actions={"search": action_obj})
        tool.__dict__["actions"] = actions

        return tool

    def test_payload_contains_primitive_defaults(self):
        """Run payload should contain primitive values, not backend default dicts."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Num Results", "num_results", "number", 10),
            _make_spec("Search Depth", "search_depth", "string", "basic"),
            _make_spec("Include Answer", "include_answer", "boolean", False),
        ]
        tool = self._create_tool_with_inputs(specs)

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
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Num Results", "num_results", "number", 10),
        ]
        tool = self._create_tool_with_inputs(specs)

        result = tool._merge_with_dynamic_attrs(action="search", data={"query": "test", "num_results": 3})

        assert result["data"]["num_results"] == 3

    def test_payload_excludes_none_defaults(self):
        """Parameters with None defaults should not appear in the payload."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Domains", "domains", "string"),
        ]
        tool = self._create_tool_with_inputs(specs)

        result = tool._merge_with_dynamic_attrs(action="search", data={"query": "test"})

        assert "domains" not in result["data"]

    def test_payload_uses_single_allowed_action_when_omitted(self):
        """Missing action should fall back to the single allowed action."""
        specs = [
            _make_spec("Query", "query", "string"),
            _make_spec("Num Results", "num_results", "number", 10),
        ]
        tool = self._create_tool_with_inputs(specs)

        result = tool._merge_with_dynamic_attrs(data={"query": "test"})

        assert result["action"] == "search"
        assert result["data"]["query"] == "test"
        assert result["data"]["num_results"] == 10
