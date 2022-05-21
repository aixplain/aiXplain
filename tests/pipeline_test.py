__author__='thiagocastroferreira'

"""
Copyright 2022 The aiXplain pipeline authors

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

from aixplain_pipelines.utils.config import TEST_PIPELINES_RUN_URL, TEST_API_KEY
from aixplain_pipelines import Pipeline

def test_mt1():
    url = TEST_PIPELINES_RUN_URL
    api_key = TEST_API_KEY

    pipeline = Pipeline(api_key=api_key, url=url)

    data = 'Hello World!'

    response = pipeline.run(data)
    assert response['success'] == True

def test_mt2():
    url = TEST_PIPELINES_RUN_URL
    api_key = TEST_API_KEY

    pipeline = Pipeline(api_key=api_key, url=url)

    data = 'https://aixplain-samples-public.s3.amazonaws.com/pipelines/radiogaga.txt'
    response = pipeline.run(data)
    assert response['success'] == True