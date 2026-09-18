"""Tests for PROD-2921: config structs and enums take plain data.

The rule under test: anything a caller has to construct or pass in accepts plain
data, so calling code does not depend on the SDK's module layout. Anything that
only ever comes back from the SDK stays an object.

Half of this file is drift guards. A `Literal` alias that has fallen behind its
enum, or a `TypedDict` that no longer matches its dataclass, is worse than having
neither: the type checker starts rejecting values the runtime accepts, and the
caller has no way to tell which is right. The classification the guards enforce
is recorded in docs/v2-plain-data.md.
"""

import dataclasses
from typing import get_args, get_type_hints

import pytest

import aixplain
import aixplain.v2 as v2
from aixplain.v2.agent import (
    Agent,
    Budget,
    BudgetDict,
    ContextOverflowStrategy,
    ContextOverflowStrategyValue,
    OutputFormat,
    OutputFormatValue,
    Task,
    TaskDict,
)
from aixplain.v2.agent_progress import ProgressFormat, ProgressFormatValue
from aixplain.v2.api_key import APIKeyLimits, APIKeyLimitsDict, TokenType, TokenTypeValue
from aixplain.v2.code_utils import UtilityModelInput, UtilityModelInputDict
from aixplain.v2.exceptions import ValidationError
from aixplain.v2.issue import IssueSeverity, IssueSeverityValue
from aixplain.v2.session import ExecutionConfig, ExecutionConfigDict
from aixplain.v2.trigger import (
    Trigger,
    TriggerConfiguration,
    TriggerConfigurationDict,
    TriggerRepeatRule,
    TriggerRepeatRuleDict,
)

#: Every input enum and the ``Literal`` alias that spells its values.
#: docs/v2-plain-data.md classifies these; a new input enum belongs in both.
ENUM_ALIASES = [
    (v2.AssetStatus, v2.AssetStatusValue),
    (v2.AttachmentType, v2.AttachmentTypeValue),
    (v2.AuthenticationScheme, v2.AuthenticationSchemeValue),
    (v2.DataType, v2.DataTypeValue),
    (v2.FileType, v2.FileTypeValue),
    (v2.Function, v2.FunctionValue),
    (v2.Language, v2.LanguageValue),
    (v2.License, v2.LicenseValue),
    (v2.OwnershipType, v2.OwnershipTypeValue),
    (v2.Privacy, v2.PrivacyValue),
    (v2.SortBy, v2.SortByValue),
    (v2.SortOrder, v2.SortOrderValue),
    (v2.SplittingOptions, v2.SplittingOptionsValue),
    (v2.StorageType, v2.StorageTypeValue),
    (v2.Supplier, v2.SupplierValue),
    (ContextOverflowStrategy, ContextOverflowStrategyValue),
    (OutputFormat, OutputFormatValue),
    (ProgressFormat, ProgressFormatValue),
    (IssueSeverity, IssueSeverityValue),
    (TokenType, TokenTypeValue),
]

#: Every input config dataclass and the ``TypedDict`` that describes it.
STRUCT_DICTS = [
    (APIKeyLimits, APIKeyLimitsDict),
    (Budget, BudgetDict),
    (ExecutionConfig, ExecutionConfigDict),
    (Task, TaskDict),
    (TriggerConfiguration, TriggerConfigurationDict),
    (TriggerRepeatRule, TriggerRepeatRuleDict),
    (UtilityModelInput, UtilityModelInputDict),
]


# -- Drift guards -------------------------------------------------------------------


@pytest.mark.parametrize("enum_cls,alias", ENUM_ALIASES, ids=[e.__name__ for e, _ in ENUM_ALIASES])
def test_literal_alias_lists_exactly_the_enum_values(enum_cls, alias):
    """A member added to the enum must reach its alias, or the two disagree."""
    assert set(get_args(alias)) == {member.value for member in enum_cls}, (
        f"{enum_cls.__name__}Value has drifted from {enum_cls.__name__}. A type checker would "
        "reject a value the runtime accepts (or the reverse)."
    )


