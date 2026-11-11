"""Unit tests for the `session=` run path on Agent.run().

Passing `session=` (a Session object or id string) posts a user message to that
Session (carrying its `executionConfig`) and then polls the
`/sdk/agents/{request_id}/result` endpoint using the request_id the backend
stamps on the user message. That preserves the full `AgentRunResult` shape
(steps, execution_stats, used_credits, run_time) while routing the trigger
through sessions. There is no `via_session` flag and no id-only `session_id=`;
threads are managed through `aix.Session` and passed here.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain import Agent, AgentRunResult
from aixplain import ExecutionConfig, Session, SessionMessage


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


def _success_result(session_id="sess_abc", request_id="req_abc"):
    return {
        "status": "SUCCESS",
        "completed": True,
        "data": {"output": "hi back!", "session_id": session_id, "steps": [{"agent": "agent_99", "thought": "ok"}]},
        "sessionId": session_id,
        "requestId": request_id,
        "usedCredits": 0.42,
        "runTime": 1.7,
    }


# ---------------------------------------------------------------------------
# 1. session= a Session object → post to it, then poll the run result
# ---------------------------------------------------------------------------


class TestRunWithSessionObject:
    def test_session_object_posts_and_polls(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        add_calls = []

        def fake_add_message(self, role, content, **kw):
            add_calls.append({"role": role, "content": content, "kwargs": kw})
            return _user_message(request_id="req_xyz")

        BoundSession.add_message = fake_add_message
        ctx.Session = BoundSession
        ctx.client.get.return_value = _success_result(session_id="sess_obj", request_id="req_xyz")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        session = BoundSession(agent=agent, name="thread")
        session.id = "sess_obj"

        result = agent.run("hi", session=session)

        # The user message was POSTed to the passed-in session.
        assert len(add_calls) == 1
        assert add_calls[0]["role"] == "user"
        assert add_calls[0]["content"] == "hi"

        # The run-result endpoint was hit with the user message's request_id.
        get_call = ctx.client.get.call_args_list[0]
        assert "/sdk/agents/req_xyz/result" in get_call[0][0]

        # Result preserves the full result shape.
        assert isinstance(result, AgentRunResult)
        assert result.status == "SUCCESS"
        assert result.completed is True
        assert result.session_id == "sess_obj"
        assert result.request_id == "req_xyz"
        assert result.data.output == "hi back!"
        assert result.data.steps == [{"agent": "agent_99", "thought": "ok"}]
        assert result.used_credits == 0.42
        assert result.run_time == 1.7

    def test_session_object_without_context_is_bound(self):
        """A Session with no context is bound to the agent's context on run."""
        ctx = _make_mock_context()
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        session = Session(agent_id="agent_99", name="unbound")
        session.id = "sess_unbound"
        session.add_message = Mock(return_value=_user_message(request_id="req_bound"))
        assert getattr(session, "context", None) is None

        ctx.client.get.return_value = _success_result(session_id="sess_unbound", request_id="req_bound")
        agent.run("hi", session=session)

        assert session.context is ctx
        session.add_message.assert_called_once()


# ---------------------------------------------------------------------------
# 2. session= an id string → fetched via Session.get
# ---------------------------------------------------------------------------


