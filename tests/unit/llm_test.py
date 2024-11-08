from dotenv import load_dotenv
import requests_mock
from aixplain.enums import Function

load_dotenv()
from aixplain.utils import config
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.response import ModelResponse
from aixplain.modules import LLM

import pytest


@pytest.mark.parametrize(
    "status_code,error_message",
    [
        (
            401,
            "Unauthorized API key: Please verify the spelling of the API key and its current validity. Details: An unspecified error occurred while processing your request.",
        ),
        (
            465,
            "Subscription-related error: Please ensure that your subscription is active and has not expired. Details: An unspecified error occurred while processing your request.",
        ),
        (
            475,
            "Billing-related error: Please ensure you have enough credits to run this model. Details: An unspecified error occurred while processing your request.",
        ),
        (
            485,
            "Supplier-related error: Please ensure that the selected supplier provides the model you are trying to access. Details: An unspecified error occurred while processing your request.",
        ),
        (
            495,
            "An unspecified error occurred while processing your request.",
        ),
        (501, "Status 501 - Unspecified error: An unspecified error occurred while processing your request."),
    ],
)
def test_run_async_errors(status_code, error_message):
    base_url = config.MODELS_RUN_URL
    llm_id = "llm-id"
    execute_url = f"{base_url}/{llm_id}"
    ref_response = {
        "error": "An unspecified error occurred while processing your request.",
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=status_code, json=ref_response)
        test_llm = LLM(id=llm_id, name="Test llm", url=base_url, function=Function.TEXT_GENERATION)
        response = test_llm.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == error_message


def test_run_sync():
    model_id = "test-model-id"
    base_url = config.MODELS_RUN_URL
    execute_url = f"{base_url}/{model_id}".replace("/api/v1/execute", "/api/v2/execute")

    ref_response = {
        "status": "IN_PROGRESS",
        "data": "https://models.aixplain.com/api/v1/data/a90c2078-edfe-403f-acba-d2d94cf71f42",
    }

    poll_response = {
        "completed": True,
        "status": "SUCCESS",
        "data": "Test Model Result",
        "usedCredits": 0,
        "runTime": 0,
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=ref_response)

        poll_url = ref_response["data"]
        mock.get(poll_url, json=poll_response)

        test_model = LLM(
            id=model_id, name="Test Model", function=Function.TEXT_GENERATION, url=base_url, api_key=config.TEAM_API_KEY
        )

        input_data = {"data": "input_data"}
        response = test_model.run(data=input_data, temperature=0.001, max_tokens=128, top_p=1.0)

    assert isinstance(response, ModelResponse)
    assert response.status == AssetStatus.SUCCESS
    assert response.data == "Test Model Result"
    assert response.completed is True
    assert response.used_credits == 0
    assert response.run_time == 0
    assert response.usage is None
