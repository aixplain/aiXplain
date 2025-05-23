import pytest
import requests_mock
from urllib.parse import urljoin
from unittest.mock import patch, Mock

from aixplain.enums.asset_status import AssetStatus
from aixplain.factories import TeamAgentFactory
from aixplain.factories import AgentFactory
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent, InspectorTarget
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.utils import config


def test_fail_no_data_query():
    team_agent = TeamAgent("123", "Test Team Agent(-)")
    with pytest.raises(Exception) as exc_info:
        team_agent.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    team_agent = TeamAgent("123", "Test Team Agent")
    with pytest.raises(Exception) as exc_info:
        team_agent.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=[
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            ],
        )
    assert str(exc_info.value) == "When providing 'content', query must be text."


def test_fail_content_exceed_maximum():
    team_agent = TeamAgent("123", "Test Team Agent")
    with pytest.raises(Exception) as exc_info:
        team_agent.run_async(
            data={"query": "Transcribe the audios:"},
            content=[
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            ],
        )
    assert str(exc_info.value) == "The maximum number of content inputs is 3."


def test_fail_key_not_found():
    team_agent = TeamAgent("123", "Test Team Agent")
    with pytest.raises(Exception) as exc_info:
        team_agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input2": "Hello, how are you?"})
    assert str(exc_info.value) == "Key 'input2' not found in query."


def test_sucess_query_content():
    team_agent = TeamAgent("123", "Test Team Agent")
    with requests_mock.Mocker() as mock:
        url = team_agent.url
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"data": "Hello, how are you?", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = team_agent.run_async(
            data={"query": "Translate the text: {{input1}}"}, content={"input1": "Hello, how are you?"}
        )
    assert response["status"] == ref_response["status"]
    assert response["url"] == ref_response["data"]


def test_fail_number_agents():
    with pytest.raises(Exception) as exc_info:
        TeamAgentFactory.create(name="Test Team Agent(-)", agents=[])

    assert str(exc_info.value) == "TeamAgent Onboarding Error: At least one agent must be provided."


