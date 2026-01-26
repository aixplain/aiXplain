__author__ = "thiagocastroferreira"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import requests_mock

import json
from aixplain.utils import config
from aixplain.modules import Model
from aixplain.modules.model.utils import build_payload, call_run_endpoint
from aixplain.factories import ModelFactory
from aixplain.enums import Function, FunctionType
from urllib.parse import urljoin
from aixplain.modules.model.response import ModelResponse, ResponseStatus
from aixplain.modules.model.model_response_streamer import ModelResponseStreamer
import pytest
from unittest.mock import patch
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.model_parameters import ModelParameters
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.model.index_model import IndexModel
from aixplain.modules.model.utility_model import UtilityModel
from aixplain.modules.model.integration import Integration, AuthenticationSchema, build_connector_params
from aixplain.modules.model.connection import ConnectionTool, ConnectAction


def test_build_payload():
    data = "input_data"
    parameters = {"context": "context_data"}
    ref_payload = json.dumps({"data": data, **parameters})
    hyp_payload = build_payload(data, parameters)
    assert hyp_payload == ref_payload


def test_call_run_endpoint_async():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = f"{base_url}/{model_id}"
    payload = {"data": "input_data"}
    ref_response = {
        "completed": True,
        "status": "IN_PROGRESS",
        "data": "https://models.aixplain.com/api/v1/data/a90c2078-edfe-403f-acba-d2d94cf71f42",
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=ref_response)
        response = call_run_endpoint(url=execute_url, api_key=config.TEAM_API_KEY, payload=payload)

    print(response)
    assert response["completed"] == ref_response["completed"]
    assert response["status"] == ref_response["status"]
    assert response["url"] == ref_response["data"]


def test_call_run_endpoint_sync():
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = f"{base_url}/{model_id}".replace("/api/v1/execute", "/api/v2/execute")
    payload = {"data": "input_data"}
    ref_response = {"completed": True, "status": ResponseStatus.SUCCESS, "data": "Hello"}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=ref_response)
        response = call_run_endpoint(url=execute_url, api_key=config.TEAM_API_KEY, payload=payload)

    assert response["completed"] == ref_response["completed"]
    assert response["status"] == ref_response["status"]
    assert response["data"] == ref_response["data"]


def test_success_poll():
    with requests_mock.Mocker() as mock:
        poll_url = "https://models.aixplain.com/api/v1/data/a90c2078-edfe-403f-acba-d2d94cf71f42"
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"completed": True, "data": "Concluded with success"}
        mock.get(poll_url, headers=headers, json=ref_response)
        test_model = Model("", "")
        hyp_response = test_model.poll(poll_url=poll_url)
    assert isinstance(hyp_response, ModelResponse)
    assert hyp_response["completed"] == ref_response["completed"]
    assert hyp_response.get("status") == ResponseStatus.SUCCESS


def test_failed_poll():
    with requests_mock.Mocker() as mock:
        poll_url = "https://models.aixplain.com/api/v1/data/a90c2078-edfe-403f-acba-d2d94cf71f42"
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
    ref_response = {"completed": True, "status": "FAILED", "error_message": "Some error occurred"}

    with requests_mock.Mocker() as mock:
        mock.get(poll_url, headers=headers, json=ref_response)
        model = Model(id="test-id", name="Test Model")
        response = model.poll(poll_url=poll_url)

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.FAILED
    assert response.error_message == "Some error occurred"
    assert response.completed is True


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
            "Billing-related error: Please ensure you have enough credits to run this asset. Details: An unspecified error occurred while processing your request.",
        ),
        (
            485,
            "Supplier-related error: Please ensure that the selected supplier provides the asset you are trying to access. Details: An unspecified error occurred while processing your request.",
        ),
        (
            495,
            "Validation-related error: Please verify the request payload and ensure it is correct. Details: An unspecified error occurred while processing your request.",
        ),
        (
            501,
            "Unspecified Server Error (Status 501) Details: An unspecified error occurred while processing your request.",
        ),
    ],
)
def test_run_async_errors(status_code, error_message):
    base_url = config.MODELS_RUN_URL
    model_id = "model-id"
    execute_url = f"{base_url}/{model_id}"
    ref_response = "An unspecified error occurred while processing your request."

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, status_code=status_code, json=ref_response)
        test_model = Model(id=model_id, name="Test Model", url=base_url)
        response = test_model.run_async(data="input_data")
    assert isinstance(response, ModelResponse)
    assert response["status"] == ResponseStatus.FAILED
    assert response["error_message"] == error_message


