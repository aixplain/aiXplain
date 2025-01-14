import requests_mock
from aixplain.enums import Function, ResponseStatus
from aixplain.modules.model.record import Record
from aixplain.modules.model.response import ModelResponse
from aixplain.modules.model.index_model import IndexModel
from aixplain.utils import config
import logging


data = {"data": "Model Index", "description": "This is a dummy collection for testing."}
index_id = "id"
execute_url = f"{config.MODELS_RUN_URL}/{index_id}".replace("/api/v1/execute", "/api/v2/execute")


def test_search_success():
    mock_response = {"status": "SUCCESS"}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        response = index_model.search("test query")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_add_success():
    mock_response = {"status": "SUCCESS"}

    mock_documents = [
        Record(value="Sample document content 1", value_type="text", id=0, uri="", attributes={}),
        Record(value="Sample document content 2", value_type="text", id=1, uri="", attributes={}),
    ]

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)

        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)

        response = index_model.upsert(mock_documents)

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_update_success():
    mock_response = {"status": "SUCCESS"}

    mock_documents = [
        Record(value="Updated document content 1", value_type="text", id=0, uri="", attributes={}),
        Record(value="Updated document content 2", value_type="text", id=1, uri="", attributes={}),
    ]

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        logging.debug(f"Requesting URL: {execute_url}")

        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)

        response = index_model.upsert(mock_documents)

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_count_success():
    mock_response = {"status": "SUCCESS", "data": 4}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        logging.debug(f"Requesting URL: {execute_url}")

        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)

        response = index_model.count()

    assert isinstance(response, int)
    assert response == 4
