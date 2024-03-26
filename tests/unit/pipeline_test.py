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
import requests_mock
from aixplain.utils import config
from aixplain.factories import PipelineFactory
from aixplain.modules import Pipeline
from urllib.parse import urljoin
import pytest


def test_create_pipeline():
    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, "sdk/pipelines")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"id": "12345"}
        mock.post(url, headers=headers, json=ref_response)
        ref_pipeline = Pipeline(id="12345", name="Pipeline Test", api_key=config.TEAM_API_KEY)
        hyp_pipeline = PipelineFactory.create(pipeline={}, name="Pipeline Test")
    assert hyp_pipeline.id == ref_pipeline.id
    assert hyp_pipeline.name == ref_pipeline.name
