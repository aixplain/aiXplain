"""Guard: the team-agent tasks/tools invariant is deliberately *not* enforced.

``Agent._sync_file_references`` carried a commented-out check for eight months::

    # TODO: Re-enable this validation after backend data consistency is fixed
    # if self.agents and (self.tasks or self.tools):
    #     raise ValueError(
    #         "Team agents cannot have tasks or tools. ..."
    #     )

It was disabled inside an unrelated 88-file commit, no replacement exists
anywhere, and v1 never had it either (BUG-946). Re-enabling it as written is not
safe: ``_sync_file_references`` sits on the run and payload-build paths as well
as save, and it would fire for team agents *hydrated from the backend* -- which
is precisely the inconsistency the TODO was deferring.

So the comment is gone and the non-enforcement is now an explicit, tested
decision rather than an accident. Anyone re-introducing the invariant has to
consciously change these tests, and the backend follow-up is tracked on the PR.
"""

import pytest

from aixplain import Aixplain


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def _team_agent_with_everything(aix):
    """A team agent carrying sub-agents *and* tools *and* tasks."""
    return aix.Agent(
        name="team-agent",
        instructions="Coordinate the sub-agents.",
        agents=["sub-agent-id"],
        tools=[{"id": "tool-id", "type": "model"}],
        tasks=[{"name": "summarize", "description": "Summarize", "expectedOutput": "A summary"}],
    )


def test_team_agent_with_tools_and_tasks_constructs(aix):
    """Construction must not raise for the combination."""
    agent = _team_agent_with_everything(aix)

    assert agent.agents == ["sub-agent-id"]
    assert agent.tools
    assert agent.tasks


def test_team_agent_with_tools_and_tasks_builds_a_payload(aix):
    """``build_save_payload`` runs ``_sync_file_references``; it must not raise.

    This is the call the invariant would have broken, and it must keep emitting
    both collections.
    """
    payload = _team_agent_with_everything(aix).build_save_payload()

    assert payload["agents"]
    assert payload["tools"]


def test_backend_team_agent_with_tools_hydrates(aix):
    """Loading an existing, inconsistent team agent must keep working.

    ``Agent.from_dict`` is the ``get()`` path. Raising here would make already
    stored team agents unloadable -- the reason the guard was disabled.
    """
    agent = aix.Agent.from_dict(
        {
            "id": "team-agent-id",
            "name": "team-agent",
            "description": "A team agent",
            "role": "Coordinate the sub-agents.",
            "agents": ["sub-agent-id"],
            "tools": [{"id": "tool-id", "type": "model"}],
            "tasks": [{"name": "summarize", "description": "Summarize", "expectedOutput": "A summary"}],
        }
    )

    assert agent.agents == ["sub-agent-id"]
    assert agent.tools
    assert agent.build_save_payload()["tools"]


def test_stale_invariant_comment_is_gone():
    """The dead TODO must not come back as a comment instead of a decision."""
    from pathlib import Path

    source = Path(__file__).resolve().parents[3] / "aixplain" / "v2" / "agent.py"
    text = source.read_text()

    assert "Re-enable this validation" not in text
    assert "Team agents cannot have tasks or tools" not in text
