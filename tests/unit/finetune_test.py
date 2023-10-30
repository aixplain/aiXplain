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
from aixplain.utils import config
from aixplain.factories import ModelFactory
from aixplain.factories import FinetuneFactory
from aixplain.modules import Model, Finetune
from aixplain.enums import Function

import pytest

FIXED_HEADER = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
COST_ESTIMATION_URL = f"{config.BACKEND_URL}/sdk/finetune/cost-estimation"
COST_ESTIMATION_FILE = "tests/unit/mock_responses/cost_estimation_response.json"
FINETUNE_URL = f"{config.BACKEND_URL}/sdk/finetune"
FINETUNE_FILE = "tests/unit/mock_responses/finetune_response.json"
PERCENTAGE_EXCEPTION_FILE = "tests/unit/data/create_finetune_percentage_exception.json"
MODEL_FILE = "tests/unit/mock_responses/model_response.json"
MODEL_URL = f"{config.BACKEND_URL}/sdk/models"
LIST_FINETUNABLE_FILE = "tests/unit/mock_responses/list_models_response.json"


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
    finetune_map = read_data(FINETUNE_FILE)
    model_map = read_data(MODEL_FILE)
    asset_id = finetune_map["id"]
    with requests_mock.Mocker() as mock:
        url = f"{MODEL_URL}/{asset_id}"
        mock.get(url, headers=FIXED_HEADER, json=model_map)
        mock.post(FINETUNE_URL, headers=FIXED_HEADER, json=finetune_map)
        test_model = Model("", "")
        finetune = Finetune("", [], test_model, None)
        fine_tuned_model = finetune.start()
    assert fine_tuned_model is not None
    assert fine_tuned_model.id == model_map["id"]


def test_check_finetuner_status():
    model_map = read_data(MODEL_FILE)
    asset_id = "test_id"
    with requests_mock.Mocker() as mock:
        test_model = Model(asset_id, "")
        url = f"{MODEL_URL}/{asset_id}"
        mock.get(url, headers=FIXED_HEADER, json=model_map)
        status = test_model.check_finetune_status()
    assert status == model_map["status"]


@pytest.mark.parametrize("is_finetunable", [True, False])
def test_list_finetunable_models(is_finetunable):
    list_map = read_data(LIST_FINETUNABLE_FILE)
    with requests_mock.Mocker() as mock:
        print(f"is_finetunable: {is_finetunable}")
        url = f"{config.BACKEND_URL}/sdk/models/paginate"
        mock.post(url, headers=FIXED_HEADER, json=list_map)
        result = ModelFactory.list(function=Function.TRANSLATION, is_finetunable=is_finetunable, page_number=0, page_size=5)
        print(result)
    assert result["page_total"] == 5
    assert result["page_number"] == 0
    model_list = result["results"]
    assert len(model_list) > 0
    for model_index in range(len(model_list)):
        assert model_list[model_index].id == list_map["items"][model_index]["id"]
