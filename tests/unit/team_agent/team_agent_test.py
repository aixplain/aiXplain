import pytest
import requests_mock
from urllib.parse import urljoin
from unittest.mock import patch, Mock

from aixplain.enums.asset_status import AssetStatus
from aixplain.factories import TeamAgentFactory
from aixplain.factories import AgentFactory
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent
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
        team_agent.run_async(
            data={"query": "Translate the text: {{input1}}"}, content={"input2": "Hello, how are you?"}
        )
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
                instructions="Test Agent Instructions",
                llm_id="6646261c6eb563165658bbb1",
                tools=[ModelTool(function="text-generation")],
            )
        ],
        description="Test Team Agent Description",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=False,
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
    assert len(team_agent_dict["agents"]) == 1


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_create_team_agent(mock_model_factory_get):
    from aixplain.modules import Model
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
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
            "status": "draft",
            "pricing": {"currency": "USD", "value": 0.0},
        }
        mock.get(url, headers=headers, json=model_ref_response)

        # AGENT MOCK CREATION
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        ref_response = {
            "id": "123",
            "name": "Test Agent(-)",
            "description": "Test Agent Description",
            "instructions": "Test Agent Instructions",
            "teamId": "123",
            "version": "1.0",
            "status": "draft",
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
            instructions="Test Agent Instructions",
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
        )
        assert team_agent.id is not None
        assert team_agent.name == team_ref_response["name"]
        assert team_agent.description == team_ref_response["description"]
        assert team_agent.llm_id == team_ref_response["llmId"]
        assert team_agent.use_mentalist is True
        assert team_agent.status == AssetStatus.DRAFT
        assert len(team_agent.agents) == 1
        assert team_agent.agents[0].id == team_ref_response["agents"][0]["assetId"]

        # Mock deployment responses
        # Mock agent deployment
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}")
        deployed_agent_response = ref_response.copy()
        deployed_agent_response["status"] = "onboarded"
        mock.put(url, headers=headers, json=deployed_agent_response)
        mock.get(url, headers=headers, json=deployed_agent_response)

        # Mock team agent deployment
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}")
        deployed_team_response = team_ref_response.copy()
        deployed_team_response["status"] = "onboarded"
        mock.put(url, headers=headers, json=deployed_team_response)

        # Deploy and verify
        team_agent.deploy()
        assert team_agent.status == AssetStatus.ONBOARDED
        assert team_agent.agents[0].status == AssetStatus.ONBOARDED