class TestRunWithSessionId:
    def test_session_id_fetches_via_get(self):
        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_abc"
        existing.context = ctx
        existing.execution_config = None
        existing.add_message = Mock(return_value=_user_message(request_id="req_reuse"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_abc", request_id="req_reuse")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        result = agent.run("hi again", session="sess_abc")

        ctx.Session.get.assert_called_once_with("sess_abc")
        existing.add_message.assert_called_once()
        get_call = ctx.client.get.call_args_list[0]
        assert "/sdk/agents/req_reuse/result" in get_call[0][0]
        assert result.session_id == "sess_abc"

    def test_bad_session_type_raises(self):
        ctx = _make_mock_context()
        ctx.Session = Mock()
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.raises(TypeError, match="session must be a Session instance or a session id"):
            agent.run("hi", session=123)


# ---------------------------------------------------------------------------
# 3. Per-run execution overrides merge onto the session's config
# ---------------------------------------------------------------------------


class TestRunWithSessionOverrides:
    def test_applies_per_run_overrides_and_warns(self):
        """Per-run execution kwargs on a session must take effect.

        They are merged onto the session's stored executionConfig and the
        session is re-saved, with a warning that the config is mutated for
        all subsequent messages.
        """
        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_abc"
        existing.context = ctx
        existing.execution_config = ExecutionConfig(execution_params={"max_tokens": 64})
        existing.save = Mock()
        existing.add_message = Mock(return_value=_user_message(request_id="req_override"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_abc", request_id="req_override")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.warns(UserWarning, match="session 'sess_abc'"):
            agent.run("hi again", session="sess_abc", criteria="be brief")

        existing.save.assert_called_once()
        assert existing.execution_config.execution_params == {"max_tokens": 64}
        assert existing.execution_config.criteria == "be brief"
        existing.add_message.assert_called_once()

    def test_without_overrides_does_not_resave(self):
        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_abc"
        existing.context = ctx
        existing.execution_config = ExecutionConfig(criteria="be brief")
        existing.save = Mock()
        existing.add_message = Mock(return_value=_user_message(request_id="req_noop"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_abc", request_id="req_noop")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        agent.run("hi again", session="sess_abc")
        existing.save.assert_not_called()

    def test_matching_overrides_does_not_resave(self):
        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_abc"
        existing.context = ctx
        existing.execution_config = ExecutionConfig(criteria="be brief")
        existing.save = Mock()
        existing.add_message = Mock(return_value=_user_message(request_id="req_same"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_abc", request_id="req_same")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        import warnings as _warnings

        with _warnings.catch_warnings():
            _warnings.simplefilter("error")
            agent.run("hi again", session="sess_abc", criteria="be brief")
        existing.save.assert_not_called()

    def test_override_does_not_delete_the_session_budget(self):
        """A per-run override must not silently drop the session's spend cap.

        The merge used to rebuild ExecutionConfig from a hardcoded field list
        that omitted ``budget`` and then ``save()`` the loss, so the session ran
        uncapped from that point on (BUG-1091).
        """
        from aixplain import Budget

        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_abc"
        existing.context = ctx
        existing.execution_config = ExecutionConfig(criteria="old", budget=Budget(max_cost=5.0, max_iterations=7))
        existing.save = Mock()
        existing.add_message = Mock(return_value=_user_message(request_id="req_budget"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_abc", request_id="req_budget")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.warns(UserWarning, match="session 'sess_abc'"):
            agent.run("hi again", session="sess_abc", criteria="be brief")

        existing.save.assert_called_once()
        assert existing.execution_config.criteria == "be brief"
        assert existing.execution_config.budget == Budget(max_cost=5.0, max_iterations=7)
        assert existing.execution_config.to_api_dict()["executionParams"]["budget"] == {
            "maxCost": 5.0,
            "maxIterations": 7,
        }

    def test_agent_budget_seeds_a_session_without_one(self):
        """``agent.budget`` applied on the direct run path only; now on both."""
        from aixplain import Budget

        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_abc"
        existing.context = ctx
        existing.execution_config = None
        existing.save = Mock()
        existing.add_message = Mock(return_value=_user_message(request_id="req_seed"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_abc", request_id="req_seed")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent.budget = Budget(max_cost=1.0)
        agent._update_saved_state()

        with pytest.warns(UserWarning, match=r"budget \(from agent\.budget\)"):
            agent.run("hi again", session="sess_abc")

        existing.save.assert_called_once()
        assert existing.execution_config.budget == Budget(max_cost=1.0)


# ---------------------------------------------------------------------------
# 4. Attachments / files / audio-as-prompt
# ---------------------------------------------------------------------------


class TestRunWithSessionAttachments:
    def test_forwards_attachments_and_files_to_user_message(self):
        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_att"
        existing.context = ctx
        existing.execution_config = None
        existing.add_message = Mock(return_value=_user_message(request_id="req_att"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_att", request_id="req_att")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        attachments = [{"url": "https://s3/a.png", "type": "image"}]
        files = ["/tmp/report.pdf"]
        agent.run("describe these", session="sess_att", attachments=attachments, files=files)

        _, kwargs = existing.add_message.call_args
        assert kwargs["attachments"] == attachments
        assert kwargs["files"] == files

    def test_audio_as_prompt_allows_missing_query(self):
        # Audio-as-prompt: no text query, attachments carry the turn's input.
        ctx = _make_mock_context()

        existing = Mock(spec=Session)
        existing.id = "sess_aud"
        existing.context = ctx
        existing.execution_config = None
        existing.add_message = Mock(return_value=_user_message(request_id="req_aud"))

        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        ctx.client.get.return_value = _success_result(session_id="sess_aud", request_id="req_aud")

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        attachments = [{"url": "https://s3/a.wav", "type": "audio"}]
        agent.run(session="sess_aud", attachments=attachments)

        _, kwargs = existing.add_message.call_args
        assert kwargs["content"] == ""  # empty query coerced to empty content
        assert kwargs["attachments"] == attachments

    def test_raises_when_no_query_and_no_attachments(self):
        ctx = _make_mock_context()
        existing = Mock(spec=Session)
        existing.id = "sess_x"
        existing.context = ctx
        existing.execution_config = None
        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.raises(ValueError, match="requires a query or attachments"):
            agent.run(session="sess_x")


# ---------------------------------------------------------------------------
# 5. Missing requestId on the user message → ValueError (defensive)
# ---------------------------------------------------------------------------


class TestRunWithSessionMissingRequestId:
    def test_raises_when_user_message_has_no_request_id(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        BoundSession.add_message = lambda self, role, content, **kw: _user_message(request_id=None)
        ctx.Session = BoundSession

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        session = BoundSession(agent_id="agent_99")
        session.id = "sess_new"

        with pytest.raises(ValueError, match="requestId"):
            agent.run("hi", session=session)


# ---------------------------------------------------------------------------
# 6. Rejects legacy-only kwargs when running with a session
# ---------------------------------------------------------------------------


class TestRunWithSessionRejectsLegacyKwargs:
    @pytest.mark.parametrize(
        "legacy_kwarg",
        ["tasks", "prompt", "inspectors", "history", "variables"],
    )
    def test_rejects_legacy_kwargs(self, legacy_kwarg):
        ctx = _make_mock_context()
        existing = Mock(spec=Session)
        existing.id = "sess_x"
        existing.context = ctx
        existing.execution_config = None
        ctx.Session = Mock()
        ctx.Session.get = Mock(return_value=existing)
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.raises(ValueError, match=legacy_kwarg):
            agent.run("hi", session="sess_x", **{legacy_kwarg: ["something"]})


# ---------------------------------------------------------------------------
# 7. run_async with session= is not implemented
# ---------------------------------------------------------------------------


class TestRunAsyncWithSessionNotImplemented:
    def test_run_async_with_session_not_implemented(self):
        ctx = _make_mock_context()
        ctx.Session = Mock()
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with pytest.raises(NotImplementedError, match="session"):
            agent.run_async("hi", session="sess_x")


# ---------------------------------------------------------------------------
# 8. Default path (no session) still hits /v2/agents/{id}/run
# ---------------------------------------------------------------------------


class TestDefaultPathUnchanged:
    def test_run_default_path_hits_direct_endpoint(self):
        ctx = _make_mock_context()
        # Direct run: POST returns a polling URL, then GET resolves to a SUCCESS.
        ctx.client.request.return_value = {
            "status": "IN_PROGRESS",
            "data": "https://platform-api.aixplain.com/sdk/agents/exec_42/result",
        }
        ctx.client.get.return_value = {
            "status": "SUCCESS",
            "completed": True,
            "data": {"output": "direct reply", "session_id": None, "steps": []},
            "sessionId": None,
            "requestId": "req_direct",
            "usedCredits": 0.5,
            "runTime": 1.2,
        }

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        with patch("time.sleep"):
            result = agent.run("hi")

        # Direct POST went to v2/agents/{id}/run.
        post_call = ctx.client.request.call_args_list[0]
        assert post_call[0][0] == "post"
        assert "v2/agents/agent_99/run" in post_call[0][1]

        # Direct poll URL was used.
        get_call = ctx.client.get.call_args_list[0]
        assert "/sdk/agents/exec_42/result" in get_call[0][0]

        assert result.status == "SUCCESS"
        assert result.data.output == "direct reply"
        assert result.used_credits == 0.5


class TestSessionRunPollTimeout:
    def test_poll_waits_for_the_session_budget(self):
        ctx = _make_mock_context()

        class BoundSession(Session):
            context = ctx

        BoundSession.add_message = lambda self, role, content, **kw: _user_message(request_id="req_t")
        ctx.Session = BoundSession

        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A")
        agent._update_saved_state()

        session = BoundSession(agent=agent, name="thread")
        session.id = "sess_t"
        session.execution_config = ExecutionConfig(budget={"max_duration_seconds": 1500})

        with patch.object(Agent, "sync_poll", return_value=AgentRunResult.from_dict(_success_result())) as poll:
            agent.run("hi", session=session)

        assert poll.call_args.kwargs["timeout"] == 1500 + Agent._POLL_TIMEOUT_ALLOWANCE_SECONDS


# ---------------------------------------------------------------------------
# BUG-1457: the session path goes through the same before_run guard
# ---------------------------------------------------------------------------


class TestRunWithSessionBeforeRunGuard:
    """``run(session=…)`` must auto-save a modified draft and refuse a modified onboarded agent."""

    def _setup(self, status):
        from aixplain.v2.enums import AssetStatus

        ctx = _make_mock_context()
        BoundAgent = _bound_agent(ctx)
        agent = BoundAgent(id="agent_99", name="A", instructions="old")
        agent.status = AssetStatus(status)
        agent._update_saved_state()

        session = Session(agent_id="agent_99", name="thread")
        session.context = ctx
        session.id = "sess_guard"
        events = []

        def fake_add_message(role, content, **kw):
            events.append(("add_message", content, kw))
            return _user_message(request_id="req_guard")

        session.add_message = Mock(side_effect=fake_add_message)
        ctx.client.get.return_value = _success_result(session_id="sess_guard", request_id="req_guard")
        return ctx, BoundAgent, agent, session, events

    def test_modified_draft_is_saved_once_before_message(self):
        ctx, BoundAgent, agent, session, events = self._setup("draft")
        agent.instructions = "new"

        def fake_save(self, *args, **kwargs):
            events.append(("save", kwargs))
            self._update_saved_state()
            return self

        with patch.object(BoundAgent, "save", fake_save):
            agent.run("hi", session=session, attachments=["https://example.com/a.png"])

        assert [e[0] for e in events] == ["save", "add_message"]
        assert events[0][1] == {"as_draft": True}
        # before_run does not consume the kwargs the session path still needs.
        assert events[1][1] == "hi"
        assert events[1][2]["attachments"] == ["https://example.com/a.png"]

    def test_unmodified_draft_is_not_saved(self):
        ctx, BoundAgent, agent, session, events = self._setup("draft")
        with patch.object(BoundAgent, "save") as save:
            agent.run("hi", session=session)
        save.assert_not_called()
        session.add_message.assert_called_once()

    def test_modified_onboarded_raises_and_posts_nothing(self):
        ctx, BoundAgent, agent, session, events = self._setup("onboarded")
        agent.instructions = "new"

        with pytest.raises(ValueError, match="onboarded and cannot be modified") as session_exc:
            agent.run("hi", session=session)
        session.add_message.assert_not_called()
        ctx.client.get.assert_not_called()

        # Same error as the direct (session-less) path.
        with pytest.raises(ValueError) as direct_exc:
            agent.run("hi")
        assert str(session_exc.value) == str(direct_exc.value)

    def test_unmodified_onboarded_runs(self):
        ctx, BoundAgent, agent, session, events = self._setup("onboarded")
        result = agent.run("hi", session=session)
        session.add_message.assert_called_once()
        assert result.status == "SUCCESS"

    def test_unsaved_sub_agent_still_rejected(self):
        ctx, BoundAgent, agent, session, events = self._setup("onboarded")
        team = BoundAgent(id="team_1", name="T", agents=[BoundAgent(name="child", instructions="x")])
        team._update_saved_state()
        with pytest.raises(ValueError, match="must be saved before running"):
            team.run("hi", session=session)
        session.add_message.assert_not_called()

    def test_malformed_call_does_not_save_draft(self):
        ctx, BoundAgent, agent, session, events = self._setup("draft")
        agent.instructions = "new"
        with patch.object(BoundAgent, "save") as save:
            with pytest.raises(ValueError, match="requires a query or attachments"):
                agent.run(session=session)
        save.assert_not_called()
