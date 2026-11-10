"""RLM load bounds (BUG-949).

* The orchestrator history sent per iteration is capped to a budget derived
  from the model context window instead of resending every prior REPL output.
* Thread-pool collection has a deadline and a submit window, and the reduce
  step isolates per-group failures like the map step does.
* The upload path writes the context to the temp file without an intermediate
  encoded copy.
"""

import json
import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import aixplain.v2.rlm as rlm_v2
from aixplain.v2.exceptions import ResourceError
from aixplain.v2.rlm import (
    RLM,
    _FutureTimeout,
    _bounded_map,
    _fit_history,
    _messages_to_prompt,
)


def _make_rlm(max_iterations: int = 10, timeout: float = 600.0) -> RLM:
    """Minimal v2 RLM with stubbed context client (mirrors tests/security)."""
    rlm = RLM.__new__(RLM)
    rlm.orchestrator_id = "orch-id"
    rlm.worker_id = "worker-id"
    rlm.max_iterations = max_iterations
    rlm.timeout = timeout
    rlm._setup_session_id = None
    rlm._repl_session_id = None
    rlm._sandbox_tool = None
    rlm._orchestrator = None
    rlm._worker = None
    rlm._messages = []
    rlm._used_credits = 0.0
    rlm._credits_lock = threading.Lock()
    rlm._teardown_action_name = rlm_v2._UNRESOLVED
    client = MagicMock()
    client.backend_url = "https://platform-api.aixplain.com"
    client.api_key = "test-key"
    rlm.context = client
    return rlm


def _model_response(text: str):
    return SimpleNamespace(data=text, completed=True, status="SUCCESS", used_credits=0.0, error_message=None)


# _fit_history


def _msgs(*sizes):
    out = [{"role": "system", "content": "S" * 100}]
    for i, size in enumerate(sizes):
        out.append({"role": "user" if i % 2 else "assistant", "content": f"m{i}:" + "x" * size})
    out.append({"role": "user", "content": "NEXT ACTION"})
    return out


class TestFitHistory:
    def test_under_budget_returns_the_same_list(self):
        messages = _msgs(10, 10)
        assert _fit_history(messages, 10_000) is messages

    def test_over_budget_keeps_system_last_and_newest_suffix(self):
        messages = _msgs(1000, 1000, 1000, 1000)
        fitted = _fit_history(messages, 2600)

        assert fitted[0] is messages[0]
        assert fitted[-1] is messages[-1]
        assert "omitted" in fitted[1]["content"]
        assert fitted[-2] is messages[-2]  # newest turn kept verbatim
        assert messages[1] not in fitted  # oldest turn dropped
        assert len(_messages_to_prompt(fitted)) <= 2600

    def test_giant_single_item_is_truncated(self):
        messages = _msgs(50_000)
        fitted = _fit_history(messages, 20_000)

        assert fitted[0] is messages[0] and fitted[-1] is messages[-1]
        assert "truncated" in fitted[-2]["content"]
        assert len(_messages_to_prompt(fitted)) <= 20_000

    def test_input_is_not_mutated(self):
        messages = _msgs(5000, 5000, 5000)
        snapshot = json.loads(json.dumps(messages))
        _fit_history(messages, 6000)
        assert messages == snapshot

    @pytest.mark.parametrize("budget", [10_000, 32_000, 50_000, 150_000])
    def test_serialized_length_fits_budget(self, budget):
        """Holds for every budget ``_history_budget_chars`` can produce (floor 32k chars)."""
        messages = _msgs(*([9_000] * 20))
        assert len(_messages_to_prompt(_fit_history(messages, budget))) <= budget

    def test_newest_turn_keeps_a_minimum_slice_under_a_tiny_budget(self):
        """Below the floor the newest turn is not cut to nothing; the floor wins."""
        messages = _msgs(*([9_000] * 3))
        fitted = _fit_history(messages, 1_000)
        assert len(fitted[-2]["content"]) >= rlm_v2._MIN_HISTORY_ITEM_CHARS


# _bounded_map


