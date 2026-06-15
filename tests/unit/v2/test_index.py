"""Unit tests for the v2 Index resource (ENG-3148).

These tests exercise the typed v2 Index API (control-plane + data-plane and the
supporting types) with a mocked client context, mirroring the coverage of the
legacy ``tests/unit/index_model_test.py`` without performing any network I/O.
"""

import pytest
from unittest.mock import Mock

from aixplain.v2.enums import DataType, EmbeddingModel, ResponseStatus
from aixplain.v2.index import (
    AirParams,
    GraphRAGParams,
    Index,
    IndexFilter,
    IndexFilterOperator,
    IndexResult,
    Record,
    Splitter,
    VectaraParams,
    ZeroEntropyParams,
)

MODEL_URL = "https://models.test/api/v2/execute"
INDEX_ID = "idx-1"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ctx():
    """Build a mocked Aixplain context."""
    ctx = Mock()
    ctx.model_url = MODEL_URL
    ctx.api_key = "test-key"
    ctx.client = Mock()
    return ctx


def _index(ctx=None, index_id=INDEX_ID, name="my-index"):
    """Build an Index instance bound to a (mocked) context."""
    ctx = ctx or _ctx()
    idx = Index.from_dict({"id": index_id, "name": name})
    idx.context = ctx
    return idx


def _index_cls(ctx):
    """Build a context-bound Index subclass (as the client does dynamically)."""
    return type("Index", (Index,), {"context": ctx})


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------
class TestRecord:
    def test_to_dict_text(self):
        record = Record(value="test", value_type=DataType.TEXT, id="0", uri="", attributes={})
        d = record.to_dict()
        assert d == {"data": "test", "dataType": "text", "document_id": "0", "uri": "", "attributes": {}}

    def test_to_dict_image(self):
        record = Record(value="", value_type=DataType.IMAGE, id="0", uri="https://x.com/a.jpg")
        d = record.to_dict()
        assert d["dataType"] == "image"
        assert d["uri"] == "https://x.com/a.jpg"

    def test_auto_id(self):
        assert Record(value="x").id  # a UUID is generated

    def test_validate_text_ok(self):
        Record(value="hello").validate()  # no raise

    def test_validate_invalid_type(self):
        with pytest.raises(AssertionError) as e:
            Record(value="x", value_type="video").validate()
        assert str(e.value) == "Index Upsert Error: Invalid value type"

    def test_validate_image_requires_uri(self):
        with pytest.raises(AssertionError) as e:
            Record(value="x", value_type=DataType.IMAGE, uri="").validate()
        assert str(e.value) == "Index Upsert Error: URI is required for image records"

    def test_validate_text_requires_value_or_uri(self):
        with pytest.raises(AssertionError) as e:
            Record(value="", value_type=DataType.TEXT, uri="").validate()
        assert str(e.value) == "Index Upsert Error: Either value or uri is required for text records"

    def test_validate_local_image_uploaded_and_promoted(self, monkeypatch):
        import aixplain.v2.index as index_mod

        monkeypatch.setattr(index_mod, "_check_storage_type", lambda v: "file")
        monkeypatch.setattr(index_mod, "_is_supported_image_type", lambda v: True)
        monkeypatch.setattr(index_mod, "upload_file", lambda v: "https://hosted/test.jpg")

        record = Record(value="", value_type=DataType.IMAGE, uri="test.jpg")
        record.validate()
        assert record.value_type == DataType.IMAGE
        assert record.uri == "https://hosted/test.jpg"


class TestFilterAndSplitter:
    def test_index_filter_to_dict(self):
        f = IndexFilter(field="category", value="world", operator=IndexFilterOperator.EQUALS)
        assert f.to_dict() == {"field": "category", "value": "world", "operator": "=="}

    def test_index_filter_string_operator(self):
        f = IndexFilter(field="c", value="v", operator="!=")
        assert f.to_dict()["operator"] == "!="

    def test_splitter(self):
        s = Splitter(split=True, split_by="sentence", split_length=100, split_overlap=5)
        assert (s.split, s.split_by, s.split_length, s.split_overlap) == (True, "sentence", 100, 5)


class TestParams:
    def test_air_params(self):
        p = AirParams(name="docs", description="d")
        assert p.id == "66eae6656eb56311f2595011"
        assert p.to_dict() == {
            "description": "d",
            "data": "docs",
            "model": EmbeddingModel.OPENAI_ADA002.value,
        }

    def test_air_params_with_size(self):
        p = AirParams(name="docs", description="d", embedding_model=EmbeddingModel.BGE_M3, embedding_size=1024)
        d = p.to_dict()
        assert d["model"] == EmbeddingModel.BGE_M3.value
        assert d["additional_params"] == {"embedding_size": 1024}

    def test_vectara_params(self):
        p = VectaraParams(name="v", description="d")
        assert p.id == "655e20f46eb563062a1aa301"
        assert "model" not in p.to_dict()

    def test_zeroentropy_params(self):
        p = ZeroEntropyParams(name="z", description="d")
        assert p.id == "6807949168e47e7844c1f0c5"

    def test_graphrag_params(self):
        p = GraphRAGParams(name="g", description="d", llm="some-llm")
        assert p.id == "67dd6d487cbf0a57cf4b72f3"
        assert p.to_dict()["llm"] == "some-llm"


