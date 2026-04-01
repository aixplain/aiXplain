"""Functional tests for the Actions / Inputs object hierarchy.

Validates the full spec against real backend data:

    Actions → Action → Inputs → Input

Covers both Model (single "run" action + shorthand) and Tool (multiple actions).
"""

import pytest

from aixplain.v2.actions import Actions, Action, Inputs, Input


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def text_model_id():
    return "69b7e5f1b2fe44704ab0e7d0"  # GPT-5.4


@pytest.fixture(scope="module")
def slack_integration_id():
    return "686432941223092cb4294d3f"


@pytest.fixture(scope="module")
def model(client, text_model_id):
    return client.Model.get(text_model_id)


@pytest.fixture(scope="module")
def tool(client, slack_integration_id):
    """Find a tool backed by the Slack integration that has actions."""
    results = client.Tool.search(page_size=20).results
    for t in results:
        if t.actions_available and t.integration == slack_integration_id:
            return t
    # Fallback: just find any tool with actions
    for t in results:
        if t.actions_available:
            return t
    pytest.skip("No tool with actions found")


# =========================================================================
# MODEL — Actions / Inputs hierarchy
# =========================================================================


class TestModelActions:
    """model.actions returns Actions(['run']) with a single run action."""

    def test_model_actions_type(self, model):
        assert isinstance(model.actions, Actions)

    def test_model_actions_contains_run(self, model):
        assert "run" in model.actions

    def test_model_actions_len(self, model):
        assert len(model.actions) == 1

    def test_model_actions_iter(self, model):
        names = list(model.actions)
        assert names == ["run"]

    def test_model_actions_repr(self, model):
        r = repr(model.actions)
        assert "Actions" in r
        assert "run" in r


class TestModelAction:
    """model.actions['run'] returns an Action with inputs."""

    def test_action_type(self, model):
        action = model.actions["run"]
        assert isinstance(action, Action)

    def test_action_name(self, model):
        assert model.actions["run"].name == "run"

    def test_action_has_inputs(self, model):
        action = model.actions["run"]
        assert isinstance(action.inputs, Inputs)
        assert len(action.inputs) > 0

    def test_action_repr(self, model):
        r = repr(model.actions["run"])
        assert "Action" in r
        assert "run" in r


class TestModelInputs:
    """model.actions['run'].inputs is an Inputs collection."""

    def test_inputs_type(self, model):
        inputs = model.actions["run"].inputs
        assert isinstance(inputs, Inputs)

    def test_inputs_contains_text(self, model):
        assert "text" in model.actions["run"].inputs

    def test_inputs_keys(self, model):
        keys = model.actions["run"].inputs.keys()
        assert isinstance(keys, list)
        assert "text" in keys

    def test_inputs_len(self, model):
        assert len(model.actions["run"].inputs) > 0

    def test_inputs_iter(self, model):
        names = list(model.actions["run"].inputs)
        assert "text" in names

    def test_inputs_required(self, model):
        required = model.actions["run"].inputs.required
        assert isinstance(required, list)
        assert "text" in required

    def test_inputs_repr(self, model):
        r = repr(model.actions["run"].inputs)
        assert "Inputs" in r


class TestModelInput:
    """model.actions['run'].inputs['text'] returns an Input object."""

    def test_input_type_bracket(self, model):
        inp = model.actions["run"].inputs["text"]
        assert isinstance(inp, Input)

    def test_input_type_dot(self, model):
        inp = model.actions["run"].inputs.text
        assert isinstance(inp, Input)

    def test_input_properties(self, model):
        inp = model.actions["run"].inputs["text"]
        assert inp.name == "text"
        assert inp.required is True
        assert inp.type is not None

    def test_input_value_property(self, model):
        inp = model.actions["run"].inputs["text"]
        # value exists (may be None as default)
        assert hasattr(inp, "value")

    def test_input_repr(self, model):
        r = repr(model.actions["run"].inputs["text"])
        assert "Input" in r
        assert "text" in r


class TestModelInputSetValue:
    """Setting values via both bracket and dot notation."""

    def test_set_via_bracket(self, model):
        model.actions["run"].inputs["temperature"] = 0.7
        assert model.actions["run"].inputs["temperature"].value == 0.7

    def test_set_via_dot(self, model):
        model.actions["run"].inputs.temperature = 0.5
        assert model.actions["run"].inputs.temperature.value == 0.5

    def test_set_via_shorthand_bracket(self, model):
        model.inputs["temperature"] = 0.3
        assert model.inputs["temperature"].value == 0.3

    def test_set_via_shorthand_dot(self, model):
        model.inputs.temperature = 0.9
        assert model.inputs.temperature.value == 0.9

    def test_eq_comparison(self, model):
        model.inputs.temperature = 0.7
        assert model.inputs.temperature == 0.7
        assert model.inputs["temperature"] == 0.7

    def test_reset_single(self, model):
        model.inputs.reset("temperature")
        original = model.inputs["temperature"].value
        model.inputs.temperature = 999
        assert model.inputs["temperature"].value == 999
        model.inputs.reset("temperature")
        assert model.inputs["temperature"].value == original

    def test_reset_all(self, model):
        model.inputs.reset()
        original = model.inputs["temperature"].value
        model.inputs.temperature = 999
        model.inputs.reset()
        assert model.inputs.temperature.value == original