@pytest.mark.parametrize("struct,typed_dict", STRUCT_DICTS, ids=[s.__name__ for s, _ in STRUCT_DICTS])
def test_typed_dict_declares_exactly_the_struct_fields(struct, typed_dict):
    """The TypedDict is what flags a typo; it has to describe the real struct."""
    struct_fields = {f.name for f in dataclasses.fields(struct) if not f.name.startswith("_")}
    assert set(typed_dict.__annotations__) == struct_fields, (
        f"{typed_dict.__name__} has drifted from {struct.__name__}: a misspelled key would be "
        "flagged by the type checker but accepted at runtime, or vice versa."
    )


@pytest.mark.parametrize("struct,typed_dict", STRUCT_DICTS, ids=[s.__name__ for s, _ in STRUCT_DICTS])
def test_typed_dict_requires_exactly_what_the_struct_requires(struct, typed_dict):
    """Optionality has to match, in both directions.

    An earlier version of this test asserted "no key is required", which is right
    for the structs whose every field defaults but wrong for ``Task`` and
    ``UtilityModelInput``: it let ``{"name": "t"}`` type-check clean and then fail
    at runtime with "Missing required tasks field(s)". A TypedDict that disagrees
    with its dataclass in *either* direction is the defect.
    """
    struct_required = {
        f.name
        for f in dataclasses.fields(struct)
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
    }
    assert set(typed_dict.__required_keys__) == struct_required, (
        f"{typed_dict.__name__} requires {sorted(typed_dict.__required_keys__)} but "
        f"{struct.__name__} requires {sorted(struct_required)}: a dict would type-check and then "
        "fail at runtime, or be rejected by the checker though the runtime accepts it."
    )


# -- Everything is importable from the package root ---------------------------------


def test_package_root_exports_the_whole_v2_surface():
    """No caller should need a version segment in an import path."""
    assert aixplain.__all__ == list(v2.__all__)


def test_every_exported_name_resolves():
    """An ``__all__`` entry that does not resolve breaks ``from aixplain import *``."""
    missing = [name for name in aixplain.__all__ if not hasattr(aixplain, name)]
    assert missing == [], f"exported but not present on the package: {missing}"


@pytest.mark.parametrize(
    "name",
    [
        "Budget",
        "BudgetDict",
        "ContextOverflowStrategy",
        "ContextOverflowStrategyValue",
        "DataType",
        "ExecutionConfig",
        "ExecutionConfigDict",
        "OutputFormat",
        "Privacy",
        "PrivacyValue",
        "SplittingOptions",
        "Supplier",
        "Task",
        "TaskDict",
        "TriggerConfiguration",
        "TriggerConfigurationDict",
        "UtilityModelInput",
    ],
)
def test_named_symbol_imports_without_a_version_segment(name):
    """The acceptance criterion, one symbol at a time."""
    assert getattr(aixplain, name) is getattr(v2, name)


def test_existing_usage_is_unchanged():
    """The objects behind the new names are the same ones as before."""
    assert aixplain.Budget(max_cost=1.5).max_cost == 1.5
    assert aixplain.Privacy.PRIVATE.value == "Private"
    assert aixplain.TokenType.OUTPUT.value == "output"
    assert aixplain.APIKeyLimits(token_per_minute=10).token_per_minute == 10


# -- Config structs take dicts ------------------------------------------------------


