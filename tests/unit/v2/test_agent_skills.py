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


def test_agent_never_configured_with_skills_omits_the_key(aix):
    """An agent that never touched skills must not start sending skills=[]."""
    agent = aix.Agent(name="plain-agent", instructions="hi")

    assert "skills" not in agent.build_save_payload()


def test_unsaved_skill_survives_validation_then_list_append(aix):
    """Keep an unsaved Skill attached when the public list later changes length."""
    unsaved = aix.Skill(name="Unsaved One")
    saved = aix.Skill(id="saved-2", name="Two")
    agent = aix.Agent(name="skill-agent", instructions="hi", skills=[unsaved])

    with pytest.raises(ValueError, match="skill 'Unsaved One'.*saved before saving"):
        agent._validate_dependencies()

    agent.skills.append(saved)

    with pytest.raises(ValueError, match="All skills must be saved before saving the agent"):
        agent.build_save_payload()
    assert agent._original_skills == [unsaved, saved]


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
