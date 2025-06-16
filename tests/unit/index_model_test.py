import requests_mock
from aixplain.enums import DataType, Function, ResponseStatus, StorageType, EmbeddingModel
from aixplain.factories.index_factory import IndexFactory
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


def test_get_document_success():
    mock_response = {
        "status": "SUCCESS",
        "data": {"value": "Sample document content 1", "value_type": "text", "id": 0, "uri": "", "attributes": {}},
    }
    mock_documents = [Record(value="Sample document content 1", value_type="text", id=0, uri="", attributes={})]
    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        index_model.upsert(mock_documents)
        response = index_model.get_record(0)

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_delete_document_success():
    mock_response = {"status": "SUCCESS"}
    mock_documents = [Record(value="Sample document content 1", value_type="text", id=0, uri="", attributes={})]

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        index_model.upsert(mock_documents)
        response = index_model.delete_record("0")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_validate_record_success(mocker):
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=True)
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://example.com/test.jpg")

    record = Record(uri="test.jpg", value_type="image", id=0, attributes={})
    record.validate()
    assert record.value_type == DataType.IMAGE
    assert record.uri == "https://example.com/test.jpg"
    assert record.value == ""


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
    assert record_dict["dataType"] == "text"
    assert record_dict["uri"] == ""
    assert record_dict["data"] == "test"
    assert record_dict["document_id"] == 0
    assert record_dict["attributes"] == {}

    record = Record(value="test", value_type=DataType.IMAGE, id=0, uri="https://example.com/test.jpg", attributes={})
    record_dict = record.to_dict()
    assert record_dict["dataType"] == "image"
    assert record_dict["uri"] == "https://example.com/test.jpg"
    assert record_dict["data"] == "test"
    assert record_dict["document_id"] == 0
    assert record_dict["attributes"] == {}


def test_index_filter():
    from aixplain.modules.model.index_model import IndexFilter, IndexFilterOperator

    filter = IndexFilter(field="category", value="world", operator=IndexFilterOperator.EQUALS)
    assert filter.field == "category"
    assert filter.value == "world"
    assert filter.operator == IndexFilterOperator.EQUALS


def test_index_factory_create_failure():
    from aixplain.factories.index_factory.utils import AirParams

    with pytest.raises(Exception) as e:
        IndexFactory.create(
            name="test",
            description="test",
            embedding_model=EmbeddingModel.OPENAI_ADA002,
            params=AirParams(name="test", description="test", embedding_model=EmbeddingModel.OPENAI_ADA002),
        )
    assert (
        str(e.value)
        == "Index Factory Exception: name, description, and embedding_model must not be provided when params is provided"
    )

    with pytest.raises(Exception) as e:
        IndexFactory.create(description="test")
    assert str(e.value) == "Index Factory Exception: name, description, and embedding_model must be provided when params is not"

    with pytest.raises(Exception) as e:
        IndexFactory.create(name="test")
    assert str(e.value) == "Index Factory Exception: name, description, and embedding_model must be provided when params is not"

    with pytest.raises(Exception) as e:
        IndexFactory.create(name="test", description="test", embedding_model=None)
    assert str(e.value) == "Index Factory Exception: name, description, and embedding_model must be provided when params is not"


def test_index_model_splitter():
    from aixplain.modules.model.index_model import Splitter

    splitter = Splitter(split=True, split_by="sentence", split_length=100, split_overlap=0)
    assert splitter.split == True
    assert splitter.split_by == "sentence"
    assert splitter.split_length == 100
    assert splitter.split_overlap == 0


def test_parse_file_success(mocker):
    mock_response = {"status": "SUCCESS", "data": "parsed content"}
    mock_model = mocker.Mock()
    mock_model.run.return_value = ModelResponse(status=ResponseStatus.SUCCESS, data="parsed content")

    mocker.patch("aixplain.factories.ModelFactory.get", return_value=mock_model)
    mocker.patch("os.path.exists", return_value=True)

    response = IndexModel.parse_file("test.pdf")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS
    assert response.data == "parsed content"
    mock_model.run.assert_called_once_with("test.pdf")


def test_parse_file_not_found():
    with pytest.raises(Exception) as e:
        IndexModel.parse_file("nonexistent.pdf")
    assert str(e.value) == "File nonexistent.pdf does not exist"


def test_parse_file_error(mocker):
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("aixplain.factories.ModelFactory.get", side_effect=Exception("Model error"))

    with pytest.raises(Exception) as e:
        IndexModel.parse_file("test.pdf")
    assert str(e.value) == "Failed to parse file: Model error"


def test_upsert_with_file_path(mocker):
    mock_parse_response = ModelResponse(status=ResponseStatus.SUCCESS, data="parsed content")
    mock_upsert_response = {"status": "SUCCESS"}

    mocker.patch("aixplain.modules.model.index_model.IndexModel.parse_file", return_value=mock_parse_response)
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.TEXT)

    with requests_mock.Mocker() as mock:
        mock.post(execute_url, json=mock_upsert_response, status_code=200)
        index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)
        response = index_model.upsert("test.pdf")

    assert isinstance(response, ModelResponse)
    assert response.status == ResponseStatus.SUCCESS


def test_upsert_with_invalid_file_path(mocker):
    mocker.patch("aixplain.modules.model.index_model.IndexModel.parse_file", side_effect=Exception("File not found"))

    index_model = IndexModel(id=index_id, data=data, name="name", function=Function.SEARCH)

    with pytest.raises(Exception) as e:
        index_model.upsert("nonexistent.pdf")
    assert str(e.value) == "File not found"
