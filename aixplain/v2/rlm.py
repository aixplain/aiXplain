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
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
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
1. FINAL(your final answer here) — to provide the answer as literal text. Use `FINAL(...)` only when you are completely finished: you will make no further REPL calls, need no further inspection of REPL output, and are not including any REPL code in the same response.
2. FINAL_VAR(variable_name) — to return a variable you created in the REPL as your final answer. Use `FINAL_VAR(...)` only when that variable already contains your completed final answer and you will make no further REPL calls.

Do not use `FINAL(...)` or `FINAL_VAR(...)` for intermediate status updates, plans, requests to inspect REPL output, statements such as needing more information, or any response that also includes REPL code to be executed first; those must be written as normal assistant text instead.

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


# Map-Reduce Mode

# Context rot mitigation: attention quality degrades well before the official
# model window is hit. Sizing chunks to ~25% of the worker window keeps each
# map call inside the "comfortable" zone where recall stays high.
_CONTEXT_ROT_FRACTION = 0.25

# Rough char→token conversion. English text averages ~4 chars per token.
_CHARS_PER_TOKEN = 4

# Per-chunk overhead reserved (tokens) for the map prompt template + query.
_RESERVED_PROMPT_TOKENS = 800

# Output budget reserved (tokens) for the worker's response.
_RESERVED_OUTPUT_TOKENS = 4096

# Fallback worker window if not declared in model metadata.
_DEFAULT_WORKER_WINDOW_TOKENS = 32_000

# Overlap (chars) between adjacent text chunks so boundary facts aren't lost.
_CHUNK_OVERLAP_CHARS = 400

# Cap on concurrent worker calls to avoid hammering the API.
_MAX_PARALLEL_WORKERS = 8

# Number of partial answers combined per call in hierarchical reduce.
_REDUCE_FAN_IN = 8

# Query keywords that suggest 'recursive' mode is the better choice (multi-hop
# or cross-chunk reasoning that a single map+reduce pass would likely miss).
_RECURSIVE_QUERY_HINTS = (
    "compare across",
    "compare between",
    "inconsistenc",
    "contradict",
    "cross-reference",
    "cross reference",
    "verify against",
    "step by step",
    "iteratively",
    "trace through",
    "find all instances",
    "reason across",
)

_MAP_PROMPT = """You are analyzing part {idx} of {total} of a larger document.

User's query: {query}

Extract from this part anything relevant to the query. Be concise but complete — preserve specific facts, names, numbers, and direct quotes. If nothing in this part is relevant, respond with exactly: NONE

Content:
{chunk}
"""

_REDUCE_PROMPT = """You are synthesizing partial findings from {n} parts of a larger document into a single coherent answer.

User's original query: {query}

Partial findings (in document order):
{answers}

Produce a single, complete answer to the user's query. Combine information across parts, resolve any overlaps, and ignore any "NONE" responses. Write as if you analyzed the whole document — do not refer to "parts" or "chunks".
"""

_SINGLE_CALL_PROMPT = """User's query: {query}

Context:
{context}

Answer the user's query using the context above. Be complete and accurate."""


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


# Map-Reduce Helpers


def _compute_chunk_budget_chars(worker_window_tokens: int) -> int:
    """Compute the per-chunk content budget in characters.

    Applies the context-rot fraction first (each map call uses only a
    comfortable portion of the worker's window), then subtracts overhead for
    the map prompt template and the reserved output budget.
    """
    usable_tokens = int(worker_window_tokens * _CONTEXT_ROT_FRACTION)
    content_tokens = max(usable_tokens - _RESERVED_PROMPT_TOKENS - _RESERVED_OUTPUT_TOKENS, 1000)
    return content_tokens * _CHARS_PER_TOKEN


