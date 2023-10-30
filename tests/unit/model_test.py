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
