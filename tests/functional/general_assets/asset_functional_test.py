import json
from dotenv import load_dotenv

load_dotenv()
from aixplain.factories import ModelFactory, DatasetFactory, MetricFactory, PipelineFactory
from pathlib import Path
from aixplain.enums import Function, Supplier

import pytest

INPUTS_PATH = Path(r"tests/functional/general_assets/data/asset_run_test_data.json")


@pytest.fixture
def inputs():
    with open(INPUTS_PATH) as f:
        return json.load(f)


def __get_asset_factory(asset_name):
    if asset_name == "model":
        AssetFactory = ModelFactory
    elif asset_name == "dataset":
        AssetFactory = DatasetFactory
    elif asset_name == "metric":
        AssetFactory = MetricFactory
    elif asset_name == "pipeline":
        AssetFactory = PipelineFactory
    return AssetFactory


@pytest.mark.parametrize("asset_name", ["model", "dataset", "metric"])
def test_list(asset_name):
    AssetFactory = __get_asset_factory(asset_name)
    asset_list = AssetFactory.list()
    assert asset_list["page_total"] == len(asset_list["results"])


@pytest.mark.parametrize("asset_name", ["model", "pipeline", "metric"])
def test_run(inputs, asset_name):
    asset_details = inputs[asset_name]
    AssetFactory = __get_asset_factory(asset_name)
    asset = AssetFactory.get(asset_details["id"])
    payload = asset_details["data"]
    if type(payload) is dict:
        output = asset.run(**payload)
    else:
        output = asset.run(payload)
    assert output["completed"] and output["status"] == "SUCCESS"

def test_model_function():
    desired_function = Function.TRANSLATION
    models = ModelFactory.list(function=desired_function)['results']
    for model in models:
        assert model.function == desired_function
        
def test_model_supplier():
    desired_suppliers = [Supplier.GOOGLE]
    models = ModelFactory.list(suppliers = desired_suppliers)['results']
    for model in models:
        assert model.supplier in [desired_supplier.value for desired_supplier in desired_suppliers]
        
def test_model_query():
    query = "Mongo"
    models = ModelFactory.list(query = query)['results']
    for model in models:
        assert query in model.name