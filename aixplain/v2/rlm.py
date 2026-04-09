"""RLM (Recursive Language Model) for aiXplain SDK v2.

Orchestrates long-context analysis via an iterative REPL sandbox. The
orchestrator model plans and writes Python code to chunk and explore a large
context; a worker model handles per-chunk analysis via ``llm_query()`` calls
injected into the sandbox session.
"""

__author__ = "aiXplain"

import json
import logging
import os
import pathlib
import re
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config as dj_config
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from .resource import BaseResource, Result
from .mixins import ToolableMixin, ToolDict
from .upload_utils import FileUploader
from .exceptions import ResourceError

if TYPE_CHECKING:
    from .core import Aixplain

logger = logging.getLogger(__name__)


# Constants

# aiXplain managed Python sandbox tool ID.
_SANDBOX_TOOL_ID = "microsoft/code-execution/microsoft"

# Maximum characters of sandbox output fed back to the orchestrator per step.
_REPL_OUTPUT_MAX_CHARS = 100_000


# Prompt Templates

_SYSTEM_PROMPT = """You are tasked with answering a query with associated context. You can access, transform, and analyze this context interactively in a REPL environment that can recursively query sub-LLMs, which you are strongly encouraged to use as much as possible. You will be queried iteratively until you provide a final answer.

The REPL environment is initialized with:
1. A `context` variable that contains extremely important information about your query. You should check the content of the `context` variable to understand what you are working with. Make sure you look through it sufficiently as you answer your query.
2. A `llm_query` function that allows you to query an LLM with a context window of {worker_context_window} inside your REPL environment. You must take this context window into consideration when deciding how much text to pass in each call.
3. The ability to use `print()` statements to view the output of your REPL code and continue your reasoning.

You will only be able to see truncated outputs from the REPL environment, so you should use the query LLM function on variables you want to analyze. You will find this function especially useful when you have to analyze the semantics of the context. Use these variables as buffers to build up your final answer.
Make sure to explicitly look through the entire context in REPL before answering your query. An example strategy is to first look at the context and figure out a chunking strategy, then break up the context into smart chunks, and query an LLM per chunk with a particular question and save the answers to a buffer, then query an LLM with all the buffers to produce your final answer.

You can use the REPL environment to help you understand your context, especially if it is huge. Remember that your sub LLMs are powerful -- they have a context window of {worker_context_window}, so don't be afraid to put a lot of context into them.

When you want to execute Python code in the REPL environment, wrap it in triple backticks with the 'repl' language identifier:
```repl
# your Python code here
chunk = context[:10000]
answer = llm_query(f"What is the key finding in this text?\\n{{chunk}}")
print(answer)
```

IMPORTANT: When you are done with the iterative process, you MUST provide a final answer using one of these two forms (NOT inside a code block):
1. FINAL(your final answer here) — to provide the answer as literal text. Use `FINAL(...)` only when you are completely finished and will make no further REPL calls, request no further inspection, and need no additional intermediate outputs.
2. FINAL_VAR(variable_name) — to return a variable you created in the REPL as your final answer

Do not use `FINAL(...)` or `FINAL_VAR(...)` for intermediate status updates, plans, requests to inspect REPL output, or statements such as needing more information; those must be written as normal assistant text instead.

Think step by step carefully, plan, and execute this plan immediately — do not just say what you will do.
"""

_USER_PROMPT = (
    "Think step-by-step on what to do using the REPL environment (which contains the context) "
    'to answer the original query: "{query}".\n\n'
    "Continue using the REPL environment, which has the `context` variable, and querying sub-LLMs "
    "by writing to ```repl``` tags, and determine your answer. Your next action:"
)

_FIRST_ITER_PREFIX = (
    "You have not interacted with the REPL environment or seen your context yet. "
    "Your next action should be to look through the context first — do not provide a final answer yet.\n\n"
)

_CONTINUING_PREFIX = "The history above is your previous interactions with the REPL environment. "

_FORCE_FINAL_PROMPT = (
    "Based on all the information gathered so far, provide a final answer to the user's query. "
    "Use FINAL(your answer) or FINAL_VAR(variable_name)."
)

_DEFAULT_QUERY = (
    "Please read through the context and answer any queries or respond to any instructions contained within it."
)


# Prompt Helpers


