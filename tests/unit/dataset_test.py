import pytest
import requests_mock
from aixplain.factories import DatasetFactory
from urllib.parse import urljoin
from aixplain.utils import config


def test_list_dataset_error_response():
    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, "sdk/datasets/paginate")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"message": "Internal Server Error"}
        mock.post(url, headers=headers, json=error_response, status_code=500)

        with pytest.raises(Exception) as excinfo:
            DatasetFactory.list(query="test_query", page_number=0, page_size=20)

        assert "Dataset List Error: Status 500 - {'message': 'Internal Server Error'}" in str(excinfo.value)


def test_get_dataset_error_response():
    with requests_mock.Mocker() as mock:
        dataset_id = "invalid_dataset_id"
        url = urljoin(config.BACKEND_URL, f"sdk/datasets/{dataset_id}/overview")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"message": "Not Found"}
        mock.get(url, headers=headers, json=error_response, status_code=404)

        with pytest.raises(Exception) as excinfo:
            DatasetFactory.get(dataset_id=dataset_id)

        assert "Dataset GET Error: Status 404 - {'message': 'Not Found'}" in str(excinfo.value)
