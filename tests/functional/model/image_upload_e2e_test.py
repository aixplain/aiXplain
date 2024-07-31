__author__ = "michaellam"

from pathlib import Path
import json
from aixplain.factories.model_factory import ModelFactory
from tests.test_utils import delete_asset, delete_service_account
from aixplain.utils import config
import docker
import pytest


def test_create_and_upload_model():
    # List the host machines
    host_response = ModelFactory.list_host_machines()
    for hosting_machine_dict in host_response:
        assert "code" in hosting_machine_dict.keys()
        assert "type" in hosting_machine_dict.keys()
        assert "cores" in hosting_machine_dict.keys()
        assert "memory" in hosting_machine_dict.keys()
        assert "hourlyCost" in hosting_machine_dict.keys()

    # List the functions
    response = ModelFactory.list_functions()
    items = response["items"]
    for item in items:
        assert "output" not in item.keys()
        assert "params" not in item.keys()
        assert "id" not in item.keys()
        assert "name" in item.keys()

    # Register the model, and create an image repository for it.
    with open(Path("tests/test_requests/create_asset_request.json")) as f:
        mock_register_payload = json.load(f)
    name = mock_register_payload["name"]
    description = mock_register_payload["description"]
    function = mock_register_payload["function"]
    source_language = mock_register_payload["sourceLanguage"]
    input_modality = mock_register_payload["input_modality"]
    output_modality = mock_register_payload["output_modality"]
    documentation_url = mock_register_payload["documentation_url"]
    register_response = ModelFactory.create_asset_repo(name, description, function, source_language, input_modality, output_modality, documentation_url, config.TEAM_API_KEY)
    assert "id" in register_response.keys()
    assert "repositoryName" in register_response.keys()
    model_id = register_response["id"]
    repo_name = register_response["repositoryName"]

    # Log into the image repository.
    login_response = ModelFactory.asset_repo_login()

    assert login_response["username"] == "AWS"
    assert login_response["registry"] == "535945872701.dkr.ecr.us-east-1.amazonaws.com"
    assert "password" in login_response.keys()

    username = login_response["username"]
    password = login_response["password"]
    registry = login_response["registry"]

    # Push an image to ECR
    low_level_client = docker.APIClient(base_url="unix://var/run/docker.sock")
    low_level_client.pull("bash")
    low_level_client.tag("bash", f"{registry}/{repo_name}")
    low_level_client.push(f"{registry}/{repo_name}", auth_config={"username": username, "password": password})

    # Send an email to finalize onboarding process
    ModelFactory.onboard_model(model_id, "latest", "fake_hash")

    # Clean up
    delete_service_account(config.TEAM_API_KEY)
    delete_asset(model_id, config.TEAM_API_KEY)
