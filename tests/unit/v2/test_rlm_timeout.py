"""RLM recursive-mode ``timeout`` is a real wall-clock bound (BUG-1453).

The deadline used to be checked only at the top of each iteration: the
orchestrator ``Model.run``, every sandbox execution and every ``llm_query``
ran unbounded, and after the timeout a forced-final orchestrator call was made
and the run reported ``SUCCESS``.

Budgets here are kept small (fractions of a second) so the suite stays fast.
"""

import threading
import time
from unittest.mock import MagicMock

import aixplain.v2.rlm as rlm_v2
from aixplain.v2.exceptions import TimeoutError as AixTimeoutError
from aixplain.v2.rlm import RLM, RLMResult

CODE_REPLY = "Let me look.\n```repl\nprint(1)\n```\n"


def _make_rlm(max_iterations: int = 10) -> RLM:
    rlm = RLM.__new__(RLM)
    rlm.orchestrator_id = "orch-id"
    rlm.worker_id = "worker-id"
    rlm.max_iterations = max_iterations
    rlm.timeout = 600.0
    rlm._setup_session_id = None
    rlm._repl_session_id = None
    rlm._sandbox_tool = None
    rlm._orchestrator = None
    rlm._worker = None
    rlm._messages = []
    rlm._used_credits = 0.0
    rlm._credits_lock = threading.Lock()
    rlm._teardown_action_name = None  # no close action: teardown wipes instead
    client = MagicMock()
    client.backend_url = "https://platform-api.aixplain.com"
    client.api_key = "test-key"
    client.model_url = "https://models.aixplain.com/api/v2/execute"
    rlm.context = client
    worker = MagicMock()
    worker.attributes = {"max_context_length": "128000"}
    worker.run.return_value = MagicMock(completed=True, status="SUCCESS", data="w", used_credits=0)
    rlm._worker = worker
    return rlm


class _Sandbox:
    """Records every run call; optionally sleeps on code containing ``slow``."""

    def __init__(self, slow: float = 0.0):
        self.slow = slow
        self.calls = []

    def list_actions(self):
        return []

    def run(self, data=None, action="run", **kwargs):
        data = data or {}
        self.calls.append({"code": data.get("code"), "kwargs": kwargs})
        if "slow" in (data.get("code") or ""):
            time.sleep(self.slow)
        return MagicMock(used_credits=0.0, data={"stdout": "", "stderr": ""})


def _orchestrator(replies, delay: float = 0.0):
    orch = MagicMock()
    turns = list(replies)

    def run(**kwargs):
        time.sleep(delay)
        reply = turns.pop(0) if len(turns) > 1 else turns[0]
        if isinstance(reply, BaseException):
            raise reply
        return MagicMock(completed=True, status="SUCCESS", data=reply, used_credits=0)

    orch.run.side_effect = run
    return orch


def _run(rlm, sandbox, orchestrator, timeout):
    rlm._sandbox_tool = sandbox
    rlm._orchestrator = orchestrator
    return rlm._run_recursive("https://storage.example.com/ctx.txt", "q?", "t", time.time(), timeout)