def test_to_dict():
    team_agent = TeamAgent(
        id="123",
        name="Test Team Agent(-)",
        agents=[
            Agent(
                id="",
                name="Test Agent(-)",
                description="Test Agent Description",
                instructions="Test Agent Role",
                llm_id="6646261c6eb563165658bbb1",
                tools=[ModelTool(function="text-generation")],
            )
        ],
        description="Test Team Agent Description",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=False,
        inspectors=[
            Inspector(
                name="Test Inspector",
                model_id="6646261c6eb563165658bbb1",
                model_params={"prompt": "Test Prompt"},
                policy=InspectorPolicy.ADAPTIVE,
            )
        ],
        inspector_targets=[InspectorTarget.STEPS, InspectorTarget.OUTPUT],
    )

    team_agent_dict = team_agent.to_dict()

    assert team_agent_dict["id"] == "123"
    assert team_agent_dict["name"] == "Test Team Agent(-)"
    assert team_agent_dict["description"] == "Test Team Agent Description"
    assert team_agent_dict["llmId"] == "6646261c6eb563165658bbb1"
    assert team_agent_dict["supervisorId"] == "6646261c6eb563165658bbb1"

    assert team_agent_dict["agents"][0]["assetId"] == ""
    assert team_agent_dict["agents"][0]["number"] == 0
    assert team_agent_dict["agents"][0]["type"] == "AGENT"
    assert team_agent_dict["agents"][0]["label"] == "AGENT"

    assert team_agent_dict["plannerId"] is None
    assert len(team_agent_dict["inspectors"]) == 1
    assert team_agent_dict["inspectors"][0]["name"] == "Test Inspector"
    assert team_agent_dict["inspectors"][0]["modelId"] == "6646261c6eb563165658bbb1"
    assert team_agent_dict["inspectors"][0]["modelParams"] == {"prompt": "Test Prompt"}
    assert team_agent_dict["inspectors"][0]["policy"] == "adaptive"
    assert team_agent_dict["inspectorTargets"] == ["steps", "output"]
    assert len(team_agent_dict["agents"]) == 1


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_create_team_agent(mock_model_factory_get):
    from aixplain.modules import Model
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1", name="Test LLM", description="Test LLM Description", function=Function.TEXT_GENERATION
    )
    mock_model_factory_get.return_value = mock_model

    with requests_mock.Mocker() as mock:
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        # MOCK GET LLM
        url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
        model_ref_response = {
            "id": "6646261c6eb563165658bbb1",
            "name": "Test LLM",
            "description": "Test LLM Description",
            "function": {"id": "text-generation"},
            "supplier": "openai",
            "version": {"id": "1.0"},
            "status": "onboarded",
            "pricing": {"currency": "USD", "value": 0.0},
        }
        mock.get(url, headers=headers, json=model_ref_response)

        # AGENT MOCK CREATION
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        ref_response = {
            "id": "123",
            "name": "Test Agent(-)",
            "description": "Test Agent Description",
            "role": "Test Agent Role",
            "teamId": "123",
            "version": "1.0",
            "status": "onboarded",
            "llmId": "6646261c6eb563165658bbb1",
            "pricing": {"currency": "USD", "value": 0.0},
            "assets": [
                {
                    "type": "model",
                    "supplier": "openai",
                    "version": "1.0",
                    "assetId": "6646261c6eb563165658bbb1",
                    "function": "text-generation",
                }
            ],
        }
        mock.post(url, headers=headers, json=ref_response)

        agent = AgentFactory.create(
            name="Test Agent(-)",
            description="Test Agent Description",
            instructions="Test Agent Role",
            llm_id="6646261c6eb563165658bbb1",
            tools=[ModelTool(model="6646261c6eb563165658bbb1")],
        )

        # AGENT MOCK GET
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}")
        mock.get(url, headers=headers, json=ref_response)

        # TEAM MOCK CREATION
        url = urljoin(config.BACKEND_URL, "sdk/agent-communities")
        team_ref_response = {
            "id": "team_agent_123",
            "name": "TEST Multi agent(-)",
            "status": "draft",
            "teamId": 645,
            "description": "TEST Multi agent",
            "llmId": "6646261c6eb563165658bbb1",
            "assets": [],
            "agents": [{"assetId": "123", "type": "AGENT", "number": 0, "label": "AGENT"}],
            "links": [],
            "plannerId": "6646261c6eb563165658bbb1",
            "supervisorId": "6646261c6eb563165658bbb1",
            "createdAt": "2024-10-28T19:30:25.344Z",
            "updatedAt": "2024-10-28T19:30:25.344Z",
        }
        mock.post(url, headers=headers, json=team_ref_response)

        team_agent = TeamAgentFactory.create(
            name="TEST Multi agent(-)",
            agents=[agent],
            llm_id="6646261c6eb563165658bbb1",
            description="TEST Multi agent",
            use_mentalist=True,
            # TODO: inspectors=[Inspector(name="Test Inspector", model_id="6646261c6eb563165658bbb1", model_params={"prompt": "Test Prompt"}, policy=InspectorPolicy.ADAPTIVE)],
            # TODO: inspector_targets=[InspectorTarget.STEPS, InspectorTarget.OUTPUT],
        )
        assert team_agent.id is not None
        assert team_agent.name == team_ref_response["name"]
        assert team_agent.description == team_ref_response["description"]
        assert team_agent.llm_id == team_ref_response["llmId"]
        assert team_agent.use_mentalist is True
        assert team_agent.status == AssetStatus.DRAFT
        assert len(team_agent.agents) == 1
        assert team_agent.agents[0].id == team_ref_response["agents"][0]["assetId"]

        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}")
        team_ref_response = {
            "id": "team_agent_123",
            "name": "TEST Multi agent(-)",
            "status": "onboarded",
            "teamId": 645,
            "description": "TEST Multi agent",
            "llmId": "6646261c6eb563165658bbb1",
            "assets": [],
            "agents": [{"assetId": "123", "type": "AGENT", "number": 0, "label": "AGENT"}],
            "links": [],
            "plannerId": "6646261c6eb563165658bbb1",
            "inspectorId": "6646261c6eb563165658bbb1",
            "supervisorId": "6646261c6eb563165658bbb1",
            "createdAt": "2024-10-28T19:30:25.344Z",
            "updatedAt": "2024-10-28T19:30:25.344Z",
        }
        mock.put(url, headers=headers, json=team_ref_response)

        team_agent.deploy()
        assert team_agent.status.value == "onboarded"