def test_build_team_agent(mocker):
    from aixplain.factories.team_agent_factory.utils import build_team_agent
    from aixplain.modules.agent import Agent, AgentTask

    agent1 = Agent(
        id="agent1",
        name="Test Agent 1",
        description="Test Agent Description",
        instructions="Test Agent Instructions",
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
        instructions="Test Agent Instructions",
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


def test_deploy_team_agent_with_nested_agents():
    """Test that deploying a team agent properly deploys its nested agents."""
    # Create mock agents
    mock_agent1 = Mock()
    mock_agent1.id = "agent-1"
    mock_agent1.name = "Test Agent 1"
    mock_agent1.status = AssetStatus.DRAFT
    mock_agent1.deploy = Mock()

    mock_agent2 = Mock()
    mock_agent2.id = "agent-2"
    mock_agent2.name = "Test Agent 2"
    mock_agent2.status = AssetStatus.DRAFT
    mock_agent2.deploy = Mock()

    # Create the team agent
    team_agent = TeamAgent(
        id="team-agent-id", name="Test Team Agent", agents=[mock_agent1, mock_agent2], status=AssetStatus.DRAFT
    )

    # Mock the update method
    team_agent.update = Mock()

    # Deploy the team agent
    team_agent.deploy()

    # Verify that each agent's deploy method was called
    mock_agent1.deploy.assert_called_once()
    mock_agent2.deploy.assert_called_once()

    # Verify that status was updated and update was called
    assert team_agent.status == AssetStatus.ONBOARDED
    team_agent.update.assert_called_once()


def test_team_agent_serialization_completeness():
    """Test that TeamAgent to_dict includes all necessary fields."""
    from unittest.mock import Mock

    # Create mock agents
    mock_agent1 = Mock()
    mock_agent1.id = "agent-1"
    mock_agent1.name = "Agent 1"

    mock_agent2 = Mock()
    mock_agent2.id = "agent-2"
    mock_agent2.name = "Agent 2"

    # Create test team agent with comprehensive data
    team_agent = TeamAgent(
        id="test-team-123",
        name="Test Team",
        agents=[mock_agent1, mock_agent2],
        description="A test team agent",
        llm_id="6646261c6eb563165658bbb1",
        supervisor_llm=None,
        mentalist_llm=None,
        supplier="aixplain",
        version="1.0.0",
        use_mentalist=False,
        status=AssetStatus.DRAFT,
        instructions="You are a helpful team agent",
    )

    # Test to_dict includes all expected fields
    team_dict = team_agent.to_dict()

    required_fields = {
        "id",
        "name",
        "agents",
        "links",
        "description",
        "llmId",
        "supervisorId",
        "plannerId",
        "supplier",
        "version",
        "status",
        "instructions",
        "outputFormat",
        "expectedOutput",
    }

    assert set(team_dict.keys()) == required_fields

    # Verify field values
    assert team_dict["id"] == "test-team-123"
    assert team_dict["name"] == "Test Team"
    assert team_dict["description"] == "A test team agent"
    assert team_dict["instructions"] == "You are a helpful team agent"
    assert team_dict["llmId"] == "6646261c6eb563165658bbb1"
    assert team_dict["supplier"] == "aixplain"
    assert team_dict["version"] == "1.0.0"
    assert team_dict["status"] == "draft"
    assert team_dict["links"] == []
    assert team_dict["plannerId"] is None  # use_mentalist=False
    assert team_dict["outputFormat"] == "text"
    assert team_dict["expectedOutput"] is None

    # Verify agents serialization
    assert isinstance(team_dict["agents"], list)
    assert len(team_dict["agents"]) == 2
    agent_dict = team_dict["agents"][0]
    assert agent_dict["assetId"] == "agent-1"
    assert agent_dict["number"] == 0
    assert agent_dict["type"] == "AGENT"
    assert agent_dict["label"] == "AGENT"



def test_team_agent_serialization_with_llms():
    """Test TeamAgent to_dict when LLM instances are provided."""
    from unittest.mock import Mock

    # Mock different LLMs
    mock_llm = Mock()
    mock_llm.id = "main-llm-id"

    mock_supervisor = Mock()
    mock_supervisor.id = "supervisor-llm-id"

    mock_mentalist = Mock()
    mock_mentalist.id = "mentalist-llm-id"

    team_agent = TeamAgent(
        id="test-team",
        name="Test Team",
        agents=[],
        description="Test team with LLMs",
        llm_id="fallback-llm-id",
        llm=mock_llm,
        supervisor_llm=mock_supervisor,
        mentalist_llm=mock_mentalist,
        use_mentalist=True,
    )

    team_dict = team_agent.to_dict()

    # Should use LLM instance IDs
    assert team_dict["llmId"] == "main-llm-id"
    assert team_dict["supervisorId"] == "supervisor-llm-id"
    assert team_dict["plannerId"] == "mentalist-llm-id"


def test_team_agent_serialization_mentalist_logic():
    """Test TeamAgent to_dict plannerId logic based on use_mentalist and mentalist_llm."""

    # Case 1: use_mentalist=True but no mentalist_llm
    team_agent1 = TeamAgent(id="team1", name="Team 1", agents=[], use_mentalist=True, llm_id="main-llm")

    dict1 = team_agent1.to_dict()
    assert dict1["plannerId"] == "main-llm"  # Falls back to main LLM

    # Case 2: use_mentalist=False
    team_agent2 = TeamAgent(id="team2", name="Team 2", agents=[], use_mentalist=False, llm_id="main-llm")

    dict2 = team_agent2.to_dict()
    assert dict2["plannerId"] is None


@pytest.mark.parametrize(
    "status_input,expected_output",
    [
        (AssetStatus.DRAFT, "draft"),
        (AssetStatus.ONBOARDED, "onboarded"),
        (AssetStatus.COMPLETED, "completed"),
    ],
)
def test_team_agent_serialization_status_enum(status_input, expected_output):
    """Test TeamAgent to_dict properly serializes AssetStatus enum."""
    team_agent = TeamAgent(
        id="test-team", name="Test Team", agents=[], description="Test description", status=status_input
    )

    team_dict = team_agent.to_dict()
    assert team_dict["status"] == expected_output


def test_team_agent_serialization_supervisor_fallback():
    """Test TeamAgent to_dict supervisorId fallback behavior."""

    # Case 1: No supervisor_llm provided
    team_agent1 = TeamAgent(id="team1", name="Team 1", agents=[], llm_id="main-llm-id")

    dict1 = team_agent1.to_dict()
    assert dict1["supervisorId"] == "main-llm-id"  # Falls back to main LLM

    # Case 2: supervisor_llm provided
    from unittest.mock import Mock

    mock_supervisor = Mock()
    mock_supervisor.id = "supervisor-llm-id"

    team_agent2 = TeamAgent(id="team2", name="Team 2", agents=[], llm_id="main-llm-id", supervisor_llm=mock_supervisor)

    dict2 = team_agent2.to_dict()
    assert dict2["supervisorId"] == "supervisor-llm-id"


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_update_success(mock_model_factory_get):
    from aixplain.modules import Model
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
    )
    mock_model_factory_get.return_value = mock_model

    team_agent = TeamAgent(
        id="123",
        name="Test Team Agent(-)",
        agents=[
            Agent(
                id="agent123",
                name="Test Agent(-)",
                description="Test Agent Description",
                instructions="Test Agent Instructions",
                llm_id="6646261c6eb563165658bbb1",
                tools=[ModelTool(model="6646261c6eb563165658bbb1")],
            )
        ],
        description="Test Team Agent Description",
        llm_id="6646261c6eb563165658bbb1",
    )

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {
            "id": "123",
            "name": "Test Team Agent(-)",
            "status": "onboarded",
            "teamId": 645,
            "description": "Test Team Agent Description",
            "llmId": "6646261c6eb563165658bbb1",
            "assets": [],
            "agents": [{"assetId": "agent123", "type": "AGENT", "number": 0, "label": "AGENT"}],
            "links": [],
            "plannerId": None,
            "supervisorId": "6646261c6eb563165658bbb1",
            "createdAt": "2024-10-28T19:30:25.344Z",
            "updatedAt": "2024-10-28T19:30:25.344Z",
        }
        mock.put(url, headers=headers, json=ref_response)

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

        # Capture warnings
        with pytest.warns(
            DeprecationWarning,
            match="update\(\) is deprecated and will be removed in a future version. Please use save\(\) instead.",  # noqa: W605
        ):
            team_agent.update()

    assert team_agent.id == ref_response["id"]
    assert team_agent.name == ref_response["name"]
    assert team_agent.description == ref_response["description"]
    assert team_agent.llm_id == ref_response["llmId"]
    assert team_agent.agents[0].id == ref_response["agents"][0]["assetId"]


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_save_success(mock_model_factory_get):
    from aixplain.modules import Model
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
    )
    mock_model_factory_get.return_value = mock_model

    team_agent = TeamAgent(
        id="123",
        name="Test Team Agent(-)",
        agents=[
            Agent(
                id="agent123",
                name="Test Agent(-)",
                description="Test Agent Description",
                instructions="Test Agent Instructions",
                llm_id="6646261c6eb563165658bbb1",
                tools=[ModelTool(model="6646261c6eb563165658bbb1")],
            )
        ],
        description="Test Team Agent Description",
        llm_id="6646261c6eb563165658bbb1",
    )

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {
            "id": "123",
            "name": "Test Team Agent(-)",
            "status": "onboarded",
            "teamId": 645,
            "description": "Test Team Agent Description",
            "llmId": "6646261c6eb563165658bbb1",
            "assets": [],
            "agents": [{"assetId": "agent123", "type": "AGENT", "number": 0, "label": "AGENT"}],
            "links": [],
            "plannerId": None,
            "supervisorId": "6646261c6eb563165658bbb1",
            "createdAt": "2024-10-28T19:30:25.344Z",
            "updatedAt": "2024-10-28T19:30:25.344Z",
        }
        mock.put(url, headers=headers, json=ref_response)

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

        import warnings

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Trigger all warnings

            # Call the save method
            team_agent.save()

            # Assert the correct number of warnings were raised
            assert len(w) == 3, f"Warnings were raised: {[str(warning.message) for warning in w]}"

    assert team_agent.id == ref_response["id"]
    assert team_agent.name == ref_response["name"]
    assert team_agent.description == ref_response["description"]
    assert team_agent.llm_id == ref_response["llmId"]
    assert team_agent.agents[0].id == ref_response["agents"][0]["assetId"]
