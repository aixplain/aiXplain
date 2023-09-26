__author__ = "michaellam"
from pathlib import Path
import json
import requests

from aixplain.factories.model_factory import ModelFactory

def test_login():
    response = ModelFactory.asset_repo_login()
    assert response["username"] == "AWS"
    assert response["registry"] == "535945872701.dkr.ecr.us-east-1.amazonaws.com"

def test_create_asset_repo():
    with open(Path("tests/mock_requests/create_asset_request.json")) as f:
        mock_register_payload = json.load(f)
    name = mock_register_payload["name"]
    host_machine = mock_register_payload["hostingMachine"]
    version = mock_register_payload["version"]
    description = mock_register_payload["description"]
    function = mock_register_payload["function"]
    source_language = mock_register_payload["source_language"]
    response = ModelFactory.create_asset_repo(name, host_machine, version, description, function, source_language)
    response_dict = dict(response)
    assert "id" in response_dict.keys()
    assert "repositoryName" in response_dict.keys()

def test_list_host_machines():
    response = ModelFactory.list_host_machines()
    for hosting_machine_dict in response:
        assert "code" in hosting_machine_dict.keys()
        assert "type" in hosting_machine_dict.keys()
        assert "cores" in hosting_machine_dict.keys()
        assert "memory" in hosting_machine_dict.keys()
        assert "hourlyCost" in hosting_machine_dict.keys()

def test_get_functions():
    # Verbose
    response = ModelFactory.list_functions(True)
    items = response["items"]
    for item in items:
        assert "output" in item.keys()
        assert "params" in item.keys()
        assert "id" in item.keys()
        assert "name" in item.keys()

    # Non-verbose
    response = ModelFactory.list_functions() # Not verbose by default
    for function in response:
        assert "output" not in function.keys()
        assert "params" not in function.keys()
        assert "id" not in function.keys()
        assert "name" in function.keys()

def list_image_repo_tags():
    response = ModelFactory.list_image_repo_tags()
    assert "Image tags" in response.keys()
    assert "nextToken" in response.keys()