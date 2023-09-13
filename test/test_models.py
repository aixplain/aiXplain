import pytest
import httpretty
import os
from urllib.parse import urljoin, urlencode
from aixplain.assets.models import Model

MODELS_RUN_URL = os.getenv('MODELS_RUN_URL', 'https://api.example.com/api/v1/execute/')
BASE_URL = os.getenv('BACKEND_URL', 'https://api.example.com/')

"""@pytest.fixture
def setup_httpretty():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()"""

@httpretty.activate
@pytest.mark.skip("not implemented yet")
def test_model_run():
    # Create a test model
    model = Model({'id': '123'})
    httpretty.register_uri(httpretty.POST, urljoin(MODELS_RUN_URL,'123'), json={"result": "synchronous_result"}, status=200)

    result = model.run("input_data")
    assert result == {"result": "synchronous_result"}
    
@httpretty.activate
def test_model_run_async():
    # Create a test model
    model = Model({'id': '123'})
    httpretty.register_uri(httpretty.POST, urljoin(MODELS_RUN_URL,'123'), json={"data": "model_run_data"}, status=200, body=f'{{"data": "{urljoin(MODELS_RUN_URL,"123")}"}}')

    result = model.run_async("input_data", models_run_url=MODELS_RUN_URL)
    assert result['status'] == "IN_PROGRESS"
    assert result["url"] == urljoin(MODELS_RUN_URL,"123")

"""@httpretty.activate
def test_model_enable_disable():
    model_id_enable = '123'
    model_id_disable = '321'
    httpretty.register_uri(httpretty.GET, urljoin(BASE_URL,f'/sdk/inventory/models/{model_id_enable}/enable'), status=201, body=f'{{"id": "{model_id_disable}", "apiKey": "123"}}')
    httpretty.register_uri(httpretty.GET, urljoin(BASE_URL,f'/sdk/inventory/models/{model_id_disable}/disable'), status=201, body=f'{{"deleted" : true, "id": "{model_id_disable}", "apiKey": "123"}}')
    model_to_enable = Model({'id': model_id_enable})
    model_to_disable = Model({'id': model_id_disable})
    model_to_enable.get('')"""
    
@httpretty.activate
def test_get_model():
    model_id = '61af7662e116cb1eecfa5410'
    asset_path = 'inventory/models'
    model = Model({'id': model_id})
    #prepare mock response
    with open('./test/mock_responses/get_model_response.json') as f:
        mock_response = f.read()
    
    url = urljoin(BASE_URL,os.path.join('sdk',asset_path,model_id))
    
    httpretty.register_uri(httpretty.GET, url, status=200, body = mock_response)
    
    resp = model.get(asset_id = model_id)
    
    assert resp.id == model_id
    assert resp.supplier['id'] == 'AWS'

@httpretty.activate
def test_list_models():
    model_id = '61af7662e116cb1eecfa5410'
    asset_path = 'inventory/models'
    model = Model({'id': model_id})
    
    with open('./test/mock_responses/list_models_response.json') as f:
        mock_response = f.read()
    
    params = {
        "pageNumber" : 0
    }
    url = urljoin(BASE_URL,os.path.join('sdk',asset_path)) + "?" + urlencode(params)
    httpretty.register_uri(httpretty.GET, url, status=200, body = mock_response)
    
    resp = model.list()
    
    assert len(resp) == 10
    assert isinstance(resp[0], Model)
