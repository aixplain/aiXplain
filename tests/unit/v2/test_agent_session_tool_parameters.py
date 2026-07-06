"""Unit tests for session-level / per-message tool-parameter overrides.

PROD-2481. Sessions extend the per-tool override shape introduced for
single-shot runs in #967 (``tools=[{"id": <id>, "parameters": {...}}]``):

* A session may be created carrying session-level per-tool params, persisted
  inside ``executionConfig.tools`` as the platform ``[{id, parameters:
  [{name, value}]}]`` shape.
* A message added to a session (or a ``via_session=True`` run) may override
  those params per message — the message POST carries its own ``tools``,
  which the backend merges over the session-level params by tool id.
* ``via_session=True`` must no longer silently drop ``tools`` (the confirmed
  bug): the run-time ``tools`` kwarg becomes the per-message override.

These tests mock the HTTP/client layer and assert the payloads carry the
normalized ``tools``. They mirror ``test_agent_tool_parameters.py`` and
``test_agent_via_session.py``.
"""

from typing import Any, Dict, List
from unittest.mock import Mock

from aixplain.v2.agent import Agent
from aixplain.v2.session import ExecutionConfig, Session, SessionMessage


def _params_as_dict(parameters: List[dict]) -> Dict[str, Any]:
    return {item["name"]: item["value"] for item in parameters}


def _tool_by_id(tools: List[dict], tool_id: str) -> dict:
    return next(t for t in tools if t.get("id") == tool_id or t.get("assetId") == tool_id)


def _make_mock_context(**overrides):
    client = Mock()
    ctx = Mock(client=client, backend_url="https://platform-api.aixplain.com", api_key="test_key")
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


# ---------------------------------------------------------------------------
# ExecutionConfig carries normalized tools into the session-create payload.
# ---------------------------------------------------------------------------


class TestExecutionConfigTools:
    def test_to_api_dict_includes_tools(self):
        cfg = ExecutionConfig(
            tools=[{"id": "tool-1", "parameters": [{"name": "top_k", "value": 5}]}],
        )
        api = cfg.to_api_dict()
        tool = _tool_by_id(api["tools"], "tool-1")
        assert _params_as_dict(tool["parameters"]) == {"top_k": 5}

    def test_to_api_dict_omits_tools_when_unset(self):
        assert "tools" not in ExecutionConfig(criteria="x").to_api_dict()

    def test_coerce_dict_roundtrips_tools(self):
        cfg = ExecutionConfig.coerce({"tools": [{"id": "tool-1", "parameters": [{"name": "lang", "value": "es"}]}]})
        assert cfg.tools == [{"id": "tool-1", "parameters": [{"name": "lang", "value": "es"}]}]


# ---------------------------------------------------------------------------
# create_session forwards session-level tool params (normalized).
# ---------------------------------------------------------------------------


class TestCreateSessionTools:
    def test_create_session_normalizes_session_level_tools(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        captured = {}

        def fake_save(self, *a, **kw):
            self.id = "sess_new"
            captured["config"] = self.execution_config
            return self

        BoundSession.save = fake_save
        ctx.Session = BoundSession

        agent = _bound_agent(ctx)(id="agent_99", name="A")
        agent._update_saved_state()

        agent.create_session(tools=[{"id": "tool-1", "parameters": {"top_k": 7}}])

        cfg = captured["config"]
        assert isinstance(cfg, ExecutionConfig)
        tool = _tool_by_id(cfg.tools, "tool-1")
        assert _params_as_dict(tool["parameters"]) == {"top_k": 7}

    def test_create_session_string_tool_id(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        captured = {}
        BoundSession.save = lambda self, *a, **kw: (
            setattr(self, "id", "s") or captured.update(config=self.execution_config) or self
        )
        ctx.Session = BoundSession

        agent = _bound_agent(ctx)(id="agent_99", name="A")
        agent._update_saved_state()

        agent.create_session(tools=["tool-1"])
        assert captured["config"].tools == [{"id": "tool-1"}]


# ---------------------------------------------------------------------------
# add_message forwards a per-message tool override in the POST payload.
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
# via_session=True no longer drops tools; it routes them to the message.
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

    def test_via_session_routes_tools_to_message_override(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        add_calls = []
        BoundSession.save = lambda self, *a, **kw: setattr(self, "id", "sess_new") or self

        def fake_add_message(self, role, content, **kw):
            add_calls.append(kw)
            return _user_message(request_id="req_xyz")

        BoundSession.add_message = fake_add_message
        ctx.Session = BoundSession
        self._wire_poll_success(ctx, "req_xyz")

        agent = _bound_agent(ctx)(id="agent_99", name="A")
        agent._update_saved_state()

        agent.run(
            "hi",
            via_session=True,
            tools=[{"id": "tool-1", "parameters": {"top_k": 3}}],
        )

        assert len(add_calls) == 1
        tool = _tool_by_id(add_calls[0]["tools"], "tool-1")
        assert _params_as_dict(tool["parameters"]) == {"top_k": 3}

    def test_via_session_without_tools_passes_none(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        add_calls = []
        BoundSession.save = lambda self, *a, **kw: setattr(self, "id", "sess_new") or self

        def fake_add_message(self, role, content, **kw):
            add_calls.append(kw)
            return _user_message(request_id="req_xyz")

        BoundSession.add_message = fake_add_message
        ctx.Session = BoundSession
        self._wire_poll_success(ctx, "req_xyz")

        agent = _bound_agent(ctx)(id="agent_99", name="A")
        agent._update_saved_state()

        agent.run("hi", via_session=True)
        assert add_calls[0].get("tools") is None


# ---------------------------------------------------------------------------
# Single-shot (non-session) behavior from #967 is unchanged.
# ---------------------------------------------------------------------------


class TestSingleShotUnchanged:
    def test_run_payload_still_normalizes_tools(self):
        agent = Agent(name="n", description="d")
        agent.context = Mock()
        agent.id = "agent-1"
        payload = agent.build_run_payload(query="hi", tools=[{"id": "tool-1", "parameters": {"top_k": 8}}])
        assert _params_as_dict(_tool_by_id(payload["tools"], "tool-1")["parameters"]) == {"top_k": 8}

    def test_save_payload_still_normalizes_tools(self):
        agent = Agent(name="n", description="d", tools=[{"id": "tool-1", "parameters": {"top_k": 5}}])
        agent.context = Mock()
        payload = agent.build_save_payload()
        assert _params_as_dict(_tool_by_id(payload["tools"], "tool-1")["parameters"]) == {"top_k": 5}