class TestExecutionConfigDicts:
    """``aix.Session(agent=..., execution_config={...})``."""

    def test_execution_config_from_a_dict(self):
        config = ExecutionConfig.coerce(
            {
                "execution_params": {"output_format": "json"},
                "criteria": "be terse",
                "identifier": "run-7",
            }
        )

        assert isinstance(config, ExecutionConfig)
        assert config.criteria == "be terse"
        assert config.identifier == "run-7"
        assert config.to_api_dict()["executionParams"] == {"outputFormat": "json"}

    def test_session_accepts_an_execution_config_dict(self):
        from aixplain.v2.session import Session

        session = Session(agent_id="agent-1", execution_config={"criteria": "be terse"})

        assert isinstance(session.execution_config, ExecutionConfig)
        assert session.execution_config.criteria == "be terse"

    def test_assignment_after_construction_coerces(self):
        """``session.execution_config = {...}`` died on save as a raw dict."""
        from aixplain.v2.session import Session

        session = Session(agent="abc")
        session.execution_config = {"criteria": "be terse"}

        assert isinstance(session.execution_config, ExecutionConfig)
        assert session.build_save_payload()["executionConfig"] == {"criteria": "be terse"}

    def test_assignment_after_construction_validates(self):
        from aixplain.v2.session import Session

        session = Session(agent="abc")
        with pytest.raises(ValidationError, match="Unknown execution_config field"):
            session.execution_config = {"critera": "typo"}

    def test_a_nested_budget_typo_raises_on_the_input_path(self):
        with pytest.raises(ValidationError, match="Unknown budget field"):
            ExecutionConfig.coerce({"budget": {"max_iteration": 3}})

    def test_unknown_key_raises_naming_the_accepted_fields(self):
        with pytest.raises(ValidationError) as excinfo:
            ExecutionConfig.coerce({"critera": "be terse"})

        message = str(excinfo.value)
        assert "critera" in message
        assert "criteria" in message and "execution_params" in message

    def test_camel_case_wire_keys_still_decode(self):
        """The same entry point takes a caller's dict and a backend payload."""
        config = ExecutionConfig.coerce({"executionParams": {"outputFormat": "json"}})

        assert config.execution_params == {"outputFormat": "json"}


class TestBudgetDicts:
    """``agent.budget`` already took a dict; an unknown key no longer passes."""

    def test_budget_from_a_dict(self):
        agent = Agent(name="a")
        agent.budget = {"max_cost": 0.5, "max_iterations": 10}

        assert isinstance(agent.budget, Budget)
        assert agent.budget.max_cost == 0.5
        assert agent.budget.max_iterations == 10

    def test_camel_case_budget_keys_still_work(self):
        assert Agent._coerce_budget({"maxCost": 0.5}).max_cost == 0.5

    def test_unknown_budget_key_raises_on_the_input_path(self):
        """``max_iteration`` used to pass through and silently mean "no cap"."""
        with pytest.raises(ValidationError) as excinfo:
            Agent(name="a").budget = {"max_iteration": 10}

        message = str(excinfo.value)
        assert "max_iteration" in message and "max_iterations" in message

    def test_the_deserialization_path_stays_permissive(self):
        """A backend that adds a budget field must not break reads.

        ``_coerce_budget`` serves both the input path and deserialization, so the
        strict check is opt-in. With it on by default, every ``Session.get()``
        would have started failing the day the backend grew a budget field — on
        data the SDK only reads.
        """
        budget = Agent._coerce_budget({"maxCost": 1.0, "maxTokens": 9})

        assert budget.max_cost == 1.0

    def test_a_session_hydrates_through_an_unknown_budget_field(self):
        from aixplain.v2.session import Session

        session = Session.from_dict(
            {"id": "s", "executionConfig": {"executionParams": {"budget": {"maxCost": 1.0, "maxTokens": 9}}}}
        )

        assert session.execution_config.budget.max_cost == 1.0

    def test_an_agent_hydrates_through_an_unknown_budget_field(self):
        assert (
            Agent.from_dict({"id": "a", "name": "n", "budget": {"maxCost": 2.0, "maxTokens": 9}}).budget.max_cost == 2.0
        )