def test_get_model_error_response():
    with requests_mock.Mocker() as mock:
        model_id = "test-model-id"
        url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"statusCode": 404, "message": "Model not found"}
        mock.get(url, headers=headers, json=error_response, status_code=404)

        with pytest.raises(Exception) as excinfo:
            ModelFactory.get(model_id)

        assert "Model GET Error: Failed to retrieve model test-model-id" in str(excinfo.value)


def test_get_assets_from_page_error():
    from aixplain.factories.model_factory.mixins.model_list import get_assets_from_page

    with requests_mock.Mocker() as mock:
        query = "test-query"
        page_number = 0
        page_size = 2
        url = urljoin(config.BACKEND_URL, "sdk/models/paginate")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"statusCode": 500, "message": "Internal Server Error"}
        mock.post(url, headers=headers, json=error_response, status_code=500)

        with pytest.raises(Exception) as excinfo:
            get_assets_from_page(
                query=query,
                page_number=page_number,
                page_size=page_size,
                function=Function.TEXT_GENERATION,
                suppliers=None,
                source_languages=None,
                target_languages=None,
            )

        assert "Listing Models Error: Failed to retrieve models" in str(excinfo.value)


def test_get_model_from_ids():
    from aixplain.factories.model_factory.utils import get_model_from_ids

    with requests_mock.Mocker() as mock:
        model_ids = ["test-model-id-1", "test-model-id-2"]
        url = urljoin(config.BACKEND_URL, f"sdk/models?ids={','.join(model_ids)}")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        ref_response = {
            "items": [
                {
                    "id": "test-model-id-1",
                    "name": "Test Model 1",
                    "status": "onboarded",
                    "description": "Test Description 1",
                    "function": {"id": "text-generation"},
                    "supplier": {"id": "aiXplain"},
                    "pricing": {"id": "free"},
                    "version": {"id": "1.0.0"},
                    "params": [],
                },
                {
                    "id": "test-model-id-2",
                    "name": "Test Model 2",
                    "status": "onboarded",
                    "description": "Test Description 2",
                    "function": {"id": "text-generation"},
                    "supplier": {"id": "aiXplain"},
                    "pricing": {"id": "free"},
                    "version": {"id": "1.0.0"},
                    "params": [],
                },
            ]
        }
        mock.get(url, headers=headers, json=ref_response)
        models = get_model_from_ids(model_ids)

    assert len(models) == 2
    assert models[0].id == "test-model-id-1"
    assert models[1].id == "test-model-id-2"


def test_list_models_error():
    model_ids = ["test-model-id-1", "test-model-id-2"]

    with pytest.raises(Exception) as excinfo:
        ModelFactory.list(model_ids=model_ids, function=Function.TEXT_GENERATION, api_key=config.AIXPLAIN_API_KEY)

    assert str(excinfo.value) == (
        "Cannot filter by function, suppliers, "
        "source languages, target languages, is finetunable, ownership, sort by when using model ids"
    )

    with pytest.raises(Exception) as excinfo:
        ModelFactory.list(model_ids=model_ids, page_size=1, api_key=config.AIXPLAIN_API_KEY)
    assert str(excinfo.value) == "Page size must be greater than the number of model ids"


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

        test_model = Model(id=model_id, name="Test Model", url=base_url, api_key=config.TEAM_API_KEY)

        input_data = {"data": "input_data"}
        response = test_model.run(data=input_data, name="test_run")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS
    assert response.data == "Test Model Result"
    assert response.completed is True
    assert response.used_credits == 0
    assert response.run_time == 0
    assert response.usage is None