def _build_system_messages(worker_context_window: str) -> List[Dict[str, str]]:
    return [{"role": "system", "content": _SYSTEM_PROMPT.format(worker_context_window=worker_context_window)}]


def _next_action_message(query: str, iteration: int, force_final: bool = False) -> Dict[str, str]:
    if force_final:
        return {"role": "user", "content": _FORCE_FINAL_PROMPT}
    prefix = _FIRST_ITER_PREFIX if iteration == 0 else _CONTINUING_PREFIX
    return {"role": "user", "content": prefix + _USER_PROMPT.format(query=query)}


def _messages_to_prompt(messages: List[Dict[str, str]]) -> str:
    """Serialize a chat message list to a single prompt string for Model.run()."""
    return "\n\n".join(f"[{msg['role'].upper()}]: {msg['content']}" for msg in messages)


# Response Parsing


def _find_code_blocks(text: str) -> Optional[List[str]]:
    """Extract all ```repl ... ``` code blocks from a model response."""
    results = [m.group(1).strip() for m in re.finditer(r"```repl\s*\n(.*?)\n```", text, re.DOTALL)]
    return results if results else None


def _find_final_answer(text: str) -> Optional[tuple]:
    """Return (type, content) for FINAL_VAR or FINAL declarations, or None."""
    match = re.search(r"^\s*FINAL_VAR\((.*?)\)", text, re.MULTILINE | re.DOTALL)
    if match:
        return ("FINAL_VAR", match.group(1).strip())
    match = re.search(r"^\s*FINAL\((.*?)\)", text, re.MULTILINE | re.DOTALL)
    if match:
        return ("FINAL", match.group(1).strip())
    return None


def _truncate(text: str, max_chars: int = _REPL_OUTPUT_MAX_CHARS) -> str:
    if len(text) > max_chars:
        return text[:max_chars] + f"\n... [truncated — {len(text) - max_chars} chars omitted]"
    return text


# Result


@dataclass_json
@dataclass(repr=False)
class RLMResult(Result):
    """Result returned by :meth:`RLM.run`.

    Extends the standard :class:`~aixplain.v2.resource.Result` with
    RLM-specific fields.

    Attributes:
        iterations_used: Number of orchestrator iterations consumed.
        used_credits: Total credits consumed across all orchestrator calls,
            sandbox executions, and worker ``llm_query()`` invocations.
        repl_logs: Per-iteration REPL execution log (excluded from
            serialization; present only on live instances).
    """

    iterations_used: int = field(default=0)
    used_credits: float = field(default=0.0, metadata=dj_config(field_name="usedCredits"))
    repl_logs: List[Dict] = field(
        default_factory=list,
        repr=False,
        compare=False,
        metadata=dj_config(exclude=lambda x: True),
    )


# RLM


