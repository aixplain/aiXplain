"""Unit tests for tool-parameter overrides through the session run path (PROD-2481).

Per-tool parameters are set by mutating the agent's tool objects (object API).
``run(via_session=True)`` serializes the agent's *current* tool parameter state
into the per-message override, matching the single-shot run path. The
session-level ``tools`` dict kwargs that PR #967 added were removed in favor of
this object-based flow.
"""

from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

from aixplain.v2.agent import Agent
from aixplain.v2.model import Model, Parameter
from aixplain.v2.session import ExecutionConfig, Session, SessionMessage
from aixplain.v2.tool import Tool


def _params_as_dict(parameters: List[dict]) -> Dict[str, Any]:
    return {item["name"]: item["value"] for item in parameters}


def _tool_by_id(tools: List[dict], tool_id: str) -> dict:
    return next(t for t in tools if t.get("id") == tool_id or t.get("assetId") == tool_id)


def _make_mock_context(**overrides):
    client = Mock()
    ctx = Mock(client=client, backend_url="https://platform-api.aixplain.com", api_key="test_key")
    ctx.Model = Model
    ctx.Tool = Tool
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


def _bound_agent(ctx):
    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


def _user_message(request_id="req_abc"):
    return SessionMessage(
        id="msg_user",
        session_id="sess_abc",
        role="user",
        content="hi",
        sequence=1,
        request_id=request_id,
    )


def _model_tool(temperature: Any = None) -> Model:
    model = Model(id="m2", name="translate", params=[Parameter(name="temperature", data_type="number")])
    if temperature is not None:
        model.inputs.temperature = temperature
    return model


# ---------------------------------------------------------------------------
# ExecutionConfig no longer carries a session-level tools override.
# ---------------------------------------------------------------------------


class TestExecutionConfigNoTools:
    def test_to_api_dict_has_no_tools(self):
        assert "tools" not in ExecutionConfig(criteria="x").to_api_dict()

    def test_execution_config_has_no_tools_field(self):
        assert "tools" not in ExecutionConfig().__dict__

    def test_create_session_rejects_tools_kwarg(self):
        agent = _bound_agent(_make_mock_context())(id="agent_99", name="A")
        agent._update_saved_state()
        with pytest.raises(TypeError):
            agent.create_session(tools=[{"id": "tool-1"}])


# ---------------------------------------------------------------------------
# add_message still accepts a per-message tools override in the POST payload.
# ---------------------------------------------------------------------------


class TestAddMessageTools:
    def test_add_message_payload_carries_tools(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = {"id": "m1", "role": "user", "content": "hi"}

        session = Session(agent_id="agent_99", name="A")
        session.context = ctx
        session.id = "sess_abc"
        session._update_saved_state()

        tools = [{"id": "tool-1", "parameters": [{"name": "top_k", "value": 9}]}]
        session.add_message(role="user", content="hi", tools=tools)

        _, kwargs = ctx.client.request.call_args
        assert kwargs["json"]["tools"] == tools

    def test_add_message_without_tools_omits_key(self):
        ctx = _make_mock_context()
        ctx.client.request.return_value = {"id": "m1", "role": "user", "content": "hi"}

        session = Session(agent_id="agent_99", name="A")
        session.context = ctx
        session.id = "sess_abc"
        session._update_saved_state()

        session.add_message(role="user", content="hi")
        _, kwargs = ctx.client.request.call_args
        assert "tools" not in kwargs["json"]


# ---------------------------------------------------------------------------
# via_session=True forwards the agent's current tool params as the override.
# ---------------------------------------------------------------------------


class TestRunViaSessionTools:
    def _wire_poll_success(self, ctx, request_id):
        ctx.client.get.return_value = {
            "status": "SUCCESS",
            "completed": True,
            "data": {"output": "ok", "session_id": "sess_new", "steps": []},
            "sessionId": "sess_new",
            "requestId": request_id,
            "usedCredits": 0.0,
            "runTime": 0.5,
        }

    def _bound_session(self, ctx, add_calls):
        class BoundSession(Session):
            context = ctx

        BoundSession.save = lambda self, *a, **kw: setattr(self, "id", "sess_new") or self

        def fake_add_message(self, role, content, **kw):
            add_calls.append(kw)
            return _user_message(request_id="req_xyz")

        BoundSession.add_message = fake_add_message
        ctx.Session = BoundSession

    def test_via_session_routes_agent_tool_params(self):
        ctx = _make_mock_context()
        add_calls: List[dict] = []
        self._bound_session(ctx, add_calls)
        self._wire_poll_success(ctx, "req_xyz")

        agent = _bound_agent(ctx)(id="agent_99", name="A", tools=[_model_tool(temperature=0.7)])
        agent._update_saved_state()

        agent.run("hi", via_session=True)

        assert len(add_calls) == 1
        tool = _tool_by_id(add_calls[0]["tools"], "m2")
        assert _params_as_dict(tool["parameters"]) == {"temperature": 0.7}

    def test_via_session_without_tool_params_passes_none(self):
        ctx = _make_mock_context()
        add_calls: List[dict] = []
        self._bound_session(ctx, add_calls)
        self._wire_poll_success(ctx, "req_xyz")

        agent = _bound_agent(ctx)(id="agent_99", name="A")
        agent._update_saved_state()

        agent.run("hi", via_session=True)
        assert add_calls[0].get("tools") is None


# ---------------------------------------------------------------------------
# Single-shot (non-session) object-API behavior.
# ---------------------------------------------------------------------------


class TestSingleShot:
    def test_run_payload_carries_object_tool_params(self):
        agent = Agent(name="n", description="d", tools=[_model_tool(temperature=0.8)])
        agent.context = Mock()
        agent.id = "agent-1"
        payload = agent.build_run_payload(query="hi")
        assert _params_as_dict(_tool_by_id(payload["tools"], "m2")["parameters"]) == {"temperature": 0.8}

    def test_save_payload_carries_object_tool_params(self):
        agent = Agent(name="n", description="d", tools=[_model_tool(temperature=0.5)])
        agent.context = Mock()
        payload = agent.build_save_payload()
        assert _params_as_dict(_tool_by_id(payload["tools"], "m2")["parameters"]) == {"temperature": 0.5}
