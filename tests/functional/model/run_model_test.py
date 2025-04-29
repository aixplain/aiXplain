__author__ = "thiagocastroferreira"

from aixplain.enums import Function
from aixplain.factories import ModelFactory
from aixplain.modules import LLM
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
import random
import json

MULTI_ASSET_DATA_INPUT = Path(__file__).parent / "data" / "multi_asset_data.json"

def get_llm_models(number_of_models: int = 5):
    """Helper function to get list of LLM models for testing"""
    four_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=4)
    models = ModelFactory.list(function=Function.TEXT_GENERATION)["results"]
    
    # Get predefined models
    predefined_models = []
    for predefined_model in ["Llama 3.2 1B Instruct", "Chat GPT 3.5", "GPT-4", "GPT-4o Mini", "GPT-4.1 Nano"]:
        predefined_models.extend([
            m for m in ModelFactory.list(query=predefined_model, function=Function.TEXT_GENERATION)["results"]
            if m.name == predefined_model and "aiXplain-testing" not in str(m.supplier)
        ])
    
    # Get recent models
    recent_models = [
        model for model in models 
        if model.created_at and model.created_at >= four_weeks_ago and "aiXplain-testing" not in str(model.supplier)
    ]
    
    return random.sample(recent_models + predefined_models, number_of_models)


def fetch_multi_asset_parameters(return_in_order: bool = True):
    """Helper function to fetch multi asset parameters"""
    with open(MULTI_ASSET_DATA_INPUT, "r") as f:
        data = json.load(f)
    
    items = list(data.items())
    if not return_in_order:
        random.shuffle(items)

    for function, function_data in items:
        selected_model = random.choice(function_data["model_ids"])
        input_data = function_data["input"]
        if "speech-recognition" in function:
            input_data = Path(__file__).parent / input_data
            input_data = input_data.resolve()
            input_data = str(input_data)
        output_keyword = function_data["output_keyword"]

        yield function, selected_model, input_data, output_keyword



@pytest.mark.parametrize("llm_model", get_llm_models(number_of_models=3), ids=lambda model: f"{model.name.replace(' ', '_')}({model.id})")
def test_llm_name_response(llm_model):
    """Testing LLMs with history context"""

    name = "Richard Feynman"
    history = [
        {"role": "user", "content": f"Hello! My name is {name}."},
        {"role": "assistant", "content": "Hello!"},
    ]
    question = f"What is my name?"

    assert isinstance(llm_model, LLM)
    response = llm_model.run(
        data=question,
        history=history,
    )
    assert response["status"] == "SUCCESS"
    assert name.lower() in response["data"].lower() 


def test_run_async():
    """Testing Model Async"""
    function, selected_model, input_data, output_keyword = next(fetch_multi_asset_parameters(return_in_order=False))
    print(f"Testing {function} with {selected_model} and {input_data} and {output_keyword}")
    model = ModelFactory.get(selected_model)
    response = model.run_async(input_data)
    poll_url = response["url"]
    response = model.sync_poll(poll_url)
    assert response["status"] == "SUCCESS"
    assert output_keyword.lower() in response["data"].lower()


def test_index_model():
    from uuid import uuid4
    from aixplain.modules.model.record import Record
    from aixplain.factories import IndexFactory

    for index in IndexFactory.list()["results"]:
        index.delete()

    index_model = IndexFactory.create(name=str(uuid4()), description=str(uuid4()))
    index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})])
    response = index_model.search("Hello")
    assert str(response.status) == "SUCCESS"
    assert "world" in response.data.lower()
    assert index_model.count() == 1
    index_model.upsert([Record(value="Hello, aiXplain!", value_type="text", uri="", id="1", attributes={})])
    response = index_model.search("aiXplain")
    assert str(response.status) == "SUCCESS"
    assert "aixplain" in response.data.lower()
    assert index_model.count() == 1
    index_model.delete()


def test_llm_run_with_file():
    """Testing LLM with local file input containing emoji"""

    # Create test file path
    test_file_path = Path(__file__).parent / "data" / "test_input.txt"

    # Get a text generation model
    llm_model = ModelFactory.get("674a17f6098e7d5b18453da7")  # Llama 3.1 Nemotron 70B Instruct

    assert isinstance(llm_model, LLM)

    # Run model with file path
    response = llm_model.run(data=str(test_file_path))

    # Verify response
    assert response["status"] == "SUCCESS"
    assert "🤖" in response["data"], "Robot emoji should be present in the response"




@pytest.mark.parametrize("function, selected_model, input_data, output_keyword", fetch_multi_asset_parameters())
def test_multi_asset_run(function, selected_model, input_data, output_keyword):
    """Testing Multi Asset Run"""
    print(f"Testing {function} with {selected_model} and {input_data} and {output_keyword}")
    model = ModelFactory.get(selected_model)
    response = model.run(input_data)
    assert response["status"] == "SUCCESS"
    assert output_keyword.lower() in response["data"].lower()
