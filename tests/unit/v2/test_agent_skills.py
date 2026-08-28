"""Tests for Skill references on v2 Agents."""

from unittest.mock import Mock

import pytest

from aixplain import Aixplain


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def test_replacing_fetched_agent_skills_changes_save_payload(aix):
    """Use the current public skills list instead of its construction-time snapshot."""
    agent = aix.Agent(
        id="agent-id",
        name="skill-agent",
        skills=[{"id": "original-id", "name": "Original", "type": "skill"}],
    )

    agent.skills = ["replacement-id"]

    assert agent.build_save_payload()["skills"] == [
        {"id": "replacement-id", "type": "skill", "assetId": "replacement-id"}
    ]


def test_appending_skill_object_changes_save_payload(aix):
    """Honor in-place additions to the public skills list."""
    original = aix.Skill(id="original-id", name="Original")
    added = aix.Skill(id="added-id", name="Added")
    agent = aix.Agent(id="agent-id", name="skill-agent", skills=[original])

    agent.skills.append(added)

    assert [skill["id"] for skill in agent.build_save_payload()["skills"]] == ["original-id", "added-id"]
    assert agent.skills == ["original-id", "added-id"]


def test_clearing_agent_skills_emits_empty_list(aix):
    """Allow callers to detach all skills on save."""
    agent = aix.Agent(id="agent-id", name="skill-agent", skills=["original-id"])

    agent.skills.clear()

    assert agent.build_save_payload()["skills"] == []


def test_save_subcomponents_uses_newly_assigned_skill(aix):
    """Recursively save an unsaved Skill assigned after Agent construction."""
    skill = aix.Skill(name="New Skill")
    skill.save = Mock(side_effect=lambda: setattr(skill, "id", "new-skill-id") or skill)
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "skill-agent", "skills": []})
    agent = aix.Agent(name="skill-agent")
    agent.skills = [skill]

    agent.save(save_subcomponents=True)

    skill.save.assert_called_once_with()
    request_payload = aix.client.request.call_args.kwargs["json"]
    assert request_payload["skills"][0]["id"] == "new-skill-id"
