import pytest
import time
import uuid


def _agent_ids(agents) -> list:
    """Ids of a team's ``agents``, which may hold id strings, dicts or ``Agent`` objects."""
    ids = []
    for agent in agents or []:
        if isinstance(agent, str):
            ids.append(agent)
        elif isinstance(agent, dict):
            ids.append(agent.get("id"))
        else:
            ids.append(getattr(agent, "id", None))
    return [agent_id for agent_id in ids if agent_id]


@pytest.fixture(scope="module")
def source_agent(client, module_resource_tracker):
    """Create a source agent to duplicate from, cleaned up after all tests."""
    agent = client.Agent(
        name=f"Dup Source {int(time.time())}-{uuid.uuid4().hex[:6]}",
        description="Agent created as a source for duplicate functional tests",
        instructions="You are a helpful assistant for duplication testing.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


class TestAgentDuplicate:
    def test_duplicate_default(self, client, source_agent, resource_tracker):
        """Duplicate an agent with default settings (no subagent cloning, auto name)."""
        duplicated = source_agent.duplicate()
        resource_tracker.append(duplicated)

        assert duplicated.id is not None
        assert isinstance(duplicated.id, str)
        assert duplicated.id != source_agent.id

        assert duplicated.name is not None
        assert duplicated.name != ""

        assert duplicated.description == source_agent.description
        assert duplicated.instructions == source_agent.instructions

    def test_duplicate_is_retrievable(self, client, source_agent, resource_tracker):
        """The duplicated agent should be retrievable via get()."""
        duplicated = source_agent.duplicate()
        resource_tracker.append(duplicated)

        retrieved = client.Agent.get(duplicated.id)
        assert retrieved.id == duplicated.id
        assert retrieved.name == duplicated.name
        assert retrieved.description == duplicated.description
        assert retrieved.instructions == duplicated.instructions

    def test_duplicate_is_independent(self, client, source_agent, resource_tracker):
        """Modifying the duplicate should not affect the original."""
        duplicated = source_agent.duplicate()
        resource_tracker.append(duplicated)

        original_description = source_agent.description
        duplicated.description = "Modified description on duplicate"
        duplicated.save(as_draft=True)

        refetched_source = client.Agent.get(source_agent.id)
        assert refetched_source.description == original_description

    def test_duplicate_auto_generates_unique_name(self, client, source_agent, resource_tracker):
        """The platform should auto-generate a unique name for the duplicate."""
        dup1 = source_agent.duplicate()
        resource_tracker.append(dup1)
        dup2 = source_agent.duplicate()
        resource_tracker.append(dup2)

        assert dup1.name != dup2.name, "Each duplicate should get a unique auto-generated name"


class TestAgentDuplicateWithSubagents:
    @pytest.fixture(scope="class")
    def team_agent(self, client, module_resource_tracker):
        """Create a team agent (agent with subagents) for testing duplicate_subagents."""
        sub = client.Agent(
            name=f"Sub for Dup {int(time.time())}-{uuid.uuid4().hex[:6]}",
            description="A subagent used to test duplicate_subagents",
            instructions="You are a subagent.",
        )
        sub.save()
        module_resource_tracker.append(sub)

        team = client.Agent(
            name=f"Team for Dup {int(time.time())}-{uuid.uuid4().hex[:6]}",
            description="A team agent with subagents for duplicate testing",
            instructions="You orchestrate subagents.",
            agents=[sub],
        )
        team.save()
        module_resource_tracker.append(team)

        return team, sub

    def test_duplicate_keep_references(self, client, team_agent, resource_tracker):
        """Duplicate a team agent keeping references to original subagents."""
        team, sub = team_agent
        duplicated = team.duplicate(duplicate_subagents=False)
        resource_tracker.append(duplicated)

        assert duplicated.id is not None
        assert duplicated.id != team.id
        assert _agent_ids(duplicated.agents) == [sub.id], (
            f"Expected the duplicate to reference the original subagent {sub.id}, got {duplicated.agents}"
        )

    def test_duplicate_subagents(self, client, team_agent, resource_tracker):
        """Duplicate a team agent with independent copies of subagents."""
        team, sub = team_agent
        duplicated = team.duplicate(duplicate_subagents=True)
        resource_tracker.append(duplicated)

        # The copies are new agents: register each *before* the team that uses
        # them, so newest-first teardown deletes the team first.
        copied_ids = _agent_ids(duplicated.agents)
        for copied_id in copied_ids:
            if copied_id != sub.id:
                resource_tracker.insert(resource_tracker.index(duplicated), client.Agent.get(copied_id))

        assert duplicated.id is not None
        assert duplicated.id != team.id
        assert len(copied_ids) == 1, f"Expected one copied subagent, got {duplicated.agents}"
        assert copied_ids[0] != sub.id, "With duplicate_subagents=True, the subagent should be a new copy"
