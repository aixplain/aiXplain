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
import requests_mock

load_dotenv()
import re
import json
from aixplain.utils import config
from aixplain.modules import Model
from aixplain.modules.model.utils import build_payload, call_run_endpoint
from aixplain.factories import ModelFactory
from aixplain.enums import Function
from urllib.parse import urljoin

import pytest


def test_build_payload():
    data = "input_data"
    parameters = {"context": "context_data"}
    ref_payload = json.dumps({"data": data, **parameters})
    hyp_payload = build_payload(data, parameters)
    assert hyp_payload == ref_payload


def test_call_run_endpoint_async():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = f"{base_url}/{model_id}"
    payload = {"data": "input_data"}
    ref_response = {
        "completed": True,
        "status": "IN_PROGRESS",
        "data": "https://models.aixplain.com/api/v1/data/a90c2078-edfe-403f-acba-d2d94cf71f42",
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=ref_response)
        response = call_run_endpoint(url=execute_url, api_key=config.TEAM_API_KEY, payload=payload)

    print(response)
    assert response["completed"] == ref_response["completed"]
    assert response["status"] == ref_response["status"]
    assert response["url"] == ref_response["data"]


def test_call_run_endpoint_sync():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = f"{base_url}/{model_id}".replace("/api/v1/execute", "/api/v2/execute")
    payload = {"data": "input_data"}
    ref_response = {"completed": True, "status": "SUCCESS", "data": "Hello"}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=ref_response)
        response = call_run_endpoint(url=execute_url, api_key=config.TEAM_API_KEY, payload=payload)

    assert response["completed"] == ref_response["completed"]
    assert response["status"] == ref_response["status"]
    assert response["data"] == ref_response["data"]


def test_success_poll():
    with requests_mock.Mocker() as mock:
        poll_url = "https://models.aixplain.com/api/v1/data/a90c2078-edfe-403f-acba-d2d94cf71f42"
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"completed": True, "data": "Concluded with success"}
        mock.get(poll_url, headers=headers, json=ref_response)
        test_model = Model("", "")
        hyp_response = test_model.poll(poll_url=poll_url)
    assert hyp_response["completed"] == ref_response["completed"]
    assert hyp_response["status"] == "SUCCESS"


def test_failed_poll():
    with requests_mock.Mocker() as mock:
        poll_url = "https://models.aixplain.com/api/v1/data/a90c2078-edfe-403f-acba-d2d94cf71f42"
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {
            "completed": True,
            "error": "err.supplier_error",
            "supplierError": re.escape(
                '{"error":{"message":"The model `<supplier_model_id>` does not exist","type":"invalid_request_error","param":null,"code":"model_not_found"}}'
            ),
        }
        mock.get(poll_url, headers=headers, json=ref_response)
        test_model = Model("", "")
        hyp_response = test_model.poll(poll_url=poll_url)
    assert hyp_response["completed"] == ref_response["completed"]
    assert hyp_response["error"] == ref_response["error"]
    assert hyp_response["supplierError"] == ref_response["supplierError"]
    assert hyp_response["status"] == "FAILED"


@pytest.mark.parametrize(
    "status_code,error_message",
    [
        (
            401,
            "Unauthorized API key: Please verify the spelling of the API key and its current validity. Details: {'error': 'An unspecified error occurred while processing your request.'}",
        ),
        (
            465,
            "Subscription-related error: Please ensure that your subscription is active and has not expired. Details: {'error': 'An unspecified error occurred while processing your request.'}",
        ),
        (
            475,
            "Billing-related error: Please ensure you have enough credits to run this model. Details: {'error': 'An unspecified error occurred while processing your request.'}",
        ),
        (
            485,
            "Supplier-related error: Please ensure that the selected supplier provides the model you are trying to access. Details: {'error': 'An unspecified error occurred while processing your request.'}",
        ),
        (
            495,
            "Validation-related error: Please ensure all required fields are provided and correctly formatted. Details: {'error': 'An unspecified error occurred while processing your request.'}",
        ),
        (501, "Status 501 - Unspecified error: {'error': 'An unspecified error occurred while processing your request.'}"),
    ],
)
def test_run_async_errors(status_code, error_message):
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = f"{base_url}/{model_id}"
    ref_response = {
        "error": "An unspecified error occurred while processing your request.",
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=status_code, json=ref_response)
        test_model = Model(id=model_id, name="Test Model", url=base_url)
        response = test_model.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == error_message


def test_get_model_error_response():
    with requests_mock.Mocker() as mock:
        model_id = "test-model-id"
        url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
        headers = {"x-aixplain-key": config.AIXPLAIN_API_KEY, "Content-Type": "application/json"}

        error_response = {"statusCode": 404, "message": "Model not found"}
        mock.get(url, headers=headers, json=error_response, status_code=404)

        with pytest.raises(Exception) as excinfo:
            ModelFactory.get(model_id)

        assert "Model GET Error: Failed to retrieve model test-model-id" in str(excinfo.value)


def test_get_assets_from_page_error():
    with requests_mock.Mocker() as mock:
        query = "test-query"
        page_number = 0
        page_size = 2
        url = urljoin(config.BACKEND_URL, "sdk/models/paginate")
        headers = {"x-aixplain-key": config.AIXPLAIN_API_KEY, "Content-Type": "application/json"}

        error_response = {"statusCode": 500, "message": "Internal Server Error"}
        mock.post(url, headers=headers, json=error_response, status_code=500)

        with pytest.raises(Exception) as excinfo:
            ModelFactory._get_assets_from_page(
                query=query,
                page_number=page_number,
                page_size=page_size,
                function=Function.TEXT_GENERATION,
                suppliers=None,
                source_languages=None,
                target_languages=None,
            )

        assert "Listing Models Error: Failed to retrieve models" in str(excinfo.value)
