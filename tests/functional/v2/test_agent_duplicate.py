import pytest
import time


@pytest.fixture(scope="module")
def source_agent(client):
    """Create a source agent to duplicate from, cleaned up after all tests."""
    agent = client.Agent(
        name=f"Dup Source {int(time.time())}",
        description="Agent created as a source for duplicate functional tests",
        instructions="You are a helpful assistant for duplication testing.",
    )
    agent.save()

    yield agent

    try:
        agent.delete()
    except Exception:
        pass


class TestAgentDuplicate:
    def test_duplicate_default(self, client, source_agent):
        """Duplicate an agent with default settings (no subagent cloning, auto name)."""
        duplicated = source_agent.duplicate()

        try:
            assert duplicated.id is not None
            assert isinstance(duplicated.id, str)
            assert duplicated.id != source_agent.id

            assert duplicated.name is not None
            assert duplicated.name != ""

            assert duplicated.description == source_agent.description
            assert duplicated.instructions == source_agent.instructions
        finally:
            try:
                duplicated.delete()
            except Exception:
                pass

    def test_duplicate_is_retrievable(self, client, source_agent):
        """The duplicated agent should be retrievable via get()."""
        duplicated = source_agent.duplicate()

        try:
            retrieved = client.Agent.get(duplicated.id)
            assert retrieved.id == duplicated.id
            assert retrieved.name == duplicated.name
            assert retrieved.description == duplicated.description
            assert retrieved.instructions == duplicated.instructions
        finally:
            try:
                duplicated.delete()
            except Exception:
                pass

    def test_duplicate_is_independent(self, client, source_agent):
        """Modifying the duplicate should not affect the original."""
        duplicated = source_agent.duplicate()

        try:
            original_description = source_agent.description
            duplicated.description = "Modified description on duplicate"
            duplicated.save(as_draft=True)

            refetched_source = client.Agent.get(source_agent.id)
            assert refetched_source.description == original_description
        finally:
            try:
                duplicated.delete()
            except Exception:
                pass

    def test_duplicate_auto_generates_unique_name(self, client, source_agent):
        """The platform should auto-generate a unique name for the duplicate."""
        dup1 = source_agent.duplicate()
        dup2 = source_agent.duplicate()

        try:
            assert dup1.name != dup2.name, "Each duplicate should get a unique auto-generated name"
        finally:
            for d in [dup1, dup2]:
                try:
                    d.delete()
                except Exception:
                    pass


class TestAgentDuplicateWithSubagents:
    @pytest.fixture(scope="class")
    def team_agent(self, client):
        """Create a team agent (agent with subagents) for testing duplicate_subagents."""
        sub = client.Agent(
            name=f"Sub for Dup {int(time.time())}",
            description="A subagent used to test duplicate_subagents",
            instructions="You are a subagent.",
        )
        sub.save()

        team = client.Agent(
            name=f"Team for Dup {int(time.time())}",
            description="A team agent with subagents for duplicate testing",
            instructions="You orchestrate subagents.",
            subagents=[sub],
        )
        team.save()

        yield team, sub

        for resource in [team, sub]:
            try:
                resource.delete()
            except Exception:
                pass

    def test_duplicate_keep_references(self, client, team_agent):
        """Duplicate a team agent keeping references to original subagents."""
        team, sub = team_agent
        duplicated = team.duplicate(duplicate_subagents=False)

        try:
            assert duplicated.id is not None
            assert duplicated.id != team.id

            if duplicated.subagents:
                assert sub.id in duplicated.subagents, (
                    f"Expected original subagent ID {sub.id} in duplicated.subagents={duplicated.subagents}"
                )
        finally:
            try:
                duplicated.delete()
            except Exception:
                pass

    def test_duplicate_subagents(self, client, team_agent):
        """Duplicate a team agent with independent copies of subagents."""
        team, sub = team_agent
        duplicated = team.duplicate(duplicate_subagents=True)

        cloned_subs_to_clean = []
        try:
            assert duplicated.id is not None
            assert duplicated.id != team.id

            if duplicated.subagents:
                for sa_id in duplicated.subagents:
                    if isinstance(sa_id, str):
                        assert sa_id != sub.id, (
                            "With duplicate_subagents=True, subagent IDs should differ from the originals"
                        )
                        cloned_subs_to_clean.append(sa_id)
        finally:
            try:
                duplicated.delete()
            except Exception:
                pass
            for sa_id in cloned_subs_to_clean:
                try:
                    cloned_sub = client.Agent.get(sa_id)
                    cloned_sub.delete()
                except Exception:
                    pass
