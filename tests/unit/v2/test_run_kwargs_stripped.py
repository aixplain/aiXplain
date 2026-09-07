"""SDK-control run kwargs must never reach the wire body (BUG-1091).

``api_key`` and ``resource_path`` are declared on ``BaseParams``, so they can
arrive on *any* v2 call. Neither is a backend body field:

- ``api_key`` authenticates nothing — ``Client.request_raw`` always overlays
  ``_auth_headers()`` from the Aixplain context — so its only observable effect
  was riding into the model input body and, from there, the supplier's prompt
  logs.
- ``resource_path`` is consumed by the URL builders.

Both are also not ``requests`` kwargs, which is why the same root cause made
``delete(resource_path=…)`` and ``get(id, api_key=…)`` raise deep inside
``requests``.
"""

from dataclasses import dataclass
from unittest.mock import MagicMock, Mock

import pytest
from dataclasses_json import dataclass_json

from aixplain.v2.actions import Action, Actions, Inputs
from aixplain.v2.agent import Agent
from aixplain.v2.integration import ActionInputSpec
from aixplain.v2.model import Model
from aixplain.v2.resource import (
    BaseDeleteParams,
    BaseResource,
    DeleteResourceMixin,
    DeleteResult,
    GetResourceMixin,
    RunnableResourceMixin,
)
from aixplain.v2.tool import Tool

SDK_REQUEST_KWARGS = {"api_key": "SECRET-TEAM-KEY", "resource_path": "v2/custom"}


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
    """A Tool with one allowed action, wired to a mock client."""
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


class TestControlKeysAreDeclaredOnce:
    """One authoritative set, inherited by every runnable."""

    def test_base_mixin_strips_the_dispatch_keys(self):
        assert {"api_key", "resource_path"} <= RunnableResourceMixin._RUN_CONTROL_KEYS

    def test_base_mixin_strips_the_progress_display_keys(self):
        assert {
            "show_progress",
            "progress_format",
            "progress_verbosity",
            "progress_truncate",
        } <= RunnableResourceMixin._RUN_CONTROL_KEYS

    @pytest.mark.parametrize("cls", [Model, Tool, Agent])
    def test_every_runnable_inherits_them(self, cls):
        assert {"api_key", "resource_path"} <= cls._RUN_CONTROL_KEYS


class TestApiKeyNeverReachesARunBody:
    def test_model_build_run_payload(self):
        assert _model().build_run_payload(text="hi", **SDK_REQUEST_KWARGS) == {"text": "hi"}

    def test_tool_build_run_payload(self):
        assert _model(Tool).build_run_payload(text="hi", **SDK_REQUEST_KWARGS) == {"text": "hi"}

    def test_model_posted_body(self):
        model = _model()
        model.run(text="hi", **SDK_REQUEST_KWARGS)

        body = model.context.client.request.call_args.kwargs["json"]
        assert body == {"text": "hi"}

    def test_tool_posted_body(self):
        tool = _tool()
        tool.run(data={"query": "hi"}, **SDK_REQUEST_KWARGS)

        body = tool.context.client.request.call_args.kwargs["json"]
        assert body == {"action": "search", "data": {"query": "hi"}}

    def test_agent_posted_body(self):
        agent = _agent()
        agent.run(query="hi", **SDK_REQUEST_KWARGS)

        body = agent.context.client.request.call_args.kwargs["json"]
        assert "api_key" not in body
        assert "resource_path" not in body
        assert SDK_REQUEST_KWARGS["api_key"] not in str(body)

    def test_resource_path_still_selects_the_run_url(self):
        """Stripping it from the *body* must not stop it steering the URL."""
        model = _model()
        model.run(text="hi", **SDK_REQUEST_KWARGS)

        url = model.context.client.request.call_args[0][1]
        assert url.endswith("/test-model-id")


class TestDeleteAcceptsTheDispatchKeys:
    """``delete()`` forwarded every kwarg to ``requests``, so passing either key
    raised ``TypeError`` inside ``session.request()``."""

    def _resource(self):
        @dataclass_json
        @dataclass
        class DeletableResource(BaseResource, DeleteResourceMixin[BaseDeleteParams, DeleteResult]):
            RESOURCE_PATH = "deletable"

        resource = DeletableResource(id="123", name="to delete")
        resource.context = Mock()
        resource.context.client.request_raw = Mock(return_value=Mock())
        return resource

    def test_delete_with_resource_path_succeeds_and_uses_it(self):
        resource = self._resource()

        resource.delete(resource_path="sdk/agents")

        call_args = resource.context.client.request_raw.call_args
        assert call_args[0][0] == "delete"
        assert "sdk/agents/123" in call_args[0][1]
        assert "resource_path" not in call_args.kwargs

    def test_delete_with_api_key_succeeds(self):
        resource = self._resource()

        resource.delete(api_key="SECRET-TEAM-KEY")

        call_args = resource.context.client.request_raw.call_args
        assert "deletable/123" in call_args[0][1]
        assert "api_key" not in call_args.kwargs

    def test_delete_still_forwards_genuine_request_kwargs(self):
        resource = self._resource()

        resource.delete(timeout=30)

        assert resource.context.client.request_raw.call_args.kwargs["timeout"] == 30


class TestGetAcceptsTheDispatchKeys:
    def _cls(self):
        @dataclass_json
        @dataclass
        class Gettable(BaseResource, GetResourceMixin[dict, "Gettable"]):
            RESOURCE_PATH = "gettable"

        Gettable.context = Mock()
        Gettable.context.client.get = Mock(return_value={"id": "123", "name": "got"})
        return Gettable

    def test_get_with_api_key_succeeds(self):
        cls = self._cls()

        instance = cls.get("123", api_key="SECRET-TEAM-KEY")

        assert instance.id == "123"
        call_args = cls.context.client.get.call_args
        assert call_args[0][0] == "gettable/123"
        assert "api_key" not in call_args.kwargs

    def test_get_still_forwards_genuine_request_kwargs(self):
        cls = self._cls()

        cls.get("123", timeout=30)

        assert cls.context.client.get.call_args.kwargs["timeout"] == 30
