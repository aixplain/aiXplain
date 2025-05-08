__author__ = "thiagocastroferreira"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from dotenv import load_dotenv
import pytest

load_dotenv()
import requests_mock
from aixplain.utils import config
from aixplain.factories import PipelineFactory
from aixplain.modules import Pipeline
from urllib.parse import urljoin
from aixplain.enums import ResponseStatus
from aixplain.modules.pipeline.response import PipelineResponse


def test_create_pipeline():
    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, "sdk/pipelines")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"id": "12345"}
        mock.post(url, headers=headers, json=ref_response)
        ref_pipeline = Pipeline(id="12345", name="Pipeline Test", api_key=config.TEAM_API_KEY)
        hyp_pipeline = PipelineFactory.create(pipeline={"nodes": []}, name="Pipeline Test")
    assert hyp_pipeline.id == ref_pipeline.id
    assert hyp_pipeline.name == ref_pipeline.name


@pytest.mark.parametrize(
    "status_code,error_message",
    [
        (
            401,
            "{'error': 'Unauthorized API key: Please verify the spelling of the API key and its current validity.', 'status': 'ERROR'}",
        ),
        (
            465,
            "{'error': 'Subscription-related error: Please ensure that your subscription is active and has not expired.', 'status': 'ERROR'}",
        ),
        (
            475,
            "{'error': 'Billing-related error: Please ensure you have enough credits to run this asset.', 'status': 'ERROR'}",
        ),
        (
            485,
            "{'error': 'Supplier-related error: Please ensure that the selected supplier provides the asset you are trying to access.', 'status': 'ERROR'}",
        ),
        (
            495,
            "{'error': 'Validation-related error: Please verify the request payload and ensure it is correct.', 'status': 'ERROR'}",
        ),
        (
            501,
            "{'error': 'Unspecified Server Error (Status 501)', 'status': 'ERROR'}",
        ),
    ],
)
def test_run_async_errors(status_code, error_message):
    base_url = config.BACKEND_URL
    pipeline_id = "pipeline_id"
    execute_url = f"{base_url}/assets/pipeline/execution/run/{pipeline_id}"

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=status_code)
        test_pipeline = Pipeline(
            id=pipeline_id,
            api_key=config.TEAM_API_KEY,
            name="Test Pipeline",
            url=base_url,
        )
        response = test_pipeline.run_async(data="input_data")
    assert response["status"] == ResponseStatus.FAILED
    assert str(response["error"]) == error_message


def test_list_pipelines_error_response():
    with requests_mock.Mocker() as mock:
        query = "test-query"
        page_number = 0
        page_size = 20
        url = urljoin(config.BACKEND_URL, "sdk/pipelines/paginate")
        headers = {
            "Authorization": f"Token {config.AIXPLAIN_API_KEY}",
            "Content-Type": "application/json",
        }

        error_response = {"statusCode": 400, "message": "Bad Request"}
        mock.post(url, headers=headers, json=error_response, status_code=400)

        with pytest.raises(Exception) as excinfo:
            PipelineFactory.list(query=query, page_number=page_number, page_size=page_size)

        assert "Pipeline List Error: Failed to retrieve pipelines. Status Code: 400" in str(excinfo.value)


def test_get_pipeline_error_response():
    with requests_mock.Mocker() as mock:
        pipeline_id = "test-pipeline-id"
        url = urljoin(config.BACKEND_URL, f"sdk/pipelines/{pipeline_id}")
        headers = {
            "Authorization": f"Token {config.TEAM_API_KEY}",
            "Content-Type": "application/json",
        }

        error_response = {"statusCode": 404, "message": "Pipeline not found"}
        mock.get(url, headers=headers, json=error_response, status_code=404)

        with pytest.raises(Exception) as excinfo:
            PipelineFactory.get(pipeline_id=pipeline_id)

        assert "Pipeline GET Error: Failed to retrieve pipeline test-pipeline-id. Status Code: 404" in str(excinfo.value)


@pytest.fixture
def mock_pipeline():
    return Pipeline(id="12345", name="Pipeline Test", api_key=config.TEAM_API_KEY)


def test_run_async_success(mock_pipeline):
    with requests_mock.Mocker() as mock:
        execute_url = urljoin(config.BACKEND_URL, f"assets/pipeline/execution/run/{mock_pipeline.id}")
        success_response = PipelineResponse(status=ResponseStatus.SUCCESS, url=execute_url)
        mock.post(execute_url, json=success_response.__dict__, status_code=200)

        response = mock_pipeline.run_async(data="input_data")

    assert isinstance(response, PipelineResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_run_sync_success(mock_pipeline):
    with requests_mock.Mocker() as mock:
        poll_url = urljoin(config.BACKEND_URL, f"assets/pipeline/execution/poll/{mock_pipeline.id}")
        execute_url = urljoin(config.BACKEND_URL, f"assets/pipeline/execution/run/{mock_pipeline.id}")
        success_response = {"status": "SUCCESS", "url": poll_url, "completed": True}
        poll_response = {"status": "SUCCESS", "data": {"output": "poll_result"}, "completed": True}
        mock.post(execute_url, json=success_response, status_code=200)
        mock.get(poll_url, json=poll_response, status_code=200)
        response = mock_pipeline.run(data="input_data")

    assert isinstance(response, PipelineResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_poll_success(mock_pipeline):
    with requests_mock.Mocker() as mock:
        poll_url = urljoin(config.BACKEND_URL, f"assets/pipeline/execution/poll/{mock_pipeline.id}")
        poll_response = PipelineResponse(status=ResponseStatus.SUCCESS, data={"output": "poll_result"})
        mock.get(poll_url, json=poll_response.__dict__, status_code=200)

        response = mock_pipeline.poll(poll_url=poll_url)

    assert isinstance(response, PipelineResponse)
    assert response.status == ResponseStatus.SUCCESS
    assert response.data["output"] == "poll_result"


def test_deploy_pipeline():
    with requests_mock.Mocker() as mock:
        pipeline_id = "test-pipeline-id"
        url = urljoin(config.BACKEND_URL, f"sdk/pipelines/{pipeline_id}")
        headers = {
            "Authorization": f"Token {config.TEAM_API_KEY}",
            "Content-Type": "application/json",
        }

        mock.put(url, headers=headers, json={"status": "SUCCESS", "id": pipeline_id})

        pipeline = Pipeline(
            id=pipeline_id,
            api_key=config.TEAM_API_KEY,
            name="Test Pipeline",
            url=config.BACKEND_URL,
        )
        pipeline.deploy()

        assert pipeline.id == pipeline_id
        assert pipeline.status.value == "onboarded"
