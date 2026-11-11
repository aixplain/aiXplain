"""Unit tests for ``RLM.run(mode="recursive")``, sandbox session handling and ``run()`` dispatch.

The orchestrator and worker are scripted fakes. The sandbox is either a
recording fake or ``ExecSandbox``, which executes code in-process so the
``llm_query`` prelude / marker / answer-injection protocol is exercised end to
end. ``FileUploader`` is patched so no upload request is made.
"""

import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from aixplain.v2 import rlm as rlm_mod
from aixplain.v2.exceptions import ResourceError

from tests.unit.v2._rlm_fakes import (
    API_KEY,
    ExecSandbox,
    FakeModel,
    FakeSandbox,
    ScriptedModel,
    make_context,
    make_rlm,
    resp,
)

DOWNLOAD_URL = "https://storage.example.invalid/tmp/context?sig=abc"


@pytest.fixture(autouse=True)
def _no_env_keys(monkeypatch):
    monkeypatch.delenv("TEAM_API_KEY", raising=False)
    monkeypatch.delenv("AIXPLAIN_API_KEY", raising=False)


@pytest.fixture
def uploads(monkeypatch):
    """Patch FileUploader; record the uploaded file's name and bytes."""
    seen = []

    class _Uploader:
        def __init__(self, backend_url, api_key):
            seen.append({"backend_url": backend_url, "api_key": api_key})

        def upload(self, file_path, is_temp, return_download_link):
            with open(file_path, "rb") as fh:
                seen[-1].update(
                    name=os.path.basename(file_path),
                    path=file_path,
                    body=fh.read(),
                    is_temp=is_temp,
                    return_download_link=return_download_link,
                )
            return DOWNLOAD_URL

    monkeypatch.setattr(rlm_mod, "FileUploader", _Uploader)
    return seen


def _recursive_rlm(orchestrator, sandbox, worker=None, **kwargs):
    worker = worker or FakeModel(responder=lambda t: "worker-answer", max_context_length=64_000)
    ctx = make_context(models={"orch": orchestrator, "worker": worker}, sandbox=sandbox)
    return make_rlm(ctx, **kwargs)


def _block(code):
    return f"```repl\n{code}\n```"


# ---------------------------------------------------------------------------
# Readiness / validation
# ---------------------------------------------------------------------------


class TestRunValidation:
    def test_recursive_without_orchestrator_raises(self, uploads):
        rlm = make_rlm(make_context(), orchestrator_id="")
        with pytest.raises(ResourceError, match="orchestrator_id"):
            rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")
        assert uploads == []

    def test_assert_ready_requires_worker(self):
        with pytest.raises(ResourceError, match="worker_id"):
            make_rlm(worker_id="")._assert_ready()

    def test_invalid_mode(self):
        with pytest.raises(ValueError, match="Invalid mode"):
            make_rlm().run(data="c", mode="turbo")

    def test_missing_worker(self):
        with pytest.raises(ResourceError, match="worker_id"):
            make_rlm(worker_id="").run(data="c", mode="parallel")

    def test_dict_without_context(self):
        with pytest.raises(ValueError, match="'context' key"):
            make_rlm().run(data={"query": "Q"})

    @pytest.mark.parametrize("bad", [42, ["a"], None])
    def test_unsupported_data_type(self, bad):
        with pytest.raises(ValueError, match="Unsupported data type"):
            make_rlm().run(data=bad)


