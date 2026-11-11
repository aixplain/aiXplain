"""Unit tests for the `session=` run path on Agent.run().

Passing `session=` (a Session object or id string) posts a user message to that
Session (carrying its `executionConfig`) and then polls the
`/sdk/agents/{request_id}/result` endpoint using the request_id the backend
stamps on the user message. That preserves the full `AgentRunResult` shape
(steps, execution_stats, used_credits, run_time) while routing the trigger
through sessions. There is no `via_session` flag and no id-only `session_id=`;
threads are managed through `aix.Session` and passed here.

Without `session=` the SDK creates a new Session for the run and goes through
the same path, so every run is a session run. Only kwargs the session endpoint
cannot carry (`tasks`/`prompt`/`inspectors`/`history`/`variables`, a non-string
query, the `session_id`/`agent_name` headers or any other kwarg the direct path
forwards) keep the direct `/v2/agents/{id}/run` path.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain import Agent, AgentRunNotStartedError, AgentRunResult
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
# 5. Missing requestId on the user message → AgentRunNotStartedError (also a ValueError)
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

        # Still a ValueError, as before, and now an APIError too.
        with pytest.raises(ValueError, match="requestId") as raised:
            agent.run("hi", session=session)
        assert isinstance(raised.value, AgentRunNotStartedError)


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
# 7. run_async with a session submits the message and returns a pollable result
# ---------------------------------------------------------------------------


class _AutoSessionHarness:
    """A context whose ``Session`` records what the SDK creates for a sessionless run."""

    def __init__(self):
        self.ctx = _make_mock_context()
        self.created = []
        self.posted = []
        harness = self

        class BoundSession(Session):
            context = self.ctx

            def save(self, *args, **kwargs):
                self.id = "sess_auto"
                harness.created.append(self)
                return self

            def add_message(self, role, content, **kw):
                harness.posted.append({"session": self.id, "role": role, "content": content, **kw})
                return _user_message()

        self.ctx.Session = BoundSession
        self.agent = _bound_agent(self.ctx)(id="agent_99", name="A")
        self.agent._update_saved_state()


class TestRunAsyncWithSession:
    def test_run_async_with_a_session_returns_the_poll_url(self):
        harness = _AutoSessionHarness()
        session = harness.ctx.Session(agent_id="agent_99")
        session.id = "sess_given"

        result = harness.agent.run_async("hi", session=session)

        assert harness.created == []  # the given session is used, not a new one
        assert harness.posted[0]["session"] == "sess_given"
        assert result.completed is False
        assert result.url == "https://platform-api.aixplain.com/sdk/agents/req_abc/result"
        assert result.request_id == "req_abc"
        assert result.session_id == "sess_given"
        harness.ctx.client.request.assert_not_called()  # no direct /v2/agents/{id}/run

    def test_run_async_without_a_session_creates_one(self):
        harness = _AutoSessionHarness()

        result = harness.agent.run_async("hi")

        assert [s.agent_id for s in harness.created] == ["agent_99"]
        assert harness.posted[0]["session"] == "sess_auto"
        assert result.session_id == "sess_auto"
        assert result.url.endswith("/sdk/agents/req_abc/result")
        harness.ctx.client.request.assert_not_called()


# ---------------------------------------------------------------------------
# 8. No session: the SDK creates one and runs through it
# ---------------------------------------------------------------------------


class TestRunWithoutSessionCreatesOne:
    def test_run_creates_a_session_and_posts_through_it(self):
        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result(session_id=None)))

        result = harness.agent.run("hi")

        assert len(harness.created) == 1
        assert harness.created[0].agent_id == "agent_99"
        assert harness.posted == [
            {"session": "sess_auto", "role": "user", "content": "hi", "attachments": None, "files": None, "tools": None}
        ]
        assert harness.agent.sync_poll.call_args.args == ("req_abc",)
        # No direct POST /v2/agents/{id}/run.
        harness.ctx.client.request.assert_not_called()
        assert result.session_id == "sess_auto"
        assert result.data.session_id == "sess_auto"
        assert result.request_id == "req_abc"

    def test_each_run_gets_its_own_session(self):
        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))

        harness.agent.run("one")
        harness.agent.run("two")

        assert len(harness.created) == 2
        assert harness.created[0] is not harness.created[1]

    def test_overrides_go_into_the_new_sessions_config_without_a_warning(self):
        import warnings

        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))

        with warnings.catch_warnings():
            warnings.simplefilter("error")  # the "updating the stored executionConfig" warning must not fire
            harness.agent.run("hi", execution_params={"output_format": "markdown"}, criteria="be brief")

        config = harness.created[0].execution_config
        assert isinstance(config, ExecutionConfig)
        assert config.criteria == "be brief"
        assert config.to_api_dict()["executionParams"]["outputFormat"] == "markdown"

    def test_agent_budget_seeds_the_new_session(self):
        from aixplain import Budget

        harness = _AutoSessionHarness()
        harness.agent.budget = Budget(max_cost=1.5)
        harness.agent._update_saved_state()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))

        harness.agent.run("hi")

        assert harness.created[0].execution_config.budget.max_cost == 1.5

    def test_deprecated_max_iterations_folds_like_the_direct_path(self):
        from aixplain import Budget

        harness = _AutoSessionHarness()
        harness.agent.budget = Budget(max_iterations=9)
        harness.agent._update_saved_state()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))

        with pytest.warns(DeprecationWarning, match="max_iterations"), pytest.warns(UserWarning, match="precedence"):
            harness.agent.run("hi", execution_params={"max_iterations": 3, "max_tokens": 100})

        wire = harness.created[0].execution_config.to_api_dict()["executionParams"]
        assert wire["budget"]["maxIterations"] == 9  # the agent's budget wins, as on the direct path
        assert "maxIterations" not in wire and "max_iterations" not in wire
        assert wire["maxTokens"] == 100

    def test_identifier_reaches_the_new_sessions_config(self):
        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))

        harness.agent.run("hi", identifier="end-user-1")

        assert harness.created[0].execution_config.identifier == "end-user-1"

    def test_a_new_draft_agent_is_saved_before_its_session_is_created(self):
        harness = _AutoSessionHarness()
        agent = _bound_agent(harness.ctx)(name="Draft")
        order = []

        def fake_save(*args, **kwargs):
            order.append("agent.save")
            agent.id = "agent_new"

        agent.save = fake_save
        agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))
        harness.ctx.Session.save = lambda self, *a, **k: (order.append("session.save"), setattr(self, "id", "s"))[0]
        harness.ctx.Session.add_message = lambda self, role, content, **kw: _user_message()

        agent.run("hi")

        assert order == ["agent.save", "session.save"]

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"variables": {"persona": "x"}},
            {"history": [{"role": "user", "content": "earlier"}]},
            {"tasks": ["t"]},
            {"prompt": "p"},
            {"inspectors": []},
        ],
        ids=["variables", "history", "tasks", "prompt", "inspectors"],
    )
    def test_kwargs_the_session_endpoint_cannot_carry_keep_the_direct_path(self, kwargs):
        harness = _AutoSessionHarness()
        harness.ctx.client.request.return_value = {"status": "SUCCESS", "completed": True, "data": {"output": "ok"}}

        harness.agent.run("hi", **kwargs)

        assert harness.created == []
        post_call = harness.ctx.client.request.call_args_list[0]
        assert post_call.args[0] == "post"
        assert "v2/agents/agent_99/run" in post_call.args[1]

    def test_a_dict_query_keeps_the_direct_path(self):
        harness = _AutoSessionHarness()
        harness.ctx.client.request.return_value = {"status": "SUCCESS", "completed": True, "data": {"output": "ok"}}

        harness.agent.run({"input": "hi"})

        assert harness.created == []
        assert "v2/agents/agent_99/run" in harness.ctx.client.request.call_args_list[0].args[1]


class TestSessionPathRunsTheAfterRunHook:
    """``after_run`` keeps its direct-path contract now that every run goes through a session."""

    def test_after_run_may_substitute_a_successful_result(self):
        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))
        substitute = AgentRunResult.from_dict(_success_result())
        harness.agent.after_run = lambda result, *a, **k: substitute

        assert harness.agent.run("hi") is substitute

    def test_after_run_sees_a_failure_but_cannot_swallow_it(self):
        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(side_effect=RuntimeError("boom"))
        seen = []

        def after_run(result, *a, **k):
            seen.append(result)
            return AgentRunResult.from_dict(_success_result())

        harness.agent.after_run = after_run

        with pytest.raises(RuntimeError, match="boom"):
            harness.agent.run("hi")
        assert len(seen) == 1 and isinstance(seen[0], RuntimeError)

    def test_run_async_after_run_sees_a_failed_submission(self):
        harness = _AutoSessionHarness()
        harness.ctx.Session.add_message = Mock(side_effect=RuntimeError("post failed"))
        seen = []
        harness.agent.after_run = lambda result, *a, **k: seen.append(result)

        with pytest.raises(RuntimeError, match="post failed"):
            harness.agent.run_async("hi")
        assert len(seen) == 1 and isinstance(seen[0], RuntimeError)


class TestExplicitSessionRunsBeginRun:
    """``session=`` runs go through ``before_run`` too, as the direct path does (BUG-1457)."""

    def test_an_onboarded_agent_with_local_edits_raises_before_posting(self):
        from aixplain.v2 import AssetStatus

        harness = _AutoSessionHarness()
        harness.agent.status = AssetStatus.ONBOARDED
        harness.agent._update_saved_state()
        harness.agent.instructions = "edited locally, not saved"
        # Without the guard the run would reach the poll; keep that fast so a regression fails, not hangs.
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))
        session = harness.ctx.Session(agent_id="agent_99")
        session.id = "sess_given"

        with pytest.raises(ValueError, match="onboarded and cannot be modified"):
            harness.agent.run("hi", session=session)

        assert harness.posted == []

    def test_an_edited_draft_is_saved_before_the_message_is_posted(self):
        harness = _AutoSessionHarness()
        agent = harness.agent
        agent.instructions = "edited draft"
        order = []
        agent.save = lambda *a, **k: order.append("agent.save")
        harness.ctx.Session.add_message = lambda self, role, content, **kw: (
            order.append("message"),
            _user_message(),
        )[1]
        agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))
        session = harness.ctx.Session(agent_id="agent_99")
        session.id = "sess_given"

        agent.run("hi", session=session)

        assert order == ["agent.save", "message"]


# ---------------------------------------------------------------------------
# 9. On the wire: the end user as x-user-id, and run_retries on both POSTs
# ---------------------------------------------------------------------------


class _WireHarness:
    """A real Session over a recording ``client.request``, so headers and retries are visible.

    ``fail`` queues exceptions per POST: ``{"sessions": [...], "messages": [...]}``.
    Each queued exception is raised once, in order, before that POST succeeds.
    """

    def __init__(self, fail=None):
        from aixplain import AgentRunResult

        self.ctx = _make_mock_context()
        self.calls = []
        self.fail = {key: list(errors) for key, errors in (fail or {}).items()}

        class BoundSession(Session):
            context = self.ctx

        def request(method, path, **kwargs):
            self.calls.append((method, path, kwargs))
            key = "messages" if path.endswith("/messages") else "sessions"
            queued = self.fail.get(key)
            if method == "post" and queued:
                raise queued.pop(0)
            if key == "messages":
                return {
                    "id": "msg_user",
                    "sessionId": "sess_wire",
                    "userId": "u1",
                    "agentId": "agent_99",
                    "role": "user",
                    "content": "hi",
                    "sequence": 1,
                    "requestId": "req_abc",
                    "createdAt": "2025-06-01T10:01:00Z",
                }
            return {"id": "sess_wire", "agentId": "agent_99", "status": "active"}

        self.ctx.client.request.side_effect = request
        self.ctx.Session = BoundSession
        self.agent = _bound_agent(self.ctx)(id="agent_99", name="A")
        self.agent._update_saved_state()
        self.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result(session_id="sess_wire")))

    def posts(self, kind):
        """The POSTs to ``v1/sessions`` (``kind="sessions"``) or to ``.../messages``."""
        return [
            (path, kwargs)
            for method, path, kwargs in self.calls
            if method == "post" and path.endswith("/messages") == (kind == "messages")
        ]


class TestEndUserIsSentAsXUserId:
    """The backend scopes a session to the end user only through ``x-user-id`` on create.

    Without it the session is visible to every caller on the team. The direct
    path sent ``identifier`` as ``x-user-id`` on the run; the session path sends it
    on the session create and on the message (per-user rate limits).
    """

    def test_identifier_is_sent_on_the_create_and_the_message(self):
        harness = _WireHarness()

        harness.agent.run("hi", identifier="end-user-1")

        ((create_path, create_kwargs),) = harness.posts("sessions")
        ((_, message_kwargs),) = harness.posts("messages")
        assert create_path == "v1/sessions"
        assert create_kwargs["headers"] == {"x-user-id": "end-user-1"}
        assert create_kwargs["json"]["executionConfig"]["identifier"] == "end-user-1"
        assert message_kwargs["headers"] == {"x-user-id": "end-user-1"}

    def test_without_identifier_no_header_is_sent(self):
        harness = _WireHarness()

        harness.agent.run("hi")

        ((_, create_kwargs),) = harness.posts("sessions")
        ((_, message_kwargs),) = harness.posts("messages")
        assert "headers" not in create_kwargs
        assert "headers" not in message_kwargs

    def test_run_async_sends_it_too(self):
        harness = _WireHarness()

        harness.agent.run_async("hi", identifier="end-user-1")

        assert harness.posts("sessions")[0][1]["headers"] == {"x-user-id": "end-user-1"}
        assert harness.posts("messages")[0][1]["headers"] == {"x-user-id": "end-user-1"}

    def test_a_given_session_gets_it_on_the_message_and_is_left_unbound(self):
        harness = _WireHarness()
        session = harness.ctx.Session(agent_id="agent_99")
        session.id = "sess_given"
        session._update_saved_state()

        harness.agent.run("hi", session=session, identifier="end-user-1")

        assert harness.posts("sessions") == []  # the given session is used
        assert harness.posts("messages")[0][1]["headers"] == {"x-user-id": "end-user-1"}
        # The executionConfig update is not scoped by the header: the given
        # session may have been created without one, and a scoped PUT would miss it.
        puts = [kwargs for method, _, kwargs in harness.calls if method == "put"]
        assert puts and all("headers" not in kwargs for kwargs in puts)
        assert session._end_user_id is None  # the caller's object is not changed

    def test_a_non_ascii_identifier_raises_before_anything_is_sent(self):
        harness = _WireHarness()

        with pytest.raises(ValueError, match="x-user-id"):
            harness.agent.run("hi", identifier="Ürün")

        assert harness.calls == []


class TestRunRetriesOnTheSessionPath:
    """``run_retries`` covers the session create and the message POST, as it covers the direct run POST."""

    @staticmethod
    def _unavailable():
        from aixplain import APIError

        return APIError("busy", status_code=503)

    def test_a_failed_session_create_is_retried(self):
        harness = _WireHarness(fail={"sessions": [self._unavailable()]})

        with patch("aixplain.v2.agent.sleep_with_jitter") as sleep:
            result = harness.agent.run("hi", run_retries=2, run_retry_wait=0)

        assert len(harness.posts("sessions")) == 2
        assert len(harness.posts("messages")) == 1
        assert sleep.call_count == 1
        assert result.session_id == "sess_wire"

    def test_a_failed_message_post_is_retried(self):
        harness = _WireHarness(fail={"messages": [self._unavailable()]})

        with patch("aixplain.v2.agent.sleep_with_jitter"):
            harness.agent.run("hi", run_retries=1, run_retry_wait=0)

        assert len(harness.posts("sessions")) == 1
        assert len(harness.posts("messages")) == 2

    def test_run_async_retries_too(self):
        harness = _WireHarness(fail={"messages": [self._unavailable()]})

        with patch("aixplain.v2.agent.sleep_with_jitter"):
            result = harness.agent.run_async("hi", run_retries=1, run_retry_wait=0)

        assert len(harness.posts("messages")) == 2
        assert result.request_id == "req_abc"

    def test_without_run_retries_nothing_is_resent(self):
        from aixplain import APIError

        harness = _WireHarness(fail={"messages": [self._unavailable()]})

        with pytest.raises(APIError):
            harness.agent.run("hi")

        assert len(harness.posts("messages")) == 1

    def test_a_non_retryable_error_is_not_retried(self):
        from aixplain import APIError

        harness = _WireHarness(fail={"messages": [APIError("bad request", status_code=400)]})

        with patch("aixplain.v2.agent.sleep_with_jitter") as sleep, pytest.raises(APIError):
            harness.agent.run("hi", run_retries=3, run_retry_wait=0)

        assert len(harness.posts("messages")) == 1
        sleep.assert_not_called()

    def test_retries_stop_at_the_limit(self):
        from aixplain import APIError, ResourceError

        harness = _WireHarness(fail={"sessions": [self._unavailable() for _ in range(5)]})

        with patch("aixplain.v2.agent.sleep_with_jitter"), pytest.raises(APIError) as raised:
            harness.agent.run("hi", run_retries=2, run_retry_wait=0)

        # The last attempt's APIError, not the ResourceError Session.save() wraps it in.
        assert raised.value.status_code == 503
        assert not isinstance(raised.value, ResourceError)
        assert len(harness.posts("sessions")) == 3  # 1 + run_retries
        assert harness.posts("messages") == []


class TestSessionPathRefusalsKeepTheAPIErrorContract:
    """A refused run raises an ``APIError`` with the platform's status, as on the direct path."""

    @pytest.mark.parametrize("status", [401, 403, 500])
    def test_a_refused_session_create_raises_the_api_error(self, status):
        from aixplain import APIError, ResourceError

        refusal = APIError("refused", status_code=status, error="err.refused")
        harness = _WireHarness(fail={"sessions": [refusal]})

        with pytest.raises(APIError) as raised:
            harness.agent.run("hi")

        assert raised.value is refusal
        assert not isinstance(raised.value, ResourceError)
        assert raised.value.__cause__ is None and raised.value.__suppress_context__
        assert harness.posts("messages") == []

    def test_run_async_raises_it_too(self):
        from aixplain import APIError

        harness = _WireHarness(fail={"sessions": [APIError("refused", status_code=401)]})

        with pytest.raises(APIError) as raised:
            harness.agent.run_async("hi")

        assert raised.value.status_code == 401

    def test_a_session_save_failure_without_an_api_error_is_left_alone(self):
        from aixplain import ResourceError

        harness = _WireHarness(fail={"sessions": [RuntimeError("socket closed")]})

        with pytest.raises(ResourceError, match="socket closed"):
            harness.agent.run("hi")

    def test_a_run_the_platform_did_not_start_raises_agent_run_not_started(self):
        from aixplain import AgentRunNotStartedError, APIError

        harness = _AutoSessionHarness()
        harness.ctx.Session.add_message = lambda self, role, content, **kw: _user_message(request_id=None)
        harness.agent.sync_poll = Mock()
        seen = []
        harness.agent.after_run = lambda result, *a, **k: seen.append(result)

        with pytest.raises(AgentRunNotStartedError, match="did not start the agent run") as raised:
            harness.agent.run("hi")

        error = raised.value
        assert isinstance(error, APIError) and isinstance(error, ValueError)
        assert error.retryable is False
        assert error.session_id == "sess_auto"
        harness.agent.sync_poll.assert_not_called()
        assert seen == [error]

    def test_it_is_not_retried(self):
        from aixplain import AgentRunNotStartedError

        harness = _AutoSessionHarness()
        posts = []
        harness.ctx.Session.add_message = lambda self, role, content, **kw: (
            posts.append(1),
            _user_message(request_id=None),
        )[1]

        with patch("aixplain.v2.agent.sleep_with_jitter"), pytest.raises(AgentRunNotStartedError):
            harness.agent.run_async("hi", run_retries=3, run_retry_wait=0)

        assert len(posts) == 1


