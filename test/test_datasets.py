import pytest
import os
import httpretty
from urllib.parse import urljoin
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

test_dataset_team_page()