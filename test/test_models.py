import pytest
import httpretty
from aixplain.client import AixplainClient
from aixplain.assets.models import Model

#TODO: to change it and make it actually call an actual model
# Define a test model class that inherits from Model
class TestModel(Model):
    def run(self, data, name="model_process", timeout=300, parameters={}, wait_time=0.5):
        return {"result": "synchronous_result"}

    def run_async(self, input, name="model_process", parameters={}, models_run_url=None):
        return {"status": "IN_PROGRESS", "url": "https://example.com/model_run/123"}

# Fixture to set up httpretty
@pytest.fixture
def setup_httpretty():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()

# Fixture to create a test AixplainClient
@pytest.fixture
def create_test_client():
    base_url = 'https://api.example.com'
    client = AixplainClient(base_url, team_api_key='your_api_key')
    return client

# Test the Model class
def test_model_run(setup_httpretty, create_test_client):
    # Create a test model
    model = TestModel({'id': '123'})

    # Mock the HTTP request to run the model synchronously
    httpretty.register_uri(httpretty.POST, 'https://api.example.com/models/123', json={"result": "synchronous_result"}, status=200)

    result = model.run("input_data")
    assert result == {"result": "synchronous_result"}

def test_model_run_async(setup_httpretty, create_test_client):
    # Create a test model
    model = TestModel({'id': '123'})

    # Mock the HTTP request to run the model asynchronously
    httpretty.register_uri(httpretty.POST, 'https://api.example.com/models/123', json={"data": "model_run_data"}, status=200)

    result = model.run_async("input_data")
    assert result == {"status": "IN_PROGRESS", "url": "https://example.com/model_run/123"}