class TestKwargsASessionRunDoesNotSend:
    """``session_id`` / ``agent_name`` and unknown kwargs keep the direct path, where they are sent."""

    @staticmethod
    def _direct_harness():
        harness = _AutoSessionHarness()
        harness.ctx.client.request.return_value = {"status": "SUCCESS", "completed": True, "data": {"output": "ok"}}
        # The direct run answers completed, so nothing polls; a session run would, so fail it fast.
        harness.agent.sync_poll = Mock(side_effect=AssertionError("the run took the session path"))
        return harness

    @staticmethod
    def _run_post(harness):
        method, url = harness.ctx.client.request.call_args_list[0].args[:2]
        assert (method, "v2/agents/agent_99/run" in url) == ("post", True)
        return harness.ctx.client.request.call_args_list[0].kwargs

    @pytest.mark.parametrize(
        ("kwarg", "header"),
        [("session_id", "x-session-id"), ("agent_name", "x-agent")],
        ids=["session_id", "agent_name"],
    )
    def test_header_kwargs_keep_the_direct_path_and_its_header(self, kwarg, header):
        harness = self._direct_harness()

        harness.agent.run("hi", **{kwarg: "corr-1"})

        assert harness.created == []
        assert self._run_post(harness)["headers"][header] == "corr-1"

    def test_run_async_keeps_them_on_the_direct_path_too(self):
        harness = self._direct_harness()
        harness.ctx.client.request.return_value = {
            "status": "IN_PROGRESS",
            "completed": False,
            "url": "https://platform-api.aixplain.com/sdk/agents/r/result",
        }

        harness.agent.run_async("hi", session_id="corr-1", agent_name="caller")

        assert harness.created == []
        assert self._run_post(harness)["headers"] == {"x-session-id": "corr-1", "x-agent": "caller"}

    def test_an_unknown_kwarg_keeps_the_direct_path_and_is_forwarded(self):
        harness = self._direct_harness()

        harness.agent.run("hi", custom_flag="on")

        assert harness.created == []
        assert self._run_post(harness)["json"]["custom_flag"] == "on"

    def test_sdk_control_kwargs_stay_on_the_session_path(self):
        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))

        harness.agent.run("hi", timeout=30, wait_time=1, run_retries=1, run_retry_wait=0, show_progress=False)

        assert len(harness.created) == 1
        harness.ctx.client.request.assert_not_called()

    def test_an_explicit_session_warns_that_they_are_not_sent(self):
        harness = _AutoSessionHarness()
        harness.agent.sync_poll = Mock(return_value=AgentRunResult.from_dict(_success_result()))
        session = harness.ctx.Session(agent_id="agent_99")
        session.id = "sess_given"

        with pytest.warns(UserWarning, match=r"\['agent_name', 'session_id'\] are not sent") as caught:
            harness.agent.run("hi", session=session, session_id="corr-1", agent_name="caller")

        assert caught[0].filename == __file__
        assert harness.posted[0]["session"] == "sess_given"
        harness.ctx.client.request.assert_not_called()


