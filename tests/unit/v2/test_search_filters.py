"""Wire-level guards on how v2 search filters serialize their arguments.

``OwnershipType``, ``SortBy``, ``SortOrder`` and ``Supplier`` are all
``class X(str, Enum)``, so ``str(member)`` yields the *member repr*
(``"OwnershipType.PRIVATE"``) rather than the wire value (``"PRIVATE"``).
The filter builders used to call ``str()`` eagerly, which silently produced
filters the backend could not match (BUG-1092): the request succeeded and
returned the *unfiltered* catalogue.

These tests are deliberately effect-based -- they assert on the exact JSON
body handed to ``client.request``, because that is the only place the defect
was observable. They also assert ``type(...) is str`` where relevant: a raw
``str``-subclass enum member would otherwise satisfy a plain ``==``.
"""

import warnings
from enum import Enum

import pytest
from unittest.mock import Mock

from aixplain import Agent
from aixplain import OwnershipType, SortBy, SortOrder, Supplier
from aixplain.v2.enums import AssetStatus, Function
from aixplain.v2.exceptions import ValidationError
from aixplain import Integration
from aixplain import Model
from aixplain import Skill
from aixplain import Tool

# Resources whose filters come straight from ``_populate_base_filters``, plus
# the ones with overrides, so the fix is proven to be inherited rather than
# per-class.
RESOURCES = [Agent, Model, Tool, Integration, Skill]
RESOURCE_IDS = [cls.__name__ for cls in RESOURCES]


def _bind(monkeypatch, cls):
    """Bind *cls* to a mock context and return the mock client."""
    context = Mock(client=Mock(), backend_url="https://platform-api.aixplain.com", api_key="test_key")
    context.client.request.return_value = {"items": [], "results": [], "total": 0, "pageTotal": 0}
    monkeypatch.setattr(cls, "context", context, raising=False)
    return context.client


def _body(client):
    """Return the JSON body of the single request the client received."""
    client.request.assert_called_once()
    return client.request.call_args.kwargs["json"]


# =============================================================================
# ownership
# =============================================================================

# ``v2/models|tools|integrations|agents/paginate`` do not read ``ownership``
# (BUG-1459): those resources warn and drop it. Skill still sends it.
SENDS_OWNERSHIP = [Skill]
DROPS_OWNERSHIP = [Agent, Model, Tool, Integration]


@pytest.mark.parametrize("cls", SENDS_OWNERSHIP, ids=lambda c: c.__name__)
def test_ownership_enum_sends_value(monkeypatch, cls):
    """``ownership=OwnershipType.PRIVATE`` must send ``"PRIVATE"``."""
    client = _bind(monkeypatch, cls)

    cls.search(ownership=OwnershipType.PRIVATE)

    ownership = _body(client)["ownership"]
    assert ownership == "PRIVATE"
    assert type(ownership) is str, "enum member leaked into the request body"


@pytest.mark.parametrize("cls", SENDS_OWNERSHIP, ids=lambda c: c.__name__)
def test_ownership_string_is_unchanged(monkeypatch, cls):
    """Plain strings keep their exact pre-fix wire representation."""
    client = _bind(monkeypatch, cls)

    cls.search(ownership="team")

    assert _body(client)["ownership"] == "team"


def test_ownership_sequence_sends_list_of_values(monkeypatch):
    """A sequence of enums becomes a list of values, not a stringified list."""
    client = _bind(monkeypatch, Skill)

    Skill.search(ownership=[OwnershipType.PRIVATE, OwnershipType.TEAM])

    ownership = _body(client)["ownership"]
    assert ownership == ["PRIVATE", "TEAM"]
    assert all(type(o) is str for o in ownership)


def test_ownership_tuple_sends_list_of_values(monkeypatch):
    """Tuples are accepted too -- ``BaseSearchParams`` types ownership as one."""
    client = _bind(monkeypatch, Skill)

    Skill.search(ownership=(OwnershipType.PUBLIC,))

    assert _body(client)["ownership"] == ["PUBLIC"]