class TestDeadline:
    def test_slow_orchestrator_returns_within_t_plus_d_and_flags_timeout(self):
        """Acceptance: returns in ~T + d, one orchestrator call, no forced final."""
        rlm, sandbox = _make_rlm(), _Sandbox()
        orch = _orchestrator([CODE_REPLY], delay=0.4)

        started = time.time()
        result = _run(rlm, sandbox, orch, timeout=0.2)
        elapsed = time.time() - started

        assert elapsed < 0.2 + 0.4 + 0.25
        assert orch.run.call_count == 1
        assert isinstance(result, RLMResult)
        assert result.timed_out is True
        assert result.status == "FAILED"
        assert result.data is None
        assert "timeout of 0.2s" in result.error_message
        assert "timed_out=True" in repr(result)

    def test_every_call_receives_the_remaining_budget(self):
        rlm, sandbox = _make_rlm(), _Sandbox()
        orch = _orchestrator([CODE_REPLY, "FINAL(done)"])

        result = _run(rlm, sandbox, orch, timeout=5.0)

        assert result.status == "SUCCESS" and result.data == "done" and result.timed_out is False
        for call in orch.run.call_args_list:
            assert 0 < call.kwargs["timeout"] <= 5.0
        budgeted = [c for c in sandbox.calls if c["code"] is not None and "timeout" in c["kwargs"]]
        # preflight, context setup/prelude and the emitted block are all bounded.
        assert budgeted
        for call in budgeted:
            assert 0 < call["kwargs"]["timeout"] <= 5.0

    def test_remaining_blocks_skipped_after_deadline(self):
        rlm, sandbox = _make_rlm(), _Sandbox(slow=0.3)
        reply = "```repl\nslow = 1\n```\n```repl\nsecond_block = 2\n```\n"
        orch = _orchestrator([reply])

        result = _run(rlm, sandbox, orch, timeout=0.2)

        codes = [c["code"] for c in sandbox.calls if c["code"]]
        assert any("slow" in c for c in codes)
        assert not any("second_block" in c for c in codes)
        assert result.timed_out is True
        assert orch.run.call_count == 1

    def test_literal_final_survives_mid_iteration_timeout(self):
        rlm, sandbox = _make_rlm(), _Sandbox(slow=0.3)
        orch = _orchestrator(["```repl\nslow = 1\n```\nFINAL(the answer)"])

        result = _run(rlm, sandbox, orch, timeout=0.2)

        assert result.status == "SUCCESS"
        assert result.data == "the answer"
        assert result.timed_out is False

    def test_orchestrator_timeout_after_deadline_is_reported_as_timeout(self):
        rlm, sandbox = _make_rlm(), _Sandbox()
        orch = MagicMock()

        def run(**kwargs):
            time.sleep(kwargs["timeout"] + 0.01)
            raise AixTimeoutError("Operation timed out")

        orch.run.side_effect = run
        result = _run(rlm, sandbox, orch, timeout=0.2)

        assert result.timed_out is True
        assert result.status == "FAILED"
        assert "RLM run error" not in result.error_message

    def test_early_timeout_error_is_a_regular_failure(self):
        rlm, sandbox = _make_rlm(), _Sandbox()
        orch = _orchestrator([AixTimeoutError("upstream gave up early")])

        result = _run(rlm, sandbox, orch, timeout=5.0)

        assert result.status == "FAILED"
        assert result.timed_out is False
        assert "RLM run error" in result.error_message

    def test_forced_final_still_runs_when_iterations_run_out(self):
        rlm, sandbox = _make_rlm(max_iterations=2), _Sandbox()
        orch = _orchestrator([CODE_REPLY, CODE_REPLY, "forced answer"])

        result = _run(rlm, sandbox, orch, timeout=5.0)

        assert orch.run.call_count == 3
        assert "timeout" in orch.run.call_args_list[-1].kwargs
        assert result.status == "SUCCESS"
        assert result.data == "forced answer"
        assert result.timed_out is False

    def test_deadline_cleared_and_teardown_runs_on_timeout(self):
        rlm, sandbox = _make_rlm(), _Sandbox()
        orch = _orchestrator([CODE_REPLY], delay=0.3)

        _run(rlm, sandbox, orch, timeout=0.1)

        assert rlm._deadline is None
        assert rlm._repl_session_id is None and rlm._setup_session_id is None
        wipes = [c for c in sandbox.calls if c["code"] == rlm_v2._SESSION_WIPE_CODE]
        assert len(wipes) == 2
        assert all("timeout" not in c["kwargs"] for c in wipes)


class TestWorkerBudget:
    def test_worker_call_is_bounded_inside_a_recursive_run(self):
        rlm = _make_rlm()
        rlm._deadline = time.time() + 5.0
        rlm._worker_call("p")
        assert 0 < rlm._worker.run.call_args.kwargs["timeout"] <= 5.0

    def test_worker_call_unbounded_outside_recursive_mode(self):
        """Parallel/rag modes share ``_worker_call`` and keep their old behaviour."""
        rlm = _make_rlm()
        rlm._deadline = None
        rlm._worker_call("p")
        assert "timeout" not in rlm._worker.run.call_args.kwargs

    def test_rlm_result_timed_out_defaults_false_and_serializes(self):
        result = RLMResult(status="SUCCESS", completed=True, data="x")
        assert result.timed_out is False
        assert result.to_dict()["timedOut"] is False