class TestTaskDicts:
    def test_tasks_from_dicts(self):
        agent = Agent(name="a", tasks=[{"name": "t1", "instructions": "do it", "expected_output": "a result"}])

        assert isinstance(agent.tasks[0], Task)
        assert agent.tasks[0].instructions == "do it"

    def test_task_objects_still_work(self):
        """``Task.from_dict`` on a ``Task`` used to raise ``AttributeError``."""
        agent = Agent(name="a", tasks=[Task(name="t1", instructions="do it", expected_output="a result")])

        assert agent.tasks[0].name == "t1"

    def test_unknown_task_key_raises(self):
        with pytest.raises(ValidationError, match="Unknown tasks field"):
            Agent(name="a", tasks=[{"nmae": "t1"}])

    def test_assignment_after_construction_serialises_the_wire_names(self):
        """The quiet one: no exception, just the wrong keys on the wire.

        ``dataclass_json`` passes an unrecognised dict through untouched, so a
        task assigned after construction reached the backend with
        ``instructions`` / ``expected_output`` instead of ``description`` /
        ``expectedOutput``, and ``dependencies`` dropped.
        """
        task = {"name": "t", "instructions": "i", "expected_output": "e"}
        assigned = Agent(name="a", description="d")
        assigned.tasks = [task]
        constructed = Agent(name="a", description="d", tasks=[task])

        assert assigned.build_save_payload()["tasks"] == constructed.build_save_payload()["tasks"]
        assert assigned.build_save_payload()["tasks"][0]["description"] == "i"

    def test_assignment_after_construction_validates(self):
        agent = Agent(name="a", description="d")
        with pytest.raises(ValidationError, match="Unknown tasks field"):
            agent.tasks = [{"nam": "t"}]

    def test_wire_spellings_still_decode(self):
        agent = Agent(name="a", tasks=[{"name": "t1", "description": "do it", "expectedOutput": "a result"}])

        assert agent.tasks[0].instructions == "do it"
        assert agent.tasks[0].expected_output == "a result"


class TestTriggerDicts:
    """A trigger can be configured with a dict."""

    def test_configuration_from_a_dict(self):
        trigger = Trigger(
            name="Daily digest",
            configuration={"type": "recurring", "time": "09:00", "timezone": "Europe/London"},
        )

        assert isinstance(trigger.configuration, TriggerConfiguration)
        assert trigger.configuration.time == "09:00"

    def test_nested_repeat_rule_from_a_dict(self):
        trigger = Trigger(name="Hourly", configuration={"type": "recurring", "repeat": {"every": 2, "unit": "hour"}})

        assert isinstance(trigger.configuration.repeat, TriggerRepeatRule)
        assert trigger.configuration.repeat.every == 2

    def test_configuration_assignment_after_construction(self):
        trigger = Trigger(name="Later")
        trigger.configuration = {"type": "once", "run_at": "2026-01-26T12:00:00Z"}

        assert isinstance(trigger.configuration, TriggerConfiguration)
        assert trigger.configuration.run_at == "2026-01-26T12:00:00Z"

    def test_repeat_assignment_after_construction(self):
        """``config.repeat = {...}`` has to coerce too, not only the constructor.

        ``_hydrate_schedule_fields`` reads ``config.repeat.unit``, so a dict left
        in place surfaces much later as an AttributeError on a fetched trigger.
        """
        config = TriggerConfiguration(type="recurring")
        config.repeat = {"every": 2, "unit": "hour"}

        assert isinstance(config.repeat, TriggerRepeatRule)
        assert config.repeat.unit == "hour"

    def test_an_assigned_repeat_dict_survives_serialization(self):
        config = TriggerConfiguration(type="recurring")
        config.repeat = {"every": 2, "unit": "hour"}

        assert config.to_dict()["repeat"] == {"every": 2, "unit": "hour"}

    def test_unknown_repeat_key_raises(self):
        with pytest.raises(ValidationError, match="Unknown repeat field"):
            TriggerConfiguration(type="recurring", repeat={"evry": 2})

    def test_unknown_configuration_key_raises(self):
        with pytest.raises(ValidationError) as excinfo:
            Trigger(name="Bad", configuration={"typ": "once"})

        message = str(excinfo.value)
        assert "typ" in message and "timezone" in message

    def test_wire_spellings_still_decode(self):
        trigger = Trigger(name="Weekly", configuration={"type": "recurring", "daysOfWeek": ["mon"]})

        assert trigger.configuration.days_of_week == ["mon"]


