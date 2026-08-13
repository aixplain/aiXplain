"""Unit tests for RLM context resolution, sandbox setup, credit tracking, and context window.

The v2 suite additionally covers BUG-936: no credential may reach the sandbox,
model-emitted code must run in its own session, and sessions must be torn down.
"""

import ast
import contextlib
import inspect
import io
import json
import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import aixplain.v2.rlm as rlm_v2
from aixplain.v1.modules.model.rlm import RLM as RLMV1
from aixplain.v2.rlm import (
    RLM as RLMV2,
    RLMResult,
    _LLM_PENDING_SENTINEL,
    _LLM_REQUEST_MARKER,
    _REPL_SESSION,
    _SETUP_SESSION,
    _extract_llm_requests,
    _prompt_key,
)


# Parametrize over both implementations
RLM_IMPLS = [
    pytest.param(RLMV1, id="v1"),
    pytest.param(RLMV2, id="v2"),
]


# _resolve_context
class TestResolveContext:
    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_local_text_file(self, RLM, tmp_path):
        p = tmp_path / "doc.txt"
        p.write_text("file content", encoding="utf-8")
        assert RLM._resolve_context(str(p)) == "file content"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_local_json_file(self, RLM, tmp_path):
        data = {"a": 1}
        p = tmp_path / "data.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        assert RLM._resolve_context(str(p)) == data

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_pathlib_path(self, RLM, tmp_path):
        p = tmp_path / "doc.txt"
        p.write_text("pathlib content", encoding="utf-8")
        assert RLM._resolve_context(p) == "pathlib content"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_raw_string(self, RLM):
        assert RLM._resolve_context("just raw text") == "just raw text"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_dict_passthrough(self, RLM):
        d = {"x": 1}
        assert RLM._resolve_context(d) is d

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_list_passthrough(self, RLM):
        lst = [1, 2, 3]
        assert RLM._resolve_context(lst) is lst

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_non_string_fallback(self, RLM):
        assert RLM._resolve_context(42) == "42"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_http_url_passes_through_unchanged(self, RLM):
        url = "http://example.com/doc.txt"
        assert RLM._resolve_context(url) == url

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_https_url_passes_through_unchanged(self, RLM):
        url = "https://example.com/data.json"
        assert RLM._resolve_context(url) == url


# _setup_repl — URL branch
def _make_v1_rlm() -> RLMV1:
    """Minimal v1 RLM with stubbed models."""
    rlm = RLMV1.__new__(RLMV1)
    rlm.api_key = "test-key"
    rlm.orchestrator = MagicMock()
    rlm.worker = MagicMock()
    rlm.worker.url = "https://models.aixplain.com/api/v2/execute"
    rlm.worker.id = "worker-id"
    rlm.worker.additional_info = {}
    rlm._session_id = None
    rlm._sandbox_tool = None
    rlm._messages = []
    rlm._used_credits = 0.0
    return rlm


def _make_v2_rlm(api_key: str = "test-key", max_iterations: int = 10) -> RLMV2:
    """Minimal v2 RLM with stubbed context client."""
    rlm = RLMV2.__new__(RLMV2)
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
    client = MagicMock()
    client.backend_url = "https://platform-api.aixplain.com"
    client.api_key = api_key
    client.model_url = "https://models.aixplain.com/api/v2/execute"
    rlm.context = client
    return rlm


