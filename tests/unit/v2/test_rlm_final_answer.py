"""RLM final-answer parsing and the forced final answer (BUG-1460).

No network: the orchestrator, sandbox and REPL setup are stubbed.
"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

import aixplain.v2.rlm as rlm_v2
from aixplain.v2.rlm import RLM, RLMResult, _find_final_answer


# _find_final_answer


@pytest.mark.parametrize(
    "text, expected",
    [
        ("FINAL(Paris)", ("FINAL", "Paris")),
        (
            "FINAL(Revenue was $5M (up 10% YoY) in Q3, driven by EMEA.)",
            ("FINAL", "Revenue was $5M (up 10% YoY) in Q3, driven by EMEA."),
        ),
        ("FINAL(Revenue was $5M (up 10% YoY) in Q3.)", ("FINAL", "Revenue was $5M (up 10% YoY) in Q3.")),
        ("FINAL(The function f(x) returns 2.)", ("FINAL", "The function f(x) returns 2.")),
        ("FINAL(a (b (c) d) e)", ("FINAL", "a (b (c) d) e")),
        ("FINAL(Paris)\n\n(Note: from REPL)", ("FINAL", "Paris")),
        ("FINAL(Paris) (confidence: high)", ("FINAL", "Paris")),
        # Text after the balanced ")" is never part of the answer, even when it
        # holds an extra ")" (an emoticon or a list marker).
        ("FINAL(Paris) — see the note :)", ("FINAL", "Paris")),
        ("FINAL(42) (see 1) above)", ("FINAL", "42")),
        ("FINAL(Paris) 1) see list", ("FINAL", "Paris")),
        # An unclosed "(" falls back to the last ")" in the declaration's paragraph.
        ("FINAL(see item (a in the list)", ("FINAL", "see item (a in the list")),
        ("FINAL(Great :( sorry)\n\n(Note: computed in the REPL)", ("FINAL", "Great :( sorry")),
        ("FINAL(Option (a is best)\n\nSources (REPL output) checked.", ("FINAL", "Option (a is best")),
        ("FINAL(Option (a is best)\n  \nSources (REPL output) checked.", ("FINAL", "Option (a is best")),
        # No ")" in that paragraph at all: the last ")" in the reply is used.
        ("FINAL(first (part\n\nsecond part)", ("FINAL", "first (part\n\nsecond part")),
        ("FINAL(line1\nline2 (x)\nline3)", ("FINAL", "line1\nline2 (x)\nline3")),
        ("Some reasoning first.\n  FINAL(x)", ("FINAL", "x")),
        ("FINAL_VAR(answer)", ("FINAL_VAR", "answer")),
        ("FINAL(no closing paren", None),
        ("no declaration here", None),
    ],
)
def test_find_final_answer(text, expected):
    assert _find_final_answer(text) == expected


# Forced final answer


def _make_rlm(max_iterations: int = 2) -> RLM:
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
    rlm._teardown_action_name = rlm_v2._UNRESOLVED
    rlm.context = MagicMock()
    return rlm


def _sandbox_result(stdout: str = "", stderr: str = ""):
    result = MagicMock()
    result.data = {"stdout": stdout, "stderr": stderr}
    result.used_credits = 0.0
    return result


def _run(rlm: RLM, loop_reply: str, forced_reply: str, repl=None, start_time=None, timeout=600.0):
    """Drive ``_run_recursive`` with stubbed REPL setup and orchestrator.

    ``repl`` maps variable names to values for ``print(str(name))`` lookups.
    Returns ``(result, events)`` where ``events`` records sandbox lookups and
    ``close`` in call order.
    """
    repl = repl or {}
    events = []
    replies = []

    def _completion(messages):
        last = messages[-1]["content"]
        reply = forced_reply if last == rlm_v2._FORCE_FINAL_PROMPT else loop_reply
        replies.append(reply)
        return reply

    def _run_sandbox(sandbox, code, session=None):
        events.append(("sandbox", code))
        for name, value in repl.items():
            if code == f"print(str({name}))":
                return _sandbox_result(stdout=value)
        return _sandbox_result(stderr="NameError: name is not defined")

    with (
        patch.object(RLM, "_preflight"),
        patch.object(RLM, "_setup_repl"),
        patch.object(RLM, "_get_worker_context_window", return_value=128000),
        patch.object(RLM, "_get_sandbox", return_value=MagicMock()),
        patch.object(RLM, "_run_sandbox", side_effect=_run_sandbox),
        patch.object(RLM, "_orchestrator_completion", side_effect=_completion),
        patch.object(RLM, "close", side_effect=lambda: events.append(("close", None))),
    ):
        result = rlm._run_recursive("ctx", "Capital of France?", "test", start_time or time.time(), timeout)
    return result, events, replies


class TestForcedFinalAnswer:
    def test_final_var_resolved_before_close(self):
        result, events, _ = _run(_make_rlm(), "Still thinking.", "FINAL_VAR(x)", repl={"x": "Paris"})

        assert result.status == "SUCCESS"
        assert result.data == "Paris"
        assert result.final_answer_forced is True
        assert events.index(("sandbox", "print(str(x))")) < events.index(("close", None))

    def test_final_parsed(self):
        result, _, _ = _run(_make_rlm(), "Still thinking.", "FINAL(Paris)")

        assert result.status == "SUCCESS"
        assert result.data == "Paris"
        assert result.final_answer_forced is True

    def test_final_with_parentheses(self):
        result, _, _ = _run(_make_rlm(), "Still thinking.", "FINAL(The function f(x) returns 2.)")

        assert result.status == "SUCCESS"
        assert result.data == "The function f(x) returns 2."

    def test_unparseable_reply_is_failed(self):
        result, _, _ = _run(_make_rlm(), "Still thinking.", "I think it's Paris")

        assert result.status == "FAILED"
        assert result.data == "I think it's Paris"
        assert "FINAL" in result.error_message
        assert result.final_answer_forced is True

    def test_unresolvable_final_var_is_failed(self):
        result, _, _ = _run(_make_rlm(), "Still thinking.", "FINAL_VAR(missing)")

        assert result.status == "FAILED"
        assert result.data == "FINAL_VAR(missing)"
        assert "missing" in result.error_message

    @pytest.mark.parametrize("reply", ["FINAL()", "FINAL(   )"])
    def test_empty_final_is_failed(self, reply):
        result, _, _ = _run(_make_rlm(), "Still thinking.", reply)

        assert result.status == "FAILED"
        assert result.data == reply
        assert "empty" in result.error_message
        assert result.final_answer_forced is True

    def test_final_var_lookup_error_keeps_raw_reply(self):
        with patch.object(RLM, "_get_repl_variable", side_effect=RuntimeError("sandbox down")):
            result, _, _ = _run(_make_rlm(), "Still thinking.", "FINAL_VAR(x)")

        assert result.status == "FAILED"
        assert result.data == "FINAL_VAR(x)"
        assert "sandbox down" in result.error_message
        assert result.final_answer_forced is True

    def test_invalid_identifier_is_failed_without_sandbox_call(self):
        result, events, _ = _run(_make_rlm(), "Still thinking.", "FINAL_VAR(1bad)")

        assert result.status == "FAILED"
        assert not [e for e in events if e[0] == "sandbox"]

    def test_timeout_reaches_forced_parse(self):
        result, _, replies = _run(
            _make_rlm(max_iterations=5),
            "Still thinking.",
            "FINAL_VAR(x)",
            repl={"x": "Paris"},
            start_time=time.time() - 100,
            timeout=1.0,
        )

        assert replies == ["FINAL_VAR(x)"]
        assert result.status == "SUCCESS"
        assert result.data == "Paris"
        assert result.final_answer_forced is True

    def test_in_loop_answer_is_not_forced(self):
        result, _, replies = _run(_make_rlm(), "FINAL(Paris (France))", "FINAL(unused)")

        assert result.status == "SUCCESS"
        assert result.data == "Paris (France)"
        assert result.final_answer_forced is False
        assert replies == ["FINAL(Paris (France))"]


def test_final_answer_forced_not_serialized():
    result = RLMResult(status="SUCCESS", completed=True, data="Paris")
    result.final_answer_forced = True

    assert "final_answer_forced" not in result.to_dict()
    assert "finalAnswerForced" not in result.to_dict()
    assert "final_answer_forced=True" in repr(result)