class TestUtilityModelInputPlainData:
    def test_string_type_is_accepted(self):
        assert UtilityModelInput(name="n", description="d", type="number").type is v2.DataType.NUMBER

    def test_string_type_reaches_the_payload_as_a_string(self):
        """``to_dict`` reads ``self.type.value``, so a raw string would crash."""
        assert UtilityModelInput(name="n", description="d", type="text").to_dict()["type"] == "text"

    def test_unknown_type_names_the_accepted_values(self):
        with pytest.raises(ValueError, match="Accepted values"):
            UtilityModelInput(name="n", description="d", type="nombre")


class TestMissingRequiredFields:
    """A dict short of a required field is a ``ValidationError``, not a ``TypeError``.

    ``cls(**kwargs)`` would raise ``Task.__init__() missing 1 required positional
    argument: 'expected_output'``, which names a dunder rather than the thing the
    caller was writing -- the opposite of what a plain-data entry point is for.
    """

    def test_missing_field_raises_validation_error_naming_it(self):
        from aixplain.v2.plain_data import coerce_struct

        with pytest.raises(ValidationError) as excinfo:
            coerce_struct({"name": "t1"}, Task, label="tasks")

        message = str(excinfo.value)
        assert "instructions" in message and "expected_output" in message
        assert "__init__" not in message

    def test_missing_field_raises_through_the_agent_constructor(self):
        with pytest.raises(ValidationError, match="Missing required tasks field"):
            Agent(name="a", tasks=[{"name": "t1"}])

    def test_fields_with_a_default_are_not_reported_missing(self):
        """Only genuinely required fields count -- including ``default_factory``."""
        task = Task(name="t1", instructions="i", expected_output="e")

        assert task.dependencies == []

    def test_a_fully_optional_struct_accepts_an_empty_dict(self):
        assert Budget() == Agent._coerce_budget({})


# -- Input enums accept their string values -----------------------------------------


class TestInputEnumStrings:
    def test_context_overflow_strategy_takes_a_string(self):
        """The acceptance criterion, verbatim."""
        agent = Agent(name="a")
        agent.context_overflow_strategy = "summarize"

        assert agent.context_overflow_strategy == "summarize"
        assert agent.context_overflow_strategy == ContextOverflowStrategy.SUMMARIZE

    def test_context_overflow_strategy_takes_the_enum(self):
        agent = Agent(name="a", context_overflow_strategy=ContextOverflowStrategy.SUMMARIZE)

        assert agent.context_overflow_strategy == "summarize"

    def test_output_format_takes_a_string(self):
        agent = Agent(name="a", output_format="json")

        assert agent.output_format == OutputFormat.JSON

    @pytest.mark.parametrize("enum_cls,_alias", ENUM_ALIASES, ids=[e.__name__ for e, _ in ENUM_ALIASES])
    def test_every_input_enum_round_trips_its_string_values(self, enum_cls, _alias):
        """``Enum(value)`` must accept every string the alias advertises."""
        for member in enum_cls:
            assert enum_cls(member.value) is member


def test_str_enums_compare_equal_to_their_values():
    """Why passing the plain string works at runtime, and always did.

    Every input enum but ``TokenType`` subclasses ``str``. This is the property
    the ``Literal`` aliases exist to document, so it is worth pinning: if one of
    them stopped subclassing ``str``, the aliases would start advertising strings
    the code no longer accepts.
    """
    non_str = [enum_cls.__name__ for enum_cls, _ in ENUM_ALIASES if not issubclass(enum_cls, str)]

    assert non_str == ["TokenType"], f"these input enums no longer subclass str: {non_str}"


def test_conversation_message_is_still_the_reference_shape():
    """The pattern the rest of this follows, pinned so it does not quietly change."""
    hints = get_type_hints(v2.ConversationMessage, include_extras=False)

    assert set(get_args(hints["role"])) == {"user", "assistant"}
    assert hints["content"] is str


def test_timeout_error_does_not_shadow_the_builtin():
    """``from aixplain import *`` rebinds ``TimeoutError`` in the caller's module.

    Without inheriting the builtin as well, a plain ``except TimeoutError:``
    would quietly stop catching socket and asyncio timeouts — the name would
    catch strictly *less* than before the star export existed.
    """
    import builtins

    assert issubclass(aixplain.TimeoutError, builtins.TimeoutError)
    assert issubclass(aixplain.TimeoutError, v2.AixplainV2Error)


