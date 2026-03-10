"""Unit tests for Agent poll URL resolution and AgentRunResult.execution_id.

These tests verify that:
- Agent.poll() and Agent.sync_poll() accept both full URLs and bare execution IDs.
- AgentRunResult.execution_id extracts the ID from the poll URL or request_id.
- The correct /sdk/agents/{id}/result endpoint is constructed (NOT /sdk/runs/{id}).
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from aixplain.v2.agent import Agent, AgentRunResult


BACKEND_URL = "https://platform-api.aixplain.com"


def _create_agent():
    """Create an Agent instance with mocked context."""

    @dataclass_json
    @dataclass
    class BoundAgent(Agent):
        pass

    agent = BoundAgent(id="agent-123", name="test-agent")
    agent.context = Mock()
    agent.context.backend_url = BACKEND_URL
    return agent


class TestAgentRunResultExecutionId:
    """Tests for AgentRunResult.execution_id property."""

    def test_execution_id_from_request_id(self):
        """Should return request_id directly when available."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id="direct-request-id-123",
            url="https://example.com/sdk/agents/url-id/result",
        )

        assert result.execution_id == "direct-request-id-123"

    def test_execution_id_from_url_uuid(self):
        """Should extract UUID execution ID from poll URL."""
        result = AgentRunResult(
            status="IN_PROGRESS",
            completed=False,
            request_id=None,
            url=f"{BACKEND_URL}/sdk/agents/a1b2c3d4-e5f6-7890-abcd-ef1234567890/result",
        )

        assert result.execution_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    def test_execution_id_from_url_non_uuid(self):
        """Should extract non-UUID execution ID from poll URL."""
        result = AgentRunResult(
            status="IN_PROGRESS",
            completed=False,
            request_id=None,
            url=f"{BACKEND_URL}/sdk/agents/simple-id-123/result",
        )

        assert result.execution_id == "simple-id-123"

    def test_execution_id_none_when_no_data(self):
        """Should return None when neither request_id nor URL is available."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id=None,
            url=None,
        )

        assert result.execution_id is None

    def test_execution_id_none_for_non_matching_url(self):
        """Should return None when URL doesn't match /sdk/agents/{id}/ pattern."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id=None,
            url="https://example.com/some/other/path",
        )

        assert result.execution_id is None

    def test_execution_id_prefers_request_id(self):
        """Should prefer request_id over URL extraction."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id="request-id-wins",
            url=f"{BACKEND_URL}/sdk/agents/url-id-loses/result",
        )

        assert result.execution_id == "request-id-wins"


class TestAgentResolvePollUrl:
    """Tests for Agent._resolve_poll_url method."""

    def test_full_url_passed_through(self):
        """Full HTTP(S) URLs should be returned unchanged."""
        agent = _create_agent()
        url = f"{BACKEND_URL}/sdk/agents/exec-id-1/result"

        assert agent._resolve_poll_url(url) == url

    def test_execution_id_builds_correct_url(self):
        """Bare execution ID should be expanded to /sdk/agents/{id}/result."""
        agent = _create_agent()

        resolved = agent._resolve_poll_url("exec-id-1")

        assert resolved == f"{BACKEND_URL}/sdk/agents/exec-id-1/result"

    def test_uuid_execution_id(self):
        """UUID-style execution ID should be expanded correctly."""
        agent = _create_agent()

        resolved = agent._resolve_poll_url("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

        assert resolved == f"{BACKEND_URL}/sdk/agents/a1b2c3d4-e5f6-7890-abcd-ef1234567890/result"

    def test_trailing_slash_on_backend_url(self):
        """Backend URL with trailing slash should not cause double slash."""
        agent = _create_agent()
        agent.context.backend_url = f"{BACKEND_URL}/"

        resolved = agent._resolve_poll_url("exec-id-1")

        assert resolved == f"{BACKEND_URL}/sdk/agents/exec-id-1/result"
        assert "//" not in resolved.replace("https://", "")

    def test_empty_poll_url_raises(self):
        """Empty poll_url should raise ValueError (would produce sdk/agents//result)."""
        agent = _create_agent()

        with pytest.raises(ValueError, match="poll_url must be a full URL or non-empty execution ID"):
            agent._resolve_poll_url("")


class TestAgentPollWithExecutionId:
    """Tests for Agent.poll() accepting execution IDs."""

    def test_poll_with_full_url(self):
        """poll() with a full URL should forward it to the base implementation."""
        agent = _create_agent()
        full_url = f"{BACKEND_URL}/sdk/agents/exec-id-1/result"
        agent.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": {},
            }
        )

        agent.poll(full_url)

        agent.context.client.get.assert_called_once_with(full_url)

    def test_poll_with_execution_id(self):
        """poll() with a bare execution ID should construct the correct URL."""
        agent = _create_agent()
        agent.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": {},
            }
        )

        agent.poll("exec-id-1")

        expected_url = f"{BACKEND_URL}/sdk/agents/exec-id-1/result"
        agent.context.client.get.assert_called_once_with(expected_url)

    def test_poll_does_not_use_sdk_runs_endpoint(self):
        """poll() must NOT construct /sdk/runs/{id} (that endpoint returns 404)."""
        agent = _create_agent()
        agent.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": {},
            }
        )

        agent.poll("exec-id-1")

        actual_url = agent.context.client.get.call_args[0][0]
        assert "/sdk/runs/" not in actual_url
        assert "/sdk/agents/" in actual_url


class TestAgentSyncPollWithExecutionId:
    """Tests for Agent.sync_poll() accepting execution IDs."""

    def test_sync_poll_with_full_url(self):
        """sync_poll() with a full URL should forward it unchanged."""
        agent = _create_agent()
        full_url = f"{BACKEND_URL}/sdk/agents/exec-id-1/result"
        agent.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": {},
            }
        )

        agent.sync_poll(full_url)

        agent.context.client.get.assert_called_once_with(full_url)

    def test_sync_poll_with_execution_id(self):
        """sync_poll() with a bare execution ID should construct the correct URL."""
        agent = _create_agent()
        agent.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": {},
            }
        )

        agent.sync_poll("exec-id-1")

        expected_url = f"{BACKEND_URL}/sdk/agents/exec-id-1/result"
        agent.context.client.get.assert_called_once_with(expected_url)

    def test_sync_poll_does_not_use_sdk_runs_endpoint(self):
        """sync_poll() must NOT use /sdk/runs/{id}."""
        agent = _create_agent()
        agent.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": {},
            }
        )

        agent.sync_poll("exec-id-1")

        actual_url = agent.context.client.get.call_args[0][0]
        assert "/sdk/runs/" not in actual_url
        assert "/sdk/agents/" in actual_url


class TestAgentPollUrlTemplate:
    """Tests for Agent.POLL_URL_TEMPLATE class attribute."""

    def test_template_uses_agents_path(self):
        """POLL_URL_TEMPLATE should use /sdk/agents/ not /sdk/runs/."""
        assert "sdk/agents/" in Agent.POLL_URL_TEMPLATE
        assert "sdk/runs/" not in Agent.POLL_URL_TEMPLATE

    def test_template_contains_execution_id_placeholder(self):
        """POLL_URL_TEMPLATE should contain {execution_id} placeholder."""
        assert "{execution_id}" in Agent.POLL_URL_TEMPLATE
