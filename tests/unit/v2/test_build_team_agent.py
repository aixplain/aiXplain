"""v2 port of the legacy team-agent builder unit test (ENG-3689).

The v1 file lived at ``tests/functional/team_agent/build_team_agent_test.py``
but used ``mocker`` and touched no backend, so it was a unit test occupying a
functional CI leg. It now lives under ``tests/unit/v2/``.

v1's ``aixplain.factories.team_agent_factory.utils.build_team_agent(payload)``
was removed with v1; in v2 the same job is ``Agent.from_dict(payload)``. The
assertions below preserve the legacy intent: a team payload decodes to an agent
whose ``agents`` are the referenced subagent ids, and a task dependency resolves
to the depended-on task's name.
"""

from aixplain.v2 import Agent
from aixplain.v2.agent import Task

TEAM_PAYLOAD = {
    "id": "123",
    "name": "Test Team Agent(-)",
    "description": "Test Team Agent Description",
    "model": {"id": "llm-1"},
    "planner": {"id": "planner-1"},
    "agents": [{"id": "agent1"}, {"id": "agent2"}],
    "tools": [{"id": "tool-1", "type": "model"}],
    "status": "onboarded",
}


def test_team_payload_decodes_core_fields_and_agents():
    """The decoded team keeps its identity and references both subagents."""
    team = Agent.from_dict(TEAM_PAYLOAD)

    assert team.id == "123"
    assert team.name == "Test Team Agent(-)"
    assert team.description == "Test Team Agent Description"
    assert sorted(team.agents) == ["agent1", "agent2"]
    assert team.planner == {"id": "planner-1"}


def test_task_dependency_on_a_task_object_resolves_to_its_name():
    """A ``Task`` passed as a dependency is stored, and saved, as that task's name.

    This is the v2 shape of the legacy ``agent1.tasks[0].dependencies[0].name``
    assertion: ``Task.__post_init__`` normalizes a ``Task`` dependency to its
    name, which is what the backend expects on the wire.
    """
    gather = Task(name="Test Task 2", instructions="Gather the facts", expected_output="facts")
    summarize = Task(
        name="Test Task 1",
        instructions="Test Task Description",
        expected_output="Test Task Output",
        dependencies=[gather],
    )
    agent = Agent(name="Test Agent 1", tasks=[summarize, gather])

    assert agent.tasks[0].dependencies == ["Test Task 2"]
    saved_tasks = agent.build_save_payload()["tasks"]
    assert saved_tasks[0]["dependencies"] == ["Test Task 2"]
    assert saved_tasks[0]["description"] == "Test Task Description"
    assert saved_tasks[0]["expectedOutput"] == "Test Task Output"


def test_team_save_payload_serializes_agents_as_objects():
    """A decoded team round-trips to the ``agents: [{id, inspectors}]`` wire shape."""
    payload = Agent.from_dict(TEAM_PAYLOAD).build_save_payload()

    assert payload["agents"] == [{"id": "agent1", "inspectors": []}, {"id": "agent2", "inspectors": []}]