@pytest.mark.parametrize("cls", DROPS_OWNERSHIP, ids=lambda c: c.__name__)
@pytest.mark.parametrize("ownership", [OwnershipType.PRIVATE, "team", [OwnershipType.PRIVATE, OwnershipType.TEAM]])
def test_ownership_is_warned_and_not_sent_where_unread(monkeypatch, cls, ownership):
    """The backend ignores ``ownership`` here, so it warns instead of silently not filtering."""
    client = _bind(monkeypatch, cls)

    with pytest.warns(FutureWarning, match="ownership"):
        cls.search(ownership=ownership)

    assert "ownership" not in _body(client)


# =============================================================================
# sortBy / sortOrder
# =============================================================================


def test_sort_enums_send_values(monkeypatch):
    """``sort_by``/``sort_order`` enums must send their values."""
    client = _bind(monkeypatch, Skill)

    Skill.search(sort_by=SortBy.NAME, sort_order=SortOrder.DESC)

    body = _body(client)
    assert body["sortBy"] == "NAME"
    assert body["sortOrder"] == "DESC"
    assert type(body["sortBy"]) is str
    assert type(body["sortOrder"]) is str


def test_sort_strings_are_unchanged(monkeypatch):
    """Plain strings pass through verbatim -- no case normalization."""
    client = _bind(monkeypatch, Skill)

    Skill.search(sort_by="name", sort_order="asc")

    body = _body(client)
    assert body["sortBy"] == "name"
    assert body["sortOrder"] == "asc"


@pytest.mark.parametrize("cls", DROPS_OWNERSHIP, ids=lambda c: c.__name__)
@pytest.mark.parametrize(
    "sort_by, sort_order, expected",
    [
        (SortBy.NAME, SortOrder.DESC, {"field": "name", "dir": -1}),
        (SortBy.CREATED_AT, SortOrder.ASC, {"field": "createdAt", "dir": 1}),
        ("name", "asc", {"field": "name", "dir": 1}),
    ],
    ids=["enum-name-desc", "enum-created-asc", "str-name-asc"],
)
def test_sort_maps_to_sort_array_without_sortby_keys(monkeypatch, cls, sort_by, sort_order, expected):
    """Models/tools/integrations/agents read only ``sort[]``, never ``sortBy``/``sortOrder``."""
    client = _bind(monkeypatch, cls)

    cls.search(sort_by=sort_by, sort_order=sort_order)

    body = _body(client)
    assert body["sort"] == [expected]
    assert "sortBy" not in body
    assert "sortOrder" not in body


# =============================================================================
# Model.sort[].dir -- the backend contract is +/-1
# =============================================================================


@pytest.mark.parametrize(
    "sort_order, expected_dir",
    [
        (SortOrder.ASC, 1),
        (SortOrder.DESC, -1),
        ("asc", 1),
        ("ASC", 1),
        ("desc", -1),
        ("DESC", -1),
    ],
    ids=["enum-asc", "enum-desc", "str-asc", "str-ASC", "str-desc", "str-DESC"],
)
def test_model_sort_dir_is_plus_or_minus_one(monkeypatch, sort_order, expected_dir):
    """``sort[].dir`` is an integer +/-1 for both enum and string inputs."""
    client = _bind(monkeypatch, Model)

    Model.search(sort_by=SortBy.NAME, sort_order=sort_order)

    sort = _body(client)["sort"]
    assert sort == [{"field": "name", "dir": expected_dir}]
    assert type(sort[0]["dir"]) is int


