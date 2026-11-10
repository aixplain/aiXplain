"""PROD-2921 follow-up: typing marker, bound-resource types, classification coverage, enum validation."""

import dataclasses
import enum
import importlib
import inspect
import pkgutil
import re
from pathlib import Path
from typing import get_args, get_origin, get_type_hints

import pytest

import aixplain.v2 as v2
from aixplain import Agent, Aixplain, ContextOverflowStrategy, ContextOverflowStrategyValue, File, ValidationError
from aixplain import UtilityModelInput
from aixplain.v2.plain_data import WireValue
from aixplain.v2.resource import BaseResource

REPO_ROOT = Path(__file__).resolve().parents[3]


# -- Type checkers can see the package ----------------------------------------------


def test_package_ships_the_py_typed_marker():
    assert (REPO_ROOT / "aixplain" / "py.typed").is_file()
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert re.search(r'\[tool\.setuptools\.package-data\]\s*\naixplain = \["py\.typed"\]', pyproject)


def _bound_resource_hints():
    hints = get_type_hints(Aixplain)
    return {name: get_args(hint)[0] for name, hint in hints.items() if get_origin(hint) is type}


def test_bound_resources_are_typed_as_classes():
    hints = _bound_resource_hints()

    assert {"Agent", "Model", "Session", "Tool", "File"} <= set(hints)


@pytest.mark.parametrize("name", sorted(_bound_resource_hints()))
def test_bound_resource_is_a_subclass_of_its_annotation(name):
    aix = Aixplain(api_key="test-key")

    assert issubclass(getattr(aix, name), _bound_resource_hints()[name])


# -- Every enum and non-resource dataclass is classified ------------------------------


def _v2_enums_and_dataclasses():
    found = set()
    for info in pkgutil.iter_modules(v2.__path__):
        module = importlib.import_module(f"aixplain.v2.{info.name}")
        for name, obj in vars(module).items():
            if not inspect.isclass(obj) or obj.__module__ != module.__name__:
                continue
            if issubclass(obj, enum.Enum) or (dataclasses.is_dataclass(obj) and not issubclass(obj, BaseResource)):
                found.add(name)
    return found


def test_every_enum_and_non_resource_dataclass_is_classified():
    doc = (REPO_ROOT / "docs" / "v2-plain-data.md").read_text(encoding="utf-8")
    named = set(re.findall(r"`([A-Za-z_]\w*)`", doc))

    missing = sorted(_v2_enums_and_dataclasses() - named)

    assert not missing, f"add these to docs/v2-plain-data.md: {missing}"


# -- Bad enum strings raise instead of being sent -----------------------------------


class TestAgentEnumStrings:
    @pytest.mark.parametrize("field", ["output_format", "context_overflow_strategy"])
    def test_constructor_rejects_an_unknown_string(self, field):
        with pytest.raises(ValidationError, match=f"Unknown {field} 'bogus'. Accepted values"):
            Agent(name="a", **{field: "bogus"})

    @pytest.mark.parametrize("field", ["output_format", "context_overflow_strategy"])
    def test_assignment_rejects_an_unknown_string(self, field):
        agent = Agent(name="a")

        with pytest.raises(ValidationError, match=f"Unknown {field}"):
            setattr(agent, field, "bogus")

    def test_value_is_case_sensitive(self):
        with pytest.raises(ValidationError):
            Agent(name="a", context_overflow_strategy="SUMMARIZE")

    def test_enum_member_is_stored_as_its_value(self):
        agent = Agent(name="a")
        agent.output_format = v2.OutputFormat.JSON

        assert type(agent.output_format) is str
        assert agent.output_format == "json"

    def test_none_clears_the_field(self):
        agent = Agent(name="a", context_overflow_strategy="summarize")
        agent.context_overflow_strategy = None

        assert agent.context_overflow_strategy is None

    @pytest.mark.parametrize("key", ["context_overflow_strategy", "contextOverflowStrategy"])
    def test_per_run_override_rejects_an_unknown_string(self, key):
        agent = Agent(name="a")

        with pytest.raises(ValidationError, match="Unknown context_overflow_strategy"):
            agent.build_run_payload(query="q", execution_params={key: "bogus"})

    def test_per_run_override_sends_the_string_value(self):
        agent = Agent(name="a")
        payload = agent.build_run_payload(
            query="q", execution_params={"context_overflow_strategy": ContextOverflowStrategy.NONE}
        )

        assert payload["executionParams"]["contextOverflowStrategy"] == "none"

    def test_backend_value_the_sdk_does_not_know_still_decodes(self):
        agent = Agent.from_dict({"name": "a", "outputFormat": "future", "contextOverflowStrategy": "later"})

        assert agent.output_format == "future"
        assert isinstance(agent.context_overflow_strategy, WireValue)
        assert agent.build_run_payload(query="q")["executionParams"]["contextOverflowStrategy"] == "later"

    def test_assignment_after_decoding_is_still_validated(self):
        agent = Agent.from_dict({"name": "a", "outputFormat": "future"})

        with pytest.raises(ValidationError):
            agent.output_format = "bogus"


