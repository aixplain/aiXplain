"""Unit tests for ``RLM.run(mode="parallel")``: chunk -> parallel map -> reduce.

The worker is an in-memory fake; no orchestrator, sandbox or network is used.
"""

import pytest

from aixplain.v2 import rlm as rlm_mod
from aixplain.v2.exceptions import ResourceError

from tests.unit.v2._rlm_fakes import FakeModel, make_context, make_rlm, resp

# Tiny worker window -> chunk budget hits the floor of 1000 tokens * 4 = 4000 chars.
SMALL_WINDOW = 100
BUDGET = rlm_mod._compute_chunk_budget_chars(SMALL_WINDOW)


def _rlm_with_worker(worker):
    return make_rlm(make_context(models={"worker": worker}))


def _is_map(text):
    return text.startswith("You are analyzing part")


def _is_reduce(text):
    return text.startswith("You are synthesizing")


def test_small_context_single_worker_call():
    worker = FakeModel(responder=lambda t: "the answer", max_context_length=SMALL_WINDOW, credits=0.25)
    rlm = _rlm_with_worker(worker)

    result = rlm.run(data={"context": "short doc", "query": "What?"}, mode="parallel")

    assert result.status == "SUCCESS"
    assert result.completed is True
    assert result.data == "the answer"
    assert result.iterations_used == 1
    assert result.used_credits == pytest.approx(0.25)
    assert result.run_time >= 0
    assert len(worker.calls) == 1
    prompt = worker.calls[0]["text"]
    assert prompt.startswith("User's query: What?")
    assert "short doc" in prompt
    assert worker.calls[0]["max_tokens"] == rlm_mod._RESERVED_OUTPUT_TOKENS


def test_large_context_maps_each_chunk_then_reduces():
    def responder(text):
        if _is_map(text):
            idx = text.split("part ", 1)[1].split(" ", 1)[0]
            return f"finding-{idx}"
        assert _is_reduce(text)
        return "merged"

    worker = FakeModel(responder=responder, max_context_length=SMALL_WINDOW, credits=1.0)
    rlm = _rlm_with_worker(worker)
    context = "x" * (BUDGET * 2)  # -> 3 overlapping chunks
    n_chunks = len(rlm_mod._chunk_text(context, BUDGET))
    assert n_chunks == 3

    result = rlm.run(data={"context": context, "query": "Summarize"}, mode="parallel")

    assert result.status == "SUCCESS"
    assert result.data == "merged"
    assert result.iterations_used == n_chunks
    map_calls = [c["text"] for c in worker.calls if _is_map(c["text"])]
    reduce_calls = [c["text"] for c in worker.calls if _is_reduce(c["text"])]
    assert len(map_calls) == n_chunks
    assert len(reduce_calls) == 1
    for i in range(1, n_chunks + 1):
        assert sum(f"part {i} of {n_chunks} " in c for c in map_calls) == 1
    # Partial answers reach the reducer in document order.
    reduce_prompt = reduce_calls[0]
    assert reduce_prompt.index("[Part 1]: finding-1") < reduce_prompt.index("[Part 3]: finding-3")
    # Credits: every map call plus the reduce call.
    assert result.used_credits == pytest.approx(n_chunks + 1)


def test_all_none_answers_short_circuit_reduce():
    worker = FakeModel(responder=lambda t: "NONE." if _is_map(t) else "unexpected", max_context_length=SMALL_WINDOW)
    rlm = _rlm_with_worker(worker)

    result = rlm.run(data={"context": "y" * (BUDGET * 2), "query": "Q"}, mode="parallel")

    assert result.data == "No information relevant to the query was found in the document."
    assert not any(_is_reduce(c["text"]) for c in worker.calls)


def test_single_meaningful_answer_still_goes_through_reduce():
    def responder(text):
        if _is_map(text):
            return "only fact" if "part 2 of" in text else "NONE"
        return "final wording"

    worker = FakeModel(responder=responder, max_context_length=SMALL_WINDOW)
    rlm = _rlm_with_worker(worker)

    result = rlm.run(data={"context": "z" * (BUDGET * 2), "query": "Q"}, mode="parallel")

    assert result.data == "final wording"
    reduce_calls = [c["text"] for c in worker.calls if _is_reduce(c["text"])]
    assert len(reduce_calls) == 1
    assert "[Part]: only fact" in reduce_calls[0]
    assert "from 1 parts" in reduce_calls[0]


