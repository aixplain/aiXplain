"""Shared offline fakes for the ``aixplain.v2.rlm`` unit tests.

``Aixplain`` binds resources as ``type("RLM", (RLM,), {"context": aix})``; the
helpers here bind a ``MagicMock`` context the same way so ``ctx.Model.get``,
``ctx.Tool.get`` and ``ctx.Tool(...)`` can be stubbed without any network.
"""

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

from aixplain.v2.rlm import RLM

API_KEY = "fake-unit-test-key"  # deliberately low-entropy: not a real credential


def resp(data=None, status="SUCCESS", completed=True, used_credits=0.0, error_message=None):
    """Build a model/tool response with the attributes rlm.py reads."""
    return SimpleNamespace(
        data=data,
        status=status,
        completed=completed,
        used_credits=used_credits,
        error_message=error_message,
    )


class FakeModel:
    """Model stand-in whose ``run`` answers via ``responder(text)`` and records calls."""

    def __init__(self, responder=None, max_context_length=None, credits=0.0):
        self._responder = responder or (lambda text: "answer")
        self.attributes = {} if max_context_length is None else {"max_context_length": max_context_length}
        self.credits = credits
        self.calls = []
        self._lock = threading.Lock()

    def run(self, text, max_tokens=None, timeout=None):
        with self._lock:
            self.calls.append({"text": text, "max_tokens": max_tokens})
        out = self._responder(text)
        if isinstance(out, BaseException):
            raise out
        if isinstance(out, SimpleNamespace):
            return out
        return resp(data=out, used_credits=self.credits)


class ScriptedModel(FakeModel):
    """Model stand-in that returns a fixed sequence of text responses."""

    def __init__(self, responses, credits=0.0):
        self._queue = list(responses)
        super().__init__(responder=self._next, credits=credits)

    def _next(self, text):
        if not self._queue:
            raise AssertionError("ScriptedModel ran out of responses")
        return self._queue.pop(0)


class FakeSandbox:
    """Sandbox Tool stand-in that records every ``run`` and answers via ``handler``.

    ``handler(code)`` returns ``{"stdout": ..., "stderr": ...}`` (or any
    ``data`` value). The default handler prints nothing.
    """

    def __init__(self, handler=None, actions=None, credits=0.0):
        self._handler = handler or (lambda code: {"stdout": "", "stderr": ""})
        self.actions = actions
        self.credits = credits
        self.calls = []

    def list_actions(self):
        if isinstance(self.actions, BaseException):
            raise self.actions
        return [SimpleNamespace(name=a) for a in (self.actions or [])]

    def run(self, data, action, timeout=None):
        self.calls.append({"data": data, "action": action})
        if action != "run":
            return resp(data={"closed": True})
        return resp(data=self._handler(data["code"]), used_credits=self.credits)

    def codes(self):
        """Return the code of every ``action="run"`` call, in order."""
        return [c["data"].get("code") for c in self.calls if c["action"] == "run"]


def make_context(models=None, sandbox=None):
    """Return a MagicMock Aixplain context resolving model ids from ``models``."""
    ctx = MagicMock()
    ctx.api_key = API_KEY
    ctx.backend_url = "https://platform-api.example.invalid"
    models = models or {}
    ctx.Model.get.side_effect = lambda model_id: models[model_id]
    if sandbox is not None:
        ctx.Tool.get.return_value = sandbox
    return ctx


def make_rlm(ctx=None, **kwargs):
    """Construct an RLM bound to ``ctx`` exactly like ``Aixplain`` binds it."""
    ctx = ctx if ctx is not None else make_context()
    bound = type("RLM", (RLM,), {"context": ctx})
    kwargs.setdefault("orchestrator_id", "orch")
    kwargs.setdefault("worker_id", "worker")
    return bound(**kwargs)


class ExecSandbox(FakeSandbox):
    """Sandbox stand-in that really executes code in-process, one namespace per session.

    Gives a faithful REPL round-trip (prelude, ``llm_query`` markers, answer
    injection, ``FINAL_VAR`` lookup) without any network: the context-download
    block is intercepted and ``context`` is set directly from ``context_value``.
    """

    def __init__(self, context_value=None, actions=None, credits=0.0):
        super().__init__(handler=self._exec, actions=actions, credits=credits)
        self.context_value = context_value
        self.namespaces = {}
        self._current = None

    def run(self, data, action, timeout=None):
        self._current = data.get("sessionId")
        return super().run(data, action, timeout=timeout)

    def _exec(self, code):
        import contextlib
        import io
        import traceback

        ns = self.namespaces.setdefault(self._current, {"__name__": "__sandbox__"})
        if "__requests.get(_url" in code:
            ns["context"] = self.context_value
            return {"stdout": "", "stderr": ""}
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                exec(compile(code, "<sandbox>", "exec"), ns)
            except Exception:
                traceback.print_exc()
        return {"stdout": out.getvalue(), "stderr": err.getvalue()}
