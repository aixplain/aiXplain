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
from aixplain.modules.finetune.cost import FinetuneCost
from aixplain.enums import Function, Language
from datetime import datetime, timedelta, timezone

import pytest
from aixplain import aixplain_v2 as v2

TIMEOUT = 20000.0
RUN_FILE = "tests/functional/finetune/data/finetune_test_end2end.json"
ESTIMATE_COST_FILE = "tests/functional/finetune/data/finetune_test_cost_estimation.json"
LIST_FILE = "tests/functional/finetune/data/finetune_test_list_data.json"
PROMPT_FILE = "tests/functional/finetune/data/finetune_test_prompt_validator.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(ESTIMATE_COST_FILE))
def estimate_cost_input_map(request):
    return request.param


@pytest.fixture(scope="module", params=read_data(LIST_FILE))
def list_input_map(request):
    return request.param


@pytest.fixture(scope="module", params=read_data(PROMPT_FILE))
def validate_prompt_input_map(request):
    return request.param


def pytest_generate_tests(metafunc):
    if "input_map" in metafunc.fixturenames:
        four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
        models = ModelFactory.list(function=Function.TEXT_GENERATION, is_finetunable=True)["results"]
        recent_models = [
            {
                "model_name": model.name,
                "model_id": model.id,
                "dataset_name": "Test text generation dataset",
                "inference_data": "Hello!",
                "required_dev": True,
                "search_metadata": False,
            }
            for model in models
            if model.created_at is not None
            and model.created_at >= four_weeks_ago
            and "aiXplain-testing" not in str(model.supplier)
        ]

        run_file_models = read_data(RUN_FILE)
        for model_data in run_file_models:
            if not any(rm["model_id"] == model_data["model_id"] for rm in recent_models):
                recent_models.append(model_data)
        model_ids = [model["model_id"] for model in recent_models]
        metafunc.parametrize("input_map", recent_models, ids=model_ids)


@pytest.mark.parametrize("FinetuneFactory", [FinetuneFactory, v2.Finetune])
def test_end2end(input_map, FinetuneFactory):
    model = input_map["model_id"]
    dataset_list = [DatasetFactory.list(query=input_map["dataset_name"])["results"][0]]
    train_percentage, dev_percentage = 100, 0
    if input_map["required_dev"]:
        train_percentage, dev_percentage = 80, 20
    finetune = FinetuneFactory.create(
        str(uuid.uuid4()), dataset_list, model, train_percentage=train_percentage, dev_percentage=dev_percentage
    )
    assert type(finetune.cost) is FinetuneCost
    cost_map = finetune.cost.to_dict()
    assert "trainingCost" in cost_map
    assert "hostingCost" in cost_map
    assert "inferenceCost" in cost_map
    finetune_model = finetune.start()
    start, end = time.time(), time.time()
    status = finetune_model.check_finetune_status().model_status.value
    while status != "onboarded" and (end - start) < TIMEOUT:
        status = finetune_model.check_finetune_status().model_status.value
        assert status != "failed"
        time.sleep(5)
        end = time.time()
    assert finetune_model.check_finetune_status().model_status.value == "onboarded"
    time.sleep(30)
    print(f"Model dict: {finetune_model.__dict__}")
    result = finetune_model.run(input_map["inference_data"])
    print(f"Result: {result}")
    assert result is not None
    if input_map["search_metadata"]:
        assert "details" in result
        assert len(result["details"]) > 0
        assert "metadata" in result["details"][0]
        assert len(result["details"][0]["metadata"]) > 0
    finetune_model.delete()


@pytest.mark.parametrize("FinetuneFactory", [FinetuneFactory, v2.Finetune])
def test_cost_estimation_text_generation(estimate_cost_input_map, FinetuneFactory):
    model = ModelFactory.get(estimate_cost_input_map["model_id"])
    dataset_list = [DatasetFactory.list(query=estimate_cost_input_map["dataset_name"])["results"][0]]
    finetune = FinetuneFactory.create(str(uuid.uuid4()), dataset_list, model)
    assert type(finetune.cost) is FinetuneCost
    cost_map = finetune.cost.to_dict()
    assert "trainingCost" in cost_map
    assert "hostingCost" in cost_map
    assert "inferenceCost" in cost_map


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_list_finetunable_models(list_input_map, ModelFactory):
    model_list = ModelFactory.list(
        function=Function(list_input_map["function"]),
        source_languages=Language(list_input_map["source_language"]) if "source_language" in list_input_map else None,
        target_languages=Language(list_input_map["target_language"]) if "target_language" in list_input_map else None,
        is_finetunable=True,
    )["results"]
    assert len(model_list) > 0


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_prompt_validator(validate_prompt_input_map, ModelFactory):
    model = ModelFactory.get(validate_prompt_input_map["model_id"])
    dataset_list = [DatasetFactory.list(query=validate_prompt_input_map["dataset_name"])["results"][0]]
    if validate_prompt_input_map["is_valid"]:
        finetune = FinetuneFactory.create(
            str(uuid.uuid4()), dataset_list, model, prompt_template=validate_prompt_input_map["prompt_template"]
        )
        assert finetune is not None
    else:
        with pytest.raises(Exception) as exc_info:
            finetune = FinetuneFactory.create(
                str(uuid.uuid4()), dataset_list, model, prompt_template=validate_prompt_input_map["prompt_template"]
            )
        assert exc_info.type is AssertionError
