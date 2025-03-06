import requests_mock
from aixplain.enums import DataType, EmbeddingModel, Function, ResponseStatus, StorageType
from aixplain.modules.model.record import Record
from aixplain.modules.model.response import ModelResponse
from aixplain.modules.model.index_model import IndexModel
from aixplain.utils import config
import logging
import pytest

data = {"data": "Model Index", "description": "This is a dummy collection for testing."}
index_id = "id"
execute_url = f"{config.MODELS_RUN_URL}/{index_id}".replace("/api/v1/execute", "/api/v2/execute")


def test_text_search_success(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.TEXT)
    mock_response = {"status": "SUCCESS"}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        response = index_model.search("test query")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_image_search_success(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=True)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://example.com/test.jpg")

    mock_response = {"status": "SUCCESS"}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(
            id=index_id,
            data=data,
            name="name",
            function=Function.SEARCH,
            embedding_model=EmbeddingModel.JINA_CLIP_V2_MULTIMODAL,
        )
        response = index_model.search("test.jpg")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_image_search_failure_wrong_embedding_model(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=False)
    mock_response = {"status": "FAILED", "error_message": "Unsupported file type"}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        response = index_model.search("test.jpg")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.FAILED
    assert response.error_message == "Unsupported file type for the used embedding model."


def test_text_add_success(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", side_effect=[StorageType.TEXT] * 4)
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


def test_image_add_success(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", side_effect=[StorageType.FILE] * 4)
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=True)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://example.com/test.jpg")
    mock_response = {"status": "SUCCESS"}

    mock_documents = [
        Record(value="https://example.com/test.jpg", value_type="image", id=0, uri="", attributes={}),
    ]

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        response = index_model.upsert(mock_documents)

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_text_update_success(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", side_effect=[StorageType.TEXT] * 4)
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


def test_validate_record_success(mocker):
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=True)
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://example.com/test.jpg")

    record = Record(value="test.jpg", value_type="text", id=0, uri="", attributes={})
    record.validate()
    assert record.value_type == DataType.IMAGE
    assert record.value == "https://example.com/test.jpg"


def test_validate_record_failure(mocker):
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=False)
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://example.com/test.jpg")
    record = Record(value="test.mov", value_type="text", id=0, uri="", attributes={})
    with pytest.raises(Exception) as e:
        record.validate()
    assert str(e.value) == "Index Upsert Error: Unsupported file type (test.mov)"
