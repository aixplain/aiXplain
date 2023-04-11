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


import time
from aixplain.utils.config import PIPELINES_RUN_URL, PIPELINE_API_KEY
from aixplain.factories.pipeline_factory import PipelineFactory
import pytest

@pytest.mark.skip()
def test_mt1():
    url = PIPELINES_RUN_URL
    api_key = PIPELINE_API_KEY

    pipeline = PipelineFactory.create_from_api_key(api_key=api_key, url=url)

    data = "Hello World!"
    response = pipeline.run(data)
    assert response["status"] == "SUCCESS"

@pytest.mark.skip()
def test_mt2():
    url = PIPELINES_RUN_URL
    api_key = PIPELINE_API_KEY

    pipeline = PipelineFactory.create_from_api_key(api_key=api_key, url=url)

    data = "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/bestofyou.txt"
    response = pipeline.run(data)
    assert response["status"] == "SUCCESS"

@pytest.mark.skip()
def test_mt1_async():
    url = PIPELINES_RUN_URL
    api_key = PIPELINE_API_KEY

    pipeline = PipelineFactory.create_from_api_key(api_key=api_key, url=url)

    data = "Hello World!"
    response = pipeline.run_async(data)
    poll_url = response["url"]
    completed = False
    while not completed:
        response = pipeline.poll(poll_url)
        completed = response["completed"]
        time.sleep(3)
    assert response["status"] == "SUCCESS"

@pytest.mark.skip()
def test_mt2_async():
    url = PIPELINES_RUN_URL
    api_key = PIPELINE_API_KEY

    pipeline = PipelineFactory.create_from_api_key(api_key=api_key, url=url)

    data = "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/bestofyou.txt"
    response = pipeline.run_async(data)
    poll_url = response["url"]
    completed = False
    while not completed:
        response = pipeline.poll(poll_url)
        completed = response["completed"]
        time.sleep(3)
    assert response["status"] == "SUCCESS"