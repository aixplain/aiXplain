"""RLM parallel-mode chunk failures and rag-mode result count (BUG-1462)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from aixplain.v2.rlm import RLM, RLMResult

SECRET = "sk-test-secret-value-1234567890"


def _rlm(monkeypatch, worker_call):
    """An RLM with its worker, context window and chunking stubbed out."""
    rlm = RLM.__new__(RLM)
    rlm.context = SimpleNamespace(api_key=SECRET)
    rlm._used_credits = 0.0
    rlm.rag_top_k = 2
    rlm.rag_index_id = None
    rlm.rag_max_chunk_chars = 10_000
    monkeypatch.setattr(RLM, "_get_worker", lambda self: object())
    monkeypatch.setattr(RLM, "_get_worker_context_tokens", lambda self: 8_000)
    monkeypatch.setattr(RLM, "_worker_call", lambda self, prompt, *a, **k: worker_call(prompt))
    return rlm


@pytest.fixture
def three_chunks(monkeypatch):
    monkeypatch.setattr("aixplain.v2.rlm._chunk_context", lambda context, budget: ["part-A", "part-B", "part-C"])


class TestParallelChunkFailures:
    def test_every_chunk_failing_returns_failed_without_reduce(self, monkeypatch, three_chunks):
        prompts = []

        def worker(prompt):
            prompts.append(prompt)
            raise RuntimeError("429 rate limited")

        rlm = _rlm(monkeypatch, worker)
        result = rlm._run_parallel("ctx", "q", "t", 0.0)

        assert result.status == "FAILED"
        assert result.failed_chunks == 3
        assert "all 3 chunk(s) failed" in result.error_message
        assert "429 rate limited" in result.error_message
        # Only the three map calls: no reduce call synthesizing error strings.
        assert len(prompts) == 3

    def test_partial_failure_reports_count_and_keeps_errors_out_of_reduce(self, monkeypatch, three_chunks):
        reduce_prompts = []

        def worker(prompt):
            if "part-B" in prompt:
                raise RuntimeError("boom")
            if "part-A" in prompt or "part-C" in prompt:
                return "finding"
            reduce_prompts.append(prompt)
            return "final"

        rlm = _rlm(monkeypatch, worker)
        result = rlm._run_parallel("ctx", "q", "t", 0.0)

        assert result.status == "SUCCESS"
        assert result.data == "final"
        assert result.failed_chunks == 1
        assert reduce_prompts
        assert all("Error analyzing" not in p and "boom" not in p for p in reduce_prompts)

    def test_error_message_is_redacted(self, monkeypatch, three_chunks):
        def worker(prompt):
            raise RuntimeError(f"bad key {SECRET}")

        rlm = _rlm(monkeypatch, worker)
        result = rlm._run_parallel("ctx", "q", "t", 0.0)

        assert result.status == "FAILED"
        assert SECRET not in result.error_message

    def test_generic_parallel_error_is_redacted(self, monkeypatch):
        def boom(context, budget):
            raise RuntimeError(f"leak {SECRET}")

        monkeypatch.setattr("aixplain.v2.rlm._chunk_context", boom)
        rlm = _rlm(monkeypatch, lambda prompt: "x")
        result = rlm._run_parallel("ctx", "q", "t", 0.0)

        assert result.status == "FAILED"
        assert SECRET not in result.error_message

    def test_failed_chunks_defaults_to_zero_and_serializes(self):
        result = RLMResult(status="SUCCESS", completed=True)
        assert result.failed_chunks == 0
        result.failed_chunks = 2
        assert result.to_dict()["failedChunks"] == 2
        assert "failed_chunks=2" in repr(result)


class TestRagTopK:
    def test_search_sends_num_results_and_trims_to_top_k(self, monkeypatch):
        monkeypatch.setattr("aixplain.v2.rlm._chunk_context", lambda context, budget: [f"chunk-{i}" for i in range(6)])
        synthesis = []

        def worker(prompt):
            synthesis.append(prompt)
            return "answer"

        rlm = _rlm(monkeypatch, worker)
        index = MagicMock()
        search_records = [{"text": f"chunk-{i}", "metadata": {"position": i}, "score": 1.0} for i in range(5)]

        def index_run(action, data):
            if action == "search":
                return SimpleNamespace(data=search_records, used_credits=0)
            return SimpleNamespace(data=None, used_credits=0)

        index.run.side_effect = index_run
        rlm.context = SimpleNamespace(api_key=SECRET, Tool=MagicMock(return_value=index))

        result = rlm._run_rag("ctx", "q", "t", 0.0)

        assert result.status == "SUCCESS"
        search_call = [c for c in index.run.call_args_list if c.kwargs.get("action") == "search"][0]
        assert search_call.kwargs["data"]["top_k"] == 2
        assert search_call.kwargs["data"]["num_results"] == 2
        assert len(synthesis) == 1
        assert "chunk-0" in synthesis[0] and "chunk-1" in synthesis[0]
        assert not any(f"chunk-{i}" in synthesis[0] for i in range(2, 5))