class TestAutoDispatch:
    def _patched(self, monkeypatch):
        rlm = make_rlm()
        mocks = {m: MagicMock(return_value=m) for m in ("_run_parallel", "_run_recursive", "_run_rag")}
        for name, mock in mocks.items():
            monkeypatch.setattr(rlm, name, mock)
        return rlm, mocks

    def test_auto_picks_parallel_by_default(self, monkeypatch):
        rlm, mocks = self._patched(monkeypatch)
        assert rlm.run(data={"context": "c", "query": "Summarize it"}) == "_run_parallel"
        args = mocks["_run_parallel"].call_args.args
        assert args[:3] == ("c", "Summarize it", "rlm_process")
        mocks["_run_recursive"].assert_not_called()

    def test_auto_picks_recursive_for_multi_hop(self, monkeypatch):
        rlm, mocks = self._patched(monkeypatch)
        rlm.timeout = 77.0
        assert rlm.run(data={"context": "c", "query": "Compare across sections"}, name="n") == "_run_recursive"
        context, query, name, _start, timeout = mocks["_run_recursive"].call_args.args
        assert (context, query, name, timeout) == ("c", "Compare across sections", "n", 77.0)

    def test_explicit_timeout_overrides_default(self, monkeypatch):
        rlm, mocks = self._patched(monkeypatch)
        rlm.run(data={"context": "c", "query": "Q"}, mode="recursive", timeout=5)
        assert mocks["_run_recursive"].call_args.args[4] == 5

    def test_rag_only_when_requested(self, monkeypatch):
        rlm, mocks = self._patched(monkeypatch)
        assert rlm.run(data={"context": "c", "query": "Q"}, mode="rag") == "_run_rag"

    def test_path_data_is_read(self, monkeypatch, tmp_path):
        f = tmp_path / "doc.json"
        f.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        rlm, mocks = self._patched(monkeypatch)
        rlm.run(data=f, mode="parallel")
        context, query = mocks["_run_parallel"].call_args.args[:2]
        assert context == [1, 2, 3]
        assert query == rlm_mod._DEFAULT_QUERY


# ---------------------------------------------------------------------------
# Full recursive loop
# ---------------------------------------------------------------------------