@dataclass_json
@dataclass(repr=False)
class RLM(BaseResource, ToolableMixin):
    """Recursive Language Model — long-context analysis via an iterative REPL sandbox.

    RLM wraps two aiXplain models:

    - An **orchestrator** (powerful, expensive): plans and writes Python code to
      explore the context iteratively in a managed sandbox environment.
    - A **worker** (fast, cheap): called via ``llm_query()`` inside the sandbox
      to perform focused analysis on individual context chunks.

    The sandbox is an aiXplain managed Python execution environment. Each
    ``run()`` call gets its own isolated session (UUID), so variables persist
    across REPL iterations within a single run but are cleaned up afterwards.

    RLM is a **local orchestrator** — it does not correspond to a platform
    endpoint and is not saved via ``save()``. It is registered on the
    :class:`~aixplain.v2.core.Aixplain` client exactly like other resources so
    that credentials and URLs flow through ``self.context`` automatically.

    Example::

        from aixplain.v2 import Aixplain

        aix = Aixplain(api_key="...")
        rlm = aix.RLM(
            orchestrator_id="<orchestrator-model-id>",
            worker_id="<worker-model-id>",
        )

        result = rlm.run(data={
            "context": very_long_document,
            "query": "What are the key findings?",
        })
        print(result.data)
        print(f"Completed in {result.iterations_used} iteration(s).")

    Attributes:
        orchestrator_id: Platform model ID of the orchestrator LLM.
        worker_id: Platform model ID of the worker LLM.
        max_iterations: Maximum orchestrator loop iterations (default 10).
        timeout: Maximum wall-clock seconds per ``run()`` call (default 600).
    """

    # Not a platform-backed resource — no API endpoint.
    RESOURCE_PATH = ""

    # Serializable configuration fields
    orchestrator_id: str = field(default="")
    worker_id: str = field(default="")
    max_iterations: int = field(default=10)
    timeout: float = field(default=600.0)

    # Runtime state — excluded from serialization
    _session_id: Optional[str] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=dj_config(exclude=lambda x: True),
        init=False,
    )
    _sandbox_tool: Optional[Any] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=dj_config(exclude=lambda x: True),
        init=False,
    )
    _orchestrator: Optional[Any] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=dj_config(exclude=lambda x: True),
        init=False,
    )
    _worker: Optional[Any] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=dj_config(exclude=lambda x: True),
        init=False,
    )
    _messages: List[Dict] = field(
        default_factory=list,
        repr=False,
        compare=False,
        metadata=dj_config(exclude=lambda x: True),
        init=False,
    )
    _used_credits: float = field(
        default=0.0,
        repr=False,
        compare=False,
        metadata=dj_config(exclude=lambda x: True),
        init=False,
    )

    def __post_init__(self) -> None:
        """Auto-assign a UUID when no id is provided."""
        if not self.id:
            self.id = str(uuid.uuid4())

    # Validation

    def _assert_ready(self) -> None:
        """Raise if orchestrator_id or worker_id are missing."""
        if not self.orchestrator_id:
            raise ResourceError(
                "RLM requires an orchestrator_id. Pass orchestrator_id= when constructing aix.RLM(...)."
            )
        if not self.worker_id:
            raise ResourceError("RLM requires a worker_id. Pass worker_id= when constructing aix.RLM(...).")

    # Context Resolution

    @staticmethod
    def _resolve_context(context: Any) -> Union[str, dict, list]:
        """Normalize context to a ``str``, ``dict``, or ``list``.

        Accepted input forms:

        - ``pathlib.Path`` or ``str`` pointing to an existing file → file is
          read; ``.json`` files are parsed with ``json.load()``, everything else
          is read as plain text.
        - ``str`` HTTP/HTTPS URL → returned as-is; :meth:`_setup_repl` streams
          it directly into the sandbox without an intermediate re-upload.
        - ``str`` that is **not** a file path or URL → returned as-is (raw text).
        - ``dict`` / ``list`` → passed through unchanged.
        - Anything else → converted via ``str()``.

        Args:
            context: Raw context value passed by the caller.

        Returns:
            Normalized context ready for :meth:`_setup_repl`.

        Raises:
            ValueError: If the path exists but the file cannot be read or parsed.
        """
        if isinstance(context, pathlib.Path):
            context = str(context)

        if isinstance(context, str) and os.path.isfile(context):
            ext = os.path.splitext(context)[1].lower()
            try:
                if ext == ".json":
                    with open(context, "r", encoding="utf-8") as fh:
                        return json.load(fh)
                else:
                    with open(context, "r", encoding="utf-8") as fh:
                        return fh.read()
            except Exception as exc:
                raise ValueError(f"RLM: failed to read context file '{context}': {exc}") from exc

        if isinstance(context, (str, dict, list)):
            return context

        return str(context)

    # Lazy Model / Tool Resolution

    def _get_orchestrator(self) -> Any:
        """Lazily resolve and cache the orchestrator Model instance."""
        if self._orchestrator is None:
            self._orchestrator = self.context.Model.get(self.orchestrator_id)
            logger.debug(f"RLM: orchestrator resolved (id={self.orchestrator_id}).")
        return self._orchestrator

    def _get_worker(self) -> Any:
        """Lazily resolve and cache the worker Model instance."""
        if self._worker is None:
            self._worker = self.context.Model.get(self.worker_id)
            logger.debug(f"RLM: worker resolved (id={self.worker_id}).")
        return self._worker

    def _get_sandbox(self) -> Any:
        """Lazily resolve and cache the sandbox Tool instance."""
        if self._sandbox_tool is None:
            self._sandbox_tool = self.context.Tool.get(_SANDBOX_TOOL_ID)
            logger.debug("RLM: sandbox tool resolved.")
        return self._sandbox_tool

    # Worker Context Window

    def _get_worker_context_window(self) -> str:
        """Return a human-readable description of the worker model's context window."""
        worker = self._get_worker()
        attrs = getattr(worker, "attributes", None) or {}
        raw = attrs.get("max_context_length", None)
        if raw is not None:
            try:
                tokens = int(raw)
                if tokens >= 1_000_000:
                    return f"{tokens / 1_000_000:.1f}M tokens"
                if tokens >= 1_000:
                    return f"{tokens / 1_000:.0f}K tokens"
                return f"{tokens} tokens"
            except (ValueError, TypeError):
                return str(raw)
        return "a large context window"

    # Sandbox Setup

    def _setup_repl(self, context: Union[str, dict, list]) -> None:
        """Initialize a fresh sandbox session and load context + ``llm_query`` into it.

        Two paths are used to get context into the sandbox:

        - **URL** (``str`` starting with ``http://`` or ``https://``): the sandbox
          downloads the file directly from the caller's URL. The ``Content-Type``
          response header and the URL path extension are both checked to decide
          whether to load the result as JSON or plain text. No local temp file or
          intermediate upload is needed.
        - **Everything else**: context is serialized to a local temp file, uploaded
          to aiXplain storage via :class:`~aixplain.v2.upload_utils.FileUploader`,
          then downloaded inside the sandbox.

        In both cases a ``llm_query(prompt)`` helper is injected into the sandbox
        after the context is loaded.

        Args:
            context: Normalized context (str, dict, or list).
        """
        self._session_id = str(uuid.uuid4())
        sandbox = self._get_sandbox()
        logger.info(f"RLM: sandbox session started (id={self._session_id}).")

        # --- URL fast path: stream directly into the sandbox, no re-upload ---
        if isinstance(context, str) and (context.startswith("http://") or context.startswith("https://")):
            context_code = f"""import requests as __requests
import json as __json

_url = {repr(context)}
_url_path = _url.split("?")[0].lower()

with __requests.get(_url, stream=True) as _r:
    _r.raise_for_status()
    _content_type = _r.headers.get("Content-Type", "")
    _is_json = "application/json" in _content_type or _url_path.endswith(".json")
    _filename = "context.json" if _is_json else "context.txt"
    with open(_filename, "wb") as _f:
        for _chunk in _r.iter_content(chunk_size=8192):
            if _chunk:
                _f.write(_chunk)

if _is_json:
    try:
        with open(_filename, "r", encoding="utf-8") as _f:
            context = __json.load(_f)
    except Exception:
        with open(_filename, "r", encoding="utf-8") as _f:
            context = _f.read()
else:
    with open(_filename, "r", encoding="utf-8") as _f:
        context = _f.read()
"""
            self._run_sandbox(sandbox, context_code)
            logger.debug("RLM: context loaded into sandbox from URL (direct stream).")

        else:
            # --- Upload path: serialize locally, upload, then download in sandbox ---
            if isinstance(context, str):
                ext = ".txt"
                content_bytes = context.encode("utf-8")
                load_code = "with open(_filename, 'r', encoding='utf-8') as _f:\n    context = _f.read()"
            elif isinstance(context, (dict, list)):
                ext = ".json"
                content_bytes = json.dumps(context).encode("utf-8")
                load_code = (
                    "import json as __json\n"
                    "with open(_filename, 'r', encoding='utf-8') as _f:\n"
                    "    context = __json.load(_f)"
                )
            else:
                ext = ".txt"
                content_bytes = str(context).encode("utf-8")
                load_code = "with open(_filename, 'r', encoding='utf-8') as _f:\n    context = _f.read()"

            tmp_dir = tempfile.mkdtemp()
            tmp_path = os.path.join(tmp_dir, f"context{ext}")
            try:
                with open(tmp_path, "wb") as fh:
                    fh.write(content_bytes)

                uploader = FileUploader(
                    backend_url=self.context.backend_url,
                    api_key=self.context.api_key,
                )
                download_url = uploader.upload(
                    file_path=tmp_path,
                    is_temp=True,
                    return_download_link=True,
                )
                logger.debug(f"RLM: context uploaded ({ext}, {len(content_bytes)} bytes).")
            finally:
                try:
                    os.unlink(tmp_path)
                    os.rmdir(tmp_dir)
                except OSError:
                    pass

            sandbox_filename = f"context{ext}"

            context_code = f"""import requests as __requests

_url = {repr(download_url)}
_filename = {repr(sandbox_filename)}

with __requests.get(_url, stream=True) as _r:
    _r.raise_for_status()
    with open(_filename, "wb") as _f:
        for _chunk in _r.iter_content(chunk_size=8192):
            if _chunk:
                _f.write(_chunk)

{load_code}
"""
            self._run_sandbox(sandbox, context_code)
            logger.debug(f"RLM: context loaded into sandbox ({sandbox_filename}).")

        # Inject llm_query
        # worker_url = https://models.aixplain.com/api/v2/execute/<worker_id>
        worker_url = f"{self.context.model_url}/{self.worker_id}"

        llm_query_code = f"""import requests as __requests
import time as __time
import json as __json

_total_llm_query_credits = 0.0

def llm_query(prompt):
    global _total_llm_query_credits
    _headers = {{"x-api-key": "{self.context.api_key}", "Content-Type": "application/json"}}
    _payload = __json.dumps({{"data": prompt, "max_tokens": 8192}})
    try:
        _resp = __requests.post("{worker_url}", headers=_headers, data=_payload, timeout=60)
        _result = _resp.json()
        if _result.get("status") == "IN_PROGRESS":
            _poll_url = _result.get("url")
            _wait = 0.5
            _start = __time.time()
            while not _result.get("completed") and (__time.time() - _start) < 300:
                __time.sleep(_wait)
                _r = __requests.get(_poll_url, headers=_headers, timeout=30)
                _result = _r.json()
                _wait = min(_wait * 1.1, 60)
        _total_llm_query_credits += float(_result.get("usedCredits", 0) or 0)
        return str(_result.get("data", "Error: no data in worker response"))
    except Exception as _e:
        return f"Error: llm_query failed \u2014 {{_e}}"
"""
        self._run_sandbox(sandbox, llm_query_code)
        logger.debug("RLM: llm_query injected into sandbox.")

    # Sandbox Helpers

    def _run_sandbox(self, sandbox: Any, code: str) -> Any:
        """Execute code in the sandbox and return the raw ToolResult."""
        result = sandbox.run(
            data={"code": code, "sessionId": self._session_id},
            action="run",
        )
        self._used_credits += float(getattr(result, "used_credits", 0) or 0)
        return result

    def _execute_code(self, code: str) -> str:
        """Execute a code block in the sandbox and return formatted output.

        Runs the code in the current session (preserving all previously defined
        variables), captures stdout and stderr, and returns them as a string
        truncated to :data:`_REPL_OUTPUT_MAX_CHARS` characters.

        Args:
            code: Python source code to execute.

        Returns:
            Formatted string combining stdout and stderr. Returns ``"No output"``
            if both are empty.
        """
        result = self._run_sandbox(self._get_sandbox(), code)
        inner = result.data if isinstance(result.data, dict) else {}
        stdout = inner.get("stdout", "")
        stderr = inner.get("stderr", "")

        parts = []
        if stdout:
            parts.append(stdout)
        if stderr:
            parts.append(f"[stderr]: {stderr}")

        raw_output = "\n".join(parts) if parts else "No output"
        return _truncate(raw_output)

    def _get_repl_variable(self, variable_name: str) -> Optional[str]:
        """Retrieve a named variable's string value from the current sandbox session.

        Called when the orchestrator declares ``FINAL_VAR(variable_name)``.

        Args:
            variable_name: Name of the variable to retrieve (quotes are stripped).

        Returns:
            String representation of the variable, or ``None`` on error.
        """
        var = variable_name.strip().strip("\"'")
        result = self._run_sandbox(self._get_sandbox(), f"print(str({var}))")
        inner = result.data if isinstance(result.data, dict) else {}
        stdout = inner.get("stdout", "")
        stderr = inner.get("stderr", "")

        if stderr and not stdout:
            logger.warning(f"RLM: FINAL_VAR('{var}') error: {stderr.strip()}")
            return None
        return stdout.strip() if stdout else None

    # Credit Tracking

    def _collect_llm_query_credits(self) -> None:
        """Retrieve accumulated ``llm_query`` worker credits from the sandbox.

        The injected ``llm_query`` function tracks per-call ``usedCredits``
        from the worker model API in a global ``_total_llm_query_credits``
        variable inside the sandbox session. This method reads that variable
        and adds it to ``self._used_credits``.
        """
        try:
            raw = self._get_repl_variable("_total_llm_query_credits")
            if raw is not None:
                self._used_credits += float(raw)
        except Exception:
            logger.debug("RLM: could not retrieve llm_query credits from sandbox.")

    # Orchestrator

    def _orchestrator_completion(self, messages: List[Dict[str, str]]) -> str:
        """Query the orchestrator model with the full conversation history.

        Serializes the message list to a formatted prompt string and calls
        ``Model.run()`` on the resolved orchestrator.

        Args:
            messages: Full conversation history as role/content dicts.

        Returns:
            The orchestrator's text response.

        Raises:
            ResourceError: If the orchestrator model call fails or returns an error.
        """
        response = self._get_orchestrator().run(text=_messages_to_prompt(messages), max_tokens=8192)
        self._used_credits += float(getattr(response, "used_credits", 0) or 0)
        if response.completed or response.status == "SUCCESS":
            return str(response.data)
        raise ResourceError(
            f"RLM: orchestrator model failed — {getattr(response, 'error_message', None) or response.status}"
        )

    # Core Orchestration Loop

    def run(
        self,
        data: Union[str, dict, pathlib.Path],
        name: str = "rlm_process",
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> RLMResult:
        """Run the RLM orchestration loop over a (potentially large) context.

        A fresh sandbox session is created for each call. The orchestrator is
        called iteratively; each iteration it may execute ``repl`` code blocks in
        the sandbox (outputs fed back into the conversation) and eventually declare
        a final answer via ``FINAL(...)`` or ``FINAL_VAR(...)``.

        Args:
            data: Input context. Accepted forms:

                - ``str`` **raw text** — used directly as context; default query applied.
                - ``str`` **HTTP/HTTPS URL** — content is downloaded automatically;
                  ``.json`` URLs or ``application/json`` responses are parsed into a
                  dict/list, all other content decoded as plain text.
                - ``str`` **file path** — file is read automatically; ``.json`` files are
                  parsed into a dict/list, all other formats read as plain text.
                - ``pathlib.Path`` — resolved and read like a file-path string.
                - ``dict`` — must contain ``"context"`` (required) and optionally
                  ``"query"`` (defaults to a generic analysis prompt). The value
                  of ``"context"`` itself may also be a URL, a file path, or a
                  ``pathlib.Path``.

            name: Identifier used in log messages. Defaults to ``"rlm_process"``.
            timeout: Maximum wall-clock seconds. Overrides ``self.timeout`` when
                provided. Defaults to ``None`` (uses ``self.timeout``).
            **kwargs: Ignored; kept for API compatibility.

        Returns:
            :class:`RLMResult` with:

            - ``data``: Final answer string.
            - ``status``: ``"SUCCESS"`` or ``"FAILED"``.
            - ``completed``: ``True``.
            - ``used_credits``: Total credits consumed across all orchestrator
              calls, sandbox executions, and worker ``llm_query()`` invocations.
            - ``iterations_used``: Number of orchestrator iterations consumed.
            - ``repl_logs``: Per-iteration execution log (not serialized).

        Raises:
            ResourceError: If ``orchestrator_id`` or ``worker_id`` are unset,
                or if the orchestrator model call fails.
            ValueError: If ``data`` is a dict missing ``"context"``, or an
                unsupported type.
        """
        self._assert_ready()
        effective_timeout = timeout if timeout is not None else self.timeout

        # Normalise data argument
        if isinstance(data, pathlib.Path):
            data = str(data)

        if isinstance(data, str):
            context: Any = data
            query = _DEFAULT_QUERY
        elif isinstance(data, dict):
            if "context" not in data:
                raise ValueError(
                    "When passing data as a dict, it must contain a 'context' key. Optionally include a 'query' key."
                )
            context = data["context"]
            query = data.get("query", _DEFAULT_QUERY)
        else:
            raise ValueError(
                f"Unsupported data type: {type(data)}. "
                "Expected a str (raw text or file path), a pathlib.Path, "
                "or a dict with a 'context' key."
            )

        logger.info(f"RLM '{name}': starting. Query: {query[:120]!r}")
        start_time = time.time()
        iterations_used = 0
        final_answer: Optional[str] = None
        repl_logs: List[Dict] = []
        self._used_credits = 0.0

        # Resolve file-path context, initialise sandbox + conversation
        context = self._resolve_context(context)
        self._setup_repl(context)
        self._messages = _build_system_messages(self._get_worker_context_window())

        try:
            for iteration in range(self.max_iterations):
                iterations_used = iteration + 1

                if (time.time() - start_time) > effective_timeout:
                    logger.warning(f"RLM '{name}': timeout after {iteration} iterations — forcing final answer.")
                    break

                # Ask orchestrator for its next action
                response_text = self._orchestrator_completion(self._messages + [_next_action_message(query, iteration)])
                logger.debug(f"RLM '{name}' iter {iteration}: orchestrator responded.")

                # Execute any repl code blocks
                code_blocks = _find_code_blocks(response_text)
                if code_blocks:
                    self._messages.append({"role": "assistant", "content": response_text})
                    for code in code_blocks:
                        output = self._execute_code(code)
                        repl_logs.append({"iteration": iteration, "code": code, "output": output})
                        logger.debug(
                            f"RLM '{name}' iter {iteration}: executed {len(code)} chars → {len(output)} chars output."
                        )
                        self._messages.append(
                            {
                                "role": "user",
                                "content": (f"Code executed:\n```python\n{code}\n```\n\nREPL output:\n{output}"),
                            }
                        )
                else:
                    self._messages.append({"role": "assistant", "content": response_text})

                # Check for final answer declaration
                final_result = _find_final_answer(response_text)
                if final_result is not None:
                    answer_type, content = final_result
                    if answer_type == "FINAL":
                        final_answer = content
                        break
                    elif answer_type == "FINAL_VAR":
                        retrieved = self._get_repl_variable(content)
                        if retrieved is not None:
                            final_answer = retrieved
                            break
                        logger.warning(f"RLM '{name}': FINAL_VAR('{content}') not found in sandbox — continuing.")

            # Force a final answer if loop exhausted or timed out without one
            if final_answer is None:
                logger.info(f"RLM '{name}': requesting forced final answer after {iterations_used} iteration(s).")
                self._messages.append(_next_action_message(query, iterations_used, force_final=True))
                final_answer = self._orchestrator_completion(self._messages)

        except Exception as exc:
            error_msg = f"RLM run error: {exc}"
            logger.error(error_msg)
            self._collect_llm_query_credits()
            result = RLMResult(
                status="FAILED",
                completed=True,
                error_message=error_msg,
                data=None,
            )
            result.iterations_used = iterations_used
            result.used_credits = self._used_credits
            result.repl_logs = repl_logs
            return result

        self._collect_llm_query_credits()
        run_time = time.time() - start_time
        logger.info(f"RLM '{name}': done in {iterations_used} iteration(s), {run_time:.1f}s.")

        result = RLMResult(
            status="SUCCESS",
            completed=True,
            data=final_answer or "",
        )
        result.iterations_used = iterations_used
        result.used_credits = self._used_credits
        result.repl_logs = repl_logs
        result._raw_data = {"run_time": run_time}
        return result

    # ToolableMixin

    def as_tool(self) -> ToolDict:
        """Serialize this RLM as a tool for agent creation.

        Allows an :class:`~aixplain.v2.agent.Agent` to invoke the RLM as one of
        its tools, passing a query (and optionally context) as the ``data``
        argument.

        Returns:
            :class:`~aixplain.v2.mixins.ToolDict` representing this RLM.
        """
        return {
            "id": self.id,
            "name": self.name or "RLM",
            "description": (self.description or "Recursive Language Model for long-context analysis."),
            "supplier": "aixplain",
            "parameters": None,
            "function": "text-generation",
            "type": "model",
            "version": "1.0",
            "assetId": self.id,
        }

    # Unsupported async / stream

    def run_async(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """Not supported — raises :exc:`NotImplementedError`."""
        raise NotImplementedError("RLM does not support async execution. Use run() instead.")

    def run_stream(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        """Not supported — raises :exc:`NotImplementedError`."""
        raise NotImplementedError("RLM does not support streaming responses.")

    # Representation

    def __repr__(self) -> str:
        """Return string representation of this RLM instance."""
        return (
            f"RLM("
            f"orchestrator_id={self.orchestrator_id!r}, "
            f"worker_id={self.worker_id!r}, "
            f"max_iterations={self.max_iterations}, "
            f"id={self.id!r}"
            f")"
        )
