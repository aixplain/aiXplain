import json
from dotenv import load_dotenv
load_dotenv()
from aixplain.factories import ModelFactory, DatasetFactory, MetricFactory, PipelineFactory
from pathlib import Path

import pytest

INPUTS_PATH = Path(r"tests\functional\general_assets\data\asset_run_test_data.json")

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


@pytest.mark.parametrize(
    "asset_name", ["model", "dataset", "metric"]
)
def test_list(asset_name):
    AssetFactory = __get_asset_factory(asset_name)
    asset_list = AssetFactory.list()
    assert asset_list["page_total"] == len(asset_list["results"])


@pytest.mark.parametrize(
    "asset_name", ["model", "pipeline", "metric"]
)
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
