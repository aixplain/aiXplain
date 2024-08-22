import pytest
import requests_mock
from aixplain.modules import Agent
from aixplain.utils import config
from aixplain.factories import AgentFactory
from aixplain.modules.agent import PipelineTool, ModelTool


def test_fail_no_data_query():
    agent = Agent("123", "Test Agent")
    with pytest.raises(Exception) as exc_info:
        agent.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_must_be_provided():
    agent = Agent("123", "Test Agent")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={})
    assert str(exc_info.value) == "When providing a dictionary, 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    agent = Agent("123", "Test Agent")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=["https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"],
        )
    assert str(exc_info.value) == "When providing 'content', query must be text."


def test_fail_content_exceed_maximum():
    agent = Agent("123", "Test Agent")
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
    agent = Agent("123", "Test Agent")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input2": "Hello, how are you?"})
    assert str(exc_info.value) == "Key 'input2' not found in query."


def test_sucess_query_content():
    agent = Agent("123", "Test Agent")
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
            name="Test", tools=[PipelineTool(pipeline="309851793", description="Test")], llm_id="6646261c6eb563165658bbb1"
        )
    assert str(exc_info.value) == "Pipeline Tool Unavailable. Make sure Pipeline '309851793' exists or you have access to it."


def test_invalid_modeltool():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="Test", tools=[ModelTool(model="309851793")], llm_id="6646261c6eb563165658bbb1")
    assert str(exc_info.value) == "Model Tool Unavailable. Make sure Model '309851793' exists or you have access to it."