class TestRecursiveLoop:
    def test_happy_path_code_then_final(self, uploads):
        orch = ScriptedModel([f"Look first.\n{_block('print(context[:5])')}", "FINAL(The answer is 42)"], credits=1.0)
        sandbox = ExecSandbox(context_value="hello world", credits=0.5)
        rlm = _recursive_rlm(orch, sandbox, max_iterations=5)

        result = rlm.run(data={"context": "hello world", "query": "What?"}, mode="recursive")

        assert result.status == "SUCCESS", result.error_message
        assert result.data == "The answer is 42"
        assert result.iterations_used == 2
        assert result.repl_logs == [{"iteration": 0, "code": "print(context[:5])", "output": "hello\n"}]
        # 2 orchestrator calls + 4 sandbox runs (preflight, context, prelude, block).
        assert result.used_credits == pytest.approx(2 * 1.0 + 4 * 0.5)
        assert result.run_time >= 0

        # The context was uploaded as a text file, never with the key in sandbox code.
        assert uploads[0]["name"] == "context.txt"
        assert uploads[0]["body"] == b"hello world"
        assert uploads[0]["is_temp"] is True
        assert not os.path.exists(uploads[0]["path"])
        assert all(API_KEY not in (c.get("data", {}).get("code") or "") for c in sandbox.calls)

        # Two distinct sessions; setup only ever receives the preflight probe.
        setup_id = sandbox.calls[0]["data"]["sessionId"]
        repl_id = sandbox.calls[1]["data"]["sessionId"]
        assert setup_id != repl_id
        assert sandbox.calls[0]["data"]["code"] == rlm_mod._PREFLIGHT_CODE
        assert DOWNLOAD_URL in sandbox.calls[1]["data"]["code"]
        assert sandbox.calls[2]["data"]["code"] == rlm_mod._LLM_QUERY_PRELUDE
        setup_codes = [c["data"].get("code") for c in sandbox.calls if c["data"]["sessionId"] == setup_id]
        assert setup_codes == [rlm_mod._PREFLIGHT_CODE, rlm_mod._SESSION_WIPE_CODE]

        # The second orchestrator prompt carries the REPL output.
        second_prompt = orch.calls[1]["text"]
        assert "REPL output:\nhello" in second_prompt
        assert second_prompt.startswith("[SYSTEM]:")
        assert "64K tokens" in second_prompt
        assert orch.calls[0]["max_tokens"] == 8192

        # Both sessions torn down (wiped: no close action advertised), repl first.
        wipes = [c["data"]["sessionId"] for c in sandbox.calls if c["data"].get("code") == rlm_mod._SESSION_WIPE_CODE]
        assert wipes == [repl_id, setup_id]
        assert rlm._repl_session_id is None and rlm._setup_session_id is None

    def test_dict_context_uploaded_as_json_and_loaded(self, uploads):
        orch = ScriptedModel([_block("print(context['k'])"), "FINAL(done)"])
        sandbox = ExecSandbox(context_value={"k": "v"})
        rlm = _recursive_rlm(orch, sandbox)

        result = rlm.run(data={"context": {"k": "v"}, "query": "Q"}, mode="recursive")

        assert result.status == "SUCCESS"
        assert uploads[0]["name"] == "context.json"
        assert json.loads(uploads[0]["body"]) == {"k": "v"}
        assert "__json.load(_f)" in sandbox.calls[1]["data"]["code"]
        assert result.repl_logs[0]["output"] == "v\n"

    def test_url_context_streamed_without_upload(self, uploads):
        url = "https://example.com/data.json"
        orch = ScriptedModel(["FINAL(ok)"])
        sandbox = ExecSandbox(context_value="x")
        rlm = _recursive_rlm(orch, sandbox)

        result = rlm.run(data={"context": url, "query": "Q"}, mode="recursive")

        assert result.status == "SUCCESS"
        assert uploads == []
        assert repr(url) in sandbox.calls[1]["data"]["code"]

    def test_llm_query_round_trip(self, uploads):
        code = "ans = llm_query('What is X?')\nprint(ans)"
        orch = ScriptedModel([_block(code), _block(code), "FINAL_VAR(ans)"])
        worker = FakeModel(responder=lambda t: "X is 7", credits=0.25)
        sandbox = ExecSandbox(context_value="ctx")
        rlm = _recursive_rlm(orch, sandbox, worker=worker)

        result = rlm.run(data={"context": "ctx", "query": "Q"}, mode="recursive")

        assert result.status == "SUCCESS", result.error_message
        assert result.data == "X is 7"
        assert result.iterations_used == 3
        # The worker was called SDK-side exactly once, with the llm_query budget.
        assert worker.calls == [{"text": "What is X?", "max_tokens": rlm_mod._LLM_QUERY_MAX_TOKENS}]
        first, second = (log["output"] for log in result.repl_logs)
        # Turn A: marker stripped, placeholder shown, notice appended.
        assert rlm_mod._LLM_REQUEST_MARKER not in first
        assert rlm_mod._LLM_PENDING_SENTINEL in first
        assert "1 llm_query answer(s) are now cached" in first
        # Turn B: the real answer.
        assert second == "X is 7\n"
        # The answer was injected as data and the pending list cleared.
        inject = next(c for c in sandbox.codes() if c and c.startswith("_llm_answers.update("))
        assert rlm_mod._prompt_key("What is X?") in inject
        assert inject.endswith("_llm_query_pending.clear()")
        assert result.used_credits >= 0.25

    def test_max_iterations_exhausted_forces_final(self, uploads):
        orch = ScriptedModel(["thinking", "still thinking", "plain forced answer"])
        rlm = _recursive_rlm(orch, ExecSandbox(context_value="c"), max_iterations=2)

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        # BUG-1460: a forced reply with no FINAL/FINAL_VAR declaration is not a
        # plain SUCCESS; the raw reply is kept in data and the result is flagged.
        assert result.status == "FAILED"
        assert result.data == "plain forced answer"
        assert result.final_answer_forced is True
        assert result.iterations_used == 2
        assert len(orch.calls) == 3
        assert orch.calls[-1]["text"].endswith(rlm_mod._FORCE_FINAL_PROMPT)

    def test_forced_final_unwraps_final_declaration(self, uploads):
        orch = ScriptedModel(["thinking", "FINAL(forced)"])
        rlm = _recursive_rlm(orch, ExecSandbox(context_value="c"), max_iterations=1)

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.data == "forced"

    def test_spent_timeout_makes_no_orchestrator_call(self, uploads):
        # BUG-1453: a spent budget starts no orchestrator call, not even the
        # forced final one, and the result is flagged as timed out.
        orch = ScriptedModel(["forced"])
        rlm = _recursive_rlm(orch, ExecSandbox(context_value="c"))

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive", timeout=-1)

        assert result.status == "FAILED"
        assert result.timed_out is True
        assert result.data is None
        assert orch.calls == []

    def test_forced_final_pending_placeholder_stripped(self, uploads):
        orch = ScriptedModel([f"answer: {rlm_mod._LLM_PENDING_SENTINEL}"])
        rlm = _recursive_rlm(orch, ExecSandbox(context_value="c"), max_iterations=0)

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.data == "answer: [unanswered]"

    def test_final_with_pending_placeholder_rejected(self, uploads):
        orch = ScriptedModel([f"FINAL({rlm_mod._LLM_PENDING_SENTINEL})", "FINAL(real)"])
        rlm = _recursive_rlm(orch, ExecSandbox(context_value="c"))

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.data == "real"
        assert result.iterations_used == 2
        assert rlm_mod._PENDING_REJECTED_PROMPT in orch.calls[1]["text"]

    @pytest.mark.parametrize(
        "decl",
        ["FINAL_VAR(os.system('x'))", "FINAL_VAR(undefined_name)", "FINAL_VAR(pending)"],
    )
    def test_unusable_final_var_continues(self, uploads, decl):
        setup = _block(f"pending = {rlm_mod._LLM_PENDING_SENTINEL!r}")
        orch = ScriptedModel([setup, decl, "FINAL(fallback)"])
        rlm = _recursive_rlm(orch, ExecSandbox(context_value="c"))

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.data == "fallback"
        assert result.iterations_used == 3

    def test_final_var_quoted_name_and_redacted(self, uploads, monkeypatch):
        monkeypatch.setenv("TEAM_API_KEY", "env-secret-value-123")
        code = "import os\nleak = 'k=' + os.environ['TEAM_API_KEY']\nprint(leak)"
        orch = ScriptedModel([_block(code), "FINAL_VAR('leak')"])
        rlm = _recursive_rlm(orch, ExecSandbox(context_value="c"))

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.data == "k=***REDACTED***"
        assert result.repl_logs[0]["output"] == "k=***REDACTED***\n"
        assert "env-secret-value-123" not in orch.calls[-1]["text"]

    def test_block_referencing_credential_not_executed(self, uploads):
        orch = ScriptedModel([_block(f"key = '{API_KEY}'"), "FINAL(x)"])
        sandbox = ExecSandbox(context_value="c")
        rlm = _recursive_rlm(orch, sandbox)

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.repl_logs[0]["output"].startswith("[blocked]")
        assert all(API_KEY not in (code or "") for code in sandbox.codes())

    def test_orchestrator_failure_returns_failed_result_and_tears_down(self, uploads):
        orch = ScriptedModel([resp(status="FAILED", completed=False, error_message=f"bad key {API_KEY}")])
        sandbox = ExecSandbox(context_value="c")
        rlm = _recursive_rlm(orch, sandbox)

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.status == "FAILED"
        assert result.completed is True
        assert result.data is None
        assert result.iterations_used == 1
        assert result.error_message == "RLM run error: RLM: orchestrator model failed — bad key ***REDACTED***"
        assert sandbox.codes().count(rlm_mod._SESSION_WIPE_CODE) == 2
        assert rlm._repl_session_id is None and rlm._setup_session_id is None

    def test_setup_failure_still_tears_down_started_session(self, uploads):
        def handler(code):
            if code == rlm_mod._PREFLIGHT_CODE:
                return {"stdout": "3.11", "stderr": ""}
            raise RuntimeError("sandbox unavailable")

        sandbox = FakeSandbox(handler=handler)
        orch = ScriptedModel([])
        rlm = _recursive_rlm(orch, sandbox)

        result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.status == "FAILED"
        assert "sandbox unavailable" in result.error_message
        assert result.iterations_used == 0
        assert orch.calls == []
        # Both started sessions get a teardown attempt (the wipe raises -> swallowed).
        assert sandbox.codes()[-2:] == [rlm_mod._SESSION_WIPE_CODE, rlm_mod._SESSION_WIPE_CODE]


