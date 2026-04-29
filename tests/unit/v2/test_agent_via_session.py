"""Unit tests for the opt-in `via_session=True` path on Agent.run().

The opt-in path: post a user message to a Session (carrying the agent's
`executionConfig`) and then poll the legacy `/sdk/agents/{request_id}/result`
endpoint using the request_id the backend stamps on the user message.
That preserves the full `AgentRunResult` shape (steps, execution_stats,
used_credits, run_time) while migrating the trigger surface to sessions.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain.v2.agent import Agent, AgentRunResult
from aixplain.v2.session import ExecutionConfig, Session, SessionMessage


def _make_mock_context(**overrides):
    client = Mock()
    ctx = Mock(
        client=client,
        backend_url="https://platform-api.aixplain.com",
        api_key="test_key",
    )
    for k, v in overrides.items():
        setattr(ctx, k, v)
    return ctx


def _bound_agent(ctx):
    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


def _user_message(request_id="req_abc", id_="msg_user"):
    """A user SessionMessage as the backend returns from POST .../messages."""
    return SessionMessage(
        id=id_,
        session_id="sess_abc",
        user_id="u1",
        agent_id="agent_99",
        role="user",
        content="hi",
        sequence=1,
        request_id=request_id,
        created_at="2025-06-01T10:01:00Z",
    )


# ---------------------------------------------------------------------------
# 1. Creates session when no session_id is provided, then polls legacy result
# ---------------------------------------------------------------------------


class TestRunViaSessionCreatesSession:
    def test_creates_session_then_polls_legacy_result(self):
        ctx = _make_mock_context()

        # Build a real Session subclass bound to ctx with save() + add_message()
        # mocked so we can assert how _run_via_session wires them.
        class BoundSession(Session):
            context = ctx

        save_calls = []
        add_calls = []

        def fake_save(self, *a, **kw):
            self.id = "sess_new"
            save_calls.append(
                {
                    "agent_id": self.agent_id,
                    "name": self.name,
                    "execution_config": self.execution_config,
                }
            )
            return self

        def fake_add_message(self, role, content, **kw):
            add_calls.append({"role": role, "content": content, "kwargs": kw})
            return _user_message(request_id="req_xyz")

        BoundSession.save = fake_save
        BoundSession.add_message = fake_add_message
        ctx.Session = BoundSession

        # The legacy poll endpoint returns a fully populated result.
        ctx.client.get.return_value = {
            "status": "SUCCESS",
            "completed": True,
            "data": {
                "output": "hi back!",
                "session_id": "sess_new",
                "steps": [{"agent": "agent_99", "thought": "ok"}],
            },
            "sessionId": "sess_new",
            "requestId": "req_xyz",
            "usedCredits": 0.42,
            "runTime": 1.7,
        }

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        result = agent.run(
            "hi",
            via_session=True,
            execution_params={"max_tokens": 64},
            criteria="be brief",
        )

        # Session was created with the executionConfig our shortcut kwargs implied.
        assert len(save_calls) == 1
        cfg = save_calls[0]["execution_config"]
        assert isinstance(cfg, ExecutionConfig)
        assert cfg.execution_params == {"max_tokens": 64}
        assert cfg.criteria == "be brief"

        # User message was POSTed.
        assert len(add_calls) == 1
        assert add_calls[0]["role"] == "user"
        assert add_calls[0]["content"] == "hi"

        # Legacy result endpoint was hit with the request_id from the user message.
        get_call = ctx.client.get.call_args_list[0]
        assert "/sdk/agents/req_xyz/result" in get_call[0][0]

        # Result preserves the full legacy shape.
        assert isinstance(result, AgentRunResult)
        assert result.status == "SUCCESS"
        assert result.completed is True
        assert result.session_id == "sess_new"
        assert result.request_id == "req_xyz"
        assert result.data.output == "hi back!"
        assert result.data.steps == [{"agent": "agent_99", "thought": "ok"}]
        assert result.used_credits == 0.42
        assert result.run_time == 1.7


# ---------------------------------------------------------------------------
# 2. Reuses an existing session_id without creating a new one
# ---------------------------------------------------------------------------


class TestRunViaSessionReuse:
    def test_reuses_existing_session_id(self):
        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_abc"
        existing.add_message = Mock(return_value=_user_message(request_id="req_reuse"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)

        ctx.client.get.return_value = {
            "status": "SUCCESS",
            "completed": True,
            "data": {"output": "again", "session_id": "sess_abc", "steps": []},
            "sessionId": "sess_abc",
            "requestId": "req_reuse",
            "usedCredits": 0.0,
            "runTime": 0.5,
        }

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        result = agent.run("hi again", via_session=True, session_id="sess_abc")

        ctx.Session.get.assert_called_once_with("sess_abc")
        # No new session was instantiated via ctx.Session(...).
        ctx.Session.assert_not_called()
        existing.add_message.assert_called_once()
        # And the legacy poll endpoint used the user message's request_id.
        get_call = ctx.client.get.call_args_list[0]
        assert "/sdk/agents/req_reuse/result" in get_call[0][0]
        assert result.session_id == "sess_abc"


# ---------------------------------------------------------------------------
# 3. Missing requestId on the user message → ValueError (defensive)
# ---------------------------------------------------------------------------


class TestRunViaSessionMissingRequestId:
    def test_raises_when_user_message_has_no_request_id(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        BoundSession.save = lambda self, *a, **kw: setattr(self, "id", "sess_new") or self
        BoundSession.add_message = lambda self, role, content, **kw: _user_message(request_id=None)
        ctx.Session = BoundSession

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.raises(ValueError, match="requestId"):
            agent.run("hi", via_session=True)


# ---------------------------------------------------------------------------
# 4. Rejects legacy-only kwargs under via_session=True
# ---------------------------------------------------------------------------


class TestRunViaSessionRejectsLegacyKwargs:
    @pytest.mark.parametrize(
        "legacy_kwarg",
        ["tasks", "prompt", "inspectors", "history", "variables", "allow_history_and_session_id"],
    )
    def test_rejects_legacy_kwargs(self, legacy_kwarg):
        ctx = _make_mock_context()
        ctx.Session = Mock()
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.raises(ValueError, match=legacy_kwarg):
            agent.run("hi", via_session=True, **{legacy_kwarg: ["something"]})


# ---------------------------------------------------------------------------
# 5. run_async with via_session=True is not implemented
# ---------------------------------------------------------------------------


class TestRunAsyncViaSessionNotImplemented:
    def test_run_async_via_session_not_implemented(self):
        ctx = _make_mock_context()
        ctx.Session = Mock()
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.raises(NotImplementedError, match="via_session"):
            agent.run_async("hi", via_session=True)


# ---------------------------------------------------------------------------
# 6. Default path (no via_session) still hits legacy /v2/agents/{id}/run
# ---------------------------------------------------------------------------


class TestDefaultPathUnchanged:
    def test_run_default_path_hits_legacy_endpoint(self):
        ctx = _make_mock_context()
        # Legacy run: POST returns a polling URL, then GET resolves to a SUCCESS.
        ctx.client.request.return_value = {
            "status": "IN_PROGRESS",
            "data": "https://platform-api.aixplain.com/sdk/agents/exec_42/result",
        }
        ctx.client.get.return_value = {
            "status": "SUCCESS",
            "completed": True,
            "data": {"output": "legacy reply", "session_id": None, "steps": []},
            "sessionId": None,
            "requestId": "req_legacy",
            "usedCredits": 0.5,
            "runTime": 1.2,
        }

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with patch("time.sleep"):
            result = agent.run("hi")

        # Legacy POST went to v2/agents/{id}/run.
        post_call = ctx.client.request.call_args_list[0]
        assert post_call[0][0] == "post"
        assert "v2/agents/agent_99/run" in post_call[0][1]

        # Legacy poll URL was used.
        get_call = ctx.client.get.call_args_list[0]
        assert "/sdk/agents/exec_42/result" in get_call[0][0]

        # And we did NOT touch ctx.Session at all.
        assert not hasattr(ctx.Session, "save") or not ctx.Session.save.called  # type: ignore[attr-defined]

        assert result.status == "SUCCESS"
        assert result.data.output == "legacy reply"
        assert result.used_credits == 0.5
