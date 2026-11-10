"""The RLM sandbox never receives the caller's key (ENG-3782, layer 5; restores SDK BUG-936 coverage).

SDK #1042 (SEV1) stopped baking TEAM_API_KEY into the RLM sandbox source. Its
tests lived in tests/unit/rlm_test.py and were deleted with v1 in #1136,
leaving the fix with no test at all. This restores the v2 credential-isolation
cases unchanged in substance: the sandbox payloads, a co_consts probe run for
real against the emitted prelude, the secret tripwire, and redaction of
anything a script echoes back.
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
from aixplain.v2.rlm import RLM as RLMV2
from aixplain.v2.rlm import (
    _LLM_PENDING_SENTINEL,
    _REPL_SESSION,
)


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


def _sandbox_result(stdout="", stderr="", used_credits=0.0):
    """Create a mock sandbox result."""
    r = MagicMock()
    r.data = {"stdout": stdout, "stderr": stderr}
    r.used_credits = used_credits
    return r


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