def test_fail_inspector_without_mentalist():
    with pytest.raises(Exception) as exc_info:
        TeamAgentFactory.create(
            name="Test Team Agent(-)",
            agents=[
                Agent(
                    id="123",
                    name="Test Agent(-)",
                    description="Test Agent Description",
                    instructions="Test Agent Role",
                    llm_id="6646261c6eb563165658bbb1",
                    tools=[ModelTool(function="text-generation")],
                )
            ],
            use_mentalist=False,
            inspectors=[
                Inspector(
                    name="Test Inspector",
                    model_id="6646261c6eb563165658bbb1",
                    model_params={"prompt": "Test Prompt"},
                    policy=InspectorPolicy.ADAPTIVE,
                )
            ],
        )

    assert "you must enable Mentalist" in str(exc_info.value)


def test_fail_invalid_inspector_target():
    with pytest.raises(ValueError) as exc_info:
        TeamAgentFactory.create(
            name="Test Team Agent(-)",
            agents=[
                Agent(
                    id="123",
                    name="Test Agent(-)",
                    description="Test Agent Description",
                    instructions="Test Agent Role",
                    llm_id="6646261c6eb563165658bbb1",
                    tools=[ModelTool(function="text-generation")],
                )
            ],
            use_mentalist=True,
            inspectors=[
                Inspector(
                    name="Test Inspector",
                    model_id="6646261c6eb563165658bbb1",
                    model_params={"prompt": "Test Prompt"},
                    policy=InspectorPolicy.ADAPTIVE,
                )
            ],
            inspector_targets=["invalid_target"],
        )

    assert "Invalid inspector target" in str(exc_info.value)


def test_build_team_agent(mocker):
    from aixplain.factories.team_agent_factory.utils import build_team_agent
    from aixplain.modules.agent import Agent, AgentTask

    agent1 = Agent(
        id="agent1",
        name="Test Agent 1",
        description="Test Agent Description",
        instructions="Test Agent Role",
        llm_id="6646261c6eb563165658bbb1",
        tools=[ModelTool(model="6646261c6eb563165658bbb1")],
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
        instructions="Test Agent Role",
        llm_id="6646261c6eb563165658bbb1",
        tools=[ModelTool(model="6646261c6eb563165658bbb1")],
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
        "plannerId": "6646261c6eb563165658bbb1",
        "inspectorId": "6646261c6eb563165658bbb1",
        "llmId": "6646261c6eb563165658bbb1",
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


def test_deploy_team_agent():
    # Create a mock agent with ONBOARDED status
    mock_agent = Mock()
    mock_agent.id = "agent-id"
    mock_agent.name = "Test Agent"
    mock_agent.status = AssetStatus.ONBOARDED

    # Create the team agent
    team_agent = TeamAgent(id="team-agent-id", name="Test Team Agent", agents=[mock_agent], status=AssetStatus.DRAFT)

    # Mock the update method
    team_agent.update = Mock()

    # Deploy the team agent
    team_agent.deploy()

    # Verify that status was updated and update was called
    assert team_agent.status == AssetStatus.ONBOARDED
    team_agent.update.assert_called_once()