class TestSetupReplURLPath:
    def test_v1_url_skips_file_factory(self):
        rlm = _make_v1_rlm()
        sandbox_mock = MagicMock()

        with (
            patch("aixplain.factories.tool_factory.ToolFactory") as mock_tf,
            patch("aixplain.factories.file_factory.FileFactory") as mock_ff,
        ):
            mock_tf.get.return_value = sandbox_mock
            rlm._setup_repl("https://example.com/doc.txt")

        mock_ff.create.assert_not_called()

    def test_v1_url_sandbox_code_contains_url(self):
        rlm = _make_v1_rlm()
        sandbox_mock = MagicMock()
        captured = []

        def capture_run(inputs, action):
            captured.append(inputs["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run

        with patch("aixplain.factories.tool_factory.ToolFactory") as mock_tf:
            mock_tf.get.return_value = sandbox_mock
            rlm._setup_repl("https://example.com/doc.txt")

        context_code = captured[0]
        assert "https://example.com/doc.txt" in context_code
        assert "_content_type" in context_code
        assert "_is_json" in context_code
        assert "__json.load" in context_code

    def test_v2_url_skips_file_uploader(self):
        rlm = _make_v2_rlm()
        sandbox_mock = MagicMock()
        rlm._sandbox_tool = sandbox_mock

        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            rlm._setup_repl("https://example.com/doc.txt")

        mock_uploader.assert_not_called()

    def test_v2_url_sandbox_code_contains_url(self):
        rlm = _make_v2_rlm()
        sandbox_mock = MagicMock()
        rlm._sandbox_tool = sandbox_mock
        captured = []

        def capture_run(data, action):
            captured.append(data["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run

        rlm._setup_repl("https://example.com/doc.txt")

        context_code = captured[0]
        assert "https://example.com/doc.txt" in context_code
        assert "_content_type" in context_code
        assert "_is_json" in context_code
        assert "__json.load" in context_code


# Credit tracking
def _sandbox_result(stdout="", stderr="", used_credits=0.0):
    """Create a mock sandbox result."""
    r = MagicMock()
    r.data = {"stdout": stdout, "stderr": stderr}
    r.used_credits = used_credits
    return r


def _model_response_v1(data="response text", used_credits=0.0, completed=True, status="SUCCESS"):
    """Create a mock v1 model response."""
    r = MagicMock()
    r.data = data
    r.used_credits = used_credits
    r.get = lambda k, default=None: {"completed": completed, "data": data, "status": status, "error_message": ""}.get(
        k, default
    )
    r.__getitem__ = lambda self_, k: {"completed": completed, "data": data, "status": status}.get(k)
    return r


class TestV1CreditTracking:
    def test_orchestrator_credits_accumulated(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm.orchestrator.run.return_value = _model_response_v1(used_credits=0.05)

        rlm._orchestrator_completion([{"role": "user", "content": "test"}])

        assert rlm._used_credits == pytest.approx(0.05)

    def test_sandbox_credits_accumulated(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm._sandbox_tool = MagicMock()
        rlm._sandbox_tool.run.return_value = _sandbox_result(used_credits=0.01)
        rlm._session_id = "test-session"

        rlm._run_sandbox("print('hello')")

        assert rlm._used_credits == pytest.approx(0.01)

    def test_execute_code_credits_accumulated(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm._sandbox_tool = MagicMock()
        rlm._sandbox_tool.run.return_value = _sandbox_result(stdout="done", used_credits=0.02)
        rlm._session_id = "test-session"

        output = rlm._execute_code("x = 1\nprint('done')")

        assert "done" in output
        assert rlm._used_credits == pytest.approx(0.02)

    def test_collect_llm_query_credits(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 1.0
        rlm._sandbox_tool = MagicMock()
        rlm._session_id = "test-session"
        rlm._sandbox_tool.run.return_value = _sandbox_result(stdout="0.35", used_credits=0.0)

        rlm._collect_llm_query_credits()

        assert rlm._used_credits == pytest.approx(1.35)

    def test_multiple_calls_accumulate(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm._session_id = "test-session"
        rlm._sandbox_tool = MagicMock()

        rlm.orchestrator.run.return_value = _model_response_v1(used_credits=0.1)
        rlm._orchestrator_completion([{"role": "user", "content": "a"}])
        rlm._orchestrator_completion([{"role": "user", "content": "b"}])

        rlm._sandbox_tool.run.return_value = _sandbox_result(stdout="ok", used_credits=0.05)
        rlm._execute_code("pass")
        rlm._execute_code("pass")

        assert rlm._used_credits == pytest.approx(0.3)


class TestV2CreditTracking:
    def test_orchestrator_credits_accumulated(self):
        rlm = _make_v2_rlm()
        rlm._used_credits = 0.0
        mock_model = MagicMock()
        resp = MagicMock()
        resp.completed = True
        resp.status = "SUCCESS"
        resp.data = "answer"
        resp.used_credits = 0.07
        mock_model.run.return_value = resp
        rlm._orchestrator = mock_model

        rlm._orchestrator_completion([{"role": "user", "content": "test"}])

        assert rlm._used_credits == pytest.approx(0.07)

    def test_sandbox_credits_accumulated(self):
        rlm = _make_v2_rlm()
        rlm._used_credits = 0.0
        sandbox = MagicMock()
        sandbox.run.return_value = _sandbox_result(used_credits=0.03)
        rlm._repl_session_id = "test-session"

        rlm._run_sandbox(sandbox, "print('hi')", session=_REPL_SESSION)

        assert rlm._used_credits == pytest.approx(0.03)

    def test_execute_code_credits_accumulated(self):
        rlm = _make_v2_rlm()
        rlm._used_credits = 0.0
        sandbox = MagicMock()
        sandbox.run.return_value = _sandbox_result(stdout="done", used_credits=0.04)
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "test-session"

        output = rlm._execute_code("print('done')")

        assert "done" in output
        assert rlm._used_credits == pytest.approx(0.04)

    def test_llm_query_credits_accumulated_via_worker_call(self):
        """Worker credits now come from SDK-side calls, not a sandbox variable.

        Replaces the old ``_collect_llm_query_credits`` test: the sandbox no
        longer tracks (or can tamper with) worker spend.
        """
        rlm = _make_v2_rlm()
        rlm._used_credits = 2.0
        assert not hasattr(rlm, "_collect_llm_query_credits")

        worker = MagicMock()
        worker.attributes = {}
        resp = MagicMock(completed=True, status="SUCCESS", data="answer", used_credits=0.25)
        worker.run.return_value = resp
        rlm._worker = worker

        answers = rlm._resolve_llm_queries(["a", "b"])

        assert len(answers) == 2
        assert rlm._used_credits == pytest.approx(2.50)

    def test_used_credits_field_on_rlm_result(self):
        result = RLMResult(status="SUCCESS", completed=True, data="answer")
        result.used_credits = 1.23
        result.iterations_used = 5

        assert result.used_credits == pytest.approx(1.23)
        serialized = result.to_dict()
        assert serialized["usedCredits"] == pytest.approx(1.23)


class TestLlmQueryCodeCreditsTracking:
    def test_v1_llm_query_code_accumulates_credits(self):
        rlm = _make_v1_rlm()
        sandbox_mock = MagicMock()
        captured = []

        def capture_run(inputs, action):
            captured.append(inputs["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run

        with (
            patch("aixplain.factories.tool_factory.ToolFactory") as mock_tf,
            patch("aixplain.factories.file_factory.FileFactory") as mock_ff,
        ):
            mock_tf.get.return_value = sandbox_mock
            mock_ff.create.return_value = "https://storage.example.com/ctx.txt"
            rlm._setup_repl("raw text context")

        llm_query_code = captured[-1]
        assert "_total_llm_query_credits" in llm_query_code
        assert "global _total_llm_query_credits" in llm_query_code
        assert "usedCredits" in llm_query_code

    def test_v2_llm_query_prelude_is_credential_free(self):
        """v2's prelude makes no network call and tracks no credits (BUG-936)."""
        rlm = _make_v2_rlm(api_key="SENTINEL-KEY-DO-NOT-LEAK")
        sandbox_mock = MagicMock()
        captured = []

        def capture_run(data, action):
            captured.append(data["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run
        rlm._sandbox_tool = sandbox_mock

        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            uploader_instance = MagicMock()
            uploader_instance.upload.return_value = "https://storage.example.com/ctx.txt"
            mock_uploader.return_value = uploader_instance
            rlm._setup_repl("raw text context")

        prelude = captured[-1]
        assert "def llm_query(" in prelude
        assert "SENTINEL-KEY-DO-NOT-LEAK" not in prelude
        assert "x-api-key" not in prelude
        assert "requests" not in prelude
        assert "_total_llm_query_credits" not in prelude
        assert _LLM_REQUEST_MARKER in prelude


# Worker context window
class TestV1WorkerContextWindow:
    def test_returns_formatted_k_tokens(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "128000"}]}
        assert rlm._get_worker_context_window() == "128K tokens"

    def test_returns_formatted_m_tokens(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "1048576"}]}
        assert rlm._get_worker_context_window() == "1.0M tokens"

    def test_returns_small_token_count(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "512"}]}
        assert rlm._get_worker_context_window() == "512 tokens"

    def test_fallback_when_no_attributes(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {}
        assert rlm._get_worker_context_window() == "a large context window"

    def test_fallback_when_attribute_missing(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "other_attr", "code": "100"}]}
        assert rlm._get_worker_context_window() == "a large context window"

    def test_non_numeric_returns_raw_string(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "unlimited"}]}
        assert rlm._get_worker_context_window() == "unlimited"


class TestV2WorkerContextWindow:
    def test_returns_formatted_k_tokens(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": "200000"}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "200K tokens"

    def test_returns_formatted_m_tokens(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": "2000000"}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "2.0M tokens"

    def test_fallback_when_no_attributes(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "a large context window"

    def test_fallback_when_attributes_none(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = None
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "a large context window"

    def test_non_numeric_returns_raw_string(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": "very_large"}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "very_large"

    def test_integer_attribute_value(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": 32000}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "32K tokens"


# BUG-936 — v2 sandbox credential isolation, session split, and teardown

SENTINEL_KEY = "SENTINEL-KEY-DO-NOT-LEAK-8f3c1a"
FAKE_CONTEXT = "alpha beta gamma delta"


class _FakeSandbox:
    """Sandbox double that really ``exec()``s payloads, one namespace per session.

    Executing for real is the point: a ``co_consts`` probe runs against the
    actual generated prelude, and separate namespaces mean the session split is
    exercised rather than merely asserted on call arguments.

    The only faked step is the context bootstrap, which would otherwise make a
    live HTTP request — ``context`` is assigned ``context_value`` instead.
    """

    def __init__(self, context_value: str = FAKE_CONTEXT, close_action: str = "close_session"):
        self.context_value = context_value
        self.close_action = close_action
        self.namespaces: dict = {}
        self.calls: list = []  # {"session", "action", "code"}
        self.closed: list = []
        self.close_raises = False

    def list_actions(self):
        actions = [SimpleNamespace(name="run")]
        if self.close_action:
            actions.append(SimpleNamespace(name=self.close_action))
        return actions

    @property
    def codes(self) -> list:
        return [c["code"] for c in self.calls if c["code"] is not None]

    def codes_for(self, session_id) -> list:
        return [c["code"] for c in self.calls if c["session"] == session_id and c["code"] is not None]

    def run(self, data=None, action="run"):
        data = data or {}
        session_id = data.get("sessionId")
        code = data.get("code")
        self.calls.append({"session": session_id, "action": action, "code": code})

        if action != "run":
            if self.close_raises:
                raise RuntimeError("close failed")
            self.closed.append(session_id)
            self.namespaces.pop(session_id, None)
            return MagicMock(used_credits=0.0, data={})

        ns = self.namespaces.setdefault(session_id, {})
        buf = io.StringIO()
        err = ""
        if "__requests.get(_url" in (code or ""):
            # Context bootstrap — don't hit the network.
            ns["context"] = self.context_value
        else:
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code, ns, ns)
            except Exception as exc:  # noqa: BLE001 - mirrors the real sandbox
                err = f"{type(exc).__name__}: {exc}"
        return MagicMock(used_credits=0.0, data={"stdout": buf.getvalue(), "stderr": err})


def _worker_response(data="worker answer", used_credits=0.0):
    return MagicMock(completed=True, status="SUCCESS", data=data, used_credits=used_credits)


def _drive_recursive(rlm, sandbox, responses, query="what is in here?", max_iterations=None):
    """Run ``_run_recursive`` against a fake sandbox and scripted orchestrator turns.

    ``responses`` is a list of orchestrator reply strings (or exceptions to
    raise). Anything past the end repeats the last entry.
    """
    rlm._sandbox_tool = sandbox
    if max_iterations is not None:
        rlm.max_iterations = max_iterations

    worker = MagicMock()
    worker.attributes = {"max_context_length": "128000"}
    worker.run.return_value = _worker_response()
    rlm._worker = worker

    turns = list(responses)

    def _completion(messages):
        reply = turns.pop(0) if len(turns) > 1 else turns[0]
        if isinstance(reply, BaseException):
            raise reply
        return reply

    with patch.object(type(rlm), "_orchestrator_completion", side_effect=_completion, autospec=False):
        return rlm._run_recursive(FAKE_CONTEXT, query, "test", time.time(), 600.0)


class TestNoCredentialInSandbox:
    """AC 1 — the key must not appear in anything sent to the sandbox."""

    def test_no_api_key_in_any_sandbox_payload(self):
        rlm = _make_v2_rlm(api_key=SENTINEL_KEY)
        sandbox = _FakeSandbox()

        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(rlm, sandbox, ["FINAL(all done)"])

        assert result.status == "SUCCESS"
        assert sandbox.calls, "expected the run to touch the sandbox"
        for code in sandbox.codes:
            assert SENTINEL_KEY not in code
            assert "x-api-key" not in code

    def test_module_source_never_interpolates_a_key_into_generated_code(self):
        """Static tripwire: fails if a credential is reintroduced into generated code."""
        tree = ast.parse(inspect.getsource(rlm_v2))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                for value in node.values:
                    if isinstance(value, ast.FormattedValue):
                        expr = ast.unparse(value.value)
                        if "api_key" in expr.lower():
                            offenders.append(expr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "x-api-key" in node.value:
                    offenders.append(node.value[:120])
        assert offenders == [], f"credential reached generated code: {offenders}"

    def test_run_sandbox_refuses_sdk_code_containing_a_secret(self):
        """AC 5 — the tripwire raises rather than transmitting a credential."""
        rlm = _make_v2_rlm(api_key=SENTINEL_KEY)
        sandbox = _FakeSandbox()
        rlm._repl_session_id = "repl-1"

        with pytest.raises(rlm_v2.ResourceError, match="BUG-936"):
            rlm._run_sandbox(sandbox, f'headers = {{"x-api-key": "{SENTINEL_KEY}"}}', session=_REPL_SESSION)

        assert sandbox.calls == []

    def test_emitted_code_containing_secret_is_blocked_not_fatal(self):
        rlm = _make_v2_rlm(api_key=SENTINEL_KEY)
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"

        output = rlm._execute_code(f"print({SENTINEL_KEY!r})")

        assert "[blocked]" in output
        assert SENTINEL_KEY not in output
        assert sandbox.calls == []

    def test_secret_values_ignores_non_string_and_short_values(self):
        rlm = _make_v2_rlm(api_key="short")
        with patch.dict("os.environ", {}, clear=True):
            assert rlm._secret_values() == ()
            assert rlm._contains_secret("short") is False

        rlm.context.api_key = object()
        with patch.dict("os.environ", {}, clear=True):
            assert rlm._secret_values() == ()

    def test_env_sourced_key_is_also_guarded(self):
        rlm = _make_v2_rlm(api_key="test-key-that-is-long")
        with patch.dict("os.environ", {"TEAM_API_KEY": SENTINEL_KEY}, clear=True):
            assert SENTINEL_KEY in rlm._secret_values()
            assert rlm._contains_secret(f"k = {SENTINEL_KEY}") is True


class TestSandboxCannotRecoverKey:
    """AC 2 — probing from inside the sandbox yields nothing."""

    def _probe(self, probe_code):
        rlm = _make_v2_rlm(api_key=SENTINEL_KEY)
        sandbox = _FakeSandbox()
        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(
                rlm,
                sandbox,
                [f"Let me look.\n```repl\n{probe_code}\n```", "FINAL(nothing found)"],
            )
        return rlm, sandbox, result

    def test_co_consts_probe_cannot_recover_key(self):
        rlm, sandbox, result = self._probe(
            "import json\nprint(llm_query.__code__.co_consts)\nprint(sorted(llm_query.__globals__))"
        )

        assert result.status == "SUCCESS"
        assert result.repl_logs, "probe block should have executed"
        probe_output = result.repl_logs[0]["output"]
        # The probe really ran against the real prelude: its only constants are
        # the docstring and the pending placeholder.
        assert _LLM_PENDING_SENTINEL in probe_output
        assert "llm_query" in probe_output
        assert SENTINEL_KEY not in probe_output
        assert "x-api-key" not in probe_output
        assert "models.aixplain.com" not in probe_output
        assert SENTINEL_KEY not in json.dumps(result.repl_logs)
        assert SENTINEL_KEY not in json.dumps(rlm._messages)
        assert SENTINEL_KEY not in str(result.data)

    def test_getsource_and_environ_probe_cannot_recover_key(self):
        rlm, sandbox, result = self._probe(
            "import inspect, os\n"
            "print(inspect.getsource(llm_query))\n"
            "print({k: v for k, v in os.environ.items() if 'KEY' in k.upper()})"
        )

        assert SENTINEL_KEY not in json.dumps(result.repl_logs)
        assert SENTINEL_KEY not in json.dumps(rlm._messages)

    def test_secret_echoed_by_emitted_code_is_redacted(self):
        """Reverse channel: a printed credential must not enter the transcript."""
        rlm = _make_v2_rlm(api_key=SENTINEL_KEY)
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        sandbox.namespaces["repl-1"] = {"leaked": SENTINEL_KEY}

        output = rlm._execute_code("print(leaked)")

        assert SENTINEL_KEY not in output
        assert "***REDACTED***" in output

    def test_failure_message_is_redacted(self):
        """A client exception quoting the key must not land in the result."""
        rlm = _make_v2_rlm(api_key=SENTINEL_KEY)
        sandbox = _FakeSandbox()

        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(
                rlm,
                sandbox,
                [RuntimeError(f"POST failed, headers={{'x-api-key': '{SENTINEL_KEY}'}}")],
            )

        assert result.status == "FAILED"
        assert SENTINEL_KEY not in result.error_message
        assert "***REDACTED***" in result.error_message


class TestSessionSplit:
    """AC 3 — model-emitted code never shares a session with SDK setup code."""

    def _run(self):
        rlm = _make_v2_rlm(api_key=SENTINEL_KEY)
        sandbox = _FakeSandbox()
        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(
                rlm,
                sandbox,
                ["```repl\nprint(len(context))\n```", "FINAL(done)"],
            )
        return rlm, sandbox, result

    def test_setup_and_repl_sessions_are_distinct(self):
        rlm, sandbox, result = self._run()
        sessions = {c["session"] for c in sandbox.calls}

        assert len(sessions) == 2
        assert None not in sessions

    def test_emitted_code_runs_only_in_the_repl_session(self):
        rlm, sandbox, result = self._run()

        setup_calls = [c for c in sandbox.calls if c["code"] == rlm_v2._PREFLIGHT_CODE]
        assert setup_calls, "preflight should have run"
        setup_session = setup_calls[0]["session"]

        emitted = [c for c in sandbox.calls if c["code"] and "print(len(context))" in c["code"]]
        assert emitted, "emitted block should have run"
        for call in emitted:
            assert call["session"] != setup_session

        # The prelude and the context bootstrap share the REPL session by design.
        prelude_calls = [c for c in sandbox.calls if c["code"] and "def llm_query(" in c["code"]]
        assert prelude_calls
        assert prelude_calls[0]["session"] == emitted[0]["session"]

    def test_setup_session_state_is_unreachable_from_repl_session(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._setup_session_id = "setup-1"
        rlm._repl_session_id = "repl-1"

        rlm._run_sandbox(sandbox, "setup_only_secret = 'xyz'", session=_SETUP_SESSION)
        output = rlm._execute_code("print(setup_only_secret)")

        assert "NameError" in output
        assert "xyz" not in output

    def test_run_sandbox_requires_an_explicit_session(self):
        rlm = _make_v2_rlm()
        with pytest.raises(TypeError):
            rlm._run_sandbox(_FakeSandbox(), "pass")

    def test_run_sandbox_rejects_unstarted_session(self):
        rlm = _make_v2_rlm()
        with pytest.raises(rlm_v2.ResourceError, match="has not been started"):
            rlm._run_sandbox(_FakeSandbox(), "pass", session=_REPL_SESSION)

    def test_run_sandbox_rejects_unknown_session_name(self):
        rlm = _make_v2_rlm()
        with pytest.raises(ValueError, match="unknown sandbox session"):
            rlm._run_sandbox(_FakeSandbox(), "pass", session="nope")


class TestSessionTeardown:
    """AC 4 — sessions are closed on every exit path."""

    def _run(self, responses, sandbox=None):
        rlm = _make_v2_rlm()
        sandbox = sandbox or _FakeSandbox()
        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(rlm, sandbox, responses)
        return rlm, sandbox, result

    def test_sessions_closed_on_success(self):
        rlm, sandbox, result = self._run(["FINAL(done)"])

        assert result.status == "SUCCESS"
        assert len(sandbox.closed) == 2
        assert all(c["action"] == "close_session" for c in sandbox.calls if c["action"] != "run")
        assert rlm._setup_session_id is None
        assert rlm._repl_session_id is None

    def test_sessions_closed_on_exception(self):
        rlm, sandbox, result = self._run([RuntimeError("orchestrator exploded")])

        assert result.status == "FAILED"
        assert "orchestrator exploded" in result.error_message
        assert len(sandbox.closed) == 2

    def test_session_closed_when_setup_fails(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        worker = MagicMock()
        worker.attributes = {}
        rlm._worker = worker

        with patch("aixplain.v2.rlm.FileUploader", side_effect=RuntimeError("upload down")):
            result = rlm._run_recursive(FAKE_CONTEXT, "q", "test", time.time(), 600.0)

        assert result.status == "FAILED"
        assert "upload down" in result.error_message
        # Setup blew up between starting the sessions and loading the context;
        # every session that had been started is still torn down.
        assert len(sandbox.closed) == 2
        assert rlm._setup_session_id is None
        assert rlm._repl_session_id is None

    def test_teardown_failure_does_not_mask_result(self):
        sandbox = _FakeSandbox()
        sandbox.close_raises = True
        rlm, sandbox, result = self._run(["FINAL(done)"], sandbox=sandbox)

        assert result.status == "SUCCESS"
        assert result.data == "done"
        assert sandbox.closed == []

    def test_failed_close_action_still_wipes_the_session(self):
        """A rejected close action must not leave the uploaded context behind."""
        sandbox = _FakeSandbox()
        sandbox.close_raises = True
        rlm, sandbox, result = self._run(["FINAL(done)"], sandbox=sandbox)

        wipes = [c for c in sandbox.calls if c["code"] and "_aix_gc.collect()" in c["code"]]
        assert len(wipes) == 2
        assert {c["session"] for c in wipes} == set(sandbox.namespaces)
        for session in sandbox.namespaces.values():
            assert "context" not in session

    def test_teardown_falls_back_to_wipe_without_a_close_action(self):
        sandbox = _FakeSandbox(close_action="")
        rlm, sandbox, result = self._run(["FINAL(done)"], sandbox=sandbox)

        assert result.status == "SUCCESS"
        wipes = [c for c in sandbox.calls if c["code"] and "_aix_gc.collect()" in c["code"]]
        assert len(wipes) == 2

    def test_close_is_idempotent_and_safe_without_a_sandbox(self):
        rlm = _make_v2_rlm()
        rlm.close()  # no sandbox resolved at all

        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        rlm.close()
        rlm.close()

        assert sandbox.closed == ["repl-1"]

    def test_context_manager_closes_sessions(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        with rlm as ctx:
            assert ctx is rlm
            rlm._repl_session_id = "repl-1"

        assert sandbox.closed == ["repl-1"]


class TestLlmQueryProtocol:
    """The SDK-mediated request/answer protocol replacing in-sandbox HTTP."""

    def test_extract_llm_requests_strips_markers_and_keeps_output(self):
        stdout = f"hello\n{_LLM_REQUEST_MARKER}{json.dumps(['a', 'b'])}\nworld"
        clean, prompts = _extract_llm_requests(stdout)

        assert prompts == ["a", "b"]
        assert _LLM_REQUEST_MARKER not in clean
        assert clean == "hello\nworld"

    def test_extract_llm_requests_ignores_malformed_payloads(self):
        clean, prompts = _extract_llm_requests(f"x\n{_LLM_REQUEST_MARKER}not json\ny")

        assert prompts == []
        assert clean == "x\ny"

    def test_extract_llm_requests_keeps_same_line_prefix(self):
        clean, prompts = _extract_llm_requests(f"tail{_LLM_REQUEST_MARKER}{json.dumps(['p'])}")

        assert prompts == ["p"]
        assert clean == "tail"

    def test_pending_then_resolved_across_two_turns(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        sandbox.namespaces["repl-1"] = {}
        rlm._run_sandbox(sandbox, rlm_v2._LLM_QUERY_PRELUDE, session=_REPL_SESSION)

        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response("REAL ANSWER")
        rlm._worker = worker

        block = "a = llm_query('summarize chunk 1')\nprint(a)"

        first = rlm._execute_code(block)
        assert _LLM_PENDING_SENTINEL in first
        assert "1 llm_query answer(s) are now cached" in first
        assert worker.run.call_count == 1
        assert _LLM_REQUEST_MARKER not in first

        second = rlm._execute_code(block)
        assert "REAL ANSWER" in second
        assert _LLM_PENDING_SENTINEL not in second
        # Answer was cached — no second worker call.
        assert worker.run.call_count == 1

    def test_batch_is_deduplicated_by_prompt_hash(self):
        rlm = _make_v2_rlm()
        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response()
        rlm._worker = worker

        answers = rlm._resolve_llm_queries(["a", "b", "a", "c", "b"])

        assert len(answers) == 3
        assert worker.run.call_count == 3
        assert set(answers) == {_prompt_key(p) for p in ("a", "b", "c")}

    def test_resolve_keys_on_full_prompt_but_truncates_worker_input(self):
        rlm = _make_v2_rlm()
        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response()
        rlm._worker = worker
        long_prompt = "x" * (rlm_v2._LLM_MAX_PROMPT_CHARS + 500)

        answers = rlm._resolve_llm_queries([long_prompt])

        assert list(answers) == [_prompt_key(long_prompt)]
        sent = worker.run.call_args.kwargs["text"]
        assert len(sent) == rlm_v2._LLM_MAX_PROMPT_CHARS

    def test_worker_output_budget_matches_the_old_in_sandbox_call(self):
        rlm = _make_v2_rlm()
        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response()
        rlm._worker = worker

        rlm._resolve_llm_queries(["a"])

        assert worker.run.call_args.kwargs["max_tokens"] == 8192

    def test_worker_failure_becomes_an_error_answer_not_a_crash(self):
        rlm = _make_v2_rlm()
        worker = MagicMock()
        worker.attributes = {}
        worker.run.side_effect = RuntimeError("worker down")
        rlm._worker = worker

        answers = rlm._resolve_llm_queries(["a"])

        assert "Error: llm_query failed" in answers[_prompt_key("a")]

    def test_answers_with_quotes_and_backslashes_round_trip_safely(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        rlm._run_sandbox(sandbox, rlm_v2._LLM_QUERY_PRELUDE, session=_REPL_SESSION)

        nasty = "he said \"\"\"hi\"\"\"\\n');import os;os.system('x')\n\ttab"
        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response(nasty)
        rlm._worker = worker

        block = "print(repr(llm_query('q')))"
        rlm._execute_code(block)
        second = rlm._execute_code(block)

        assert repr(nasty) in second
        ns = sandbox.namespaces["repl-1"]
        assert ns["_llm_answers"][_prompt_key("q")] == nasty
        assert "os" not in ns  # the injected payload never executed

    def test_request_marker_never_reaches_the_transcript(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(
                rlm,
                sandbox,
                ["```repl\nprint(llm_query('what is this?'))\n```", "FINAL(done)"],
            )

        assert result.status == "SUCCESS"
        assert _LLM_REQUEST_MARKER not in json.dumps(result.repl_logs)
        assert _LLM_REQUEST_MARKER not in json.dumps(rlm._messages)

    def test_pending_prompts_resubmit_after_answers_are_injected(self):
        """Pending state clears on injection so unanswered prompts can retry."""
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        rlm._run_sandbox(sandbox, rlm_v2._LLM_QUERY_PRELUDE, session=_REPL_SESSION)

        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response()
        rlm._worker = worker

        rlm._execute_code("llm_query('p1')")
        assert sandbox.namespaces["repl-1"]["_llm_query_pending"] == []

    def test_truncated_request_payload_does_not_strand_the_prompt(self):
        """A batch line cut mid-JSON must not suppress the prompt forever.

        The sandbox only prints a prompt while it is not already pending, so
        pending state has to be cleared even when nothing could be parsed —
        otherwise ``llm_query`` returns PENDING for the rest of the run.
        """
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        rlm._run_sandbox(sandbox, rlm_v2._LLM_QUERY_PRELUDE, session=_REPL_SESSION)

        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response("REAL ANSWER")
        rlm._worker = worker

        real_run = sandbox.run
        corrupt_next = {"on": True}

        def truncating_run(data=None, action="run"):
            result = real_run(data=data, action=action)
            inner = result.data if isinstance(result.data, dict) else {}
            if corrupt_next["on"] and _LLM_REQUEST_MARKER in inner.get("stdout", ""):
                corrupt_next["on"] = False
                # Cut the batch line mid-JSON, as an output cap would.
                lines = [ln[:-4] if _LLM_REQUEST_MARKER in ln else ln for ln in inner["stdout"].split("\n")]
                result.data = {**inner, "stdout": "\n".join(lines)}
            return result

        sandbox.run = truncating_run
        block = "print(llm_query('summarize'))"

        first = rlm._execute_code(block)
        assert _LLM_PENDING_SENTINEL in first
        assert worker.run.call_count == 0  # nothing was recoverable
        assert sandbox.namespaces["repl-1"]["_llm_query_pending"] == []

        rlm._execute_code(block)  # same block re-runs and resubmits
        assert worker.run.call_count == 1
        assert "REAL ANSWER" in rlm._execute_code(block)

    def test_answer_ready_note_survives_a_very_long_block_output(self):
        """The 'answers are cached' note must not be truncated away.

        Long REPL output is exactly the case RLM exists for, and the note is
        the orchestrator's signal that re-running the block will pay off.
        """
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        rlm._run_sandbox(sandbox, rlm_v2._LLM_QUERY_PRELUDE, session=_REPL_SESSION)

        worker = MagicMock()
        worker.attributes = {}
        worker.run.return_value = _worker_response()
        rlm._worker = worker

        output = rlm._execute_code(f"print('x' * {rlm_v2._REPL_OUTPUT_MAX_CHARS + 5000})\nllm_query('q')")

        assert "truncated" in output
        assert "1 llm_query answer(s) are now cached" in output


class TestContextBootstrap:
    """The context download link is a bearer capability — emitted code must not read it."""

    @staticmethod
    def _fake_response(body=b"raw text context", content_type="text/plain"):
        resp = MagicMock()
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        resp.headers = {"Content-Type": content_type}
        resp.iter_content.return_value = [body]
        return resp

    def test_upload_path_unbinds_the_download_url(self, tmp_path, monkeypatch):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox

        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt?sig=SECRETSIG"
            rlm._setup_repl("raw text context")

        code = next(c for c in sandbox.codes if "SECRETSIG" in c)
        monkeypatch.chdir(tmp_path)
        ns: dict = {}
        with patch("requests.get", return_value=self._fake_response()):
            exec(code, ns, ns)

        assert ns["context"] == "raw text context"
        assert "_url" not in ns
        assert "_r" not in ns
        assert not any("SECRETSIG" in str(v) for v in ns.values())

    def test_url_fast_path_unbinds_the_source_url(self, tmp_path, monkeypatch):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox

        rlm._setup_repl("https://example.com/big.txt?token=SECRETTOKEN")

        code = next(c for c in sandbox.codes if "SECRETTOKEN" in c)
        monkeypatch.chdir(tmp_path)
        ns: dict = {}
        with patch("requests.get", return_value=self._fake_response(b"streamed body")):
            exec(code, ns, ns)

        assert ns["context"] == "streamed body"
        assert "_url" not in ns
        assert "_url_path" not in ns
        assert "_r" not in ns
        assert not any("SECRETTOKEN" in str(v) for v in ns.values())


class TestFinalAnswerHardening:
    """FINAL_VAR validation and pending-placeholder rejection."""

    def test_final_var_rejects_non_identifier(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"

        assert rlm._get_repl_variable("__import__('os').system('x')") is None
        assert sandbox.calls == []

    def test_final_var_accepts_plain_identifier(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        sandbox.namespaces["repl-1"] = {"buf": "the answer"}

        assert rlm._get_repl_variable('"buf"') == "the answer"

    def test_final_var_rejects_pending_sentinel(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        rlm._sandbox_tool = sandbox
        rlm._repl_session_id = "repl-1"
        sandbox.namespaces["repl-1"] = {"buf": f"partial {_LLM_PENDING_SENTINEL}"}

        assert rlm._get_repl_variable("buf") is None

    def test_final_with_pending_sentinel_is_rejected_and_run_continues(self):
        rlm = _make_v2_rlm()
        sandbox = _FakeSandbox()
        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(
                rlm,
                sandbox,
                [f"FINAL(the answer is {_LLM_PENDING_SENTINEL})", "FINAL(the real answer)"],
            )

        assert result.status == "SUCCESS"
        assert result.data == "the real answer"
        assert _LLM_PENDING_SENTINEL not in result.data

    def test_forced_final_strips_pending_sentinel(self):
        rlm = _make_v2_rlm(max_iterations=1)
        sandbox = _FakeSandbox()
        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            mock_uploader.return_value.upload.return_value = "https://storage.example.com/ctx.txt"
            result = _drive_recursive(
                rlm,
                sandbox,
                [f"still thinking {_LLM_PENDING_SENTINEL}"],
                max_iterations=1,
            )

        assert result.status == "SUCCESS"
        assert _LLM_PENDING_SENTINEL not in result.data
        assert "[unanswered]" in result.data
