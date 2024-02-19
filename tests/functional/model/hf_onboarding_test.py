__author__ = "michaellam"

import time 

from aixplain.factories.model_factory import ModelFactory
from tests.test_utils import delete_asset
from aixplain.utils import config

def test_deploy_model():
    # Start the deployment
    repo_id = "tiiuae/falcon-7b"
    documentation_url = "https://huggingface.co/tiiuae/falcon-7b"
    response = ModelFactory.deploy_huggingface_model(repo_id, documentation_url, config.HF_TOKEN)
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

def test_nonexistent_model():
    # Start the deployment
    repo_id = "nonexistent-supplier/nonexistent-model"
    documentation_url = "mock_url"
    response = ModelFactory.deploy_huggingface_model(repo_id, documentation_url, config.HF_TOKEN)
    assert response["statusCode"] == 400
    assert response["message"] == "err.unable_to_onboard_model"

def test_size_limit():
    # Start the deployment
    repo_id = "tiiuae/falcon-40b"
    documentation_url = "https://huggingface.co/tiiuae/falcon-40b"
    response = ModelFactory.deploy_huggingface_model(repo_id, documentation_url, config.HF_TOKEN)
    assert response["statusCode"] == 400
    assert response["message"] == "err.unable_to_onboard_model"

def test_gated_model():
    # Start the deployment
    repo_id = "meta-llama/Llama-2-7b-hf"
    documentation_url = "https://huggingface.co/meta-llama/Llama-2-7b-hf"
    response = ModelFactory.deploy_huggingface_model(repo_id, documentation_url, "mock_key")
    assert response["statusCode"] == 400
    assert response["message"] == "err.unable_to_onboard_model"