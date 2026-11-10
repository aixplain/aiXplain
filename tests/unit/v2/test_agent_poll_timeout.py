"""Unit tests for how long ``Agent.run()`` / ``sync_poll`` wait for a run.

Without a caller ``timeout`` the poll used to stop at a flat 300s, while the
backend lets a run last as long as its ``budget.maxDurationSeconds`` (600s by
default). The poll now waits for the duration the backend will resolve plus an
allowance for queueing, setup and result delivery (ENG-3845).
"""

from unittest.mock import MagicMock, patch

from aixplain import Agent, ExecutionConfig
from aixplain.v2.resource import RunnableResourceMixin

ALLOWANCE = Agent._POLL_TIMEOUT_ALLOWANCE_SECONDS
SERVER_DEFAULT = Agent._SERVER_DEFAULT_MAX_DURATION_SECONDS


def _agent(budget=None):
    agent = Agent.from_dict({"id": "agent-123", "name": "test-agent"})
    agent.context = MagicMock()
    agent.context.backend_url = "https://platform-api.aixplain.com"
    if budget is not None:
        agent.budget = budget
    return agent


class TestDefaultPollTimeout:
    def test_caller_timeout_wins(self):
        agent = _agent({"max_duration_seconds": 900})
        assert agent._default_poll_timeout({"timeout": 42}) == 42

    def test_server_default_when_nothing_sets_a_duration(self):
        assert _agent()._default_poll_timeout({}) == SERVER_DEFAULT + ALLOWANCE

    def test_agent_budget_duration(self):
        assert _agent({"max_duration_seconds": 900})._default_poll_timeout({}) == 900 + ALLOWANCE

    def test_run_max_time_when_no_budget(self):
        timeout = _agent()._default_poll_timeout({"execution_params": {"max_time": 1200}})
        assert timeout == 1200 + ALLOWANCE

    def test_agent_budget_outranks_run_max_time(self):
        agent = _agent({"max_duration_seconds": 900})
        assert agent._default_poll_timeout({"execution_params": {"maxTime": 120}}) == 900 + ALLOWANCE

    def test_session_budget_outranks_agent_budget(self):
        agent = _agent({"max_duration_seconds": 900})
        config = ExecutionConfig(budget={"max_duration_seconds": 1500})
        assert agent._default_poll_timeout({}, config) == 1500 + ALLOWANCE

    def test_session_max_time_outranks_agent_budget(self):
        agent = _agent({"max_duration_seconds": 900})
        config = ExecutionConfig(execution_params={"maxTime": 450})
        assert agent._default_poll_timeout({}, config) == 450 + ALLOWANCE

    def test_session_without_duration_falls_back_to_agent_budget(self):
        agent = _agent({"max_duration_seconds": 900})
        assert agent._default_poll_timeout({}, ExecutionConfig()) == 900 + ALLOWANCE

    def test_ignores_non_positive_and_boolean_values(self):
        agent = _agent()
        params = {"execution_params": {"max_time": True}}
        assert agent._default_poll_timeout(params) == SERVER_DEFAULT + ALLOWANCE
        assert agent._default_poll_timeout({"execution_params": {"max_time": 0}}) == SERVER_DEFAULT + ALLOWANCE


class TestSyncPollUsesDerivedTimeout:
    def test_standalone_sync_poll_waits_for_the_agent_budget(self):
        agent = _agent({"max_duration_seconds": 900})
        with patch.object(RunnableResourceMixin, "sync_poll", return_value=MagicMock()) as base:
            agent.sync_poll("exec-1")
        assert base.call_args.kwargs["timeout"] == 900 + ALLOWANCE

    def test_standalone_sync_poll_keeps_a_caller_timeout(self):
        agent = _agent({"max_duration_seconds": 900})
        with patch.object(RunnableResourceMixin, "sync_poll", return_value=MagicMock()) as base:
            agent.sync_poll("exec-1", timeout=30)
        assert base.call_args.kwargs["timeout"] == 30

    def test_run_poll_uses_the_run_max_time(self):
        agent = _agent()
        with patch.object(RunnableResourceMixin, "sync_poll", return_value=MagicMock()) as base:
            agent.sync_poll("exec-1", execution_params={"max_time": 1200}, _progress_tracker=None)
        assert base.call_args.kwargs["timeout"] == 1200 + ALLOWANCE
