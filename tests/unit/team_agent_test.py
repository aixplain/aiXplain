import pytest
import requests_mock
from aixplain.modules import TeamAgent
from aixplain.factories import TeamAgentFactory
from aixplain.utils import config


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
