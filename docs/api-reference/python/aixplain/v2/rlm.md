---
sidebar_label: rlm
title: aixplain.v2.rlm
---

RLM (Recursive Language Model) for aiXplain SDK v2.

Orchestrates long-context analysis via an iterative REPL sandbox. The
orchestrator model plans and writes Python code to chunk and explore a large
context; a worker model handles per-chunk analysis via ``llm_query()`` calls
injected into the sandbox session.

### RLMResult Objects

```python
@dataclass_json

@dataclass(repr=False)
class RLMResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L372)

Result returned by :meth:`RLM.run`.

Extends the standard :class:`~aixplain.v2.resource.Result` with
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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L395)

Render the base ``Result`` repr plus RLM-specific fields.

### RLM Objects

```python
@dataclass_json

@dataclass(repr=False)
class RLM(BaseResource, ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L409)

Recursive Language Model — long-context analysis with two execution modes.

RLM wraps two aiXplain models:

- An **orchestrator** (powerful, expensive): plans and writes Python code to
explore the context iteratively in a managed sandbox environment.
Used by ``mode=&quot;recursive&quot;``.
- A **worker** (fast, cheap): called per chunk in both modes. In recursive
mode it&#x27;s invoked via ``llm_query()`` inside the sandbox; in parallel
mode it&#x27;s called directly, concurrently across chunks.

Three run modes are available via the ``mode`` argument to ``run()``:

- ``&quot;parallel&quot;`` (cheap, fast, deterministic): chunk the context to a
comfortable fraction of the worker&#x27;s window (to mitigate context rot),
call the worker in parallel on every chunk, then reduce the partial
answers into a final answer. No orchestrator, no sandbox. Best for
summarize/extract queries.
- ``&quot;rag&quot;`` (cheapest at query time): chunk the context into small
retrieval-grade pieces, upsert them into an aIR vector index, retrieve
the top-k most relevant chunks for the query, then make a single worker
call to synthesize an answer. The win is amortizing the upfront index
build across many queries: set ``rag_index_id`` to reuse a pre-built
index and skip create + upsert + delete on each call. Best for
needle-in-haystack questions on very large contexts.
- ``&quot;recursive&quot;`` (adaptive, expensive): the original iterative REPL loop
where the orchestrator drives chunking and analysis. Best for multi-hop
reasoning or queries that need to compare information across chunks.
- ``&quot;auto&quot;`` (default): picks ``&quot;recursive&quot;`` if the query reads like
multi-hop reasoning (e.g., contains words like &quot;compare across&quot;,
&quot;inconsistencies&quot;, &quot;verify against&quot;); otherwise ``&quot;parallel&quot;``.
``&quot;rag&quot;`` is opt-in only — auto never picks it because it only beats
``parallel`` when the index is reused across many calls.

The recursive mode&#x27;s sandbox is an aiXplain managed Python execution
environment. Each recursive ``run()`` call gets its own isolated session
(UUID), so variables persist across REPL iterations within a single run
but are cleaned up afterwards.

RLM is a **local orchestrator** — it does not correspond to a platform
endpoint and is not saved via ``save()``. It is registered on the
:class:``0 client exactly like other resources so
that credentials and URLs flow through ``self.context`` automatically.

Example::

from aixplain.v2 import Aixplain

aix = Aixplain(api_key=&quot;...&quot;)
rlm = aix.RLM(
orchestrator_id=&quot;&lt;orchestrator-model-id&gt;&quot;,
worker_id=&quot;&lt;worker-model-id&gt;&quot;,
)

result = rlm.run(data=\{
&quot;context&quot;: very_long_document,
&quot;query&quot;: &quot;What are the key findings?&quot;,
})
print(result.data)
print(f&quot;Completed in \{result.iterations_used} iteration(s).&quot;)

**Attributes**:

- ``3 - Platform model ID of the orchestrator LLM.
- ``4 - Platform model ID of the worker LLM.
- ``5 - Maximum orchestrator loop iterations (default 10).
- ``6 - Maximum wall-clock seconds per ``run()`` call (default 600).

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L544)

Auto-assign a UUID when no id is provided.

Also initializes the thread-safe credit lock used by parallel mode&#x27;s
concurrent worker calls. Stored as a plain instance attribute (not a
dataclass field) so it&#x27;s not serialized.

#### run