# ---------------------------------------------------------------------------
# _execute_code / llm_query resolution
# ---------------------------------------------------------------------------


class TestExecuteCode:
    def _started(self, handler):
        sandbox = FakeSandbox(handler=handler)
        rlm = make_rlm(make_context(models={"worker": FakeModel(responder=lambda t: f"A:{t}")}, sandbox=sandbox))
        rlm._repl_session_id = "repl-1"
        return rlm, sandbox

    def test_stdout_and_stderr_combined(self):
        rlm, _ = self._started(lambda code: {"stdout": "out", "stderr": "warn"})
        assert rlm._execute_code("x") == "out\n[stderr]: warn"

    def test_non_dict_data_is_no_output(self):
        rlm, _ = self._started(lambda code: "garbage")
        assert rlm._execute_code("x") == "No output"

    def test_truncation_keeps_protocol_note(self):
        limit = rlm_mod._REPL_OUTPUT_MAX_CHARS
        stdout = "y" * (limit + 50) + "\n" + rlm_mod._LLM_REQUEST_MARKER + json.dumps(["p"])
        rlm, _ = self._started(lambda code: {"stdout": stdout} if code == "x" else {})
        out = rlm._execute_code("x")
        assert out.startswith("y" * limit + "\n... [truncated — 50 chars omitted]")
        assert out.endswith("re-run that same block now to receive the real answers.")

    def test_malformed_marker_still_clears_pending(self):
        stdout = rlm_mod._LLM_REQUEST_MARKER + '["cut'
        rlm, sandbox = self._started(lambda code: {"stdout": stdout} if code == "x" else {})
        assert rlm._execute_code("x") == "No output"
        assert sandbox.codes()[-1] == "_llm_answers.update(__json.loads('{}'))\n_llm_query_pending.clear()"

    def test_resolve_llm_queries_dedups_and_reports_failures(self):
        def responder(text):
            if text == "bad":
                raise RuntimeError("nope")
            return f"A:{text}"

        worker = FakeModel(responder=responder)
        rlm = make_rlm(make_context(models={"worker": worker}))
        answers = rlm._resolve_llm_queries(["a", "a", "bad"])
        assert answers == {
            rlm_mod._prompt_key("a"): "A:a",
            rlm_mod._prompt_key("bad"): "Error: llm_query failed — nope",
        }
        assert len(worker.calls) == 2
        assert rlm._resolve_llm_queries([]) == {}

    def test_resolve_llm_queries_truncates_forwarded_prompt_but_keys_full(self, monkeypatch):
        monkeypatch.setattr(rlm_mod, "_LLM_MAX_PROMPT_CHARS", 3)
        worker = FakeModel(responder=lambda t: t)
        rlm = make_rlm(make_context(models={"worker": worker}))
        assert rlm._resolve_llm_queries(["abcdef"]) == {rlm_mod._prompt_key("abcdef"): "abc"}


