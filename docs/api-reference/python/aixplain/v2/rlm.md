---
sidebar_label: rlm
title: aixplain.v2.rlm
---

`from aixplain import RLM, RLMResult`


RLM (Recursive Language Model) for aiXplain SDK v2.

Orchestrates long-context analysis via an iterative REPL sandbox. The
orchestrator model plans and writes Python code to chunk and explore a large
context; a worker model handles per-chunk analysis via ``llm_query()``.

``llm_query`` is credential-free inside the sandbox: the injected helper submits
prompts on stdout and the SDK answers them in-process, so no API key is ever
materialised in sandbox-executed source (BUG-936). SDK-generated setup code and
model-emitted code run in separate sandbox sessions, and both are torn down when
the run ends.

### RLMResult Objects

```python
@dataclass_json

@dataclass(repr=False)
class RLMResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L590)

Result returned by `RLM.run`.

Extends the standard `Result` with
RLM-specific fields.

**Attributes**:

- `iterations_used` - Number of orchestrator iterations consumed.
- `used_credits` - Total credits consumed across all orchestrator calls,
  sandbox executions, and worker ``llm_query()`` invocations.
- `repl_logs` - Per-iteration REPL execution log (excluded from
  serialization; present only on live instances).

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L613)

Render the base ``Result`` repr plus RLM-specific fields.

### RLM Objects

```python
@dataclass_json

@dataclass(repr=False)
class RLM(BaseResource, ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L627)

Recursive Language Model — long-context analysis with two execution modes.

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
environment. Each recursive ``run()`` call gets its own pair of isolated
sessions (fresh UUIDs): a **setup** session that only ever receives
SDK-generated code, and a **repl** session holding the context and every
block the orchestrator emits. Variables persist across REPL iterations
within a single run; both sessions are torn down in a ``finally`` when the
run ends, on the success and the failure path alike. Use RLM as a context
manager (``with aix.RLM(...) as rlm:``) or call `close` to force
teardown early.

No credential is ever placed inside the sandbox. ``llm_query`` submits its
prompts on stdout and the SDK answers them in-process, so code the
orchestrator writes — which is steered by the analysed context and must be
treated as untrusted — has nothing to steal.

RLM is a **local orchestrator** — it does not correspond to a platform
endpoint and is not saved via ``save()``. It is registered on the
`Aixplain` client exactly like other resources so
that credentials and URLs flow through ``self.context`` automatically.

**Example**:

  
```python
from aixplain import Aixplain

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
```
  
  

**Attributes**:

- `orchestrator_id` - Platform model ID of the orchestrator LLM.
- `worker_id` - Platform model ID of the worker LLM.
- `max_iterations` - Maximum orchestrator loop iterations (default 10). A
  batch of ``llm_query`` calls costs two iterations in recursive mode
  — one to submit the prompts and one to consume the answers.
- `timeout` - Maximum wall-clock seconds per ``run()`` call (default 600).

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L786)

Auto-assign a UUID when no id is provided.

Also initializes the thread-safe credit lock used by parallel mode's
concurrent worker calls. Stored as a plain instance attribute (not a
dataclass field) so it's not serialized.

#### close

```python
def close() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1227)

Tear down any live sandbox sessions. Idempotent; never raises.

Called automatically in a ``finally`` at the end of every recursive run
and on ``__exit__``. Safe to call directly, and safe to call twice.

#### \_\_enter\_\_

```python
def __enter__() -> "RLM"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1239)

Enter a context manager whose exit tears down sandbox sessions.

#### \_\_exit\_\_

```python
def __exit__(exc_type: Any, exc: Any, tb: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1243)

Tear down sandbox sessions on scope exit.

#### run

```python
def run(data: Union[str, dict, pathlib.Path],
        name: str = "rlm_process",
        timeout: Optional[float] = None,
        mode: str = "auto",
        **kwargs: Any) -> RLMResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1757)

Run the RLM over a (potentially large) context, dispatching by mode.

``mode`` selects the execution strategy:

- ``"parallel"``: deterministic chunk + parallel worker calls + reduce.
Cheap, fast, predictable. Only the worker is required — no orchestrator
or sandbox. Best for summarize/extract queries. Chunks are sized to
a comfortable fraction of the worker's window to mitigate context rot.
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

**Arguments**:

- `data` - Input context. Accepted forms:
  
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
  
- `name` - Identifier used in log messages. Defaults to ``"rlm_process"``.
- `timeout` - Maximum wall-clock seconds. Applies to ``"recursive"`` mode
  only. Overrides ``self.timeout`` when provided.
- `mode` - ``"auto"``, ``"parallel"``, or ``"recursive"``. Defaults to
  ``"auto"``.
- `**kwargs` - Ignored; kept for API compatibility.
  

**Returns**:

  `RLMResult` with:
  
  - ``data``: Final answer string.
  - ``status``: ``"SUCCESS"`` or ``"FAILED"``.
  - ``completed``: ``True``.
  - ``used_credits``: Total credits across all model calls.
  - ``iterations_used``: Recursive mode → orchestrator iterations.
  Parallel mode → worker calls in the map step (= number of
  chunks), or 1 for the single-call fast path.
  - ``repl_logs``: Per-iteration execution log (recursive mode only;
  empty for parallel). Not serialized.
  

**Raises**:

- `ResourceError` - If ``worker_id`` is unset, or ``recursive`` mode is
  used without ``orchestrator_id``, or a model call fails.
- `ValueError` - If ``data`` is a dict missing ``"context"``, ``mode``
  is invalid, or ``data`` is an unsupported type.

#### as\_tool

```python
def as_tool() -> ToolDict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1995)

Serialize this RLM as a tool for agent creation.

Allows an `Agent` to invoke the RLM as one of
its tools, passing a query (and optionally context) as the ``data``
argument.

**Returns**:

  `ToolDict` representing this RLM.

#### run\_async

```python
def run_async(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L2019)

Not supported — raises `NotImplementedError`.

#### run\_stream

```python
def run_stream(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L2023)

Not supported — raises `NotImplementedError`.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L2029)

Return string representation of this RLM instance.

