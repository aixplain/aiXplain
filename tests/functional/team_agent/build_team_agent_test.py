from aixplain.modules.agent.tool.model_tool import ModelTool


def test_build_team_agent(mocker):
    from aixplain.factories.team_agent_factory.utils import build_team_agent
    from aixplain.modules.agent import Agent, AgentTask

    agent1 = Agent(
        id="agent1",
        name="Test Agent 1",
        description="Test Agent Description",
        instructions="Test Agent Instructions",
        llm_id="69b7e5f1b2fe44704ab0e7d0",
        tools=[ModelTool(model="69b7e5f1b2fe44704ab0e7d0")],
        tasks=[
            AgentTask(
                name="Test Task 1",
                description="Test Task Description",
                expected_output="Test Task Output",
                dependencies=["Test Task 2"],
            ),
        ],
    )

    agent2 = Agent(
        id="agent2",
        name="Test Agent 2",
        description="Test Agent Description",
        instructions="Test Agent Instructions",
        llm_id="69b7e5f1b2fe44704ab0e7d0",
        tools=[ModelTool(model="69b7e5f1b2fe44704ab0e7d0")],
        tasks=[
            AgentTask(name="Test Task 2", description="Test Task Description", expected_output="Test Task Output"),
        ],
    )

    # Create a function to return different values based on input
    def get_mock(agent_id):
        return {"agent1": agent1, "agent2": agent2}[agent_id]

    mocker.patch("aixplain.factories.agent_factory.AgentFactory.get", side_effect=get_mock)

    payload = {
        "id": "123",
        "name": "Test Team Agent(-)",
        "description": "Test Team Agent Description",
        "plannerId": "69b7e5f1b2fe44704ab0e7d0",
        "llmId": "69b7e5f1b2fe44704ab0e7d0",
        "agents": [
            {"assetId": "agent1"},
            {"assetId": "agent2"},
        ],
        "status": "onboarded",
    }
    team_agent = build_team_agent(payload)
    assert team_agent.id == "123"
    assert team_agent.name == "Test Team Agent(-)"
    assert team_agent.description == "Test Team Agent Description"
    assert sorted(agent.id for agent in team_agent.agents) == ["agent1", "agent2"]
    agent1 = next((agent for agent in team_agent.agents if agent.id == "agent1"), None)
    assert agent1 is not None
    assert agent1.tasks[0].dependencies[0].name == "Test Task 2"