# ---------------------------------------------------------------------------
# Sessions and teardown
# ---------------------------------------------------------------------------


class TestSessions:
    def test_session_id_for_unknown_and_unstarted(self):
        rlm = make_rlm()
        with pytest.raises(ValueError, match="unknown sandbox session"):
            rlm._session_id_for("other")
        with pytest.raises(ResourceError, match="has not been started"):
            rlm._session_id_for(rlm_mod._REPL_SESSION)

    def test_run_sandbox_refuses_secret_code(self):
        sandbox = FakeSandbox()
        rlm = make_rlm()
        rlm._setup_session_id = "s"
        with pytest.raises(ResourceError, match="BUG-936"):
            rlm._run_sandbox(sandbox, f"k = '{API_KEY}'", session=rlm_mod._SETUP_SESSION)
        assert sandbox.calls == []

    @pytest.mark.parametrize(
        "actions,expected",
        [
            (["run", "closeSession", "close"], "closeSession"),
            (["run", "close"], "close"),
            (["run"], None),
            ([], None),
            (RuntimeError("no list"), None),
        ],
    )
    def test_teardown_action_lookup(self, actions, expected):
        sandbox = FakeSandbox(actions=actions)
        rlm = make_rlm()
        assert rlm._teardown_action(sandbox) == expected

    def test_teardown_action_matches_slug_or_code_and_is_cached(self):
        sandbox = MagicMock()
        sandbox.list_actions.return_value = [SimpleNamespace(name=None, slug="delete_session", code=1)]
        rlm = make_rlm()
        assert rlm._teardown_action(sandbox) == "delete_session"
        assert rlm._teardown_action(sandbox) == "delete_session"
        sandbox.list_actions.assert_called_once()

    def test_close_uses_close_action(self):
        sandbox = FakeSandbox(actions=["close_session"])
        rlm = make_rlm()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id, rlm._setup_session_id = "r", "s"

        rlm.close()

        assert sandbox.calls == [
            {"data": {"sessionId": "r"}, "action": "close_session"},
            {"data": {"sessionId": "s"}, "action": "close_session"},
        ]
        assert rlm._repl_session_id is None and rlm._setup_session_id is None
        rlm.close()  # idempotent
        assert len(sandbox.calls) == 2

    def test_failing_close_action_falls_back_to_wipe(self):
        sandbox = MagicMock()
        sandbox.list_actions.return_value = [SimpleNamespace(name="close")]

        def run(data, action):
            if action == "close":
                raise RuntimeError("rejected")
            return None

        sandbox.run.side_effect = run
        rlm = make_rlm()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "r"

        rlm.close()

        actions = [c.kwargs["action"] for c in sandbox.run.call_args_list]
        assert actions == ["close", "run"]
        assert sandbox.run.call_args.kwargs["data"] == {"code": rlm_mod._SESSION_WIPE_CODE, "sessionId": "r"}

    def test_close_never_raises(self):
        sandbox = MagicMock()
        sandbox.list_actions.return_value = []
        sandbox.run.side_effect = RuntimeError("down")
        rlm = make_rlm()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "r"
        rlm.close()
        assert rlm._repl_session_id is None

    def test_close_without_sandbox_is_noop(self):
        rlm = make_rlm()
        rlm._repl_session_id = "r"
        rlm.close()
        assert rlm._repl_session_id is None

    def test_context_manager_closes_on_success(self):
        sandbox = FakeSandbox(actions=["close_session"])
        rlm = make_rlm()
        with rlm as entered:
            assert entered is rlm
            rlm._sandbox_tool = sandbox
            rlm._repl_session_id = "r"
        assert sandbox.calls == [{"data": {"sessionId": "r"}, "action": "close_session"}]

    def test_context_manager_closes_on_failure(self):
        sandbox = FakeSandbox(actions=["close_session"])
        rlm = make_rlm()
        with pytest.raises(RuntimeError, match="inside"):
            with rlm:
                rlm._sandbox_tool = sandbox
                rlm._setup_session_id = "s"
                raise RuntimeError("inside")
        assert sandbox.calls == [{"data": {"sessionId": "s"}, "action": "close_session"}]
        assert rlm._setup_session_id is None

    def test_recursive_run_uses_close_action_when_available(self, uploads):
        orch = ScriptedModel(["FINAL(ok)"])
        sandbox = ExecSandbox(context_value="c", actions=["close_session"])
        rlm = _recursive_rlm(orch, sandbox)

        with rlm:
            result = rlm.run(data={"context": "c", "query": "Q"}, mode="recursive")

        assert result.data == "ok"
        assert [c["action"] for c in sandbox.calls][-2:] == ["close_session", "close_session"]
        assert rlm_mod._SESSION_WIPE_CODE not in sandbox.codes()
