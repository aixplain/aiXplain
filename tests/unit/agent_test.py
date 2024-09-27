import pytest
import requests_mock
from aixplain.modules import Agent
from aixplain.utils import config
from aixplain.factories import AgentFactory
from aixplain.modules.agent import PipelineTool, ModelTool
from urllib.parse import urljoin


def test_fail_no_data_query():
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_must_be_provided():
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={})
    assert str(exc_info.value) == "When providing a dictionary, 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=["https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"],
        )
    assert str(exc_info.value) == "When providing 'content', query must be text."


def test_fail_content_exceed_maximum():
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
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
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input2": "Hello, how are you?"})
    assert str(exc_info.value) == "Key 'input2' not found in query."


def test_sucess_query_content():
    agent = Agent("123", "Test Agent", "Sample Description")
    with requests_mock.Mocker() as mock:
        url = agent.url
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"data": "Hello, how are you?", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input1": "Hello, how are you?"})
    assert response["status"] == ref_response["status"]
    assert response["url"] == ref_response["data"]


def test_invalid_pipelinetool():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test",
            description="Test Description",
            tools=[PipelineTool(pipeline="309851793", description="Test")],
            llm_id="6646261c6eb563165658bbb1",
        )
    assert str(exc_info.value) == "Pipeline Tool Unavailable. Make sure Pipeline '309851793' exists or you have access to it."


def test_invalid_modeltool():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="Test", tools=[ModelTool(model="309851793")], llm_id="6646261c6eb563165658bbb1")
    assert str(exc_info.value) == "Model Tool Unavailable. Make sure Model '309851793' exists or you have access to it."


def test_invalid_agent_name():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="[Test]", description="", tools=[], llm_id="6646261c6eb563165658bbb1")
    assert str(exc_info.value) == "Agent Creation Error: Agent name must not contain special characters."


def test_create_agent():
    from aixplain.enums import Supplier

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        ref_response = {
            "id": "123",
            "name": "Test Agent",
            "description": "Test Agent Description",
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

        agent = AgentFactory.create(
            name="Test Agent",
            description="Test Agent Description",
            llm_id="6646261c6eb563165658bbb1",
            tools=[AgentFactory.create_model_tool(supplier=Supplier.OPENAI, function="text-generation")],
        )

    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]