def test_sync_poll():
    poll_url = "https://models.aixplain.com/api/v1/data/mock-model-id/poll"

    in_progress_response = ModelResponse(
        status="IN_PROGRESS", data="", completed=False, error_message="", used_credits=0, run_time=0, usage=None
    )

    success_response = ModelResponse(
        status="SUCCESS",
        data="Polling successful result",
        details={"test": "test"},
        completed=True,
        error_message="",
        used_credits=0,
        run_time=0,
        usage=None,
    )

    model = Model(id="mock-model-id", name="Mock Model")

    with patch.object(model, "poll", side_effect=[in_progress_response, in_progress_response, success_response]):
        response = model.sync_poll(poll_url=poll_url, name="test_poll", timeout=5)

        assert isinstance(response, ModelResponse)
        assert response["status"] == "SUCCESS"
        assert response["completed"] is True
        assert response["details"] == {"test": "test"}
        assert response["data"] == "Polling successful result"


def test_run_with_parameters():
    model_id = "test-model-id"
    base_url = config.MODELS_RUN_URL
    execute_url = f"{base_url}/{model_id}".replace("/api/v1/execute", "/api/v2/execute")

    input_data = "test input"
    parameters = {"temperature": 0.7, "max_tokens": 100}
    expected_payload = json.dumps({"data": input_data, **parameters})

    ref_response = {
        "completed": True,
        "status": "SUCCESS",
        "data": "Test Model Result",
        "usedCredits": 0,
        "runTime": 0,
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=ref_response)

        test_model = Model(id=model_id, name="Test Model", url=base_url, api_key=config.TEAM_API_KEY)
        response = test_model.run(data=input_data, parameters=parameters)

        # Verify the payload was constructed correctly
        assert mock.last_request.text == expected_payload
        assert isinstance(response, ModelResponse)
        assert response.status == ResponseStatus.SUCCESS
        assert response.data == "Test Model Result"


def test_run_async_with_parameters():
    model_id = "test-model-id"
    base_url = config.MODELS_RUN_URL
    execute_url = f"{base_url}/{model_id}"

    input_data = "test input"
    parameters = {"temperature": 0.7, "max_tokens": 100}
    expected_payload = json.dumps({"data": input_data, **parameters})

    ref_response = {
        "completed": False,
        "status": "IN_PROGRESS",
        "data": "https://models.aixplain.com/api/v1/data/test-id",
        "url": "https://models.aixplain.com/api/v1/data/test-id",
    }

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=ref_response)

        test_model = Model(id=model_id, name="Test Model", url=base_url, api_key=config.TEAM_API_KEY)
        response = test_model.run_async(data=input_data, parameters=parameters)

        # Verify the payload was constructed correctly
        assert mock.last_request.text == expected_payload
        assert isinstance(response, ModelResponse)
        assert response.status == "IN_PROGRESS"
        assert response.url == ref_response["url"]


def test_successful_delete():
    with requests_mock.Mocker() as mock:
        model_id = "test-model-id"
        url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
        headers = {"Authorization": "Token " + config.TEAM_API_KEY, "Content-Type": "application/json"}

        # Mock successful deletion
        mock.delete(url, status_code=200)

        test_model = Model(id=model_id, name="Test Model")
        test_model.delete()  # Should not raise any exception

        # Verify the request was made with correct headers
        assert mock.last_request.headers["Authorization"] == headers["Authorization"]
        assert mock.last_request.headers["Content-Type"] == headers["Content-Type"]


def test_failed_delete():
    with requests_mock.Mocker() as mock:
        model_id = "test-model-id"
        url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")

        # Mock failed deletion
        mock.delete(url, status_code=404)

        test_model = Model(id=model_id, name="Test Model")

        with pytest.raises(Exception) as excinfo:
            test_model.delete()

        assert "Model Deletion Error: Make sure the model exists and you are the owner." in str(excinfo.value)


def test_model_to_dict():
    # Test with regular additional info
    model = Model(
        id="test-id",
        name="Test Model",
        description="",
        additional_info={"key1": "value1", "key2": None},
        model_params={"param1": {"required": True}},
    )
    result = model.to_dict()

    # Verify the result
    assert result["id"] == "test-id"
    assert result["name"] == "Test Model"
    assert result["description"] == ""
    assert result["additional_info"] == {"additional_info": {"key1": "value1", "key2": None}}
    assert isinstance(result["model_params"], dict)
    assert "param1" in result["model_params"]
    assert result["model_params"]["param1"]["required"]
    assert result["model_params"]["param1"]["value"] is None