@pytest.mark.parametrize(
    "sort_by, expected_field",
    [
        (SortBy.NAME, "name"),
        (SortBy.CREATED_AT, "createdAt"),
        (SortBy.UPDATED_AT, "updatedAt"),
        ("CREATED_AT", "createdAt"),
        ("created_at", "createdAt"),
        ("createdAt", "createdAt"),
        ("normalizedPrice", "normalizedPrice"),
    ],
    ids=["enum-name", "enum-created", "enum-updated", "str-CREATED_AT", "str-created_at", "raw-createdAt", "raw-other"],
)
def test_model_sort_field_is_the_backend_field_name(monkeypatch, sort_by, expected_field):
    """``/v2/models/paginate`` ignores ``"CREATED_AT"`` and only sorts on camelCase fields."""
    client = _bind(monkeypatch, Model)

    Model.search(sort_by=sort_by, sort_order=SortOrder.ASC)

    assert _body(client)["sort"] == [{"field": expected_field, "dir": 1}]


def test_model_sort_field_defaults_to_name(monkeypatch):
    """``sort_order`` alone still yields a well-formed sort entry."""
    client = _bind(monkeypatch, Model)

    Model.search(sort_order=SortOrder.DESC)

    assert _body(client)["sort"] == [{"field": "name", "dir": -1}]


def test_model_sort_empty_without_sort_args(monkeypatch):
    """Unsorted searches still send the empty sort array the backend wants."""
    client = _bind(monkeypatch, Model)

    Model.search()

    assert _body(client)["sort"] == [{}]


# =============================================================================
# Model suppliers
# =============================================================================


class _DictValuedSupplier(Enum):
    """Stand-in for v1's dict-valued ``Supplier`` enum."""

    OPENAI = {"id": "1", "code": "openai", "name": "OpenAI"}


def test_model_supplier_enum_sends_value(monkeypatch):
    """A single v2 ``Supplier`` enum must send its value, not its repr."""
    client = _bind(monkeypatch, Model)

    Model.search(vendors=Supplier.OPENAI)

    assert _body(client)["suppliers"] == ["OPENAI"]


def test_model_supplier_list_mixes_enums_and_strings(monkeypatch):
    """Lists of enums and plain strings are both normalized."""
    client = _bind(monkeypatch, Model)

    Model.search(vendors=[Supplier.OPENAI, "cohere"])

    assert _body(client)["suppliers"] == ["OPENAI", "cohere"]


def test_model_supplier_dict_valued_enum_uses_code(monkeypatch):
    """A dict-valued (v1-shaped) supplier degrades to its ``code``."""
    client = _bind(monkeypatch, Model)

    Model.search(vendors=_DictValuedSupplier.OPENAI)

    assert _body(client)["suppliers"] == ["openai"]


def test_skill_supplier_enum_sends_value(monkeypatch):
    """``Skill``'s own suppliers filter normalizes the same way."""
    client = _bind(monkeypatch, Skill)

    Skill.search(suppliers=[Supplier.OPENAI])

    assert _body(client)["suppliers"] == ["OPENAI"]


# =============================================================================
# Dead code removal
# =============================================================================


def test_find_supplier_by_id_is_gone():
    """``find_supplier_by_id`` raised ``AttributeError`` on every call."""
    import aixplain.v2.model as model_module

    assert not hasattr(model_module, "find_supplier_by_id")


# =============================================================================
# sort direction robustness
# =============================================================================


class _V1SortOrder(Enum):
    """Stand-in for v1's integer-valued ``SortOrder`` enum."""

    ASCENDING = 1
    DESCENDING = -1


@pytest.mark.parametrize(
    "sort_order, expected_dir",
    [
        (_V1SortOrder.ASCENDING, 1),
        (_V1SortOrder.DESCENDING, -1),
        (1, 1),
        (-1, -1),
        ("ascending", 1),
        ("DESCENDING", -1),
    ],
    ids=["v1-enum-asc", "v1-enum-desc", "int-asc", "int-desc", "str-ascending", "str-DESCENDING"],
)
def test_model_sort_dir_accepts_numeric_and_long_spellings(monkeypatch, sort_order, expected_dir):
    """Numeric (v1-shaped) and ``*ENDING`` sort orders keep their direction."""
    client = _bind(monkeypatch, Model)

    Model.search(sort_by=SortBy.NAME, sort_order=sort_order)

    assert _body(client)["sort"] == [{"field": "name", "dir": expected_dir}]


