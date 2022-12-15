__author__='lucaspavanelli'

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

import time
from aixtend.utils.config import MODELS_RUN_URL, MODEL_API_KEY
from aixtend.factories.model_factory import ModelFactory

def test_mt1():
    url = MODELS_RUN_URL
    api_key = MODEL_API_KEY

    model = ModelFactory.initialize(api_key=api_key, url=url)

    data = 'Hello World!'
    response = model.run(data)
    assert response['status'] == 'SUCCESS'

def test_mt2():
    url = MODELS_RUN_URL
    api_key = MODEL_API_KEY

    model = ModelFactory.initialize(api_key=api_key, url=url)

    data = 'https://aixplain-platform-assets.s3.amazonaws.com/samples/en/bestofyou.txt'
    response = model.run(data)
    assert response['status'] == 'SUCCESS'

def test_mt1_async():
    url = MODELS_RUN_URL
    api_key = MODEL_API_KEY

    model = ModelFactory.initialize(api_key=api_key, url=url)

    data = 'Hello World!'
    response = model.run_async(data)
    poll_url = response['url']
    completed = False
    while not completed:
        response = model.poll(poll_url)
        completed = response['completed']
        time.sleep(3)
    assert response['status'] == 'SUCCESS'

def test_mt2_async():
    url = MODELS_RUN_URL
    api_key = MODEL_API_KEY

    model = ModelFactory.initialize(api_key=api_key, url=url)

    data = 'https://aixplain-platform-assets.s3.amazonaws.com/samples/en/bestofyou.txt'
    response = model.run_async(data)
    poll_url = response['url']
    completed = False
    while not completed:
        response = model.poll(poll_url)
        completed = response['completed']
        time.sleep(3)
    assert response['status'] == 'SUCCESS'