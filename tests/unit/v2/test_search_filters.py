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

from enum import Enum

import pytest
from unittest.mock import Mock

from aixplain.v2.agent import Agent
from aixplain.v2.enums import OwnershipType, SortBy, SortOrder, Supplier
from aixplain.v2.integration import Integration
from aixplain.v2.model import Model
from aixplain.v2.skill import Skill
from aixplain.v2.tool import Tool

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


@pytest.mark.parametrize("cls", RESOURCES, ids=RESOURCE_IDS)
def test_ownership_enum_sends_value(monkeypatch, cls):
    """``ownership=OwnershipType.PRIVATE`` must send ``"PRIVATE"``."""
    client = _bind(monkeypatch, cls)

    cls.search(ownership=OwnershipType.PRIVATE)

    ownership = _body(client)["ownership"]
    assert ownership == "PRIVATE"
    assert type(ownership) is str, "enum member leaked into the request body"


@pytest.mark.parametrize("cls", RESOURCES, ids=RESOURCE_IDS)
def test_ownership_string_is_unchanged(monkeypatch, cls):
    """Plain strings keep their exact pre-fix wire representation."""
    client = _bind(monkeypatch, cls)

    cls.search(ownership="team")

    assert _body(client)["ownership"] == "team"


def test_ownership_sequence_sends_list_of_values(monkeypatch):
    """A sequence of enums becomes a list of values, not a stringified list."""
    client = _bind(monkeypatch, Agent)

    Agent.search(ownership=[OwnershipType.PRIVATE, OwnershipType.TEAM])

    ownership = _body(client)["ownership"]
    assert ownership == ["PRIVATE", "TEAM"]
    assert all(type(o) is str for o in ownership)


def test_ownership_tuple_sends_list_of_values(monkeypatch):
    """Tuples are accepted too -- ``BaseSearchParams`` types ownership as one."""
    client = _bind(monkeypatch, Agent)

    Agent.search(ownership=(OwnershipType.PUBLIC,))

    assert _body(client)["ownership"] == ["PUBLIC"]


# =============================================================================
# sortBy / sortOrder
# =============================================================================


@pytest.mark.parametrize("cls", RESOURCES, ids=RESOURCE_IDS)
def test_sort_enums_send_values(monkeypatch, cls):
    """``sort_by``/``sort_order`` enums must send their values."""
    client = _bind(monkeypatch, cls)

    cls.search(sort_by=SortBy.NAME, sort_order=SortOrder.DESC)

    body = _body(client)
    assert body["sortBy"] == "NAME"
    assert body["sortOrder"] == "DESC"
    assert type(body["sortBy"]) is str
    assert type(body["sortOrder"]) is str


@pytest.mark.parametrize("cls", RESOURCES, ids=RESOURCE_IDS)
def test_sort_strings_are_unchanged(monkeypatch, cls):
    """Plain strings pass through verbatim -- no case normalization."""
    client = _bind(monkeypatch, cls)

    cls.search(sort_by="name", sort_order="asc")

    body = _body(client)
    assert body["sortBy"] == "name"
    assert body["sortOrder"] == "asc"


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
    assert sort == [{"field": "NAME", "dir": expected_dir}]
    assert type(sort[0]["dir"]) is int


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
