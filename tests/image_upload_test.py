__author__ = "michaellam"

import json
import pytest
import requests_mock
from pathlib import Path
from aixplain.utils import config

from aixplain.factories.model_factory import ModelFactory
from aixplain.factories.dataset_factory import DatasetFactory
from aixplain.factories.metric_factory import MetricFactory

AUTH_FIXED_HEADER = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
API_FIXED_HEADER = {"x-api-key": f"{config.TEAM_API_KEY}", "Content-Type": "application/json"}


def test_login():
    url =  f"{config.BACKEND_URL}sdk/ecr/login"
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/login_response.json")) as f:
            mock_json = json.load(f)
        mock.post(url, headers=AUTH_FIXED_HEADER, json=mock_json)
        creds = ModelFactory.asset_repo_login(config.TEAM_API_KEY)
    assert creds == mock_json

def test_create_asset_repo():
    url =  f"{config.BACKEND_URL}sdk/models/register"
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/create_asset_repo_response.json")) as f:
            mock_json = json.load(f)
        mock.post(url, headers=API_FIXED_HEADER, json=mock_json)
        model_id = ModelFactory.create_asset_repo("mock_name", "mock_machines", True, "mock_version", 
                          "mock_description", "mock_function", False, config.TEAM_API_KEY)
    assert model_id == mock_json

def test_list_host_machines():
    url =  f"{config.BACKEND_URL}sdk/hosting-machines"
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/list_host_machines_response.json")) as f:
            mock_json = json.load(f)
        mock.get(url, headers=API_FIXED_HEADER, json=mock_json)
        machines = ModelFactory.list_host_machines(config.TEAM_API_KEY)
    assert machines == mock_json