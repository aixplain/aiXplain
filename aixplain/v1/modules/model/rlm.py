"""RLM (Recursive Language Model) module for aiXplain SDK v1."""

__author__ = "aiXplain"

"""
Copyright 2026 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain Team
Description:
    RLM (Recursive Language Model) — orchestrates long-context analysis via
    an iterative REPL sandbox. The orchestrator model plans and writes Python
    code to chunk and explore a large context; a worker model handles per-chunk
    analysis via llm_query() calls injected into the sandbox session.
"""

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
from typing import Dict, List, Optional, Text, Union

from aixplain.enums import Function, FunctionType, Supplier
from aixplain.enums.response_status import ResponseStatus
from aixplain.modules.model import Model
from aixplain.modules.model.response import ModelResponse
from aixplain.utils import config


# Sandbox

# aiXplain managed Python sandbox tool ID.
_SANDBOX_TOOL_ID = "698cda188bbb345db14ac13b"

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


# Parallel Mode

# Context rot mitigation: attention quality degrades well before the official
# model window is hit. Sizing chunks to ~80% of the worker window keeps each
# map call inside the "comfortable" zone where recall stays high.
_CONTEXT_ROT_FRACTION = 0.80

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
# or cross-chunk reasoning that a single parallel pass would likely miss).
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


# RAG Mode (aIR-backed retrieval)

# Fraction of the worker's context window allocated to the assembled
# retrieved chunks in the synthesis call. Chunk size is derived as
#     (worker_window_tokens × _RAG_ASSEMBLY_FRACTION × _CHARS_PER_TOKEN) / rag_top_k
# so the top_k retrieved chunks together fit comfortably in the worker call.
_RAG_ASSEMBLY_FRACTION = 0.80

# Floor for derived chunk size (chars). Very tiny chunks lose too much
# surrounding context to embed well.
_RAG_MIN_CHUNK_CHARS = 500

# Upper bound on chunk size (chars) imposed by the embedding model's input
# limit. The aIR-backing model's actual token limit isn't known to this
# code, so the default is a generic middle ground (~30K chars ≈ 7.5K tokens)
# that fits the 8K-token family (ada-002, text-embedding-3, BGE-M3) without
# being needlessly small. Override per-instance via `rag_max_chunk_chars`
# when you know the backing model's limit — e.g. ~2K chars for 512-token
# models (multilingual-E5, Jina CLIP), or larger when the model supports it.
_RAG_DEFAULT_MAX_CHUNK_CHARS = 30_000

# Default number of chunks retrieved from the index per query.
_RAG_DEFAULT_TOP_K = 10

_RAG_SYNTHESIS_PROMPT = """User's query: {query}

Below are excerpts retrieved from a larger document, ordered by their position in the original document. Use these excerpts to answer the user's query as completely and accurately as possible.

Retrieved excerpts:
{chunks}

Answer the user's query using only the excerpts above. Be complete and accurate."""


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


