__author__ = "lucaspavanelli"

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

import uuid
import json
from dotenv import load_dotenv

load_dotenv()
import requests_mock
from pathlib import Path
from aixplain.utils import config
from aixplain.factories import ModelFactory
from aixplain.factories import DatasetFactory
from aixplain.factories import FinetuneFactory
from aixplain.modules import Cost, Model

import pytest

FIXED_HEADER = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
COST_ESTIMATION_URL = f"{config.BACKEND_URL}/sdk/finetune/cost-estimation"
COST_ESTIMATION_FILE = "tests/unit/mock_responses/get_cost_estimation_response.json"
PERCENTAGE_EXCEPTION_FILE = "tests/unit/data/create_finetune_percentage_exception.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(PERCENTAGE_EXCEPTION_FILE))
def percentage_exception_map(request):
    return request.param


def test_create():
    with requests_mock.Mocker() as mock:
        cost_estimation_map = read_data(COST_ESTIMATION_FILE)
        mock.post(COST_ESTIMATION_URL, headers=FIXED_HEADER, json=cost_estimation_map)
        test_model = Model("", "")
        finetune = FinetuneFactory.create("", [], test_model)
    assert finetune is not None
    assert finetune.cost.to_dict() == cost_estimation_map


def test_create_train_dev_percentage(percentage_exception_map):
    with requests_mock.Mocker() as mock:
        cost_estimation_map = read_data(COST_ESTIMATION_FILE)
        mock.post(COST_ESTIMATION_URL, headers=FIXED_HEADER, json=cost_estimation_map)
        test_model = Model("", "")
        with pytest.raises(Exception) as exception_info:
            FinetuneFactory.create(
                "",
                [],
                test_model,
                train_percentage=percentage_exception_map["train_percentage"],
                dev_percentage=percentage_exception_map["dev_percentage"],
            )
    assert exception_info.type is AssertionError


def test_start():
    pass


def test_check_finetuner_status():
    pass


def test_list_finetunable_models():
    pass