def test_model_repr():
    # Test with supplier as dict
    model1 = Model(id="test-id", name="Test Model", supplier={"name": "aiXplain"})
    assert repr(model1).lower() == "model: test model by aixplain (id=test-id)".lower()

    # Test with supplier as string
    model2 = Model(id="test-id", name="Test Model", supplier="aiXplain")
    assert str(model2).lower() == "model: test model by aixplain (id=test-id)".lower()


def test_poll_with_error():
    with requests_mock.Mocker() as mock:
        poll_url = "https://models.aixplain.com/api/v1/data/test-id"
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        # Mock a response that will cause a JSON decode error
        mock.get(poll_url, headers=headers, text="Invalid JSON")

        model = Model(id="test-id", name="Test Model")
        response = model.poll(poll_url=poll_url)

        assert isinstance(response, ModelResponse)
        assert response.status == ResponseStatus.FAILED
        assert "Expecting value: line 1 column 1" in response.error_message


def test_sync_poll_with_timeout():
    poll_url = "https://models.aixplain.com/api/v1/data/test-id"
    model = Model(id="test-id", name="Test Model")

    # Mock poll method to always return not completed
    with patch.object(model, "poll") as mock_poll:
        mock_poll.return_value = {"status": "IN_PROGRESS", "completed": False, "error_message": ""}

        # Test with very short timeout
        response = model.sync_poll(poll_url=poll_url, timeout=0.1, wait_time=0.2)

        assert response["status"] == "FAILED"
        assert response["completed"] is False


def test_check_finetune_status_error():
    with requests_mock.Mocker() as mock:
        model_id = "test-id"
        url = urljoin(config.BACKEND_URL, f"sdk/finetune/{model_id}/ml-logs")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        # Mock error response
        error_response = {"statusCode": 404, "message": "Finetune not found"}
        mock.get(url, headers=headers, json=error_response, status_code=404)

        model = Model(id=model_id, name="Test Model")
        status = model.check_finetune_status()

        assert status is None


def test_check_finetune_status_with_logs():
    with requests_mock.Mocker() as mock:
        model_id = "test-id"
        url = urljoin(config.BACKEND_URL, f"sdk/finetune/{model_id}/ml-logs")

        # Mock successful response with logs using valid ResponseStatus values
        success_response = {
            "finetuneStatus": AssetStatus.COMPLETED.value,
            "modelStatus": AssetStatus.COMPLETED.value,
            "logs": [
                {"epoch": 1.0, "trainLoss": 0.5, "evalLoss": 0.4},
                {"epoch": 2.0, "trainLoss": 0.3, "evalLoss": 0.2},
            ],
        }
        mock.get(url, json=success_response)

        model = Model(id=model_id, name="Test Model", description="")

        # Test with after_epoch
        status = model.check_finetune_status(after_epoch=0)
        assert status is not None
        assert status.epoch == 1.0
        assert status.training_loss == 0.5
        assert status.validation_loss == 0.4

        # Test without after_epoch
        status = model.check_finetune_status()
        assert status is not None
        assert status.epoch == 2.0
        assert status.training_loss == 0.3
        assert status.validation_loss == 0.2


def test_check_finetune_status_partial_logs():
    with requests_mock.Mocker() as mock:
        model_id = "test-id"
        url = urljoin(config.BACKEND_URL, f"sdk/finetune/{model_id}/ml-logs")

        response = {
            "finetuneStatus": AssetStatus.IN_PROGRESS.value,
            "modelStatus": AssetStatus.IN_PROGRESS.value,
            "logs": [
                {"epoch": 1.0, "trainLoss": 0.5, "evalLoss": 0.4},
                {"epoch": 2.0, "trainLoss": 0.3, "evalLoss": 0.2},
            ],
        }
        mock.get(url, json=response)

        model = Model(id=model_id, name="Test Model", description="")
        status = model.check_finetune_status()

        assert status is not None
        assert status.epoch == 2.0
        assert status.training_loss == 0.3
        assert status.validation_loss == 0.2


def test_check_finetune_status_no_logs():
    with requests_mock.Mocker() as mock:
        model_id = "test-id"
        url = urljoin(config.BACKEND_URL, f"sdk/finetune/{model_id}/ml-logs")

        response = {
            "finetuneStatus": AssetStatus.IN_PROGRESS.value,
            "modelStatus": AssetStatus.IN_PROGRESS.value,
            "logs": [],
        }
        mock.get(url, json=response)

        model = Model(id=model_id, name="Test Model", description="")
        status = model.check_finetune_status()

        assert status is not None
        assert status.epoch is None
        assert status.training_loss is None
        assert status.validation_loss is None


