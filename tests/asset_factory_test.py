import json
import pytest
import requests_mock
from pathlib import Path
from aixtend.utils import config

from aixtend.factories.model_factory  import ModelFactory
from aixtend.factories.dataset_factory  import DatasetFactory
from aixtend.factories.metric_factory  import MetricFactory

FIXED_HEADER = {
    'Authorization': f"Token {config.TEAM_API_KEY}",
    'Content-Type': 'application/json'
}

def __get_asset_factory(asset_name):
    if asset_name == "model":
        AssetFactory = ModelFactory
    elif asset_name == "dataset":
        AssetFactory = DatasetFactory
    elif asset_name == "metric":
        AssetFactory = MetricFactory
    return AssetFactory

def test_asset_creation_from_id():
    asset_list = ["model", "metric", "dataset"]
    asset_id = "test_asset_id"
    url_dict = {
        "model" : f"{config.BENCHMARKS_BACKEND_URL}/sdk/inventory/models/{asset_id}",
        "metric": f"{config.BENCHMARKS_BACKEND_URL}/sdk/scores/{asset_id}",
        "dataset": f"{config.BENCHMARKS_BACKEND_URL}/sdk/datasets/{asset_id}",
    }
    for asset_name in asset_list:
        AssetFactory = __get_asset_factory(asset_name)
        with requests_mock.Mocker() as mock:
            url = url_dict[asset_name]
            mock_json = json.load(open(Path("tests\mock_responses\get_asset_info_responses.json")))[asset_name]
            mock.get( url, headers=FIXED_HEADER, json=mock_json)
            asset = AssetFactory.create_asset_from_id(asset_id)
        assert asset.get_asset_info()['id'] == asset_id

def test_asset_listing_from_page():
    asset_list = ["model", "dataset"]
    asset_id = "test_asset_id"
    page_number = 0
    task = "test_task"
    url_dict = {
        "model" : f"{config.BENCHMARKS_BACKEND_URL}/sdk/inventory/models/?pageNumber={page_number}&function={task}",
        "dataset": f"{config.BENCHMARKS_BACKEND_URL}/sdk/datasets?pageNumber={page_number}&function={task}"
    }
    for asset_name in asset_list:
        AssetFactory = __get_asset_factory(asset_name)
        with requests_mock.Mocker() as mock:
            url = url_dict[asset_name]
            mock_json = json.load(open(Path("tests\mock_responses\list_assets_responses.json")))[asset_name]
            mock.get( url, headers=FIXED_HEADER, json=mock_json)
            asset_list = AssetFactory.get_assets_from_page(page_number, task)
            for asset in asset_list:
                assert asset.id == asset_id

def test_k_asset_listing():
    asset_list = ["model", "dataset"]
    asset_id = "test_asset_id"
    k = 15
    task = "test_task"
    url_dict = {
        "model" : f"{config.BENCHMARKS_BACKEND_URL}/sdk/inventory/models/?pageNumber=<page_number>&function={task}",
        "dataset": f"{config.BENCHMARKS_BACKEND_URL}/sdk/datasets?pageNumber=<page_number>&function={task}"
    }
    for asset_name in asset_list:
        AssetFactory = __get_asset_factory(asset_name)
        with requests_mock.Mocker() as mock:
            mock_json = json.load(open(Path("tests\mock_responses\list_assets_responses.json")))[asset_name]
            for page_number in range(k//10 + 1):
                url = url_dict[asset_name].replace("<page_number>", str(page_number))
                mock.get( url, headers=FIXED_HEADER, json=mock_json)
            asset_list = AssetFactory.get_first_k_assets(k, task)
            for asset in asset_list:
                assert asset.id == asset_id



