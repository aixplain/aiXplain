import pytest
import requests_mock
from aixplain.modules import Community
from aixplain.utils import config


def test_fail_no_data_query():
    community = Community("123", "Test Community")
    with pytest.raises(Exception) as exc_info:
        community.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_must_be_provided():
    community = Community("123", "Test Community")
    with pytest.raises(Exception) as exc_info:
        community.run_async(data={})
    assert str(exc_info.value) == "When providing a dictionary, 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    community = Community("123", "Test Community")
    with pytest.raises(Exception) as exc_info:
        community.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=["https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"],
        )
    assert str(exc_info.value) == "When providing 'content', query must be text."


def test_fail_content_exceed_maximum():
    community = Community("123", "Test Community")
    with pytest.raises(Exception) as exc_info:
        community.run_async(
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
    community = Community("123", "Test Community")
    with pytest.raises(Exception) as exc_info:
        community.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input2": "Hello, how are you?"})
    assert str(exc_info.value) == "Key 'input2' not found in query."


def test_sucess_query_content():
    community = Community("123", "Test Community")
    with requests_mock.Mocker() as mock:
        url = community.url
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"data": "Hello, how are you?", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = community.run_async(
            data={"query": "Translate the text: {{input1}}"}, content={"input1": "Hello, how are you?"}
        )
    assert response["status"] == ref_response["status"]
    assert response["url"] == ref_response["data"]
