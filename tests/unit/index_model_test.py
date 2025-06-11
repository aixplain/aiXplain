"""
Covers
──────
• VectorIndexModel
• KnowledgeGraphIndexModel
• Record utilities
• IndexFilter dataclass
• IndexFactory negative-path rules
"""
import requests_mock
from aixplain.enums import DataType, Function, ResponseStatus, StorageType, EmbeddingModel
from aixplain.factories.index_factory import IndexFactory
from aixplain.factories.index_factory.utils import AirParams
from aixplain.modules.model.record import Record
from aixplain.modules.model.response import ModelResponse
from aixplain.modules.model.index_models import VectorIndexModel, IndexFilter, IndexFilterOperator, KnowledgeGraphIndexModel
from aixplain.utils import config
import logging
import pytest
from aixplain.modules.model.index_models.base_index_model import BaseIndexModel

logging.basicConfig(
    format="%(levelname)s • %(name)s • %(message)s",
    level=logging.DEBUG,
)

# ────────────────────────────────────────────────────────────────────────────────
# VECTOR-BASED INDEX TESTS
# ────────────────────────────────────────────────────────────────────────────────

VEC_ID = "vec-id"
VEC_EXEC_URL = f"{config.MODELS_RUN_URL}/{VEC_ID}".replace("/api/v1/execute", "/api/v2/execute")
logger = logging.getLogger("VectorIndexModelTests")


def _make_vec():
    return VectorIndexModel(
        id=VEC_ID,
        name="vec-name",
        version="airv2-dev-1-test",
        description="",
        function=Function.SEARCH,
        embedding_model=EmbeddingModel.OPENAI_ADA002,
    )


def test_vector_text_search(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.TEXT)

    with requests_mock.Mocker() as m:
        m.post(VEC_EXEC_URL, json={"status": "SUCCESS"}, status_code=200)
        logger.debug("POST %s  • payload={status:SUCCESS}", VEC_EXEC_URL)
        resp = _make_vec().search("hello world")

    assert isinstance(resp, ModelResponse)
    assert resp.status == ResponseStatus.SUCCESS


def test_vector_image_search(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=True)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://ex.com/img.jpg")

    with requests_mock.Mocker() as m:
        m.post(VEC_EXEC_URL, json={"status": "SUCCESS"}, status_code=200)
        logger.debug("POST %s  • payload={status:SUCCESS}", VEC_EXEC_URL)
        resp = _make_vec().search("img.jpg")

    assert resp.status == ResponseStatus.SUCCESS


def test_vector_upsert_text(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", side_effect=[StorageType.TEXT] * 4)

    docs = [
        Record(value="doc1", value_type="text", id=1, uri="", attributes={}),
        Record(value="doc2", value_type="text", id=2, uri="", attributes={}),
    ]

    with requests_mock.Mocker() as m:
        m.post(VEC_EXEC_URL, json={"status": "SUCCESS"}, status_code=200)
        resp = _make_vec().upsert(docs)

    assert resp.status == ResponseStatus.SUCCESS
    assert resp.data == [d.to_dict() for d in docs]


def test_vector_index_filter():
    flt = IndexFilter("category", "news", IndexFilterOperator.EQUALS)
    assert flt.to_dict() == {"field": "category", "value": "news", "operator": "=="}


# ────────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE-GRAPH INDEX TESTS
# ────────────────────────────────────────────────────────────────────────────────

KG_ID = "kg-id"
KG_EXEC_URL = f"{config.MODELS_RUN_URL}/{KG_ID}".replace("/api/v1/execute", "/api/v2/execute")

kg_logger = logging.getLogger("KGIndexModelTests")


def _make_kg():
    return KnowledgeGraphIndexModel(
        id=KG_ID,
        name="kg-name",
        version="graphrag-dev-1-test",
        description="",
        function=Function.SEARCH,
        llm="gpt-4o",
    )


def _kg_mock(m, payload):
    m.post(KG_EXEC_URL, json=payload, status_code=200)
    kg_logger.debug("POST %s  • payload=%s", KG_EXEC_URL, payload)


def test_kg_get_prompts():
    with requests_mock.Mocker() as m:
        _kg_mock(m, {"status": "SUCCESS", "data": {"sys": "hi"}})
        resp = _make_kg().get_prompts()

    assert resp.status == ResponseStatus.SUCCESS
    assert resp.data == {"sys": "hi"}


def test_kg_add_documents(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", side_effect=[StorageType.TEXT] * 4)

    docs = [Record(value="kg-doc", value_type="text", id=0, uri="", attributes={})]

    with requests_mock.Mocker() as m:
        _kg_mock(m, {"status": "SUCCESS"})
        resp = _make_kg().add_documents(docs)

    assert resp.status == ResponseStatus.SUCCESS
    assert resp.data == docs


def test_kg_manual_prompt_tune():
    prompts = {"sys": "You are helpful"}

    with requests_mock.Mocker() as m:
        _kg_mock(m, {"status": "SUCCESS"})
        resp = _make_kg().manual_prompt_tune(prompts)

    assert resp.status == ResponseStatus.SUCCESS
    assert resp.data == prompts


def test_kg_auto_prompt_tune(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", side_effect=[StorageType.TEXT] * 4)

    docs = [Record(value="auto", value_type="text", id=1, uri="", attributes={})]

    with requests_mock.Mocker() as m:
        # upload_documents
        _kg_mock(m, {"status": "SUCCESS"})
        # auto_prompt_tune
        _kg_mock(m, {"status": "SUCCESS", "data": {"sys": "ok"}})

        resp = _make_kg().auto_prompt_tune(docs)

    assert resp == {"sys": "ok"}


def test_kg_graph_indexing():
    with requests_mock.Mocker() as m:
        _kg_mock(m, {"status": "SUCCESS", "data": "started"})
        resp = _make_kg().graph_indexing()

    assert resp.status == ResponseStatus.SUCCESS


def test_kg_upsert(mocker):
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", side_effect=[StorageType.TEXT] * 4)

    docs = [Record(value="round", value_type="text", id=7, uri="", attributes={})]

    with requests_mock.Mocker() as m:
        # upload_documents
        _kg_mock(m, {"status": "SUCCESS"})
        # ingest
        _kg_mock(m, {"status": "SUCCESS", "data": "done"})

        resp = _make_kg().upsert(docs)

    assert resp.status == ResponseStatus.SUCCESS


# ────────────────────────────────────────────────────────────────────────────────
# RECORD UTILITY TESTS
# ────────────────────────────────────────────────────────────────────────────────
def test_record_validate_and_dict(mocker):
    mocker.patch("aixplain.modules.model.utils.is_supported_image_type", return_value=True)
    mocker.patch("aixplain.factories.FileFactory.check_storage_type", return_value=StorageType.FILE)
    mocker.patch("aixplain.factories.FileFactory.to_link", return_value="https://ex.com/img.jpg")

    rec = Record(uri="img.jpg", value_type="image", id=0, attributes={})
    rec.validate()
    d = rec.to_dict()

    assert d["dataType"] == DataType.IMAGE
    assert d["uri"] == "https://ex.com/img.jpg"


# ────────────────────────────────────────────────────────────────────────────────
# INDEX FACTORY TESTS
# ────────────────────────────────────────────────────────────────────────────────


def test_index_factory_create_failure():
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
    from aixplain.modules.model.index_models.base_index_model import Splitter

    splitter = Splitter(split=True, split_by="sentence", split_length=100, split_overlap=0)
    assert splitter.split == True
    assert splitter.split_by == "sentence"
    assert splitter.split_length == 100
    assert splitter.split_overlap == 0