```python
def run(data: Union[str, dict, pathlib.Path],
        name: str = "rlm_process",
        timeout: Optional[float] = None,
        mode: str = "auto",
        **kwargs: Any) -> RLMResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1245)

Run the RLM over a (potentially large) context, dispatching by mode.

``mode`` selects the execution strategy:

- ``&quot;parallel&quot;``: deterministic chunk + parallel worker calls + reduce.
Cheap, fast, predictable. Only the worker is required — no orchestrator
or sandbox. Best for summarize/extract queries. Chunks are sized to
a comfortable fraction of the worker&#x27;s window to mitigate context rot.
- ``&quot;rag&quot;``: chunk + upsert to an aIR vector index + top-k retrieve +
single worker synthesis. If ``self.rag_index_id`` is set, the index
is reused (cheapest path); otherwise a temporary index is created
and deleted per run. Best for needle-in-haystack queries on very
large reusable contexts.
- ``&quot;recursive&quot;``: the iterative REPL loop where the orchestrator drives
chunking and analysis in a sandbox. Expensive but adaptive. Best for
multi-hop reasoning that needs to compare information across chunks.
- ``&quot;auto&quot;`` (default): picks ``&quot;recursive&quot;`` when the query reads like
multi-hop reasoning (keywords such as &quot;compare across&quot;,
&quot;inconsistencies&quot;, &quot;verify against&quot;, &quot;step by step&quot;); otherwise
``&quot;parallel&quot;``. ``&quot;rag&quot;`` is opt-in only.

**Arguments**:

- ``8 - Input context. Accepted forms:
  
  - ``str`` **raw text** — used directly as context; default query applied.
  - ``str`` **HTTP/HTTPS URL** — content is downloaded automatically;
  ``.json`` URLs or ``application/json`` responses are parsed into a
  dict/list, all other content decoded as plain text.
  - ``str`` **file path** — file is read automatically; ``.json`` files are
  parsed into a dict/list, all other formats read as plain text.
  - ``pathlib.Path`` — resolved and read like a file-path string.
  - ``dict`` — must contain ``&quot;context&quot;`` (required) and optionally
  ``&quot;query&quot;`` (defaults to a generic analysis prompt). The value
  of ``&quot;context&quot;`` itself may also be a URL, a file path, or a
  ``pathlib.Path``.
  
- ``3 - Identifier used in log messages. Defaults to ``&quot;rlm_process&quot;``.
- ``6 - Maximum wall-clock seconds. Applies to ``&quot;recursive&quot;`` mode
  only. Overrides ``self.timeout`` when provided.
- ``1 - ``&quot;auto&quot;``, ``&quot;parallel&quot;``, or ``&quot;recursive&quot;``. Defaults to
  ``&quot;auto&quot;``.
- ``0 - Ignored; kept for API compatibility.
  

**Returns**:

  :class:``1 with:
  
  - ``data``: Final answer string.
  - ``status``: ``&quot;SUCCESS&quot;`` or ``&quot;FAILED&quot;``.
  - ``completed``: ``True``.
  - ``used_credits``: Total credits across all model calls.
  - ``iterations_used``: Recursive mode → orchestrator iterations.
  Parallel mode → worker calls in the map step (= number of
  chunks), or 1 for the single-call fast path.
  - ``repl_logs``: Per-iteration execution log (recursive mode only;
  empty for parallel). Not serialized.
  

**Raises**:

- ``0 - If ``worker_id`` is unset, or ``recursive`` mode is
  used without ``orchestrator_id``, or a model call fails.
- ``7 - If ``data`` is a dict missing ``&quot;context&quot;``, ``mode``
  is invalid, or ``data`` is an unsupported type.

#### as\_tool

```python
def as_tool() -> ToolDict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1464)

Serialize this RLM as a tool for agent creation.

Allows an :class:`~aixplain.v2.agent.Agent` to invoke the RLM as one of
its tools, passing a query (and optionally context) as the ``data``
argument.

**Returns**:

  :class:`~aixplain.v2.mixins.ToolDict` representing this RLM.

#### run\_async

```python
def run_async(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1488)

Not supported — raises :exc:`NotImplementedError`.

#### run\_stream

```python
def run_stream(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1492)

Not supported — raises :exc:`NotImplementedError`.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L1498)

Return string representation of this RLM instance.