def test_model_response():
    response = ModelResponse(status="SUCCESS", data="test", used_credits=0, run_time=0, usage=None)
    assert response["data"] == "test"
    response["data"] = "thiago"
    assert response["data"] == "thiago"
    value = response.get("data")
    assert value == "thiago"
    value = response.get("not_found", "default_value")
    assert value == "default_value"


def test_model_parameters_initialization():
    """Test ModelParameters class initialization and parameter access."""
    input_params = {"temperature": {"name": "temperature", "required": True}}

    params = ModelParameters(input_params)

    # Test parameter creation
    assert "temperature" in params.parameters
    assert params.parameters["temperature"].required

    # Test parameter access via attribute for defined parameter
    assert params.temperature is None  # Value starts as None

    # Test parameter access via attribute for undefined parameter
    with pytest.raises(AttributeError) as exc:
        params.undefined_param
    assert "Parameter 'undefined_param' is not defined" in str(exc.value)

    # Test setting parameter value
    params.temperature = 0.7
    assert params.temperature == 0.7

    # Test setting undefined parameter
    with pytest.raises(AttributeError) as exc:
        params.undefined_param = 0.5
    assert "Parameter 'undefined_param' is not defined" in str(exc.value)


def test_model_parameters_to_dict():
    """Test converting ModelParameters to dictionary format."""
    input_params = {"temperature": {"name": "temperature", "required": True}}

    params = ModelParameters(input_params)
    params.temperature = 0.7

    dict_output = params.to_dict()
    # Verify key fields are present and correct
    assert "temperature" in dict_output
    assert dict_output["temperature"]["name"] == "temperature"
    assert dict_output["temperature"]["required"] is True
    assert dict_output["temperature"]["value"] == 0.7


def test_model_parameters_invalid_parameter():
    """Test handling of invalid parameter access."""
    params = ModelParameters({})

    with pytest.raises(AttributeError):
        params.invalid_param = 123

    with pytest.raises(AttributeError):
        params.invalid_param


def test_model_parameters_string_representation():
    """Test string representation of ModelParameters."""
    input_params = {
        "temperature": {"name": "temperature", "required": True},
        "max_tokens": {"name": "max_tokens", "required": False},
    }

    params = ModelParameters(input_params)
    params.temperature = 0.7

    str_output = str(params)
    assert "Parameters:" in str_output
    assert "temperature: 0.7 (Required)" in str_output
    assert "max_tokens: Not set (Optional)" in str_output


def test_empty_model_parameters_string():
    """Test string representation of empty ModelParameters."""
    params = ModelParameters({})
    assert str(params) == "No parameters defined"


def test_model_response_streamer():
    """Test ModelResponseStreamer class."""
    streamer = ModelResponseStreamer(iter([]))
    assert isinstance(streamer, ModelResponseStreamer)
    assert streamer.status == ResponseStatus.IN_PROGRESS


def test_model_not_supports_streaming(mocker):
    """Test ModelResponseStreamer class."""
    mocker.patch("aixplain.modules.model.utils.build_payload", return_value={"data": "test"})
    model = Model(id="test-id", name="Test Model", supports_streaming=False)
    with pytest.raises(Exception) as excinfo:
        model.run(data="test", stream=True)
    assert f"Model '{model.name} ({model.id})' does not support streaming" in str(excinfo.value)


