from dotenv import load_dotenv
from urllib.parse import urljoin
import requests_mock
from aixplain.enums import Function

load_dotenv()
from aixplain.utils import config
from aixplain.modules import LLM

import pytest


@pytest.mark.parametrize(
    "status_code,error_message",
    [
        (401, "Unauthorized API key: Please verify the spelling of the API key and its current validity."),
        (465, "Subscription-related error: Please ensure that your subscription is active and has not expired."),
        (475, "Billing-related error: Please ensure you have enough credits to run this model. "),
        (485, "Supplier-related error: Please ensure that the selected supplier provides the model you are trying to access."),
        (
            495,
            "{'error': 'An unspecified error occurred while processing your request.'}",
        ),
        (501, "Status 501: Unspecified error: An unspecified error occurred while processing your request."),
    ],
)
def test_run_async_errors(status_code, error_message):
    base_url = config.MODELS_RUN_URL
    llm_id = "llm-id"
    execute_url = urljoin(base_url, f"execute/{llm_id}")
    ref_response = {
        "error": "An unspecified error occurred while processing your request.",
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=status_code, json=ref_response)
        test_llm = LLM(id=llm_id, name="Test llm", url=base_url, function=Function.TEXT_GENERATION)
        response = test_llm.run_async(data="input_data")
    assert response["status"] == "FAILED"
    assert response["error_message"] == error_message