def test_no_other_exported_name_shadows_a_builtin():
    """``TimeoutError`` is the only collision; a new one needs a deliberate look."""
    import builtins

    collisions = {name for name in aixplain.__all__ if hasattr(builtins, name)}

    assert collisions == {"TimeoutError"}, (
        f"new builtin shadowing from the package root: {sorted(collisions - {'TimeoutError'})}. "
        "Either make the export subclass the builtin it shadows, or keep it out of __all__."
    )


#: Field annotations that must accept the string form of their enum. The point of
#: a Literal alias is to be *attached* to something; one that is exported and
#: referenced nowhere delivers no type checking at all.
ANNOTATED_ALIASES = [
    ("aixplain/v2/agent.py", "OutputFormatValue"),
    ("aixplain/v2/agent.py", "ContextOverflowStrategyValue"),
    ("aixplain/v2/agent.py", "AssetStatusValue"),
    ("aixplain/v2/agent.py", "ProgressFormatValue"),
    ("aixplain/v2/api_key.py", "TokenTypeValue"),
    ("aixplain/v2/code_utils.py", "DataTypeValue"),
    ("aixplain/v2/file.py", "PrivacyValue"),
    ("aixplain/v2/model.py", "SupplierValue"),
    ("aixplain/v2/model.py", "LanguageValue"),
    ("aixplain/v2/model.py", "FunctionValue"),
    ("aixplain/v2/resource.py", "SortByValue"),
    ("aixplain/v2/resource.py", "SortOrderValue"),
    ("aixplain/v2/resource.py", "OwnershipTypeValue"),
    ("aixplain/v2/file.py", "FileTypeValue"),
    ("aixplain/v2/issue.py", "IssueSeverityValue"),
]

#: Aliases with no annotation site, and why. These describe enums the SDK exports
#: but never takes as a typed parameter, so there is nothing to attach them to
#: until one appears. Listed rather than silently absent, so the gap stays a
#: decision rather than an oversight; docs/v2-plain-data.md carries the same list.
UNATTACHED_ALIASES = {
    "AttachmentTypeValue": "attachment type is inferred from the MIME type; no caller-facing field",
    "AuthenticationSchemeValue": "integration connect takes untyped **kwargs today",
    "LicenseValue": "license is documented on upload_utils but is not a typed parameter",
    "SplittingOptionsValue": "index chunking has no v2 surface yet",
    "StorageTypeValue": "storage type is inferred during upload; no caller-facing field",
}


@pytest.mark.parametrize("module_path,alias", ANNOTATED_ALIASES, ids=[f"{a}" for _, a in ANNOTATED_ALIASES])
def test_literal_alias_is_used_in_an_annotation(module_path, alias):
    """Each alias is referenced by the field or param it was written for."""
    from pathlib import Path

    source = (Path(__file__).resolve().parents[3] / module_path).read_text(encoding="utf-8")
    uses = [
        line
        for line in source.splitlines()
        if alias in line
        and not line.lstrip().startswith(("#", "#:"))
        and "import" not in line
        and "= Literal" not in line
    ]

    assert uses, f"{alias} is defined and exported but annotates nothing in {module_path}"


def test_every_alias_is_either_annotated_or_explicitly_unattached():
    """No alias may drift out of both lists and become quietly decorative.

    An alias that is defined, exported, documented and drift-tested but attached
    to nothing delivers no type checking at all -- the runtime already accepted
    the string, so the annotation was the entire point of adding it.
    """
    covered = {alias for _, alias in ANNOTATED_ALIASES} | set(UNATTACHED_ALIASES)
    defined = {f"{enum_cls.__name__}Value" for enum_cls, _ in ENUM_ALIASES}

    assert defined == covered, (
        f"aliases in neither list: {sorted(defined - covered)}; "
        f"listed but no longer defined: {sorted(covered - defined)}"
    )
