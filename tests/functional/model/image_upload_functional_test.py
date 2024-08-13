__author__ = "michaellam"
from pathlib import Path
import json
from aixplain.factories.model_factory import ModelFactory
from tests.test_utils import delete_asset, delete_service_account
from aixplain.utils import config
import docker
import pytest

def test_login():
    response = ModelFactory.asset_repo_login()
    assert response["username"] == "AWS"
    assert response["registry"] == "535945872701.dkr.ecr.us-east-1.amazonaws.com"
    assert "password" in response.keys()

    # Test cleanup
    delete_service_account(config.TEAM_API_KEY)


def test_create_asset_repo():
    with open(Path("tests/test_requests/create_asset_request.json")) as f:
        mock_register_payload = json.load(f)
    name = mock_register_payload["name"]
    description = mock_register_payload["description"]
    function = mock_register_payload["function"]
    source_language = mock_register_payload["sourceLanguage"]
    input_modality = mock_register_payload["input_modality"]
    output_modality = mock_register_payload["output_modality"]
    documentation_url = mock_register_payload["documentation_url"]
    response = ModelFactory.create_asset_repo(name, description, function, source_language, input_modality, output_modality, documentation_url, config.TEAM_API_KEY)
    response_dict = dict(response)
    assert "id" in response_dict.keys()
    assert "repositoryName" in response_dict.keys()

    # Test cleanup
    delete_asset(response["id"], config.TEAM_API_KEY)


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
    response = ModelFactory.list_functions()  # Not verbose by default
    items = response["items"]
    for item in items:
        assert "output" not in item.keys()
        assert "params" not in item.keys()
        assert "id" not in item.keys()
        assert "name" in item.keys()


@pytest.mark.skip(reason="Not included in first release")
def list_image_repo_tags():
    response = ModelFactory.list_image_repo_tags()
    assert "Image tags" in response.keys()
    assert "nextToken" in response.keys()
