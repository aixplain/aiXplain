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
import time
import json
from dotenv import load_dotenv

load_dotenv()
from aixplain.factories import ModelFactory
from aixplain.factories import DatasetFactory
from aixplain.factories import FinetuneFactory
from aixplain.modules import FinetuneCost
from aixplain.enums import Function, Language

import pytest

TIMEOUT = 20000.0
RUN_FILE = "tests/functional/finetune/data/finetune_test_run_data.json"
LIST_FILE = "tests/functional/finetune/data/finetune_test_list_data.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


@pytest.fixture(scope="module", params=read_data(LIST_FILE))
def list_input_map(request):
    return request.param

def test_run(run_input_map):
    model = ModelFactory.get(run_input_map["model_id"])
    dataset_list = [DatasetFactory.get(run_input_map["dataset_id"])]
    finetune = FinetuneFactory.create(str(uuid.uuid4()), dataset_list, model)
    assert type(finetune.cost) is FinetuneCost
    cost_map = finetune.cost.to_dict()
    assert "trainingCost" in cost_map
    assert "hostingCost" in cost_map
    assert "inferenceCost" in cost_map
    finetune_model = finetune.start()
    start, end = time.time(), time.time()
    status = finetune_model.check_finetune_status()
    while status != "onboarded" and (end - start) < TIMEOUT:
        status = finetune_model.check_finetune_status()
        assert status != "failed"
        end = time.time()
    assert finetune_model.check_finetune_status() == "onboarded"

def test_list_finetunable_models(list_input_map):
    model_list = ModelFactory.list(
        function=Function(list_input_map["function"]),
        source_languages=Language(list_input_map["source_language"]) if "source_language" in list_input_map else None,
        target_languages=Language(list_input_map["target_language"]) if "target_language" in list_input_map else None,
        is_finetunable=True,
    )
    assert len(model_list) > 0
