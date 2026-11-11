"""Unit tests for ``RLM.run(mode="rag")`` and the aIR search-response parser.

The aIR index is a ``MagicMock`` returned by the bound context's ``Tool.get``
(reused index) or ``Tool(...)`` (ephemeral index); no network is used.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from aixplain.v2 import rlm as rlm_mod
from aixplain.v2.rlm import RLM

from tests.unit.v2._rlm_fakes import FakeModel, make_context, make_rlm, resp


def _index(search_data, credits=0.0):
    index = MagicMock()
    index.id = "idx-1"

    def run(action, data):
        if action == "upsert":
            return resp(data={"ok": True}, used_credits=credits)
        if action == "search":
            if isinstance(search_data, BaseException):
                raise search_data
            return resp(data=search_data, used_credits=credits)
        raise AssertionError(f"unexpected action {action}")

    index.run.side_effect = run
    return index


def _rag_rlm(worker, index, **kwargs):
    ctx = make_context(models={"worker": worker})
    ctx.Tool.get.return_value = index
    ctx.Tool.return_value = index
    return make_rlm(ctx, **kwargs), ctx


def _actions(index):
    return [c.kwargs["action"] for c in index.run.call_args_list]


def test_existing_index_reused_and_not_deleted():
    worker = FakeModel(responder=lambda t: "synth", credits=0.5)
    index = _index(
        [{"text": "B", "metadata": {"position": 2}}, {"text": "A", "metadata": {"position": 1}}], credits=0.1
    )
    rlm, ctx = _rag_rlm(worker, index, rag_index_id="prebuilt", rag_top_k=2)

    result = rlm.run(data={"context": "doc " * 50, "query": "Where?"}, mode="rag")

    assert result.status == "SUCCESS"
    assert result.data == "synth"
    assert result.iterations_used == 1
    assert result.used_credits == pytest.approx(0.6)
    ctx.Tool.get.assert_called_once_with("prebuilt")
    ctx.Tool.assert_not_called()
    assert _actions(index) == ["search"]
    index.delete.assert_not_called()
    index.save.assert_not_called()
    # Retrieved chunks are re-ordered by original document position.
    prompt = worker.calls[0]["text"]
    assert prompt.startswith("User's query: Where?")
    assert prompt.index("A\n\n---\n\nB") > 0


def test_ephemeral_index_created_upserted_searched_and_deleted():
    worker = FakeModel(responder=lambda t: "synth")
    index = _index({"results": [{"text": "hit", "metadata": {"position": 0}, "score": 0.9}]}, credits=1.0)
    rlm, ctx = _rag_rlm(worker, index, rag_top_k=3, rag_max_chunk_chars=500)
    context = "z" * 1200  # several overlapping chunks at the 500-char floor

    result = rlm.run(data={"context": context, "query": "Q"}, mode="rag")

    assert result.status == "SUCCESS"
    assert result.data == "synth"
    assert result.used_credits == pytest.approx(2.0)  # upsert + search
    tool_kwargs = ctx.Tool.call_args.kwargs
    assert tool_kwargs["integration"] == rlm_mod._AIR_INTEGRATION_ID
    assert tool_kwargs["name"].startswith("RLM-rag-")
    index.save.assert_called_once()
    assert _actions(index) == ["upsert", "search"]
    records = index.run.call_args_list[0].kwargs["data"]["records"]
    expected_chunks = rlm_mod._chunk_context(context, 500)
    assert [r["text"] for r in records] == expected_chunks
    assert [r["id"] for r in records] == [f"chunk_{i}" for i in range(len(expected_chunks))]
    assert [r["metadata"]["position"] for r in records] == list(range(len(expected_chunks)))
    search_data = index.run.call_args_list[1].kwargs["data"]
    # aIR search honours ``num_results``; ``top_k`` is sent too (BUG-1462).
    assert search_data == {"query": "Q", "top_k": 3, "num_results": 3}
    index.delete.assert_called_once()


def test_top_k_clamped_to_number_of_chunks():
    worker = FakeModel(responder=lambda t: "synth")
    index = _index([{"text": "only"}])
    rlm, _ = _rag_rlm(worker, index, rag_top_k=10)

    rlm.run(data={"context": "tiny", "query": "Q"}, mode="rag")

    assert index.run.call_args_list[-1].kwargs["data"]["top_k"] == 1


def test_ephemeral_index_deleted_on_failure_path():
    worker = FakeModel(responder=lambda t: "unused")
    index = _index(RuntimeError("search down"))
    rlm, _ = _rag_rlm(worker, index)

    result = rlm.run(data={"context": "ctx", "query": "Q"}, mode="rag")

    assert result.status == "FAILED"
    assert result.completed is True
    assert result.data is None
    assert result.error_message == "RLM rag error: search down"
    assert result.iterations_used == 0
    index.delete.assert_called_once()
    assert worker.calls == []


def test_delete_failure_does_not_fail_the_run():
    worker = FakeModel(responder=lambda t: "synth")
    index = _index([{"text": "hit"}])
    index.delete.side_effect = RuntimeError("cannot delete")
    rlm, _ = _rag_rlm(worker, index)

    result = rlm.run(data={"context": "ctx", "query": "Q"}, mode="rag")

    assert result.status == "SUCCESS"
    assert result.data == "synth"


def test_no_hits_skips_worker_call():
    worker = FakeModel(responder=lambda t: "unused")
    index = _index([])
    rlm, _ = _rag_rlm(worker, index, rag_index_id="prebuilt")

    result = rlm.run(data={"context": "ctx", "query": "Q"}, mode="rag")

    assert result.status == "SUCCESS"
    assert result.data == "No information relevant to the query was found in the document."
    assert worker.calls == []


def test_worker_failure_surfaces_as_failed_result():
    worker = FakeModel(responder=lambda t: resp(status="FAILED", completed=False, error_message="bad"))
    index = _index([{"text": "hit"}])
    rlm, _ = _rag_rlm(worker, index, rag_index_id="prebuilt")

    result = rlm.run(data={"context": "ctx", "query": "Q"}, mode="rag")

    assert result.status == "FAILED"
    assert result.error_message == "RLM rag error: RLM: worker model failed — bad"


def test_reused_index_top_k_not_clamped_by_local_context():
    worker = FakeModel(responder=lambda t: "synth")
    index = _index([{"text": "hit"}])
    rlm, _ = _rag_rlm(worker, index, rag_index_id="prebuilt", rag_top_k=10)

    rlm.run(data={"context": "placeholder", "query": "Q"}, mode="rag")

    assert index.run.call_args_list[-1].kwargs["data"]["top_k"] == 10


# ---------------------------------------------------------------------------
# _parse_rag_search_response
# ---------------------------------------------------------------------------


class TestParseRagSearchResponse:
    parse = staticmethod(RLM._parse_rag_search_response)

    def test_list_of_records(self):
        out = self.parse(SimpleNamespace(data=[{"text": "a", "metadata": {"position": "3"}, "score": 0.5}]))
        assert out == [{"text": "a", "position": 3, "score": 0.5}]

    @pytest.mark.parametrize("key", ["results", "documents", "records", "matches", "data"])
    def test_dict_wrapping_keys(self, key):
        out = self.parse(SimpleNamespace(data={key: [{"text": "a"}]}))
        assert out == [{"text": "a", "position": 0, "score": 0}]

    def test_dict_without_known_list_key(self):
        assert self.parse(SimpleNamespace(data={"results": "not-a-list"})) == []

    def test_json_string(self):
        payload = json.dumps({"matches": [{"value": "v", "attributes": {"position": 7}, "score": 1}]})
        assert self.parse(SimpleNamespace(data=payload)) == [{"text": "v", "position": 7, "score": 1}]

    def test_invalid_json_string(self):
        assert self.parse(SimpleNamespace(data="not json")) == []

    def test_raw_object_without_data_attribute(self):
        assert self.parse([{"data": "d"}]) == [{"text": "d", "position": 0, "score": 0}]

    def test_non_list_non_dict(self):
        assert self.parse(SimpleNamespace(data=42)) == []
        assert self.parse(SimpleNamespace(data=None)) == []

    def test_skips_non_dict_records_and_defaults_fields(self):
        out = self.parse(
            SimpleNamespace(
                data=[
                    "junk",
                    {"metadata": {"position": "nan"}},
                    {"text": "t", "metadata": "not-a-dict"},
                ]
            )
        )
        assert out == [
            {"text": "", "position": 0, "score": 0},
            {"text": "t", "position": 0, "score": 0},
        ]
