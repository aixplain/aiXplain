import requests_mock
from aixplain.enums import DataType, Function, ResponseStatus, StorageType
from aixplain.factories import IndexFactory
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
            embedding_model="67c5f705d8f6a65d6f74d732",
        )
        response = index_model.search("test.jpg")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_invalid_embedding_model():
    with pytest.raises(Exception) as e:
        IndexFactory.create("test", "test", "invalid_model")
    assert (
        str(e.value)
        == "Index Creation Collection Error: Invalid embedding model. Current supported models are: Snowflake Arctic-embed M-long (6658d40729985c2cf72f42ec), OpenAI Ada-002 (6734c55df127847059324d9e), Snowflake Arctic-embed L-v2.0 (678a4f8547f687504744960a), Jina Clip-v2 Multimodal (67c5f705d8f6a65d6f74d732)"
    )


def test_image_search_failure_wrong_embedding_model(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=False)
    mock_response = {"status": "FAILED", "error_message": "Unsupported file type"}

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        response = index_model.search("test.mov")

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
        Record(uri="https://example.com/test.jpg", value_type="image", id=0, attributes={}),
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

    record = Record(uri="test.jpg", value_type="image", id=0, attributes={})
    record.validate()
    assert record.value_type == DataType.IMAGE
    assert record.value == "https://example.com/test.jpg"


def test_validate_record_failure(mocker):
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=False)
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://example.com/test.jpg")
    record = Record(uri="test.mov", value_type="video", id=0, attributes={})
    with pytest.raises(Exception) as e:
        record.validate()
    assert str(e.value) == "Index Upsert Error: Invalid value type"


def test_validate_record_failure_no_uri(mocker):
    record = Record(value="test.jpg", value_type="image", id=0, uri="", attributes={})
    with pytest.raises(Exception) as e:
        record.validate()
    assert str(e.value) == "Index Upsert Error: URI is required for image records"


def test_validate_record_failure_no_value(mocker):
    record = Record(uri="test.jpg", value_type="text", id=0, attributes={})
    with pytest.raises(Exception) as e:
        record.validate()
    assert str(e.value) == "Index Upsert Error: Value is required for text records"


def test_record_to_dict():
    record = Record(value="test", value_type=DataType.TEXT, id=0, uri="", attributes={})
    record_dict = record.to_dict()
    assert record_dict["value_type"] == "text"
    assert record_dict["uri"] == ""
    assert record_dict["value"] == "test"
    assert record_dict["id"] == 0
    assert record_dict["attributes"] == {}

    record = Record(value="test", value_type=DataType.IMAGE, id=0, uri="https://example.com/test.jpg", attributes={})
    record_dict = record.to_dict()
    assert record_dict["value_type"] == "image"
    assert record_dict["uri"] == "https://example.com/test.jpg"
    assert record_dict["value"] == "test"
    assert record_dict["id"] == 0
    assert record_dict["attributes"] == {}