def _chunk_text(text: str, budget_chars: int, overlap: int = _CHUNK_OVERLAP_CHARS) -> List[str]:
    """Split text into overlapping chunks no larger than `budget_chars`."""
    if len(text) <= budget_chars:
        return [text]
    chunks: List[str] = []
    step = max(budget_chars - overlap, 1)
    i = 0
    while i < len(text):
        chunks.append(text[i:i + budget_chars])
        if i + budget_chars >= len(text):
            break
        i += step
    return chunks


def _serialize_group(group: list) -> str:
    if all(isinstance(x, str) for x in group):
        return "\n\n".join(group)
    return json.dumps(group, ensure_ascii=False, indent=2)


def _chunk_list_items(items: list, budget_chars: int) -> List[str]:
    """Group list items into string chunks each fitting within `budget_chars`."""
    chunks: List[str] = []
    current: List = []
    current_size = 0
    for item in items:
        s = item if isinstance(item, str) else json.dumps(item, ensure_ascii=False)
        size = len(s) + 2  # separator overhead
        if current_size + size > budget_chars and current:
            chunks.append(_serialize_group(current))
            current = []
            current_size = 0
        current.append(item)
        current_size += size
    if current:
        chunks.append(_serialize_group(current))
    return chunks


def _chunk_dict_items(d: dict, budget_chars: int) -> List[str]:
    """Group dict items into JSON-serialized chunks within `budget_chars`."""
    chunks: List[str] = []
    current: Dict = {}
    current_size = 0
    for k, v in d.items():
        size = len(json.dumps({k: v}, ensure_ascii=False))
        if current_size + size > budget_chars and current:
            chunks.append(json.dumps(current, ensure_ascii=False, indent=2))
            current = {}
            current_size = 0
        current[k] = v
        current_size += size
    if current:
        chunks.append(json.dumps(current, ensure_ascii=False, indent=2))
    return chunks


def _chunk_context(context: Union[str, dict, list], budget_chars: int) -> List[str]:
    """Dispatch chunking by context type; safety-pass re-chunks oversize results.

    A single dict value or list item can blow the budget on its own; the
    safety pass re-chunks any output exceeding 1.5× budget by falling back
    to character-based splitting on its serialized form.
    """
    if isinstance(context, str):
        raw_chunks = _chunk_text(context, budget_chars)
    elif isinstance(context, list):
        raw_chunks = _chunk_list_items(context, budget_chars)
    elif isinstance(context, dict):
        raw_chunks = _chunk_dict_items(context, budget_chars)
    else:
        raw_chunks = _chunk_text(str(context), budget_chars)

    safe_chunks: List[str] = []
    oversize_limit = int(budget_chars * 1.5)
    for c in raw_chunks:
        if len(c) > oversize_limit:
            safe_chunks.extend(_chunk_text(c, budget_chars))
        else:
            safe_chunks.append(c)
    return safe_chunks