# =========================================================================
# MODEL — Shorthand (model.inputs == model.actions["run"].inputs)
# =========================================================================


class TestModelShorthand:
    """model.inputs is the same object as model.actions['run'].inputs."""

    def test_same_object(self, model):
        assert model.inputs is model.actions["run"].inputs

    def test_shorthand_contains(self, model):
        assert "text" in model.inputs

    def test_shorthand_keys(self, model):
        assert model.inputs.keys() == model.actions["run"].inputs.keys()

    def test_shorthand_required(self, model):
        assert model.inputs.required == model.actions["run"].inputs.required

    def test_shorthand_set_reflects_in_action(self, model):
        model.inputs.temperature = 0.42
        assert model.actions["run"].inputs.temperature.value == 0.42

    def test_action_set_reflects_in_shorthand(self, model):
        model.actions["run"].inputs.temperature = 0.88
        assert model.inputs.temperature.value == 0.88


# =========================================================================
# TOOL — Actions / Inputs hierarchy (no shorthand)
# =========================================================================


class TestToolActions:
    """tool.actions returns an Actions collection with multiple actions."""

    def test_tool_actions_type(self, tool):
        assert isinstance(tool.actions, Actions)

    def test_tool_actions_len(self, tool):
        assert len(tool.actions) > 0

    def test_tool_actions_iter(self, tool):
        names = list(tool.actions)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    def test_tool_actions_repr(self, tool):
        r = repr(tool.actions)
        assert "Actions" in r

    def test_tool_actions_contains(self, tool):
        first_name = list(tool.actions)[0]
        assert first_name in tool.actions


def _find_action_with_inputs(tool):
    """Find the first action on the tool that has inputs."""
    for name in tool.actions:
        try:
            inputs = tool.actions[name].inputs
            if len(inputs) > 0:
                return name
        except (ValueError, Exception):
            continue
    return None


class TestToolAction:
    """tool.actions['name'] returns an Action with inputs."""

    def test_action_type(self, tool):
        first_name = list(tool.actions)[0]
        action = tool.actions[first_name]
        assert isinstance(action, Action)

    def test_action_name(self, tool):
        first_name = list(tool.actions)[0]
        action = tool.actions[first_name]
        assert action.name == first_name

    def test_action_has_inputs(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        action = tool.actions[action_name]
        assert isinstance(action.inputs, Inputs)
        assert len(action.inputs) > 0

    def test_action_repr(self, tool):
        first_name = list(tool.actions)[0]
        r = repr(tool.actions[first_name])
        assert "Action" in r


class TestToolInputs:
    """tool.actions['name'].inputs is an Inputs collection."""

    def test_inputs_type(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        inputs = tool.actions[action_name].inputs
        assert isinstance(inputs, Inputs)

    def test_inputs_keys(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        keys = tool.actions[action_name].inputs.keys()
        assert isinstance(keys, list)
        assert len(keys) > 0

    def test_inputs_required(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        required = tool.actions[action_name].inputs.required
        assert isinstance(required, list)

    def test_inputs_repr(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        r = repr(tool.actions[action_name].inputs)
        assert "Inputs" in r


class TestToolInput:
    """tool.actions['name'].inputs['param'] returns an Input object."""

    def test_input_type(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        inputs = tool.actions[action_name].inputs
        first_input_name = inputs.keys()[0]
        inp = inputs[first_input_name]
        assert isinstance(inp, Input)

    def test_input_properties(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        inputs = tool.actions[action_name].inputs
        first_input_name = inputs.keys()[0]
        inp = inputs[first_input_name]
        assert hasattr(inp, "name")
        assert hasattr(inp, "required")
        assert hasattr(inp, "type")
        assert hasattr(inp, "value")
        assert hasattr(inp, "description")

    def test_input_repr(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        inputs = tool.actions[action_name].inputs
        first_input_name = inputs.keys()[0]
        r = repr(inputs[first_input_name])
        assert "Input" in r


class TestToolInputSetValue:
    """Setting values on tool action inputs."""

    def test_set_via_bracket(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        inputs = tool.actions[action_name].inputs
        key = inputs.keys()[0]
        inputs[key] = "test_value"
        assert inputs[key].value == "test_value"

    def test_set_via_dot(self, tool):
        action_name = _find_action_with_inputs(tool)
        if not action_name:
            pytest.skip("No action with inputs found")
        inputs = tool.actions[action_name].inputs
        key = inputs.keys()[0]
        setattr(inputs, key, "dot_value")
        assert getattr(inputs, key).value == "dot_value"


# =========================================================================
# TOOL — No .inputs shorthand
# =========================================================================


class TestToolNoShorthand:
    """tool.inputs should raise AttributeError with a helpful message."""

    def test_tool_inputs_raises(self, tool):
        with pytest.raises(AttributeError, match="multiple actions"):
            _ = tool.inputs

    def test_tool_inputs_setter_raises(self, tool):
        with pytest.raises(AttributeError, match="multiple actions"):
            tool.inputs = {"foo": "bar"}
