__author__ = "michaellam"

import time 

from aixplain.factories.model_factory import ModelFactory
from tests.test_utils import delete_asset

def test_deploy_model():
    # Start the deployment
    model_name = "Test Model"
    repo_id = "tiiuae/falcon-7b"
    response = ModelFactory.deploy_huggingface_model(model_name, repo_id)
    assert "id" in response.keys()

    # Check for status
    model_id = response["id"]
    while ModelFactory.get_huggingface_model_status(model_id).lower() != "onboarded":
        time.sleep(10)

    # Clean up
    delete_asset(model_id)