class TestBoundedMap:
    def test_preserves_order_and_isolates_exceptions(self):
        def fn(i):
            if i == 3:
                raise ValueError("boom")
            time.sleep(0.001 * (10 - i))
            return i * 10

        results = _bounded_map(fn, 10, max_workers=4, timeout=10)

        assert [r for i, r in enumerate(results) if i != 3] == [i * 10 for i in range(10) if i != 3]
        assert isinstance(results[3], ValueError)

    def test_returns_within_deadline_when_a_call_hangs(self):
        release = threading.Event()

        def fn(i):
            if i == 0:
                release.wait(30)
            return i

        try:
            started = time.monotonic()
            results = _bounded_map(fn, 4, max_workers=2, timeout=0.5)
            elapsed = time.monotonic() - started
        finally:
            release.set()

        assert elapsed < 3, f"took {elapsed:.1f}s; the deadline did not release the caller"
        assert isinstance(results[0], _FutureTimeout)
        assert results[1:] == [1, 2, 3]

    def test_never_more_than_window_futures_pending(self):
        lock = threading.Lock()
        state = {"submitted": 0, "finished": 0, "max_pending": 0}
        real_submit = rlm_v2.ThreadPoolExecutor.submit

        def counting_submit(self, fn, *args, **kwargs):
            with lock:
                state["submitted"] += 1
                pending = state["submitted"] - state["finished"]
                state["max_pending"] = max(state["max_pending"], pending)

            def wrapped(*a, **kw):
                try:
                    return fn(*a, **kw)
                finally:
                    with lock:
                        state["finished"] += 1

            return real_submit(self, wrapped, *args, **kwargs)

        def fn(i):
            time.sleep(0.002)
            return i

        with patch.object(rlm_v2.ThreadPoolExecutor, "submit", counting_submit):
            results = _bounded_map(fn, 200, max_workers=4, timeout=30)

        assert results == list(range(200))
        assert state["max_pending"] <= 4 * rlm_v2._FUTURES_WINDOW_FACTOR

    def test_empty_input(self):
        assert _bounded_map(lambda i: i, 0, max_workers=4, timeout=1) == []

    def test_timeout_is_a_stall_timeout_not_a_batch_deadline(self):
        # Total runtime (~0.6s) exceeds the timeout, but some call completes
        # well inside every 0.3s window, so nothing may be abandoned.
        def fn(i):
            time.sleep(0.05)
            return i

        results = _bounded_map(fn, 12, max_workers=1, timeout=0.3)
        assert results == list(range(12))


# Parallel map / reduce / llm_query


class TestParallelIsolation:
    def test_parallel_map_marks_failed_chunks(self):
        rlm = _make_rlm()

        def worker_call(prompt, max_tokens=None):
            if "Part 2 of" in prompt or "part 2" in prompt.lower():
                raise ResourceError("worker down")
            return "ok"

        with patch.object(rlm, "_worker_call", side_effect=worker_call):
            answers = rlm._parallel_map(["a", "b", "c"], "q")

        assert len(answers) == 3
        assert sum(a.startswith("[Error analyzing this part:") for a in answers) <= 1
        assert answers.count("ok") >= 2

    def test_hierarchical_reduce_isolates_one_failed_group(self):
        rlm = _make_rlm()
        calls = {"n": 0}

        def reduce_call(formatted, query, n):
            calls["n"] += 1
            if "BAD" in formatted:
                raise ResourceError("reduce failed")
            return "combined"

        answers = ["BAD"] + ["good"] * (rlm_v2._REDUCE_FAN_IN * 2)
        with patch.object(rlm, "_reduce_call", side_effect=reduce_call):
            final = rlm._hierarchical_reduce(answers, "q")

        assert final == "combined"
        assert calls["n"] >= 2

    def test_hierarchical_reduce_raises_when_every_group_fails(self):
        rlm = _make_rlm()
        answers = ["x"] * (rlm_v2._REDUCE_FAN_IN * 2)
        with patch.object(rlm, "_reduce_call", side_effect=ResourceError("down")):
            with pytest.raises(ResourceError, match="all 2 reduce group"):
                rlm._hierarchical_reduce(answers, "q")

    def test_resolve_llm_queries_timeout_becomes_error_marker(self):
        rlm = _make_rlm(timeout=0.3)
        release = threading.Event()

        def worker_call(prompt, max_tokens=None):
            if prompt == "slow":
                release.wait(30)
            return f"answer:{prompt}"

        rlm._worker = MagicMock()
        try:
            with patch.object(rlm, "_worker_call", side_effect=worker_call):
                started = time.monotonic()
                answers = rlm._resolve_llm_queries(["fast", "slow"])
                elapsed = time.monotonic() - started
        finally:
            release.set()

        assert elapsed < 3
        assert answers[rlm_v2._prompt_key("fast")] == "answer:fast"
        assert answers[rlm_v2._prompt_key("slow")].startswith("Error: llm_query failed")