class TestIndexResult:
    def test_from_minimal_dict(self):
        r = IndexResult.from_dict({"status": "SUCCESS", "data": 4})
        assert r.status == "SUCCESS"
        assert r.completed is True
        assert r.data == 4


# ---------------------------------------------------------------------------
# Data-plane
# ---------------------------------------------------------------------------
class TestDataPlane:
    def test_search_text(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": [{"id": "1"}], "completed": True})
        idx = _index(ctx)

        result = idx.search("hello", top_k=3)

        assert isinstance(result, IndexResult)
        assert result.status == ResponseStatus.SUCCESS
        method, url = ctx.client.request.call_args[0]
        payload = ctx.client.request.call_args.kwargs["json"]
        assert method == "post"
        assert url == f"{MODEL_URL}/{INDEX_ID}"
        assert payload["action"] == "search"
        assert payload["data"] == "hello"
        assert payload["dataType"] == "text"
        assert payload["payload"]["top_k"] == 3
        assert payload["filters"] == []

    def test_search_with_filters(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": [], "completed": True})
        idx = _index(ctx)

        idx.search("q", filters=[IndexFilter("category", "tech", IndexFilterOperator.EQUALS)])

        payload = ctx.client.request.call_args.kwargs["json"]
        assert payload["filters"] == [{"field": "category", "value": "tech", "operator": "=="}]

    def test_upsert_text_echoes_payloads(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "completed": True})
        idx = _index(ctx)

        records = [Record(value="a", id="1"), Record(value="b", id="2")]
        result = idx.upsert(records)

        payload = ctx.client.request.call_args.kwargs["json"]
        assert payload["action"] == "ingest"
        assert len(payload["data"]) == 2
        # On success, the result echoes the ingested payloads.
        assert isinstance(result.data, list) and len(result.data) == 2
        assert result.data[0]["document_id"] == "1"

    def test_upsert_with_splitter(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "completed": True})
        idx = _index(ctx)

        idx.upsert([Record(value="a", id="1")], splitter=Splitter(split=True, split_length=400, split_overlap=50))

        payload = ctx.client.request.call_args.kwargs["json"]
        assert payload["additional_params"]["splitter"]["split"] is True
        assert payload["additional_params"]["splitter"]["split_length"] == 400

    def test_count(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": 4})
        idx = _index(ctx)

        assert idx.count() == 4
        assert ctx.client.request.call_args.kwargs["json"] == {"action": "count", "data": ""}

    def test_get_record(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": {"id": "1"}, "completed": True})
        idx = _index(ctx)

        result = idx.get_record("1")
        assert result.status == ResponseStatus.SUCCESS
        assert ctx.client.request.call_args.kwargs["json"] == {"action": "get_document", "data": "1"}

    def test_delete_record(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "completed": True})
        idx = _index(ctx)

        idx.delete_record("1")
        assert ctx.client.request.call_args.kwargs["json"] == {"action": "delete", "data": "1"}

    def test_retrieve_records_with_filter(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": [], "completed": True})
        idx = _index(ctx)

        idx.retrieve_records_with_filter(IndexFilter("category", "world", IndexFilterOperator.EQUALS))
        payload = ctx.client.request.call_args.kwargs["json"]
        assert payload["action"] == "retrieve_by_filter"
        assert payload["data"] == {"field": "category", "value": "world", "operator": "=="}

    def test_delete_records_by_date(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "completed": True})
        idx = _index(ctx)

        idx.delete_records_by_date(1717708800)
        assert ctx.client.request.call_args.kwargs["json"] == {"action": "delete_by_date", "data": 1717708800}

    def test_search_async_polls(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "IN_PROGRESS", "data": "https://poll.test/abc"})
        ctx.client.get = Mock(return_value={"status": "SUCCESS", "completed": True, "data": [{"id": "1"}]})
        idx = _index(ctx)

        result = idx.search("q", timeout=5)
        assert result.completed is True
        assert result.status == ResponseStatus.SUCCESS
        ctx.client.get.assert_called_with("https://poll.test/abc")

    def test_failed_action_raises(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "FAILED", "error_message": "boom", "completed": True})
        idx = _index(ctx)

        with pytest.raises(Exception):
            idx.count()

    def test_count_async_zero_does_not_crash(self):
        """A zero count via the async-poll path must return 0, not raise on int({})."""
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "IN_PROGRESS", "data": "https://poll.test/c"})
        # poll() coerces falsy data to {}; backfill from raw must restore 0.
        ctx.client.get = Mock(return_value={"status": "SUCCESS", "completed": True, "data": 0})
        idx = _index(ctx)

        assert idx.count(timeout=5) == 0

    def test_search_async_preserves_details(self):
        """Structured `details` must survive the async-poll path (poll() drops them)."""
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "IN_PROGRESS", "data": "https://poll.test/s"})
        ctx.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": "top match",
                "details": [{"score": 0.9, "data": "top match"}],
            }
        )
        idx = _index(ctx)

        result = idx.search("q", timeout=5)
        assert result.data == "top match"
        assert result.details == [{"score": 0.9, "data": "top match"}]

    def test_generic_run_disabled(self):
        """Index.run()/run_async() must raise, not send a malformed payload."""
        idx = _index()
        with pytest.raises(NotImplementedError):
            idx.run(query="x")
        with pytest.raises(NotImplementedError):
            idx.run_async(query="x")