def _select_mode(query: str) -> str:
    """Pick a mode automatically based on query characteristics.

    Defaults to the cheap, fast 'map_reduce' path. Falls back to 'recursive'
    only when the query hints at multi-hop or cross-chunk reasoning that a
    single map-then-reduce pass would likely miss.
    """
    q = query.lower()
    if any(hint in q for hint in _RECURSIVE_QUERY_HINTS):
        return "recursive"
    return "map_reduce"


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
    """Recursive Language Model — long-context analysis with two execution modes.

    RLM wraps two aiXplain models:

    - An **orchestrator** (powerful, expensive): plans and writes Python code to
      explore the context iteratively in a managed sandbox environment.
      Used by ``mode="recursive"``.
    - A **worker** (fast, cheap): called per chunk in both modes. In recursive
      mode it's invoked via ``llm_query()`` inside the sandbox; in map-reduce
      mode it's called directly in parallel.

    Two run modes are available via the ``mode`` argument to ``run()``:

    - ``"map_reduce"`` (cheap, fast, deterministic): chunk the context to ~25%
      of the worker's window (to mitigate context rot), call the worker in
      parallel on every chunk, then reduce the partial answers into a final
      answer. No orchestrator, no sandbox. Best for summarize/extract queries.
    - ``"recursive"`` (adaptive, expensive): the original iterative REPL loop
      where the orchestrator drives chunking and analysis. Best for multi-hop
      reasoning or queries that need to compare information across chunks.
    - ``"auto"`` (default): picks ``"recursive"`` if the query reads like
      multi-hop reasoning (e.g., contains words like "compare across",
      "inconsistencies", "verify against"); otherwise ``"map_reduce"``.

    The recursive mode's sandbox is an aiXplain managed Python execution
    environment. Each recursive ``run()`` call gets its own isolated session
    (UUID), so variables persist across REPL iterations within a single run
    but are cleaned up afterwards.

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
        """Auto-assign a UUID when no id is provided.

        Also initializes the thread-safe credit lock used by map-reduce mode's
        parallel worker calls. Stored as a plain instance attribute (not a
        dataclass field) so it's not serialized.
        """
        if not self.id:
            self.id = str(uuid.uuid4())
        self._credits_lock = threading.Lock()

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

    def _get_worker_context_tokens(self) -> int:
        """Return the worker model's max context window as an int.

        Falls back to ``_DEFAULT_WORKER_WINDOW_TOKENS`` when metadata is missing
        or malformed.
        """
        worker = self._get_worker()
        attrs = getattr(worker, "attributes", None) or {}
        raw = attrs.get("max_context_length", None)
        if raw is not None:
            try:
                return int(raw)
            except (ValueError, TypeError):
                pass
        return _DEFAULT_WORKER_WINDOW_TOKENS

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

    # Map-Reduce Mode

    def _worker_call(self, prompt: str) -> str:
        """Call the worker model once and return its text output.

        Thread-safe credit accumulation so this can run inside a
        ``ThreadPoolExecutor`` from the parallel map step.
        """
        response = self._get_worker().run(text=prompt, max_tokens=_RESERVED_OUTPUT_TOKENS)
        credits = float(getattr(response, "used_credits", 0) or 0)
        with self._credits_lock:
            self._used_credits += credits
        if response.completed or response.status == "SUCCESS":
            return str(response.data)
        raise ResourceError(
            f"RLM: worker model failed — {getattr(response, 'error_message', None) or response.status}"
        )

    @staticmethod
    def _resolve_url_context(context: Union[str, dict, list]) -> Union[str, dict, list]:
        """If `context` is an HTTP/HTTPS URL, fetch it locally and return parsed content.

        Map-reduce mode skips the sandbox, so URL contexts have to be resolved
        in-process. JSON content (by header or extension) is parsed; everything
        else is returned as text.
        """
        if not (isinstance(context, str) and (context.startswith("http://") or context.startswith("https://"))):
            return context
        import requests
        r = requests.get(context, timeout=60)
        r.raise_for_status()
        ct = r.headers.get("Content-Type", "")
        url_path = context.split("?")[0].lower()
        if "application/json" in ct or url_path.endswith(".json"):
            try:
                return r.json()
            except Exception:
                return r.text
        return r.text

    def _parallel_map(self, chunks: List[str], query: str) -> List[str]:
        """Run the map step: one worker call per chunk, in parallel.

        Returns answers in original chunk order. A single chunk failure does
        not fail the whole run — its slot is replaced with an error marker
        and the reduce step proceeds with what's available.
        """
        n = len(chunks)
        answers: List[Optional[str]] = [None] * n

        def _map_one(idx: int) -> str:
            prompt = _MAP_PROMPT.format(idx=idx + 1, total=n, query=query, chunk=chunks[idx])
            return self._worker_call(prompt)

        max_workers = min(n, _MAX_PARALLEL_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_map_one, i): i for i in range(n)}
            for f in as_completed(futures):
                i = futures[f]
                try:
                    answers[i] = f.result()
                except Exception as exc:
                    logger.warning(f"RLM map_reduce: chunk {i} failed: {exc}")
                    answers[i] = f"[Error analyzing this part: {exc}]"

        return [a if a is not None else "NONE" for a in answers]

    def _reduce_call(self, formatted_answers: str, query: str, n: int) -> str:
        """Single reduce call: synthesize partial answers into one final answer."""
        prompt = _REDUCE_PROMPT.format(n=n, query=query, answers=formatted_answers)
        return self._worker_call(prompt)

    def _hierarchical_reduce(self, answers: List[str], query: str) -> str:
        """Multi-level reduce when partial answers don't all fit in one call.

        Combines ``_REDUCE_FAN_IN`` answers at a time, in parallel at each
        level, until a single answer remains. log(N) depth.
        """
        while len(answers) > 1:
            groups = [answers[i:i + _REDUCE_FAN_IN] for i in range(0, len(answers), _REDUCE_FAN_IN)]

            def _reduce_group(group: List[str]) -> str:
                formatted = "\n\n".join(f"[Part]: {a}" for a in group)
                return self._reduce_call(formatted, query, len(group))

            next_level: List[Optional[str]] = [None] * len(groups)
            max_workers = min(len(groups), _MAX_PARALLEL_WORKERS)
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(_reduce_group, g): i for i, g in enumerate(groups)}
                for f in as_completed(futures):
                    i = futures[f]
                    next_level[i] = f.result()
            answers = [a for a in next_level if a is not None]
        return answers[0]

    def _reduce(self, chunk_answers: List[str], query: str, budget_chars: int) -> str:
        """Reduce step: drop NONE responses, then synthesize the rest."""
        meaningful = [(i, a) for i, a in enumerate(chunk_answers) if a.strip().rstrip(".").upper() != "NONE"]

        if not meaningful:
            return "No information relevant to the query was found in the document."

        if len(meaningful) == 1:
            # Single relevant part — pass through reduce so the final wording
            # answers the original query rather than reading like an extraction.
            return self._reduce_call(f"[Part]: {meaningful[0][1]}", query, 1)

        formatted = "\n\n".join(f"[Part {i + 1}]: {a}" for i, a in meaningful)
        if len(formatted) <= budget_chars:
            return self._reduce_call(formatted, query, len(meaningful))

        return self._hierarchical_reduce([a for _, a in meaningful], query)

    def _run_map_reduce(
        self,
        context: Union[str, dict, list],
        query: str,
        name: str,
        start_time: float,
    ) -> RLMResult:
        """Deterministic chunk → parallel map → reduce. No orchestrator, no sandbox."""
        iterations_used = 0
        try:
            context = self._resolve_url_context(context)
            # Pre-resolve worker once so the cache is populated before threads
            # start (avoids a race in the lazy _get_worker() accessor).
            self._get_worker()

            worker_tokens = self._get_worker_context_tokens()
            budget_chars = _compute_chunk_budget_chars(worker_tokens)
            chunks = _chunk_context(context, budget_chars)
            n_chunks = len(chunks)
            logger.info(
                f"RLM '{name}' map_reduce: {n_chunks} chunk(s), ~{budget_chars} chars/chunk "
                f"(worker={worker_tokens} tokens, "
                f"{int(_CONTEXT_ROT_FRACTION * 100)}% utilization to mitigate context rot)."
            )

            if n_chunks == 1:
                # Fast path: context fits comfortably in one worker call.
                prompt = _SINGLE_CALL_PROMPT.format(query=query, context=chunks[0])
                final_answer = self._worker_call(prompt)
                iterations_used = 1
            else:
                chunk_answers = self._parallel_map(chunks, query)
                final_answer = self._reduce(chunk_answers, query, budget_chars)
                iterations_used = n_chunks
        except Exception as exc:
            error_msg = f"RLM map_reduce error: {exc}"
            logger.error(error_msg)
            result = RLMResult(
                status="FAILED",
                completed=True,
                error_message=error_msg,
                data=None,
            )
            result.iterations_used = iterations_used
            result.used_credits = self._used_credits
            return result

        run_time = time.time() - start_time
        logger.info(f"RLM '{name}' map_reduce: done in {run_time:.1f}s ({iterations_used} worker call(s)).")
        result = RLMResult(
            status="SUCCESS",
            completed=True,
            data=final_answer,
        )
        result.iterations_used = iterations_used
        result.used_credits = self._used_credits
        result._raw_data = {"run_time": run_time}
        return result

    # Core Orchestration Loop

    def run(
        self,
        data: Union[str, dict, pathlib.Path],
        name: str = "rlm_process",
        timeout: Optional[float] = None,
        mode: str = "auto",
        **kwargs: Any,
    ) -> RLMResult:
        """Run the RLM over a (potentially large) context, dispatching by mode.

        ``mode`` selects the execution strategy:

        - ``"map_reduce"``: deterministic chunk + parallel worker calls + reduce.
          Cheap, fast, predictable. Only the worker is required — no orchestrator
          or sandbox. Best for summarize/extract queries. Chunks are sized to
          ~25% of the worker's window to mitigate context rot.
        - ``"recursive"``: the iterative REPL loop where the orchestrator drives
          chunking and analysis in a sandbox. Expensive but adaptive. Best for
          multi-hop reasoning that needs to compare information across chunks.
        - ``"auto"`` (default): picks ``"recursive"`` when the query reads like
          multi-hop reasoning (keywords such as "compare across",
          "inconsistencies", "verify against", "step by step"); otherwise
          ``"map_reduce"``.

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
            timeout: Maximum wall-clock seconds. Applies to ``"recursive"`` mode
                only. Overrides ``self.timeout`` when provided.
            mode: ``"auto"``, ``"map_reduce"``, or ``"recursive"``. Defaults to
                ``"auto"``.
            **kwargs: Ignored; kept for API compatibility.

        Returns:
            :class:`RLMResult` with:

            - ``data``: Final answer string.
            - ``status``: ``"SUCCESS"`` or ``"FAILED"``.
            - ``completed``: ``True``.
            - ``used_credits``: Total credits across all model calls.
            - ``iterations_used``: Recursive mode → orchestrator iterations.
              Map-reduce mode → worker calls in the map step (= number of
              chunks), or 1 for the single-call fast path.
            - ``repl_logs``: Per-iteration execution log (recursive mode only;
              empty for map-reduce). Not serialized.

        Raises:
            ResourceError: If ``worker_id`` is unset, or ``recursive`` mode is
                used without ``orchestrator_id``, or a model call fails.
            ValueError: If ``data`` is a dict missing ``"context"``, ``mode``
                is invalid, or ``data`` is an unsupported type.
        """
        if mode not in ("auto", "map_reduce", "recursive"):
            raise ValueError(f"Invalid mode: {mode!r}. Choose 'auto', 'map_reduce', or 'recursive'.")
        if not self.worker_id:
            raise ResourceError("RLM requires a worker_id. Pass worker_id= when constructing aix.RLM(...).")

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

        # Resolve mode before any context normalization so 'auto' can dispatch
        # without paying any setup cost.
        if mode == "auto":
            mode = _select_mode(query)
            logger.info(f"RLM '{name}': auto-selected mode={mode!r}.")

        logger.info(f"RLM '{name}': starting (mode={mode}). Query: {query[:120]!r}")
        start_time = time.time()
        self._used_credits = 0.0

        context = self._resolve_context(context)

        if mode == "map_reduce":
            return self._run_map_reduce(context, query, name, start_time)

        # recursive — requires orchestrator
        self._assert_ready()
        effective_timeout = timeout if timeout is not None else self.timeout
        return self._run_recursive(context, query, name, start_time, effective_timeout)

    def _run_recursive(
        self,
        context: Union[str, dict, list],
        query: str,
        name: str,
        start_time: float,
        effective_timeout: float,
    ) -> RLMResult:
        """Iterative REPL-loop path: orchestrator drives a sandbox session."""
        iterations_used = 0
        final_answer: Optional[str] = None
        repl_logs: List[Dict] = []

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