@pytest.mark.parametrize(
    "payload, expected_model_class",
    [
        (
            {
                "id": "connector-id",
                "name": "connector-name",
                "function": {"id": "utilities"},
                "functionType": "connector",
                "supplier": "aiXplain",
                "api_key": "api_key",
                "pricing": {"price": 10, "currency": "USD"},
                "params": {},
                "version": {"id": "1.0"},
                "attributes": [
                    {"name": "auth_schemes", "code": '["BEARER_TOKEN", "API_KEY", "BASIC"]'},
                ],
            },
            Integration,
        ),
        (
            {
                "id": "llm-id",
                "name": "llm-name",
                "function": {"id": "text-generation"},
                "functionType": "ai",
                "supplier": "aiXplain",
                "api_key": "api_key",
                "pricing": {"price": 10, "currency": "USD"},
                "params": {},
                "version": {"id": "1.0"},
            },
            LLM,
        ),
        (
            {
                "id": "index-id",
                "name": "index-name",
                "function": {"id": "search"},
                "functionType": "ai",
                "supplier": "aiXplain",
                "api_key": "api_key",
                "pricing": {"price": 10, "currency": "USD"},
                "params": {},
                "version": {"id": "1.0"},
            },
            IndexModel,
        ),
        (
            {
                "id": "utility-id",
                "name": "utility-name",
                "function": {"id": "utilities"},
                "functionType": "utility",
                "supplier": "aiXplain",
                "api_key": "api_key",
                "pricing": {"price": 10, "currency": "USD"},
                "params": {},
                "version": {"id": "1.0"},
            },
            UtilityModel,
        ),
    ],
)
def test_create_model_from_response(payload, expected_model_class):
    from aixplain.factories.model_factory.utils import create_model_from_response
    from aixplain.enums import FunctionType

    model = create_model_from_response(payload)
    assert isinstance(model, expected_model_class)
    assert model.id == payload["id"]
    assert model.name == payload["name"]
    assert model.function == Function(payload["function"]["id"])
    assert model.function_type == FunctionType(payload["functionType"])
    assert model.api_key == payload["api_key"]


@pytest.mark.parametrize(
    "authentication_schema, name, data",
    [
        (AuthenticationSchema.BEARER_TOKEN, "test-name", {"token": "test-token"}),
        (AuthenticationSchema.API_KEY, "test-name", {"api_key": "test-api-key"}),
        (AuthenticationSchema.BASIC, "test-name", {"username": "test-user", "password": "test-pass"}),
    ],
)
def test_connector_connect(mocker, authentication_schema, name, data):
    mocker.patch("aixplain.modules.model.integration.Integration.run", return_value={"id": "test-id"})
    additional_info = {
        "attributes": [
            {"name": "auth_schemes", "code": '["BEARER_TOKEN", "API_KEY", "BASIC"]'},
            {"name": "BEARER_TOKEN-inputs", "code": '[{"name": "token"}]'},
            {"name": "API_KEY-inputs", "code": '[{"name": "api_key"}]'},
            {"name": "BASIC-inputs", "code": '[{"name": "username"}, {"name": "password"}]'},
        ]
    }
    connector = Integration(
        id="connector-id",
        name="connector-name",
        function=Function.UTILITIES,
        function_type=FunctionType.INTEGRATION,
        supplier="aiXplain",
        api_key="api_key",
        version={"id": "1.0"},
        **additional_info,
    )
    args = build_connector_params(name=name)
    response = connector.connect(authentication_schema=authentication_schema, args=args, data=data)

    assert response["id"] == "test-id"


def test_connection_init_with_actions(mocker):
    mocker.patch(
        "aixplain.modules.model.Model.run",
        side_effect=[
            ModelResponse(
                status=ResponseStatus.SUCCESS,
                data=[{"displayName": "test-name", "description": "test-description", "name": "test-code"}],
            ),
            ModelResponse(
                status=ResponseStatus.SUCCESS,
                data=[{"inputs": [{"code": "test-code", "name": "test-name", "description": "test-description"}]}],
            ),
        ],
    )
    connection = ConnectionTool(
        id="connection-id",
        name="connection-name",
        function=Function.UTILITIES,
        function_type=FunctionType.CONNECTION,
        supplier="aiXplain",
        api_key="api_key",
        version={"id": "1.0"},
    )
    assert connection.id == "connection-id"
    assert connection.name == "connection-name"
    assert connection.function == Function.UTILITIES
    assert connection.function_type == FunctionType.CONNECTION
    assert connection.api_key == "api_key"
    assert connection.version == {"id": "1.0"}
    assert connection.actions is not None
    assert len(connection.actions) == 1
    assert connection.actions[0].name == "test-name"
    assert connection.actions[0].description == "test-description"
    assert connection.actions[0].code == "test-code"

    action = ConnectAction(code="test-code", name="test-name", description="test-description")
    inputs = connection.get_action_inputs(action)
    assert "test-code" in inputs
    assert inputs["test-code"]["name"] == "test-name"
    assert inputs["test-code"]["description"] == "test-description"


