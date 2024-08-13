__author__ = "michaellam"

import pytest
import time

from aixplain.factories.model_factory import ModelFactory
from tests.test_utils import delete_asset
from aixplain.utils import config


@pytest.mark.skip(reason="Model Deployment is deactivated for improvements.")
def test_deploy_model():
    # Start the deployment
    model_name = "Test Model"
    repo_id = "tiiuae/falcon-7b"
    response = ModelFactory.deploy_huggingface_model(model_name, repo_id, hf_token=config.HF_TOKEN)
    assert "id" in response.keys()

    # Check for status
    model_id = response["id"]
    num_retries = 120
    counter = 0
    while ModelFactory.get_huggingface_model_status(model_id)["status"].lower() != "onboarded":
        time.sleep(10)
        counter += 1
        if counter == num_retries:
            assert ModelFactory.get_huggingface_model_status(model_id)["status"].lower() == "onboarded"

    # Clean up
    delete_asset(model_id, config.TEAM_API_KEY)


# @pytest.mark.skip(reason="Model Deployment is deactivated for improvements.")
def test_nonexistent_model():
    # Start the deployment
    model_name = "Test Model"
    repo_id = "nonexistent-supplier/nonexistent-model"
    response = ModelFactory.deploy_huggingface_model(model_name, repo_id, hf_token=config.HF_TOKEN)
    assert response["statusCode"] == 400
    assert response["message"] == "err.unable_to_onboard_model"


# @pytest.mark.skip(reason="Model Deployment is deactivated for improvements.")
def test_size_limit():
    # Start the deployment
    model_name = "Test Model"
    repo_id = "tiiuae/falcon-40b"
    response = ModelFactory.deploy_huggingface_model(model_name, repo_id, hf_token=config.HF_TOKEN)
    assert response["statusCode"] == 400
    assert response["message"] == "err.unable_to_onboard_model"


# @pytest.mark.skip(reason="Model Deployment is deactivated for improvements.")
def test_gated_model():
    # Start the deployment
    model_name = "Test Model"
    repo_id = "meta-llama/Llama-2-7b-hf"
    response = ModelFactory.deploy_huggingface_model(model_name, repo_id, hf_token="mock_key")
    assert response["statusCode"] == 400
    assert response["message"] == "err.unable_to_onboard_model"