class TestSessionPathHookOrderMatchesTheDirectPath:
    """``before_run`` / ``after_run`` are called as ``RunnableResourceMixin.run`` / ``run_async`` call them."""

    def test_an_early_result_reaches_after_run_once_even_when_after_run_raises(self):
        harness = _AutoSessionHarness()
        early = AgentRunResult.from_dict(_success_result())
        harness.agent.before_run = lambda *a, **k: early
        calls = []

        def after_run(result, *a, **k):
            calls.append(result)
            raise RuntimeError("after_run failed")

        harness.agent.after_run = after_run

        with pytest.raises(RuntimeError, match="after_run failed"):
            harness.agent.run("hi")

        assert calls == [early]
        assert harness.created == []

    @pytest.mark.parametrize("method", ["run", "run_async"])
    def test_a_raising_before_run_does_not_reach_after_run(self, method):
        harness = _AutoSessionHarness()

        def before_run(*a, **k):
            raise RuntimeError("before_run failed")

        harness.agent.before_run = before_run
        seen = []
        harness.agent.after_run = lambda result, *a, **k: seen.append(result)

        with pytest.raises(RuntimeError, match="before_run failed"):
            getattr(harness.agent, method)("hi")

        assert seen == []
        assert harness.created == []

    def test_run_async_returns_an_early_result_without_after_run(self):
        harness = _AutoSessionHarness()
        early = AgentRunResult.from_dict(_success_result())
        harness.agent.before_run = lambda *a, **k: early
        seen = []
        harness.agent.after_run = lambda result, *a, **k: seen.append(result)

        assert harness.agent.run_async("hi") is early
        assert seen == []


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

    def test_a_sessionless_run_waits_for_the_agents_budget(self):
        """The session created for a run carries the agent's budget, so the poll waits for it (ENG-3845)."""
        from aixplain import Budget

        harness = _AutoSessionHarness()
        harness.agent.budget = Budget(max_duration_seconds=900)
        harness.agent._update_saved_state()

        with patch.object(Agent, "sync_poll", return_value=AgentRunResult.from_dict(_success_result())) as poll:
            harness.agent.run("hi")

        assert len(harness.created) == 1
        assert poll.call_args.kwargs["timeout"] == 900 + Agent._POLL_TIMEOUT_ALLOWANCE_SECONDS

    def test_an_explicit_timeout_still_wins(self):
        harness = _AutoSessionHarness()

        with patch.object(Agent, "sync_poll", return_value=AgentRunResult.from_dict(_success_result())) as poll:
            harness.agent.run("hi", timeout=42)

        assert poll.call_args.kwargs["timeout"] == 42