def test_hierarchical_reduce_when_answers_exceed_budget():
    big = "w" * (BUDGET // 4)

    def responder(text):
        if _is_map(text):
            return big
        return "level-answer"

    worker = FakeModel(responder=responder, max_context_length=SMALL_WINDOW)
    rlm = _rlm_with_worker(worker)
    # 10 list items of BUDGET chars each -> 10 chunks -> 10 partial answers
    # whose concatenation (~2.5 budgets) is too large for one reduce call.
    context = ["i" * (BUDGET - 10) for _ in range(10)]

    result = rlm.run(data={"context": context, "query": "Q"}, mode="parallel")

    assert result.status == "SUCCESS"
    assert result.data == "level-answer"
    assert result.iterations_used == 10
    reduce_calls = [c["text"] for c in worker.calls if _is_reduce(c["text"])]
    # Level 1: ceil(10 / fan-in 8) = 2 groups; level 2: 1 group.
    assert len(reduce_calls) == 3
    assert sorted(c.split(" parts", 1)[0].rsplit(" ", 1)[1] for c in reduce_calls) == ["2", "2", "8"]


def test_hierarchical_reduce_directly():
    worker = FakeModel(responder=lambda t: "r")
    rlm = _rlm_with_worker(worker)
    assert rlm._hierarchical_reduce([f"a{i}" for i in range(17)], "Q") == "r"
    # 17 -> 3 groups -> 1 group
    assert len(worker.calls) == 4


def test_failed_chunk_is_left_out_of_the_reduce_and_run_succeeds():
    def responder(text):
        if _is_map(text) and "part 2 of" in text:
            return resp(data=None, status="FAILED", completed=False, error_message="boom")
        if _is_map(text):
            return "ok"
        return "reduced"

    worker = FakeModel(responder=responder, max_context_length=SMALL_WINDOW)
    rlm = _rlm_with_worker(worker)

    result = rlm.run(data={"context": "q" * (BUDGET * 2), "query": "Q"}, mode="parallel")

    assert result.status == "SUCCESS"
    assert result.failed_chunks == 1
    reduce_prompt = next(c["text"] for c in worker.calls if _is_reduce(c["text"]))
    # BUG-1462: the failed slot becomes "NONE" and is dropped, so the error text
    # is never synthesized as if it were document content.
    assert "[Part 1]: ok" in reduce_prompt
    assert "[Part 3]: ok" in reduce_prompt
    assert "[Part 2]" not in reduce_prompt
    assert "boom" not in reduce_prompt


def test_worker_call_raises_resource_error_on_failed_status():
    worker = FakeModel(responder=lambda t: resp(status="FAILED", completed=False, error_message=None, used_credits=2))
    rlm = _rlm_with_worker(worker)
    with pytest.raises(ResourceError, match="worker model failed — FAILED"):
        rlm._worker_call("p")
    # Credits are still accounted for a failed call.
    assert rlm._used_credits == 2


def test_single_call_failure_returns_failed_result():
    worker = FakeModel(
        responder=lambda t: resp(status="FAILED", completed=False, error_message="quota", used_credits=0.5),
        max_context_length=SMALL_WINDOW,
    )
    rlm = _rlm_with_worker(worker)

    result = rlm.run(data={"context": "short", "query": "Q"}, mode="parallel")

    assert result.status == "FAILED"
    assert result.completed is True
    assert result.data is None
    assert result.error_message == "RLM parallel error: RLM: worker model failed — quota"
    assert result.iterations_used == 0
    assert result.used_credits == pytest.approx(0.5)


def test_reduce_failure_returns_failed_result():
    def responder(text):
        if _is_map(text):
            return "fact"
        raise RuntimeError("reduce exploded")

    worker = FakeModel(responder=responder, max_context_length=SMALL_WINDOW)
    rlm = _rlm_with_worker(worker)

    result = rlm.run(data={"context": "q" * (BUDGET * 2), "query": "Q"}, mode="parallel")

    assert result.status == "FAILED"
    assert "reduce exploded" in result.error_message


def test_used_credits_reset_between_runs():
    worker = FakeModel(responder=lambda t: "a", max_context_length=SMALL_WINDOW, credits=1.0)
    rlm = _rlm_with_worker(worker)
    rlm.run(data={"context": "c", "query": "Q"}, mode="parallel")
    second = rlm.run(data={"context": "c", "query": "Q"}, mode="parallel")
    assert second.used_credits == pytest.approx(1.0)


def test_url_context_is_resolved_before_chunking(monkeypatch):
    worker = FakeModel(responder=lambda t: "a", max_context_length=SMALL_WINDOW)
    rlm = _rlm_with_worker(worker)
    seen = []
    monkeypatch.setattr(type(rlm), "_resolve_url_context", staticmethod(lambda c: seen.append(c) or "downloaded"))

    result = rlm.run(data={"context": "https://example.com/doc.txt", "query": "Q"}, mode="parallel")

    assert result.status == "SUCCESS"
    assert seen == ["https://example.com/doc.txt"]
    assert "downloaded" in worker.calls[0]["text"]


def test_default_query_for_plain_string_data():
    worker = FakeModel(responder=lambda t: "a", max_context_length=SMALL_WINDOW)
    rlm = _rlm_with_worker(worker)
    rlm.run(data="raw body", mode="parallel")
    assert rlm_mod._DEFAULT_QUERY in worker.calls[0]["text"]
