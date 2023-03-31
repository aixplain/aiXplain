__author__='shreyassharma'

import json
import pytest
import requests_mock
from pathlib import Path
from aixplain.utils import config

from aixplain.factories.model_factory  import ModelFactory
from aixplain.factories.dataset_factory  import DatasetFactory
from aixplain.factories.metric_factory  import MetricFactory

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
            with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
                mock_json = json.load(f)[asset_name]
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
            with open(Path("tests/mock_responses/list_assets_responses.json")) as f:
                mock_json = json.load(f)[asset_name]
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
            with open(Path("tests/mock_responses/list_assets_responses.json")) as f:
                mock_json = json.load(f)[asset_name]
            for page_number in range(k//10 + 1):
                url = url_dict[asset_name].replace("<page_number>", str(page_number))
                mock.get( url, headers=FIXED_HEADER, json=mock_json)
            asset_list = AssetFactory.get_first_k_assets(k, task)
            for asset in asset_list:
                assert asset.id == asset_id

def test_metric_listing():
    task = "test_task"
    asset_id = "test_asset_id"
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/list_assets_responses.json")) as f:
            mock_json = json.load(f)['metric']
        url = f"{config.BENCHMARKS_BACKEND_URL}/sdk/scores?function={task}"
        mock.get(url, headers=FIXED_HEADER, json=mock_json)
        metric_list = MetricFactory.list_assets(task)
    for metric in metric_list:
        assert metric.id == asset_id

def test_run_model():
    asset_id = "test_asset_id"
    with requests_mock.Mocker() as mock:
        url = f"{config.BENCHMARKS_BACKEND_URL}/sdk/inventory/models/{asset_id}"
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json = json.load(f)["model"]
        mock.get(url, headers=FIXED_HEADER, json=mock_json)
        model = ModelFactory.create_asset_from_id(asset_id)
        data = "Hello World!"
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json_start = json.load(f)["modelStart"]
        headers = {"x-api-key": model.api_key, "Content-Type": "application/json"}
        mock.post(f"{model.url}/{asset_id}", headers=headers, json=mock_json_start, status_code=200)
        poll_url = mock_json_start['data']
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json_run = json.load(f)["modelRunResult"]
        mock.get(poll_url, headers=headers, json=mock_json_run, status_code=200)
        response = model.run(data)
        print(response)
    assert response == mock_json_run


        