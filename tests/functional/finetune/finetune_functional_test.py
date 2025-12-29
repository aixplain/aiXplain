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


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


@pytest.mark.parametrize("FinetuneFactory", [FinetuneFactory])
def test_end2end(run_input_map, FinetuneFactory):
    model = run_input_map["model_id"]
    dataset_list = [DatasetFactory.list(query=run_input_map["dataset_name"])["results"][0]]
    train_percentage, dev_percentage = 100, 0
    if run_input_map["required_dev"]:
        train_percentage, dev_percentage = 80, 20
    finetune = FinetuneFactory.create(
        str(uuid.uuid4()),
        dataset_list,
        model,
        train_percentage=train_percentage,
        dev_percentage=dev_percentage,
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
    result = finetune_model.run(run_input_map["inference_data"])
    print(f"Result: {result}")
    assert result is not None
    if run_input_map["search_metadata"]:
        assert "details" in result
        assert len(result["details"]) > 0
        assert "metadata" in result["details"][0]
        assert len(result["details"][0]["metadata"]) > 0
    finetune_model.delete()


@pytest.mark.parametrize("FinetuneFactory", [FinetuneFactory])
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
    # Check if we're using v2.Model (which uses search()) or v1 ModelFactory (which uses list())
    if ModelFactory.__name__ == "Model" and hasattr(ModelFactory, "search"):
        # v2 API: use search() method with functions as list of strings
        # Note: v2.Model.search() requires a context, so we use the default aixplain_v2 instance
        # which is created at module import time
        page = ModelFactory.search(
            functions=[list_input_map["function"]],
            source_languages=(
                Language(list_input_map["source_language"]) if "source_language" in list_input_map else None
            ),
            target_languages=(
                Language(list_input_map["target_language"]) if "target_language" in list_input_map else None
            ),
            is_finetunable=True,
        )
        model_list = page.results
    else:
        # v1 API: use list() method
        model_list = ModelFactory.list(
            function=Function(list_input_map["function"]),
            source_languages=(
                Language(list_input_map["source_language"]) if "source_language" in list_input_map else None
            ),
            target_languages=(
                Language(list_input_map["target_language"]) if "target_language" in list_input_map else None
            ),
            is_finetunable=True,
        )["results"]
    assert len(model_list) > 0


@pytest.mark.parametrize("ModelFactory", [ModelFactory, v2.Model])
def test_prompt_validator(validate_prompt_input_map, ModelFactory):
    model = ModelFactory.get(validate_prompt_input_map["model_id"])
    dataset_list = [DatasetFactory.list(query=validate_prompt_input_map["dataset_name"])["results"][0]]
    if validate_prompt_input_map["is_valid"]:
        finetune = FinetuneFactory.create(
            str(uuid.uuid4()),
            dataset_list,
            model,
            prompt_template=validate_prompt_input_map["prompt_template"],
        )
        assert finetune is not None
    else:
        with pytest.raises(Exception) as exc_info:
            finetune = FinetuneFactory.create(
                str(uuid.uuid4()),
                dataset_list,
                model,
                prompt_template=validate_prompt_input_map["prompt_template"],
            )
        assert exc_info.type is AssertionError