# Chunking Helpers (shared by parallel and rag modes)


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

    Defaults to the cheap, fast 'parallel' path. Falls back to 'recursive'
    only when the query hints at multi-hop or cross-chunk reasoning that a
    single map-then-reduce pass would likely miss.
    """
    q = query.lower()
    if any(hint in q for hint in _RECURSIVE_QUERY_HINTS):
        return "recursive"
    return "parallel"


# RLM Class


class RLM(Model):
    """Recursive Language Model — long-context analysis with two execution modes.

    RLM wraps two aiXplain models:

    - An **orchestrator** (powerful, expensive): plans and writes Python code to
      explore the context iteratively in a managed sandbox environment.
      Used by ``mode="recursive"``.
    - A **worker** (fast, cheap): called per chunk in both modes. In recursive
      mode it's invoked via ``llm_query()`` inside the sandbox; in parallel
      mode it's called directly, concurrently across chunks.

    Three run modes are available via the ``mode`` argument to ``run()``:

    - ``"parallel"`` (cheap, fast, deterministic): chunk the context to a
      comfortable fraction of the worker's window (to mitigate context rot),
      call the worker in parallel on every chunk, then reduce the partial
      answers into a final answer. No orchestrator, no sandbox. Best for
      summarize/extract queries.
    - ``"rag"`` (cheapest at query time): chunk the context into small
      retrieval-grade pieces, upsert them into an aIR vector index, retrieve
      the top-k most relevant chunks for the query, then make a single worker
      call to synthesize an answer. The win is amortizing the upfront index
      build across many queries: set ``rag_index_id`` to reuse a pre-built
      index and skip create + upsert + delete on each call. Best for
      needle-in-haystack questions on very large contexts.
    - ``"recursive"`` (adaptive, expensive): the original iterative REPL loop
      where the orchestrator drives chunking and analysis. Best for multi-hop
      reasoning or queries that need to compare information across chunks.
    - ``"auto"`` (default): picks ``"recursive"`` if the query reads like
      multi-hop reasoning (e.g., contains words like "compare across",
      "inconsistencies", "verify against"); otherwise ``"parallel"``.
      ``"rag"`` is opt-in only — auto never picks it because it only beats
      ``parallel`` when the index is reused across many calls.

    The recursive mode's sandbox is an aiXplain managed Python execution
    environment. Each recursive ``run()`` call gets its own isolated session
    (UUID), so variables persist across REPL iterations within a single run
    but are cleaned up afterwards.

    Example usage::

        from aixplain.factories import ModelFactory

        rlm = ModelFactory.create_rlm(
            orchestrator_model_id="<orchestrator-model-id>",
            worker_model_id="<worker-model-id>",
        )
        response = rlm.run(data={
            "context": very_long_document,
            "query": "What are the key findings?",
        })
        print(response.data)
        print(f"Completed in {response['iterations_used']} iterations.")

    Attributes:
        orchestrator (Model): Root LLM that plans and writes REPL code.
        worker (Model): Sub-LLM used inside the sandbox via ``llm_query()``.
        max_iterations (int): Maximum orchestrator loop iterations before a
            forced final answer is requested.
    """

    # aiXplain managed Python sandbox tool ID.
    SANDBOX_TOOL_ID: str = _SANDBOX_TOOL_ID

    def __init__(
        self,
        id: Text,
        name: Text = "RLM",
        description: Text = "Recursive Language Model for long-context analysis.",
        orchestrator: Optional[Model] = None,
        worker: Optional[Model] = None,
        max_iterations: int = 10,
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        rag_index_id: Optional[Text] = None,
        rag_top_k: int = _RAG_DEFAULT_TOP_K,
        rag_max_chunk_chars: int = _RAG_DEFAULT_MAX_CHUNK_CHARS,
        **additional_info,
    ) -> None:
        """Initialize a new RLM instance.

        Args:
            id (Text): Identifier for this RLM instance.
            name (Text, optional): Display name. Defaults to "RLM".
            description (Text, optional): Description. Defaults to a generic string.
            orchestrator (Model, optional): Root LLM that drives the REPL loop.
                Must be set before calling ``run()``. Defaults to None.
            worker (Model, optional): Sub-LLM called inside the sandbox via
                ``llm_query()``. Must be set before calling ``run()``. Defaults to None.
            max_iterations (int, optional): Maximum orchestrator iterations.
                Defaults to 10.
            api_key (Text, optional): API key. Defaults to ``config.TEAM_API_KEY``.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier.
                Defaults to "aiXplain".
            rag_index_id (Text, optional): ID of a pre-built aIR index for
                ``mode="rag"``. When set, the index is reused (skipping
                create + upsert + delete on each ``run()``). When ``None``,
                an ephemeral index is created per RAG run and deleted
                afterwards. Defaults to ``None``.
            rag_top_k (int, optional): Number of chunks retrieved from the
                aIR index per query in ``mode="rag"``. Defaults to 10.
            rag_max_chunk_chars (int, optional): Upper bound on a single RAG
                chunk (chars), to stay under the embedding model's input
                limit. Default ~30K chars is a generic middle ground that
                fits 8K-token models (ada-002, text-embedding-3, BGE-M3).
                Tune down for 512-token models (multilingual-E5, Jina CLIP)
                or up when the backing model supports it. Defaults to 30000.
            **additional_info: Additional metadata stored on the instance.
        """
        super().__init__(
            id=id,
            name=name,
            description=description,
            api_key=api_key or config.TEAM_API_KEY,
            supplier=supplier,
            function=Function.TEXT_GENERATION,
            function_type=FunctionType.AI,
            **additional_info,
        )
        self.orchestrator = orchestrator
        self.worker = worker
        self.max_iterations = max_iterations
        self.rag_index_id = rag_index_id
        self.rag_top_k = rag_top_k
        self.rag_max_chunk_chars = rag_max_chunk_chars

        # State reset on each run() call
        self._session_id: Optional[str] = None
        self._sandbox_tool: Optional[Model] = None
        self._messages: List[Dict[str, str]] = []
        self._used_credits: float = 0.0
        # Guards _used_credits across concurrent worker calls in parallel mode.
        self._credits_lock = threading.Lock()

    # Worker Context Window

    def _get_worker_context_window(self) -> str:
        """Return a human-readable description of the worker model's context window."""
        attributes = getattr(self.worker, "additional_info", {}).get("attributes", [])
        raw = next(
            (attr["code"] for attr in attributes if attr.get("name") == "max_context_length"),
            None,
        )
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
        attributes = getattr(self.worker, "additional_info", {}).get("attributes", [])
        raw = next(
            (attr["code"] for attr in attributes if attr.get("name") == "max_context_length"),
            None,
        )
        if raw is not None:
            try:
                return int(raw)
            except (ValueError, TypeError):
                pass
        return _DEFAULT_WORKER_WINDOW_TOKENS

    # Context Resolution

    @staticmethod
    def _resolve_context(context) -> Union[str, dict, list]:
        """Normalize context to a str, dict, or list before sandbox loading.

        Accepts context in several forms:

        - ``str`` pointing to an existing file → file is read and deserialized
          based on its extension (``.json`` → dict/list, everything else → str).
        - ``pathlib.Path`` → same file-reading logic as a path string.
        - ``str`` HTTP/HTTPS URL → returned as-is; ``_setup_repl`` streams it
          directly into the sandbox without an intermediate re-upload.
        - ``str`` that is NOT a file path or URL → used as-is (raw text content).
        - ``dict`` / ``list`` → passed through unchanged.
        - Anything else → converted to ``str`` via ``str()``.

        Supported file extensions:
            - ``.json``                              → parsed with ``json.load()`` → dict or list
            - ``.txt``, ``.md``, ``.csv``, ``.html``,
              ``.xml``, ``.yaml``, ``.yml``, ``.py``,
              and any other text format              → read as a plain string

        Args:
            context: Raw context value passed by the caller.

        Returns:
            Union[str, dict, list]: Normalized context ready for ``_setup_repl``.

        Raises:
            ValueError: If the path exists but the file cannot be read or parsed.
        """
        # Resolve pathlib.Path to a string path first
        if isinstance(context, pathlib.Path):
            context = str(context)

        # If it looks like a file path and the file exists, read it
        if isinstance(context, str) and os.path.isfile(context):
            ext = os.path.splitext(context)[1].lower()
            try:
                if ext == ".json":
                    with open(context, "r", encoding="utf-8") as f:
                        return json.load(f)
                else:
                    with open(context, "r", encoding="utf-8") as f:
                        return f.read()
            except Exception as e:
                raise ValueError(f"RLM: failed to read context file '{context}': {e}") from e

        # dict / list → pass through unchanged
        if isinstance(context, (str, dict, list)):
            return context

        # Fallback: stringify anything else
        return str(context)

    # Sandbox Setup

    def _setup_repl(self, context: Union[str, dict, list]) -> None:
        """Initialize a fresh sandbox session and load context + llm_query into it.

        Each call generates a new UUID session ID, ensuring complete isolation
        between runs. Two paths are used to get context into the sandbox:

        - **URL** (``str`` starting with ``http://`` or ``https://``): the sandbox
          downloads the file directly from the caller's URL. The Content-Type
          response header and the URL path extension are both checked to decide
          whether to load the result as JSON or plain text. No local temp file or
          intermediate upload is needed.
        - **Everything else**: the context is serialized to a local temp file,
          uploaded to aiXplain storage, then downloaded inside the sandbox.

        Supported context types (non-URL path):
            - ``str``        → ``.txt`` file, loaded with ``open().read()``
            - ``dict``/``list`` → ``.json`` file, loaded with ``json.load()``
            - other          → converted to string, stored as ``.txt``

        Args:
            context: The large context to load into the sandbox.
        """
        # Lazy import avoids circular: model_factory → rlm → tool_factory → model_factory
        from aixplain.factories.tool_factory import ToolFactory
        from aixplain.factories.file_factory import FileFactory

        self._session_id = str(uuid.uuid4())
        self._sandbox_tool = ToolFactory.get(self.SANDBOX_TOOL_ID, api_key=self.api_key)
        logging.info(f"RLM: sandbox session started (id={self._session_id}).")

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
            self._run_sandbox(context_code)
            logging.debug("RLM: context loaded into sandbox from URL (direct stream).")

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
                with open(tmp_path, "wb") as f:
                    f.write(content_bytes)

                download_url = FileFactory.create(local_path=tmp_path, is_temp=True)
                logging.debug(f"RLM: context uploaded ({ext}, {len(content_bytes)} bytes).")
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
            self._run_sandbox(context_code)
            logging.debug(f"RLM: context loaded into sandbox from uploaded file ({sandbox_filename}).")

        # Inject llm_query
        # The function is defined directly in the sandbox session so that it
        # persists for all subsequent code blocks in this run. It calls the
        # worker model's run endpoint using requests, with async polling.
        worker_url = f"{self.worker.url}/{self.worker.id}".replace("api/v1/execute", "api/v2/execute")

        llm_query_code = f"""import requests as __requests
import time as __time
import json as __json

_total_llm_query_credits = 0.0

def llm_query(prompt):
    global _total_llm_query_credits
    _headers = {{"x-api-key": "{self.api_key}", "Content-Type": "application/json"}}
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
        return f"Error: llm_query failed — {{_e}}"
"""

        self._run_sandbox(llm_query_code)
        logging.debug("RLM: llm_query injected into sandbox.")

    def _run_sandbox(self, code: str) -> ModelResponse:
        """Execute code in the sandbox and return the raw response."""
        result = self._sandbox_tool.run(
            inputs={"code": code, "sessionId": self._session_id},
            action="run",
        )
        self._used_credits += float(getattr(result, "used_credits", 0) or 0)
        return result

    # Code Execution

    def _execute_code(self, code: str) -> str:
        """Execute a Python code block in the sandbox and return formatted output.

        Runs the code in the current session (preserving all previously defined
        variables), captures stdout and stderr, and returns them as a string
        truncated to ``_REPL_OUTPUT_MAX_CHARS`` characters.

        Args:
            code: Python source code to execute.

        Returns:
            Formatted string combining stdout and stderr. Returns "No output"
            if both are empty.
        """
        result = self._run_sandbox(code)
        stdout = result.data.get("stdout", "") if isinstance(result.data, dict) else ""
        stderr = result.data.get("stderr", "") if isinstance(result.data, dict) else ""

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
        Runs ``print(str(variable_name))`` in the sandbox and returns stdout.

        Args:
            variable_name: Name of the variable to retrieve (quotes are stripped).

        Returns:
            String representation of the variable, or None if not found or on error.
        """
        var = variable_name.strip().strip("\"'")
        result = self._run_sandbox(f"print(str({var}))")
        stdout = result.data.get("stdout", "") if isinstance(result.data, dict) else ""
        stderr = result.data.get("stderr", "") if isinstance(result.data, dict) else ""

        if stderr and not stdout:
            logging.warning(f"RLM: FINAL_VAR('{var}') error: {stderr.strip()}")
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
            logging.debug("RLM: could not retrieve llm_query credits from sandbox.")

    # Orchestrator

    def _orchestrator_completion(self, messages: List[Dict[str, str]]) -> str:
        """Query the orchestrator model with the full conversation history.

        Serializes the message list to a formatted prompt string and calls
        ``orchestrator.run()``.

        Args:
            messages: Full conversation history as role/content dicts.

        Returns:
            The orchestrator's text response.

        Raises:
            RuntimeError: If the orchestrator model call fails.
        """
        # TODO: If orchestrator supports a native chat/messages API, pass
        #       messages directly instead of serializing to a flat string, e.g.:
        #   if isinstance(self.orchestrator, LLM):
        #       response = self.orchestrator.run(data={"messages": messages})
        prompt = _messages_to_prompt(messages)
        response = self.orchestrator.run(data=prompt, max_tokens=8192)
        self._used_credits += float(getattr(response, "used_credits", 0) or 0)
        if response.get("completed") or response["status"] == ResponseStatus.SUCCESS:
            return str(response["data"])
        raise RuntimeError(f"Orchestrator model failed: {response.get('error_message', 'Unknown error')}")

    # Parallel Mode

    def _worker_call(self, prompt: str) -> str:
        """Call the worker model once and return its text output.

        Thread-safe credit accumulation so this can run inside a
        ``ThreadPoolExecutor`` from the parallel map step.
        """
        response = self.worker.run(data=prompt, max_tokens=_RESERVED_OUTPUT_TOKENS, temperature=0)
        credits = float(getattr(response, "used_credits", 0) or 0)
        with self._credits_lock:
            self._used_credits += credits
        if response.get("completed") or response["status"] == ResponseStatus.SUCCESS:
            return str(response["data"])
        raise RuntimeError(f"Worker model failed: {response.get('error_message', 'Unknown error')}")

    @staticmethod
    def _resolve_url_context(context: Union[str, dict, list]) -> Union[str, dict, list]:
        """If `context` is an HTTP/HTTPS URL, fetch it locally and return parsed content.

        Parallel mode skips the sandbox, so URL contexts have to be resolved
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
                except Exception as e:
                    logging.warning(f"RLM parallel: chunk {i} failed: {e}")
                    answers[i] = f"[Error analyzing this part: {e}]"

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

    def _run_parallel(
        self,
        context: Union[str, dict, list],
        query: str,
        name: Text,
        start_time: float,
    ) -> ModelResponse:
        """Deterministic chunk → parallel map → reduce. No orchestrator, no sandbox."""
        iterations_used = 0
        try:
            context = self._resolve_url_context(context)

            worker_tokens = self._get_worker_context_tokens()
            budget_chars = _compute_chunk_budget_chars(worker_tokens)
            chunks = _chunk_context(context, budget_chars)
            n_chunks = len(chunks)
            logging.info(
                f"RLM '{name}' parallel: {n_chunks} chunk(s), ~{budget_chars} chars/chunk "
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
        except Exception as e:
            error_msg = f"RLM parallel error: {str(e)}"
            logging.error(error_msg)
            return ModelResponse(
                status=ResponseStatus.FAILED,
                completed=True,
                error_message=error_msg,
                run_time=time.time() - start_time,
                used_credits=self._used_credits,
                iterations_used=iterations_used,
            )

        run_time = time.time() - start_time
        logging.info(f"RLM '{name}' parallel: done in {run_time:.1f}s ({iterations_used} worker calls).")
        return ModelResponse(
            status=ResponseStatus.SUCCESS,
            data=final_answer,
            completed=True,
            run_time=run_time,
            used_credits=self._used_credits,
            iterations_used=iterations_used,
        )

    # RAG Mode (aIR-backed retrieval)

    @staticmethod
    def _parse_rag_search_response(response) -> List[Dict]:
        """Normalize an aIR search response into a list of ``{text, position, score}``.

        The aIR payload shape isn't strictly typed, so this handles common
        variations: ``response.data`` may be a list of records, a dict with a
        ``results``/``documents``/``matches`` key, or a JSON string.
        """
        data = getattr(response, "data", response)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return []
        if isinstance(data, dict):
            for key in ("results", "documents", "records", "matches", "data"):
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
        if not isinstance(data, list):
            return []

        out: List[Dict] = []
        for r in data:
            if not isinstance(r, dict):
                continue
            text = r.get("text") or r.get("data") or r.get("value") or ""
            meta = r.get("metadata") or r.get("attributes") or {}
            position = meta.get("position", 0) if isinstance(meta, dict) else 0
            try:
                position = int(position)
            except (ValueError, TypeError):
                position = 0
            out.append({"text": str(text), "position": position, "score": r.get("score", 0)})
        return out

    def _run_rag(self, context, query: str, name: Text, start_time: float) -> ModelResponse:
        """RAG path: chunk → upsert to aIR → retrieve top-k → single worker call.

        If ``self.rag_index_id`` is set, reuse that pre-built index and skip
        create/upsert/delete entirely (just retrieve + synthesize). Otherwise
        an ephemeral index is created for this run and deleted in ``finally``.
        """
        # Lazy imports to avoid pulling index machinery unless RAG mode is used.
        from aixplain.factories.index_factory import IndexFactory
        from aixplain.factories.index_factory.utils import AirParams
        from aixplain.factories import ModelFactory
        from aixplain.modules.model.record import Record

        iterations_used = 0
        ephemeral_index = None
        try:
            # Size chunks so that the top_k retrieved chunks together fit
            # comfortably in the synthesis call (assembly_fraction × window),
            # but never exceed the embedding model's input limit.
            worker_tokens = self._get_worker_context_tokens()
            top_k = max(self.rag_top_k, 1)
            assembly_budget = int(worker_tokens * _RAG_ASSEMBLY_FRACTION * _CHARS_PER_TOKEN / top_k)
            rag_budget = min(assembly_budget, self.rag_max_chunk_chars)
            rag_budget = max(rag_budget, _RAG_MIN_CHUNK_CHARS)
            chunks = _chunk_context(context, rag_budget)
            n_chunks = len(chunks)
            bound_by = "embedding cap" if rag_budget < assembly_budget else "assembly budget"
            logging.info(
                f"RLM '{name}' rag: {n_chunks} chunk(s), ~{rag_budget} chars/chunk "
                f"(worker={worker_tokens} tokens, top_k={top_k}, bound by {bound_by})."
            )

            # Resolve or create the index.
            if self.rag_index_id:
                index = ModelFactory.get(self.rag_index_id, api_key=self.api_key)
                logging.info(f"RLM '{name}' rag: using existing index id={self.rag_index_id!r}.")
            else:
                index = IndexFactory.create(
                    params=AirParams(
                        name=f"RLM-rag-{uuid.uuid4().hex[:8]}",
                        description="Ephemeral aIR index for an RLM rag-mode run.",
                    )
                )
                ephemeral_index = index
                logging.info(f"RLM '{name}' rag: created ephemeral index (id={index.id}).")

                records = [
                    Record(
                        value=chunks[i],
                        id=f"chunk_{i}",
                        attributes={"position": i},
                    )
                    for i in range(n_chunks)
                ]
                upsert_resp = index.upsert(records)
                self._used_credits += float(getattr(upsert_resp, "used_credits", 0) or 0)
                logging.debug(f"RLM '{name}' rag: upserted {n_chunks} chunks.")

            # Retrieve. Clamp top_k to available chunks so we never ask for more.
            top_k = min(top_k, max(n_chunks, 1))
            search_resp = index.search(query=query, top_k=top_k)
            self._used_credits += float(getattr(search_resp, "used_credits", 0) or 0)

            retrieved = self._parse_rag_search_response(search_resp)
            logging.info(f"RLM '{name}' rag: retrieved {len(retrieved)} chunk(s) (top_k={top_k}).")

            if not retrieved:
                final_answer = "No information relevant to the query was found in the document."
            else:
                retrieved.sort(key=lambda x: x["position"])
                formatted = "\n\n---\n\n".join(r["text"] for r in retrieved)
                prompt = _RAG_SYNTHESIS_PROMPT.format(query=query, chunks=formatted)
                final_answer = self._worker_call(prompt)

            iterations_used = 1
        except Exception as e:
            error_msg = f"RLM rag error: {str(e)}"
            logging.error(error_msg)
            return ModelResponse(
                status=ResponseStatus.FAILED,
                completed=True,
                error_message=error_msg,
                run_time=time.time() - start_time,
                used_credits=self._used_credits,
                iterations_used=iterations_used,
            )
        finally:
            if ephemeral_index is not None:
                try:
                    ephemeral_index.delete()
                    logging.debug(f"RLM '{name}' rag: deleted ephemeral index.")
                except Exception as exc:
                    logging.warning(f"RLM '{name}' rag: failed to delete ephemeral index: {exc}")

        run_time = time.time() - start_time
        logging.info(f"RLM '{name}' rag: done in {run_time:.1f}s.")
        return ModelResponse(
            status=ResponseStatus.SUCCESS,
            data=final_answer,
            completed=True,
            run_time=run_time,
            used_credits=self._used_credits,
            iterations_used=iterations_used,
        )

    # Core Orchestration Loop

    def run(
        self,
        data: Union[Text, Dict],
        name: Text = "rlm_process",
        timeout: float = 600,
        parameters: Optional[Dict] = None,
        wait_time: float = 0.5,
        stream: bool = False,
        mode: Text = "auto",
    ) -> ModelResponse:
        """Run the RLM over a (potentially large) context, dispatching by mode.

        ``mode`` selects the execution strategy:

        - ``"parallel"``: deterministic chunk + parallel worker calls + reduce.
          Cheap, fast, predictable. No orchestrator or sandbox needed. Best for
          summarize/extract queries. Chunks are sized to a comfortable fraction
          of the worker's window to mitigate context rot.
        - ``"rag"``: chunk + upsert to an aIR vector index + top-k retrieve +
          single worker synthesis. If ``self.rag_index_id`` is set, the index
          is reused (cheapest path); otherwise a temporary index is created
          and deleted per run. Best for needle-in-haystack queries on very
          large reusable contexts.
        - ``"recursive"``: the iterative REPL loop where the orchestrator drives
          chunking and analysis in a sandbox. Expensive but adaptive. Best for
          multi-hop reasoning that needs to compare information across chunks.
        - ``"auto"`` (default): picks ``"recursive"`` when the query reads like
          multi-hop reasoning (keywords such as "compare across",
          "inconsistencies", "verify against", "step by step"); otherwise
          ``"parallel"``. ``"rag"`` is opt-in only.

        Args:
            data (Union[Text, Dict]): Input data. Accepted formats:

                - ``str`` (raw text): Treated directly as the context content;
                  a default query is used.
                - ``str`` (HTTP/HTTPS URL): Content is downloaded automatically.
                  ``.json`` URLs or ``application/json`` responses are parsed into
                  a dict/list; all other content is decoded as plain text.
                - ``str`` (file path): If the string points to an existing file,
                  the file is read automatically. ``.json`` files are parsed into
                  a dict/list; all other text formats are read as a plain string.
                - ``pathlib.Path``: Resolved and read exactly like a file-path string.
                - ``dict``: Must contain ``"context"`` (required) and optionally
                  ``"query"`` (defaults to a generic analysis prompt). The value
                  of ``"context"`` itself may also be a URL, a file path, or a
                  ``pathlib.Path`` — it will be resolved the same way.

            name (Text, optional): Identifier used in log messages.
                Defaults to ``"rlm_process"``.
            timeout (float, optional): Maximum total wall-clock time in seconds.
                Applies to ``"recursive"`` mode only. Defaults to 600.
            parameters (Optional[Dict], optional): Reserved for future use.
            wait_time (float, optional): Kept for API compatibility. Unused.
            stream (bool, optional): Unsupported. Must be False.
            mode (Text, optional): ``"auto"``, ``"parallel"``, or
                ``"recursive"``. Defaults to ``"auto"``.

        Returns:
            ModelResponse: Standard response with:

                - ``data``: The final answer string.
                - ``completed``: True on success.
                - ``run_time``: Total elapsed seconds.
                - ``used_credits``: Total credits consumed across all model calls.
                - ``iterations_used``: Recursive mode → orchestrator iterations.
                  Parallel mode → worker calls made in the map step
                  (i.e. number of chunks), or 1 for the single-call fast path.

        Raises:
            AssertionError: If ``worker`` is not set, ``stream=True``, or
                ``mode`` is invalid. ``recursive`` mode additionally requires
                ``orchestrator`` to be set.
            ValueError: If ``data`` is a dict missing the ``"context"`` key,
                or an unsupported type.
        """
        assert self.worker is not None, (
            "RLM requires a worker model. Set rlm.worker or pass worker= to ModelFactory.create_rlm()."
        )
        assert not stream, "RLM does not support streaming responses."
        assert mode in ("auto", "parallel", "recursive", "rag"), (
            f"Invalid mode: {mode!r}. Choose 'auto', 'parallel', 'recursive', or 'rag'."
        )

        # Parse data argument
        # pathlib.Path is treated as a file-path context with the default query
        if isinstance(data, pathlib.Path):
            data = str(data)

        if isinstance(data, str):
            context = data
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

        # Resolve mode before context normalization so 'auto' can dispatch
        # without paying any setup cost.
        if mode == "auto":
            mode = _select_mode(query)
            logging.info(f"RLM '{name}': auto-selected mode={mode!r}.")

        logging.info(f"RLM '{name}': starting (mode={mode}). Query: {query[:120]!r}")
        start_time = time.time()
        self._used_credits = 0.0

        # Normalize context: resolve file paths and pathlib.Path objects
        context = self._resolve_context(context)

        if mode == "parallel":
            return self._run_parallel(context, query, name, start_time)

        if mode == "rag":
            return self._run_rag(context, query, name, start_time)

        # recursive
        assert self.orchestrator is not None, (
            "RLM 'recursive' mode requires an orchestrator model. "
            "Set rlm.orchestrator or pass orchestrator= to ModelFactory.create_rlm(), "
            "or use mode='parallel'."
        )
        return self._run_recursive(context, query, name, start_time, timeout)

    def _run_recursive(
        self,
        context: Union[str, dict, list],
        query: str,
        name: Text,
        start_time: float,
        timeout: float,
    ) -> ModelResponse:
        """Iterative REPL-loop path: orchestrator drives a sandbox session."""
        iterations_used = 0
        final_answer = None
        repl_logs: List[Dict] = []

        # Initialize sandbox and conversation
        self._setup_repl(context)
        self._messages = _build_system_messages(self._get_worker_context_window())

        try:
            for iteration in range(self.max_iterations):
                iterations_used = iteration + 1

                if (time.time() - start_time) > timeout:
                    logging.warning(f"RLM '{name}': timeout after {iteration} iterations — forcing final answer.")
                    break

                # Ask orchestrator for its next action
                response_text = self._orchestrator_completion(self._messages + [_next_action_message(query, iteration)])
                logging.debug(f"RLM '{name}' iter {iteration}: orchestrator responded.")

                # Execute repl code blocks if present
                code_blocks = _find_code_blocks(response_text)
                if code_blocks:
                    self._messages.append({"role": "assistant", "content": response_text})
                    for code in code_blocks:
                        output = self._execute_code(code)
                        repl_logs.append({"iteration": iteration, "code": code, "output": output})
                        logging.debug(
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
                        logging.warning(f"RLM '{name}': FINAL_VAR('{content}') not found in sandbox — continuing.")

            # Force a final answer if loop exhausted or timed out without one
            if final_answer is None:
                logging.info(f"RLM '{name}': requesting forced final answer after {iterations_used} iterations.")
                self._messages.append(_next_action_message(query, iterations_used, force_final=True))
                final_answer = self._orchestrator_completion(self._messages)

        except Exception as e:
            error_msg = f"RLM run error: {str(e)}"
            logging.error(error_msg)
            self._collect_llm_query_credits()
            return ModelResponse(
                status=ResponseStatus.FAILED,
                completed=True,
                error_message=error_msg,
                run_time=time.time() - start_time,
                used_credits=self._used_credits,
                iterations_used=iterations_used,
            )

        self._collect_llm_query_credits()
        run_time = time.time() - start_time
        logging.info(f"RLM '{name}': done in {iterations_used} iterations, {run_time:.1f}s.")

        return ModelResponse(
            status=ResponseStatus.SUCCESS,
            data=final_answer or "",
            completed=True,
            run_time=run_time,
            used_credits=self._used_credits,
            iterations_used=iterations_used,
        )

    def run_async(
        self,
        data: Union[Text, Dict],
        name: Text = "rlm_process",
        parameters: Optional[Dict] = None,
    ) -> ModelResponse:
        """Not supported for RLM.

        Raises:
            NotImplementedError: Always. Use ``run()`` instead.
        """
        raise NotImplementedError("RLM does not support async execution. Use run() instead.")

    def run_stream(self, data: Union[Text, Dict], parameters: Optional[Dict] = None):
        """Not supported for RLM.

        Raises:
            NotImplementedError: Always.
        """
        raise NotImplementedError("RLM does not support streaming responses.")

    @classmethod
    def from_dict(cls, data: Dict) -> "RLM":
        """Create an RLM instance from a dictionary representation.

        Reconstructs the RLM from a dict produced by ``to_dict()``. The
        orchestrator and worker models are fetched from the aiXplain platform
        using their stored IDs, so a valid API key and network access are
        required.

        Args:
            data (Dict): Dictionary as produced by ``to_dict()``, containing:
                - id: RLM instance identifier.
                - name: Display name.
                - description: Description string.
                - api_key: API key for authentication.
                - supplier: Supplier information.
                - orchestrator_model_id: ID of the orchestrator model.
                - worker_model_id: ID of the worker model.
                - max_iterations: Maximum orchestrator loop iterations.
                - additional_info: Extra metadata (optional).

        Returns:
            RLM: A fully configured RLM instance with orchestrator and worker
                models loaded, ready to call ``run()``.

        Raises:
            Exception: If either model ID cannot be fetched from the platform.
        """
        # Lazy import avoids circular: model_factory → rlm → model_factory
        from aixplain.factories.model_factory import ModelFactory

        api_key = data.get("api_key", config.TEAM_API_KEY)

        orchestrator_model_id = data.get("orchestrator_model_id")
        worker_model_id = data.get("worker_model_id")

        orchestrator = ModelFactory.get(orchestrator_model_id, api_key=api_key) if orchestrator_model_id else None
        worker = ModelFactory.get(worker_model_id, api_key=api_key) if worker_model_id else None

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "RLM"),
            description=data.get("description", ""),
            api_key=api_key,
            supplier=data.get("supplier", "aiXplain"),
            orchestrator=orchestrator,
            worker=worker,
            max_iterations=data.get("max_iterations", 10),
            **data.get("additional_info", {}),
        )

    def to_dict(self) -> Dict:
        """Convert the RLM instance to a dictionary representation.

        Extends the base ``Model.to_dict()`` with RLM-specific fields:
        orchestrator model ID, worker model ID, and max_iterations.
        The orchestrator and worker are stored as their model IDs (not full
        objects) so the dict is JSON-serializable and can be used to
        reconstruct the instance via ``ModelFactory.create_rlm()``.

        Returns:
            Dict: A dictionary containing all base model fields plus:
                - orchestrator_model_id: ID of the orchestrator model.
                - worker_model_id: ID of the worker model.
                - max_iterations: Maximum orchestrator loop iterations.
        """
        base = super().to_dict()
        base["orchestrator_model_id"] = self.orchestrator.id if self.orchestrator else None
        base["worker_model_id"] = self.worker.id if self.worker else None
        base["max_iterations"] = self.max_iterations
        return base

    def __repr__(self) -> str:
        """Return a string representation of this RLM instance."""
        orchestrator_name = self.orchestrator.name if self.orchestrator else "None"
        worker_name = self.worker.name if self.worker else "None"
        return (
            f"RLM("
            f"id={self.id!r}, "
            f"orchestrator={orchestrator_name!r}, "
            f"worker={worker_name!r}, "
            f"max_iterations={self.max_iterations}"
            f")"
        )
