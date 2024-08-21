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
from urllib.parse import urljoin
import requests_mock

load_dotenv()
import re
import requests_mock
from aixplain.utils import config
from aixplain.modules import Model

import pytest


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

def test_run_async_unauthorized_error():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = urljoin(base_url, f"execute/{model_id}")
    
    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=401)
        test_model = Model(id=model_id, name="Test Model",url=base_url)
        response = test_model.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == "Unauthorized API key: Please verify the spelling of the API key and its current validity."

def test_run_async_subscription_error():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = urljoin(base_url, f"execute/{model_id}")
    
    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=465)
        test_model = Model(id=model_id, name="Test Model",url=base_url)
        response = test_model.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == "Subscription-related error: Please ensure that your subscription is active and has not expired."

def test_run_async_billing_error():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = urljoin(base_url, f"execute/{model_id}")
    
    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=475)
        test_model = Model(id=model_id, name="Test Model",url=base_url)
        response = test_model.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == "Billing-related error: Please ensure you have enough credits to run this model. "

def test_run_async_supplier_error():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = urljoin(base_url, f"execute/{model_id}")
    
    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=485)
        test_model = Model(id=model_id, name="Test Model",url=base_url)
        response = test_model.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == "Supplier-related error: Please ensure that the selected supplier provides the model you are trying to access."


def test_run_async_validation_error():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = urljoin(base_url, f"execute/{model_id}")
    
    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=495)
        test_model = Model(id=model_id, name="Test Model",url=base_url)
        response = test_model.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == "Validation-related error: Please ensure all required fields are provided and correctly formatted."


def test_run_async_unspecified_error():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = urljoin(base_url, f"execute/{model_id}")
    
    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=501)
        test_model = Model(id=model_id, name="Test Model",url=base_url)
        response = test_model.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == "Status 501: Unspecified error: An unspecified error occurred while processing your request."