def test_model_sort_dir_unknown_order_defaults_to_ascending(monkeypatch):
    """An unrecognized sort order falls back to the documented default."""
    client = _bind(monkeypatch, Model)

    Model.search(sort_by=SortBy.NAME, sort_order="sideways")

    assert _body(client)["sort"] == [{"field": "name", "dir": 1}]


# =============================================================================
# explicit ``None`` halves must not be serialized
# =============================================================================


def test_model_sort_with_explicit_none_field(monkeypatch):
    """``sort_by=None`` falls back to ``"name"`` instead of sending ``"None"``."""
    client = _bind(monkeypatch, Model)

    Model.search(sort_by=None, sort_order=SortOrder.DESC)

    assert _body(client)["sort"] == [{"field": "name", "dir": -1}]


def test_model_sort_with_explicit_none_order(monkeypatch):
    """``sort_order=None`` falls back to ascending."""
    client = _bind(monkeypatch, Model)

    Model.search(sort_by=SortBy.CREATED_AT, sort_order=None)

    assert _body(client)["sort"] == [{"field": "createdAt", "dir": 1}]


@pytest.mark.parametrize("cls", RESOURCES, ids=RESOURCE_IDS)
def test_explicit_none_filters_are_omitted(monkeypatch, cls):
    """``None`` filters stay out of the body entirely, without a warning."""
    client = _bind(monkeypatch, cls)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        cls.search(ownership=None, sort_by=None, sort_order=None)

    body = _body(client)
    assert "ownership" not in body
    assert "sortBy" not in body
    assert "sortOrder" not in body


# =============================================================================
# Model functions filter (BUG-1459)
# =============================================================================


def test_model_function_alias_sends_kebab_code(monkeypatch):
    """MIGRATION.md's ``function=`` call filters instead of returning the catalogue."""
    client = _bind(monkeypatch, Model)

    Model.search(function=Function.TEXT_GENERATION)

    assert _body(client)["functions"] == ["text-generation"]


def test_model_function_alias_accepts_a_list(monkeypatch):
    client = _bind(monkeypatch, Model)

    Model.search(function=[Function.TEXT_GENERATION, Function.TRANSLATION])

    assert _body(client)["functions"] == ["text-generation", "translation"]


def test_model_functions_send_backend_kebab_codes(monkeypatch):
    """``v2/models/paginate`` matches kebab codes exactly; UPPER_SNAKE matched nothing."""
    client = _bind(monkeypatch, Model)

    Model.search(functions=[Function.TEXT_GENERATION, Function.UTILITIES, "speech-recognition", "TRANSLATION"])

    functions = _body(client)["functions"]
    assert functions == ["text-generation", "utilities", "speech-recognition", "translation"]
    assert all(type(f) is str for f in functions)


def test_model_functions_scalar_is_wrapped(monkeypatch):
    client = _bind(monkeypatch, Model)

    Model.search(functions=Function.IMAGE_GENERATION)

    assert _body(client)["functions"] == ["image-generation"]


def test_model_function_and_functions_together_raise(monkeypatch):
    client = _bind(monkeypatch, Model)

    with pytest.raises(ValidationError, match="function= or functions="):
        Model.search(function=Function.TEXT_GENERATION, functions=[Function.TRANSLATION])

    client.request.assert_not_called()


def test_find_function_by_id_round_trips_with_wire_code():
    """``_function_code`` is the inverse of ``find_function_by_id`` for every member."""
    from aixplain.v2.model import _function_code, find_function_by_id

    for member in Function:
        assert find_function_by_id(_function_code(member)) is member


# =============================================================================
# Model filters the backend does not read (BUG-1459)
# =============================================================================


def test_model_unread_filters_warn_and_are_not_sent(monkeypatch):
    client = _bind(monkeypatch, Model)

    with pytest.warns(FutureWarning) as record:
        Model.search(
            source_languages=["en"],
            target_languages="fr",
            is_finetunable=True,
            ownership=OwnershipType.PRIVATE,
            status=["onboarded"],
        )

    assert len(record) == 1
    message = str(record[0].message)
    for key in ("source_languages", "target_languages", "is_finetunable", "ownership", "status"):
        assert key in message
    body = _body(client)
    for wire_key in ("sourceLanguages", "targetLanguages", "isFineTunable", "ownership", "status"):
        assert wire_key not in body


