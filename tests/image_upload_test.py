__author__ = "michaellam"

import json
import requests_mock
from pathlib import Path
from aixplain.utils import config
from urllib.parse import urljoin

from aixplain.factories.model_factory import ModelFactory

AUTH_FIXED_HEADER = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
API_FIXED_HEADER = {"x-api-key": f"{config.TEAM_API_KEY}", "Content-Type": "application/json"}


def test_login():
    url =  urljoin(config.BACKEND_URL, f"sdk/ecr/login")
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/login_response.json")) as f:
            mock_json = json.load(f)
        mock.post(url, headers=AUTH_FIXED_HEADER, json=mock_json)
        creds = ModelFactory.asset_repo_login(config.TEAM_API_KEY)
    assert creds == mock_json

def test_create_asset_repo():
    url =  urljoin(config.BACKEND_URL, f"sdk/models/register")
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/create_asset_repo_response.json")) as f:
            mock_json = json.load(f)
        mock.post(url, headers=API_FIXED_HEADER, json=mock_json)
        model_id = ModelFactory.create_asset_repo("mock_name", "mock_machines", "mock_version", 
                          "mock_description", "mock_function", "en", config.TEAM_API_KEY)
    assert model_id == mock_json

def test_list_host_machines():
    url =  urljoin(config.BACKEND_URL, f"sdk/hosting-machines")
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/list_host_machines_response.json")) as f:
            mock_json = json.load(f)
        mock.get(url, headers=API_FIXED_HEADER, json=mock_json)
        machines = ModelFactory.list_host_machines(config.TEAM_API_KEY)
    '''
    machine_dict_list = []
    for machine in machines:
        machine_dict_list.append(json.loads(machine))
    mock_json_list = []
    for mock_json in mock_json_list:
        mock_json_list.append(json.loads(mock_json))
    '''
    for i in range(len(machines)):
        machine_dict = machines[i]
        mock_json_dict = mock_json[i]
        for key in machine_dict.keys():
            assert machine_dict[key] == mock_json_dict[key]

def test_get_functions():
    url =  urljoin(config.BACKEND_URL, f"sdk/functions")
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/list_functions_response.json")) as f:
            mock_json = json.load(f)
        mock.get(url, headers=AUTH_FIXED_HEADER, json=mock_json)
        functions = ModelFactory.list_functions(config.TEAM_API_KEY)
    assert functions == mock_json

def test_list_image_repo_tags():
    model_id = "mock_id"
    url =  urljoin(config.BACKEND_URL, f"sdk/models/{model_id}/images")
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/list_image_repo_tags_response.json")) as f:
            mock_json = json.load(f)
        mock.get(url, headers=AUTH_FIXED_HEADER, json=mock_json)
        tags = ModelFactory.list_image_repo_tags(model_id, config.TEAM_API_KEY)
    assert tags == mock_json