# -- One exception type for bad input -----------------------------------------------


def test_validation_error_is_a_value_error():
    assert issubclass(ValidationError, ValueError)


@pytest.mark.parametrize(
    "build",
    [
        lambda: UtilityModelInput(name="n", description="d", type="nombre"),
        lambda: File(privacy="bogus"),
        lambda: File(file_type="bogus"),
        lambda: Agent(name="a", output_format="bogus"),
    ],
    ids=["utility-input-type", "file-privacy", "file-type", "agent-output-format"],
)
def test_bad_enum_value_raises_validation_error_naming_the_accepted_values(build):
    with pytest.raises(ValidationError, match="Accepted values"):
        build()


# -- The backend's "none" strategy ----------------------------------------------------


def test_none_strategy_matches_the_backend():
    assert ContextOverflowStrategy("none") is ContextOverflowStrategy.NONE
    assert "none" in get_args(ContextOverflowStrategyValue)


def test_none_strategy_is_accepted_and_sent():
    agent = Agent(name="a", context_overflow_strategy="none")

    assert agent.build_run_payload(query="q")["executionParams"]["contextOverflowStrategy"] == "none"


@pytest.mark.parametrize("field", ["output_format", "context_overflow_strategy"])
def test_snake_case_from_dict_validates_caller_values(field):
    with pytest.raises(ValidationError, match=f"Unknown {field}"):
        Agent.from_dict({"name": "a", field: "bogus"})


@pytest.mark.parametrize("field", ["output_format", "context_overflow_strategy"])
def test_save_enum_shortcuts_raise_validation_error_before_io(field):
    from unittest.mock import Mock

    agent = Agent(name="a")
    agent.context = Mock()
    with pytest.raises(ValidationError, match=f"Unknown {field}"):
        agent.save(**{field: "bogus"})
    agent.context.client.request.assert_not_called()


@pytest.mark.parametrize(
    "field,wire",
    [
        ("output_format", "outputFormat"),
        ("context_overflow_strategy", "contextOverflowStrategy"),
    ],
)
def test_unknown_backend_value_can_be_reused_as_run_override(field, wire):
    agent = Agent.from_dict({"name": "a", wire: "future"})
    payload = agent.build_run_payload(query="q", execution_params={field: getattr(agent, field)})
    assert payload["executionParams"][wire] == "future"


@pytest.mark.parametrize(
    "field,wire",
    [
        ("output_format", "outputFormat"),
        ("context_overflow_strategy", "contextOverflowStrategy"),
    ],
)
def test_session_execution_params_validate_enums(field, wire):
    from aixplain import ExecutionConfig

    for key in (field, wire):
        with pytest.raises(ValidationError, match=f"Unknown {field}"):
            ExecutionConfig(execution_params={key: "bogus"}).to_api_dict()
    value = next(iter(getattr(v2, "OutputFormat" if field == "output_format" else "ContextOverflowStrategy")))
    config = ExecutionConfig(execution_params={field: value})
    assert config.to_api_dict()["executionParams"][wire] == value.value
    agent = Agent.from_dict({"name": "a", wire: "future"})
    config = ExecutionConfig(execution_params={field: getattr(agent, field)})
    assert config.to_api_dict()["executionParams"][wire] == "future"


@pytest.mark.parametrize("path", ["create", "row", "clone", "deepcopy", "pickle"])
def test_backend_enum_provenance_survives_resource_paths(path):
    import copy
    import pickle
    from unittest.mock import Mock

    row = {"id": "agent-id", "name": "a", "outputFormat": "future", "contextOverflowStrategy": "later"}
    context = Mock()
    if path == "create":
        agent = Agent(name="a")
        agent.context = context
        context.client.request.return_value = row
        agent._create("agents", {})
    elif path == "row":
        agent = Agent._from_row(row, context)
    else:
        original = Agent.from_dict(row)
        if path == "clone":
            agent = original.clone()
        elif path == "deepcopy":
            agent = copy.deepcopy(original)
        else:
            agent = pickle.loads(pickle.dumps(original))
    assert isinstance(agent.output_format, WireValue)
    assert isinstance(agent.context_overflow_strategy, WireValue)
    assert agent.to_dict()["outputFormat"] == "future"
    assert agent.build_run_payload(query="q")["executionParams"]["contextOverflowStrategy"] == "later"


@pytest.mark.parametrize("nested", [False, True])
def test_session_backend_enum_values_remain_forward_compatible(nested):
    from aixplain import ExecutionConfig, Session

    raw = {"executionParams": {"outputFormat": "future", "contextOverflowStrategy": "later"}}
    config = Session.from_dict({"executionConfig": raw}).execution_config if nested else ExecutionConfig.from_dict(raw)
    assert config.to_api_dict()["executionParams"] == raw["executionParams"]