def test_model_unread_filter_warning_points_at_caller(monkeypatch):
    _bind(monkeypatch, Model)

    with pytest.warns(FutureWarning) as record:
        Model.search(is_finetunable=True)

    assert record[0].filename == __file__


def test_model_supported_filters_do_not_warn(monkeypatch):
    client = _bind(monkeypatch, Model)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Model.search(
            "gpt",
            functions=[Function.TEXT_GENERATION],
            vendors=Supplier.OPENAI,
            host="openai",
            developer="OpenAI",
            path="openai/gpt-4",
            saved=True,
            sort_by=SortBy.CREATED_AT,
            sort_order=SortOrder.DESC,
            page_size=5,
        )

    assert _body(client) == {
        "q": "gpt",
        "pageNumber": 0,
        "pageSize": 5,
        "saved": True,
        "hosts": ["openai"],
        "developers": ["OpenAI"],
        "path": "openai/gpt-4",
        "functions": ["text-generation"],
        "suppliers": ["OPENAI"],
        "sort": [{"field": "createdAt", "dir": -1}],
    }


@pytest.mark.parametrize("cls", [Model, Tool, Integration, Agent], ids=lambda c: c.__name__)
def test_unknown_search_kwarg_raises(monkeypatch, cls):
    """A typo'd filter used to be dropped silently, returning unfiltered results."""
    client = _bind(monkeypatch, cls)

    with pytest.raises(ValidationError, match="typo_filter"):
        cls.search(typo_filter=1)

    client.request.assert_not_called()


def test_inspector_search_still_pins_guardrails(monkeypatch):
    from aixplain.v2.inspector import Inspector

    client = _bind(monkeypatch, Inspector)

    Inspector.search()

    assert _body(client)["functions"] == ["guardrails"]


# =============================================================================
# Agent sort / status (BUG-1459)
# =============================================================================


def test_agent_sort_and_status_follow_the_backend_contract(monkeypatch):
    client = _bind(monkeypatch, Agent)

    Agent.search(sort_by=SortBy.CREATED_AT, sort_order=SortOrder.DESC, status="draft")

    body = _body(client)
    assert body["sort"] == [{"field": "createdAt", "dir": -1}]
    assert body["status"] == "draft"
    assert "sortBy" not in body
    assert "sortOrder" not in body


@pytest.mark.parametrize(
    "status, expected",
    [
        (AssetStatus.DRAFT, "draft"),
        ("onboarded", "onboarded"),
        ([AssetStatus.ONBOARDED], "onboarded"),
        (["draft", AssetStatus.DRAFT], "draft"),
    ],
    ids=["enum", "string", "one-element-list", "duplicates"],
)
def test_agent_status_is_sent_as_one_scalar(monkeypatch, status, expected):
    """``AgentPaginateInput.status`` is a scalar ``draft``/``onboarded`` enum."""
    client = _bind(monkeypatch, Agent)

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Agent.search(status=status)

    assert _body(client)["status"] == expected


@pytest.mark.parametrize(
    "status",
    [["draft", AssetStatus.ONBOARDED], AssetStatus.DELETED, "hidden", []],
    ids=["several", "deleted", "hidden", "empty-list"],
)
def test_agent_status_the_backend_rejects_warns_and_is_not_sent(monkeypatch, status):
    client = _bind(monkeypatch, Agent)

    with pytest.warns(FutureWarning, match="status="):
        Agent.search(status=status)

    assert "status" not in _body(client)


def test_agent_search_without_sort_omits_sort(monkeypatch):
    client = _bind(monkeypatch, Agent)

    Agent.search()

    body = _body(client)
    assert "sort" not in body
    assert "status" not in body
