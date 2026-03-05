"""Tests for V2 Agent.duplicate() method."""

import pytest
from unittest.mock import patch, Mock, MagicMock
from dataclasses import dataclass

from aixplain.v2.agent import Agent
from aixplain.v2.enums import AssetStatus
from aixplain.v2.resource import ValidationError


DUPLICATE_RESPONSE = {
    "id": "duplicated-agent-456",
    "name": "Test Agent (Copy)",
    "description": "Test Agent Description",
    "instructions": "Test Agent Instructions",
    "teamId": 123,
    "status": "draft",
    "llmId": "6895d6d1d50c89537c1cf237",
    "clonedFromId": "original-agent-123",
    "tools": [],
    "assets": [],
    "tasks": [],
    "agents": [],
    "outputFormat": "text",
    "expectedOutput": "",
    "createdAt": "2026-03-05T14:53:00.625Z",
    "updatedAt": "2026-03-05T14:53:00.625Z",
    "inspectorTargets": [],
    "maxInspectors": 5,
    "maxIterations": 5,
    "maxTokens": 2048,
    "inspectors": [],
}


def _make_agent(agent_id="original-agent-123", name="Test Agent"):
    """Create a test Agent with mocked context."""
    agent = Agent.from_dict(
        {
            "id": agent_id,
            "name": name,
            "description": "Test Agent Description",
            "instructions": "Test Agent Instructions",
            "status": "onboarded",
            "teamId": 123,
            "llmId": "6895d6d1d50c89537c1cf237",
            "tools": [],
            "tasks": [],
            "agents": [],
            "outputFormat": "text",
            "expectedOutput": "",
            "inspectorTargets": [],
            "inspectors": [],
            "maxIterations": 5,
            "maxTokens": 2048,
        }
    )
    mock_context = MagicMock()
    agent.context = mock_context
    agent._update_saved_state()
    return agent


class TestAgentDuplicate:
    def test_duplicate_success(self):
        agent = _make_agent()
        agent.context.client.request.return_value = DUPLICATE_RESPONSE

        duplicated = agent.duplicate()

        assert duplicated.id == "duplicated-agent-456"
        assert duplicated.name == "Test Agent (Copy)"
        assert duplicated.description == "Test Agent Description"
        assert duplicated.id != agent.id
        assert duplicated.context is agent.context

    def test_duplicate_sends_correct_payload(self):
        agent = _make_agent()
        agent.context.client.request.return_value = DUPLICATE_RESPONSE

        agent.duplicate()

        agent.context.client.request.assert_called_once()
        call_args = agent.context.client.request.call_args
        assert call_args[0][0] == "post"
        assert call_args[0][1].endswith("/duplicate")
        assert call_args[1]["json"]["cloneSubagents"] is False
        assert call_args[1]["json"]["name"] is False

    def test_duplicate_with_clone_subagents(self):
        agent = _make_agent()
        agent.context.client.request.return_value = DUPLICATE_RESPONSE

        agent.duplicate(clone_subagents=True)

        call_args = agent.context.client.request.call_args
        assert call_args[1]["json"]["cloneSubagents"] is True

    def test_duplicate_with_custom_name(self):
        agent = _make_agent()
        custom_response = {**DUPLICATE_RESPONSE, "name": "My Custom Agent"}
        agent.context.client.request.return_value = custom_response

        duplicated = agent.duplicate(name="My Custom Agent")

        call_args = agent.context.client.request.call_args
        assert call_args[1]["json"]["name"] == "My Custom Agent"
        assert duplicated.name == "My Custom Agent"

    def test_duplicate_unsaved_agent_raises(self):
        agent = Agent.from_dict(
            {
                "id": None,
                "name": "Unsaved Agent",
                "description": "Not saved yet",
                "status": "draft",
                "tools": [],
                "tasks": [],
                "agents": [],
                "outputFormat": "text",
                "inspectorTargets": [],
                "inspectors": [],
            }
        )
        mock_context = MagicMock()
        agent.context = mock_context

        with pytest.raises(ValidationError):
            agent.duplicate()

    def test_duplicate_returns_independent_instance(self):
        agent = _make_agent()
        agent.context.client.request.return_value = DUPLICATE_RESPONSE

        duplicated = agent.duplicate()

        assert duplicated is not agent
        assert duplicated.id != agent.id

    def test_duplicate_preserves_instructions(self):
        agent = _make_agent()
        response_with_instructions = {
            **DUPLICATE_RESPONSE,
            "instructions": "Specific instructions",
        }
        agent.context.client.request.return_value = response_with_instructions

        duplicated = agent.duplicate()

        assert duplicated.instructions == "Specific instructions"

    def test_duplicate_with_subagents_in_response(self):
        agent = _make_agent()
        response_with_subagents = {
            **DUPLICATE_RESPONSE,
            "agents": [
                {"id": "subagent-1", "type": "AGENT"},
                {"id": "subagent-2", "type": "AGENT"},
            ],
        }
        agent.context.client.request.return_value = response_with_subagents

        duplicated = agent.duplicate(clone_subagents=True)

        assert len(duplicated.subagents) == 2