def test_tool_factory(mocker):
    from aixplain.factories import ToolFactory
    from aixplain.modules.model.utility_model import BaseUtilityModelParams

    # Mock Model.run to prevent API calls during ConnectionTool initialization
    mocker.patch(
        "aixplain.modules.model.Model.run",
        return_value=ModelResponse(
            status=ResponseStatus.SUCCESS,
            data=[{"displayName": "test-action", "description": "test-description", "name": "test-code"}],
        ),
    )

    # Script Connection Tool (via BaseUtilityModelParams)
    mocker.patch(
        "aixplain.factories.model_factory.ModelFactory.create_script_connection_tool",
        return_value=ConnectionTool(
            id="test-id",
            name="test-name",
            function=Function.UTILITIES,
            function_type=FunctionType.CONNECTION,
            supplier="aiXplain",
            api_key="api_key",
            version={"id": "1.0"},
        ),
    )

    def add(aaa: int, bbb: int) -> int:
        return aaa + bbb

    params = BaseUtilityModelParams(name="My Script Model", description="My Script Model Description", code=add)
    tool = ToolFactory.create(params=params)
    assert isinstance(tool, ConnectionTool)
    assert tool.id == "test-id"
    assert tool.name == "test-name"
    assert tool.function == Function.UTILITIES
    assert tool.function_type == FunctionType.CONNECTION
    assert tool.api_key == "api_key"
    assert tool.version == {"id": "1.0"}

    # Index Model
    from aixplain.factories.index_factory.utils import AirParams

    params = AirParams(name="My Search Collection", description="My Search Collection Description")
    mocker.patch(
        "aixplain.factories.index_factory.IndexFactory.create",
        return_value=IndexModel(
            id="test-id",
            name="test-name",
            function=Function.SEARCH,
            function_type=FunctionType.SEARCH,
            api_key="api_key",
            version={"id": "1.0"},
        ),
    )
    tool = ToolFactory.create(params=params)
    assert isinstance(tool, IndexModel)
    assert tool.id == "test-id"
    assert tool.name == "test-name"
    assert tool.function == Function.SEARCH
    assert tool.function_type == FunctionType.SEARCH
    assert tool.api_key == "api_key"
    assert tool.version == {"id": "1.0"}

    # Integration Model
    mocker.patch("aixplain.modules.model.connection.ConnectionTool._get_actions", return_value=[])
    mocker.patch(
        "aixplain.modules.model.integration.Integration.connect",
        return_value=ModelResponse(status=ResponseStatus.SUCCESS, data={"id": "connection-id"}),
    )

    def get_mock(id):
        additional_info = {
            "attributes": [
                {"name": "auth_schemes", "code": '["BEARER_TOKEN", "API_KEY", "BASIC"]'},
                {"name": "BEARER_TOKEN-inputs", "code": '[{"name": "token"}]'},
                {"name": "API_KEY-inputs", "code": '[{"name": "api_key"}]'},
                {"name": "BASIC-inputs", "code": '[{"name": "username"}, {"name": "password"}]'},
            ]
        }
        if id == "686432941223092cb4294d3f":
            return Integration(
                id="686432941223092cb4294d3f",
                name="test-name",
                function=Function.UTILITIES,
                function_type=FunctionType.INTEGRATION,
                api_key="api_key",
                version={"id": "1.0"},
                **additional_info,
            )
        elif id == "connection-id":
            return ConnectionTool(
                id="connection-id",
                name="test-name",
                function=Function.UTILITIES,
                function_type=FunctionType.CONNECTION,
                api_key="api_key",
                version={"id": "1.0"},
                **additional_info,
            )

    mocker.patch("aixplain.factories.tool_factory.ToolFactory.get", side_effect=get_mock)
    tool = ToolFactory.create(
        integration="686432941223092cb4294d3f",
        name="My Connector 1234",
        authentication_schema=AuthenticationSchema.BEARER_TOKEN,
        data={"token": "slack-token"},
    )
    assert isinstance(tool, ConnectionTool)
    assert tool.id == "connection-id"
    assert tool.name == "test-name"
    assert tool.function == Function.UTILITIES
    assert tool.function_type == FunctionType.CONNECTION
    assert tool.api_key == "api_key"
    assert tool.version == {"id": "1.0"}
