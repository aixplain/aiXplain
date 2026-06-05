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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L148)

Result returned by :meth:`RLM.run`.

Extends the standard :class:`~aixplain.v2.resource.Result` with
RLM-specific fields.

**Attributes**:

- `iterations_used` - Number of orchestrator iterations consumed.
- `used_credits` - Total credits consumed across all orchestrator calls,
  sandbox executions, and worker ``llm_query()`` invocations.
- `repl_logs` - Per-iteration REPL execution log (excluded from
  serialization; present only on live instances).

### RLM Objects

```python
@dataclass_json

@dataclass(repr=False)
class RLM(BaseResource, ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L177)

Recursive Language Model — long-context analysis via an iterative REPL sandbox.

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

- `orchestrator_id` - Platform model ID of the orchestrator LLM.
- ``0 - Platform model ID of the worker LLM.
- ``1 - Maximum orchestrator loop iterations (default 10).
- ``2 - Maximum wall-clock seconds per ``run()`` call (default 600).

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L273)

Auto-assign a UUID when no id is provided.

#### run

```python
def run(data: Union[str, dict, pathlib.Path],
        name: str = "rlm_process",
        timeout: Optional[float] = None,
        **kwargs: Any) -> RLMResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L635)

Run the RLM orchestration loop over a (potentially large) context.

A fresh sandbox session is created for each call. The orchestrator is
called iteratively; each iteration it may execute ``repl`` code blocks in
the sandbox (outputs fed back into the conversation) and eventually declare
a final answer via ``FINAL(...)`` or ``FINAL_VAR(...)``.

**Arguments**:

- `data` - Input context. Accepted forms:
  
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
  
- ``1 - Identifier used in log messages. Defaults to ``&quot;rlm_process&quot;``.
- ``4 - Maximum wall-clock seconds. Overrides ``self.timeout`` when
  provided. Defaults to ``None`` (uses ``self.timeout``).
- ``1 - Ignored; kept for API compatibility.
  

**Returns**:

  :class:``2 with:
  
  - ``data``: Final answer string.
  - ``status``: ``&quot;SUCCESS&quot;`` or ``&quot;FAILED&quot;``.
  - ``completed``: ``True``.
  - ``used_credits``: Total credits consumed across all orchestrator
  calls, sandbox executions, and worker ``llm_query()`` invocations.
  - ``iterations_used``: Number of orchestrator iterations consumed.
  - ``repl_logs``: Per-iteration execution log (not serialized).
  

**Raises**:

- `data`3 - If ``orchestrator_id`` or ``worker_id`` are unset,
  or if the orchestrator model call fails.
- `data`8 - If ``data`` is a dict missing ``&quot;context&quot;``, or an
  unsupported type.

#### as\_tool

```python
def as_tool() -> ToolDict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L805)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L829)

Not supported — raises :exc:`NotImplementedError`.

#### run\_stream

```python
def run_stream(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L833)

Not supported — raises :exc:`NotImplementedError`.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/rlm.py#L839)

Return string representation of this RLM instance.

