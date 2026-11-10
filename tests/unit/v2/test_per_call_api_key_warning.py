"""A per-call ``api_key=`` is ignored, so it must say so (BUG-1452).

BUG-1091 strips the per-call key from every request; authentication always
comes from the ``Aixplain`` context. Without a warning, a multi-tenant caller
passing another tenant's key would run and bill against the context's key with
no signal. Each public entry point now emits exactly one ``DeprecationWarning``
naming ``Aixplain(api_key=...)``, attributed to the caller's line.
"""

import warnings
from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from dataclasses_json import dataclass_json

from unittest.mock import MagicMock

from aixplain import Action, ActionInputSpec, Actions, Agent, DeleteResult, Inputs, Model, Tool
from aixplain.v2.resource import (
    BaseDeleteParams,
    BaseGetParams,
    BaseResource,
    BaseSearchParams,
    DeleteResourceMixin,
    GetResourceMixin,
    SearchResourceMixin,
)


def _model(cls=Model):
    model = cls.__new__(cls)
    model.id = "test-model-id"
    model.name = "Test Model"
    model.connection_type = ["synchronous"]
    model.params = None
    model.__post_init__()
    model.context = Mock()
    model.context.model_url = "https://models.aixplain.com/api/v2/execute"
    model.context.client.request.return_value = {"status": "SUCCESS", "completed": True, "data": "ok"}
    return model


def _tool():
    tool = _model(Tool)
    tool.description = "Tool description"
    tool.allowed_actions = ["search"]
    tool._dynamic_attrs = {}
    spec = ActionInputSpec(
        name="Query", code="query", datatype="string", default_value=[], required=False, description="Query"
    )
    action = Action(name="search", inputs=Inputs.from_action_input_specs([spec]))
    tool.__dict__["actions"] = Actions(actions={"search": action})
    return tool


def _agent():
    agent = Agent.from_dict({"id": "a1", "name": "t"})
    agent.context = MagicMock()
    agent.status = None
    fake_result = MagicMock()
    fake_result.url = None
    fake_result.completed = True
    agent.handle_run_response = lambda response, **kw: fake_result
    return agent


MATCH = r"Aixplain\(api_key="


def _per_call_warnings(record):
    return [w for w in record if issubclass(w.category, DeprecationWarning) and "api_key=" in str(w.message)]


def _call_and_record(fn):
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        fn()
    return _per_call_warnings(record)


def _gettable():
    @dataclass_json
    @dataclass
    class Gettable(BaseResource, GetResourceMixin[BaseGetParams, "Gettable"]):
        RESOURCE_PATH = "gettable"

    Gettable.context = Mock()
    Gettable.context.client.get = Mock(return_value={"id": "123", "name": "got"})
    return Gettable


def _searchable():
    @dataclass_json
    @dataclass
    class Searchable(BaseResource, SearchResourceMixin[BaseSearchParams, "Searchable"]):
        RESOURCE_PATH = "searchable"

    Searchable.context = Mock()
    Searchable.context.client.request = Mock(return_value={"results": [], "total": 0, "pageTotal": 0})
    return Searchable


def _deletable():
    @dataclass_json
    @dataclass
    class Deletable(BaseResource, DeleteResourceMixin[BaseDeleteParams, DeleteResult]):
        RESOURCE_PATH = "deletable"

    resource = Deletable(id="123", name="to delete")
    resource.context = Mock()
    resource.context.client.request_raw = Mock(return_value=Mock())
    return resource


CALLS = {
    "get": lambda: _gettable().get("123", api_key="OTHER-TENANT"),
    "search": lambda: _searchable().search(api_key="OTHER-TENANT"),
    "delete": lambda: _deletable().delete(api_key="OTHER-TENANT"),
    "model.run": lambda: _model().run(text="hi", api_key="OTHER-TENANT"),
    "tool.run": lambda: _tool().run(data={"query": "hi"}, api_key="OTHER-TENANT"),
    "agent.run": lambda: _agent().run(query="hi", api_key="OTHER-TENANT"),
}


@pytest.mark.parametrize("name", sorted(CALLS))
def test_per_call_api_key_warns_exactly_once(name):
    """One warning per call, even when an override delegates to ``super()``."""
    found = _call_and_record(CALLS[name])
    assert len(found) == 1, [str(w.message) for w in found]
    assert "Aixplain(api_key=" in str(found[0].message)


@pytest.mark.parametrize("name", ["get", "search", "delete", "model.run"])
def test_warning_points_at_the_caller(name):
    """The warning is attributed to user code, not to an SDK frame."""
    found = _call_and_record(CALLS[name])
    assert found and found[0].filename == __file__


def test_pytest_warns_matches_the_replacement():
    with pytest.warns(DeprecationWarning, match=MATCH):
        _gettable().get("123", api_key="OTHER-TENANT")


@pytest.mark.parametrize(
    "call",
    [
        lambda: _gettable().get("123"),
        lambda: _searchable().search(),
        lambda: _deletable().delete(),
        lambda: _model().run(text="hi"),
    ],
)
def test_no_warning_without_a_per_call_key(call):
    assert _call_and_record(call) == []


def test_the_key_is_still_never_forwarded():
    """The warning does not change BUG-1091's stripping."""
    cls = _gettable()
    with pytest.warns(DeprecationWarning, match=MATCH):
        cls.get("123", api_key="OTHER-TENANT")
    assert "api_key" not in cls.context.client.get.call_args.kwargs