# History budget in the recursive loop


class TestRecursiveHistoryBudget:
    def test_ten_iterations_with_large_outputs_stay_under_budget(self):
        rlm = _make_rlm(max_iterations=10)
        orchestrator = MagicMock()
        orchestrator.attributes = {"max_context_length": 32_000}
        sent = []

        def orch_run(text, max_tokens):
            sent.append(text)
            return _model_response(f"```repl\nprint({len(sent)})\n```")

        orchestrator.run.side_effect = orch_run
        worker = MagicMock()
        worker.attributes = {"max_context_length": 32_000}
        rlm._orchestrator = orchestrator
        rlm._worker = worker

        outputs = iter(f"ITER{i}-OUTPUT " + "y" * 100_000 for i in range(100))
        with (
            patch.object(rlm, "_preflight"),
            patch.object(rlm, "_setup_repl"),
            patch.object(rlm, "close"),
            patch.object(rlm, "_execute_code", side_effect=lambda code: next(outputs)),
        ):
            result = rlm._run_recursive("ctx", "q", "test", time.time(), 600)

        assert result.status == "SUCCESS"
        budget = rlm._history_budget_chars()
        assert len(sent) == 11  # 10 iterations + forced final
        assert all(len(text) <= budget for text in sent), [len(t) for t in sent]
        assert "ITER0-OUTPUT" not in sent[-1]
        # Full log is still retained internally / in the result.
        assert len(result.repl_logs) == 10

    def test_budget_prefers_orchestrator_window_then_worker_then_default(self):
        rlm = _make_rlm()
        rlm._orchestrator = SimpleNamespace(attributes={"max_context_length": 200_000})
        rlm._worker = SimpleNamespace(attributes={"max_context_length": 32_000})
        assert rlm._get_orchestrator_context_tokens() == 200_000

        rlm._orchestrator = SimpleNamespace(attributes={})
        assert rlm._get_orchestrator_context_tokens() == 32_000

        rlm._worker = SimpleNamespace(attributes=None)
        assert rlm._get_orchestrator_context_tokens() == rlm_v2._DEFAULT_ORCHESTRATOR_WINDOW_TOKENS

    def test_budget_has_a_floor(self):
        rlm = _make_rlm()
        rlm._orchestrator = SimpleNamespace(attributes={"max_context_length": 1000})
        rlm._worker = SimpleNamespace(attributes={})
        assert rlm._history_budget_chars() == rlm_v2._MIN_HISTORY_BUDGET_TOKENS * rlm_v2._CHARS_PER_TOKEN


# _setup_repl temp file


class TestSetupReplWritesContextFile:
    @pytest.mark.parametrize(
        "context, expected_ext",
        [({"k": [1, 2, "ü"]}, ".json"), ("plain text ü\nline two\r\n", ".txt"), ([1, {"a": None}], ".json")],
    )
    def test_uploaded_file_holds_the_context(self, context, expected_ext):
        rlm = _make_rlm()
        captured = {}

        def fake_upload(self, file_path, **kwargs):
            captured["path"] = file_path
            with open(file_path, "rb") as fh:
                captured["body"] = fh.read().decode("utf-8")
            return "https://bucket.s3.amazonaws.com/tmp/context"

        with (
            patch.object(rlm, "_get_sandbox", return_value=MagicMock()),
            patch.object(rlm, "_run_sandbox"),
            patch.object(rlm_v2.FileUploader, "upload", fake_upload),
        ):
            rlm._setup_repl(context)

        assert captured["path"].endswith(expected_ext)
        if expected_ext == ".json":
            assert json.loads(captured["body"]) == context
        else:
            assert captured["body"] == context
