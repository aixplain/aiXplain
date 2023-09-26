__author__ = "michaellam"

from pathlib import Path
import json
from aixplain.factories.model_factory import ModelFactory
from tests.test_utils import delete_asset, delete_service_account
from aixplain.utils import config
import docker

def test_create_and_upload_model():
    # List the host machines
    ModelFactory.list_host_machines()

    # List the functions
    ModelFactory.list_functions()

    # Register the model, and create an image repository for it.
    with open(Path("tests/test_requests/create_asset_request.json")) as f:
        register_payload = json.load(f)
    name = register_payload["name"]
    host_machine = register_payload["hostingMachine"]
    version = register_payload["version"]
    description = register_payload["description"]
    function = register_payload["function"]
    source_language = register_payload["sourceLanguage"]
    register_response = ModelFactory.create_asset_repo(name, host_machine, version, description, function, source_language)
    model_id = register_response["id"]
    repo_name = register_response["repositoryName"]

    # Log into the image repository.
    login_response = ModelFactory.asset_repo_login()
    username = login_response["username"]
    password = login_response["password"]
    registry = login_response["registry"]

    # Push an image to ECR
    docker_client = docker.from_env(version='1.41')
    docker_client.pull("535945872701.dkr.ecr.us-east-1.amazonaws.com/bash")
    docker_client.tag("535945872701.dkr.ecr.us-east-1.amazonaws.com/bash", f"{registry}/{repo_name}")
    docker_client.push(f"{registry}/{repo_name}", auth_config={"username":username, "password":password})

    # Send an email to finalize onboarding process
    ModelFactory.onboard_model(model_id, "latest", "fake_hash")

    # Clean up
    delete_service_account(config.TEAM_API_KEY)
    delete_asset(model_id, config.TEAM_API_KEY)