# ---------------------------------------------------------------------------
# Control-plane
# ---------------------------------------------------------------------------
class TestControlPlane:
    def test_create_with_params(self):
        ctx = _ctx()
        # store-model run returns the new collection ID in `data`
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": "new-collection-id", "completed": True})
        # subsequent get of the new collection
        ctx.client.get = Mock(return_value={"id": "new-collection-id", "name": "docs"})
        cls = _index_cls(ctx)

        index = cls.create(params=AirParams(name="docs", description="d"))

        assert isinstance(index, Index)
        assert index.id == "new-collection-id"
        # store model run hit the AIR model id
        run_url = ctx.client.request.call_args[0][1]
        assert run_url == f"{MODEL_URL}/66eae6656eb56311f2595011"
        assert ctx.client.request.call_args.kwargs["json"]["data"] == "docs"

    def test_create_legacy_args(self):
        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": "new-id", "completed": True})
        ctx.client.get = Mock(return_value={"id": "new-id", "name": "n"})
        cls = _index_cls(ctx)

        index = cls.create(name="n", description="d", embedding_model=EmbeddingModel.OPENAI_ADA002)
        assert index.id == "new-id"
        payload = ctx.client.request.call_args.kwargs["json"]
        assert payload == {"data": "n", "description": "d", "model": EmbeddingModel.OPENAI_ADA002.value}

    def test_create_rejects_params_and_name(self):
        cls = _index_cls(_ctx())
        with pytest.raises(AssertionError):
            cls.create(name="n", description="d", params=AirParams(name="n", description="d"))

    def test_create_requires_legacy_fields(self):
        cls = _index_cls(_ctx())
        with pytest.raises(AssertionError):
            cls.create(name="n")  # missing description

    def test_create_failure_raises(self):
        from aixplain.v2.exceptions import ResourceError

        ctx = _ctx()
        ctx.client.request = Mock(return_value={"status": "SUCCESS", "data": "", "completed": True})
        cls = _index_cls(ctx)
        with pytest.raises(ResourceError):
            cls.create(params=AirParams(name="n", description="d"))

    def test_list_resolves_by_name(self):
        ctx = _ctx()
        ctx.client.request = Mock(
            return_value={
                "items": [
                    {"id": "a", "name": "alpha"},
                    {"id": "b", "name": "beta"},
                ],
                "total": 2,
                "pageTotal": 2,
            }
        )
        cls = _index_cls(ctx)

        page = cls.list(query="alpha")
        assert page.total == 2
        names = [ix.name for ix in page]
        assert names == ["alpha", "beta"]
        assert all(isinstance(ix, Index) for ix in page)
        # function filter is SEARCH and endpoint is the proven paginate endpoint
        method, url = ctx.client.request.call_args[0]
        assert (method, url) == ("post", "sdk/models/paginate")
        assert ctx.client.request.call_args.kwargs["json"]["functions"] == ["search"]
        assert ctx.client.request.call_args.kwargs["headers"]["Authorization"] == "Token test-key"

    def test_delete(self):
        ctx = _ctx()
        ctx.client.request_raw = Mock(return_value=Mock(status_code=200))
        idx = _index(ctx, index_id="to-delete")

        result = idx.delete()

        assert result.deleted_id == "to-delete"
        assert result.status == ResponseStatus.SUCCESS
        assert idx.is_deleted is True
        method, url = ctx.client.request_raw.call_args[0]
        assert method == "delete"
        assert url == "sdk/models/to-delete"
        # legacy-compatible auth header
        headers = ctx.client.request_raw.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Token test-key"
