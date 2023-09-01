import pytest
import httpretty
import os
from urllib.parse import urljoin
from aixplain.client import AixplainClient
from aixplain.assets.models import Model

MODELS_RUN_URL = os.getenv('MODELS_RUN_URL', 'https://api.example.com/api/v1/execute/')
@pytest.fixture
def setup_httpretty():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()

@httpretty.activate
@pytest.mark.skip("not implemented yet")
def test_model_run():
    # Create a test model
    model = Model({'id': '123'})

    # Mock the HTTP request to run the model synchronously
    httpretty.register_uri(httpretty.POST, urljoin(MODELS_RUN_URL,'123'), json={"result": "synchronous_result"}, status=200)

    result = model.run("input_data")
    assert result == {"result": "synchronous_result"}
    
@httpretty.activate
def test_model_run_async():
    # Create a test model
    model = Model({'id': '123'})

    # Mock the HTTP request to run the model asynchronously
    httpretty.register_uri(httpretty.POST, urljoin(MODELS_RUN_URL,'123'), json={"data": "model_run_data"}, status=200, body=f'{{"data": "{urljoin(MODELS_RUN_URL,"123")}"}}')

    result = model.run_async("input_data", models_run_url=MODELS_RUN_URL)
    assert result['status'] == "IN_PROGRESS"
    assert result["url"] == urljoin(MODELS_RUN_URL,"123")
