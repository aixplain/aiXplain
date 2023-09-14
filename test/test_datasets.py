import pytest
import os
import httpretty
from urllib.parse import urljoin, urlencode
from aixplain.assets.datasets import Dataset


# Mocking the AixplainClient
BASE_URL = os.getenv('BACKEND_URL', 'https://api.example.com')

"""@pytest.fixture
def setup_httpretty():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()"""

def test_dataset_initialization():
    dataset_dict = {
        'id': '123',
        'name': 'Test Dataset',
        'description': 'A sample dataset for testing purposes',
    }

    dataset = Dataset(dataset_dict)

    assert dataset.id == '123'
    assert dataset.name == 'Test Dataset'
    assert dataset.description == 'A sample dataset for testing purposes'

@httpretty.activate
def test_dataset_download():
    dataset_dict = {
        'id': '123',
        'name': 'Test Dataset',
    }
    dataset = Dataset(dataset_dict)
    # Mock the HTTP response
    httpretty.register_uri(httpretty.GET, urljoin(BASE_URL,'/sdk/datasets/123/download'), status=200)
    response = dataset.download()
    assert response.status_code == 200

@httpretty.activate
def test_dataset_team_page():
    dataset_dict = {
        'id': '123',
        'name': 'Test Dataset',
    }

    dataset = Dataset(dataset_dict)

    # Mock the HTTP response
    httpretty.register_uri(httpretty.GET, urljoin(BASE_URL,'/sdk/datasets/team?pageNumber=0&team_id=456'), status=200, body='{"items": []}')

    team_datasets = dataset.team_page(page_number=0, filters={'team_id': '456'})

    assert isinstance(team_datasets, list)
    assert len(team_datasets) == 0

@httpretty.activate
def test_get_model():
    dataset_id = '61af7662e116cb1eecfa5410'
    asset_path = 'datasets'
    dataset = Dataset({'id': dataset_id})
    #prepare mock response
    with open('./test/mock_responses/get_dataset_response.json') as f:
        mock_response = f.read()
    
    url = urljoin(BASE_URL,os.path.join('sdk',asset_path,dataset_id))
    
    httpretty.register_uri(httpretty.GET, url, status=200, body = mock_response)
    
    resp = dataset.get(asset_id = dataset_id)
    
    assert resp.team == 155
    assert resp.function == 'translation'

@httpretty.activate
def test_list_models_pagination():
    dataset_id = '61af7662e116cb1eecfa5410'
    asset_path = 'datasets'
    dataset = Dataset({'id': dataset_id})
    
    with open('./test/mock_responses/list_datasets_response.json') as f:
        mock_response = f.read()
    
    params = {
        "pageNumber" : 0
    }
    url = urljoin(BASE_URL,os.path.join('sdk',asset_path, 'paginate')) + "?" + urlencode(params)
    httpretty.register_uri(httpretty.GET, url, status=200, body = mock_response)
    # this need to be implemented in a different way inside the Dataset function
    resp = dataset.list(subpaths = ['paginate'])
    
    first_dataset = resp[0]
    assert first_dataset.id == '6441b997b5c8cb00128e1b92'
    assert isinstance(first_dataset, Dataset)
    assert isinstance(resp, list)