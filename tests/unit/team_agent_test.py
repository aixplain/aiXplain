import pytest
import requests_mock
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules import Agent, TeamAgent
from aixplain.modules.agent import ModelTool
from aixplain.factories import TeamAgentFactory
from aixplain.factories import AgentFactory
from aixplain.utils import config
from urllib.parse import urljoin


def test_fail_no_data_query():
    team_agent = TeamAgent("123", "Test Team Agent")
    with pytest.raises(Exception) as exc_info:
        team_agent.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_must_be_provided():
    team_agent = TeamAgent("123", "Test Team Agent")
    with pytest.raises(Exception) as exc_info:
        team_agent.run_async(data={})
    assert str(exc_info.value) == "When providing a dictionary, 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    team_agent = TeamAgent("123", "Test Team Agent")
    with pytest.raises(Exception) as exc_info:
        team_agent.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=["https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"],
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
        TeamAgentFactory.create(name="Test Team Agent", agents=[])

    assert str(exc_info.value) == "TeamAgent Onboarding Error: At least one agent must be provided."


def test_to_dict():
    team_agent = TeamAgent(
        id="123",
        name="Test Team Agent",
        agents=[
            Agent(
                id="",
                name="Test Agent",
                description="Test Agent Description",
                llm_id="6646261c6eb563165658bbb1",
                tools=[ModelTool(function="text-generation")],
            )
        ],
        description="Test Team Agent Description",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist_and_inspector=False,
    )

    team_agent_dict = team_agent.to_dict()
    assert team_agent_dict["id"] == "123"
    assert team_agent_dict["name"] == "Test Team Agent"
    assert team_agent_dict["description"] == "Test Team Agent Description"
    assert team_agent_dict["llmId"] == "6646261c6eb563165658bbb1"
    assert team_agent_dict["supervisorId"] == "6646261c6eb563165658bbb1"
    assert team_agent_dict["plannerId"] is None
    assert len(team_agent_dict["agents"]) == 1
    assert team_agent_dict["agents"][0]["assetId"] == ""
    assert team_agent_dict["agents"][0]["number"] == 0
    assert team_agent_dict["agents"][0]["type"] == "AGENT"
    assert team_agent_dict["agents"][0]["label"] == "AGENT"


def test_create_team_agent():
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
            "name": "Test Agent",
            "description": "Test Agent Description",
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
            name="Test Agent",
            description="Test Agent Description",
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
            "name": "TEST Multi agent",
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
            name="TEST Multi agent",
            description="TEST Multi agent",
            use_mentalist_and_inspector=True,
            llm_id="6646261c6eb563165658bbb1",
            agents=[agent],
        )
    assert team_agent.id is not None
    assert team_agent.name == team_ref_response["name"]
    assert team_agent.description == team_ref_response["description"]
    assert team_agent.llm_id == team_ref_response["llmId"]
    assert team_agent.use_mentalist_and_inspector is True
    assert team_agent.status == AssetStatus.DRAFT
    assert len(team_agent.agents) == 1
    assert team_agent.agents[0].id == team_ref_response["agents"][0]["assetId"]
