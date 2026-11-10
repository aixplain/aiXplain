---
sidebar_label: model
title: aixplain.v2.model
---

`from aixplain import CompletionTokensDetails, Detail, Message, Model, ModelResponseStreamer, ModelResult, Parameter, Pricing, PromptTokensDetails, StreamChunk, Usage, VendorInfo, Version`


Model resource for v2 API.

### Message Objects

```python
@dataclass_json

@dataclass
class Message()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L87)

Message structure from the API response.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L101)

Canonicalize supplier-specific reasoning fields onto ``reasoning_content``.

### Detail Objects

```python
@dataclass_json

@dataclass
class Detail()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L110)

Detail structure from the API response.

### PromptTokensDetails Objects

```python
@dataclass_json

@dataclass
class PromptTokensDetails()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L151)

Breakdown of prompt token usage.

### CompletionTokensDetails Objects

```python
@dataclass_json

@dataclass
class CompletionTokensDetails()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L162)

Breakdown of completion token usage.

### Usage Objects

```python
@dataclass_json

@dataclass
class Usage()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L182)

Usage structure from the API response.

Token counts are nullable because some model providers (GPT-5.4, Claude,
Mistral Large) return ``"NaN"`` or ``null`` instead of integers. The
detail blocks are ``None`` when the model does not report them.

#### cached\_tokens

```python
@property
def cached_tokens() -> Optional[int]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L212)

Cached prompt tokens, or None when the model did not report them.

#### reasoning\_tokens

```python
@property
def reasoning_tokens() -> Optional[int]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L217)

Reasoning completion tokens, or None when the model did not report them.

### ModelResult Objects

```python
@dataclass_json

@dataclass
class ModelResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L240)

Result for model runs with specific fields from the backend response.

``details`` is typed ``Any`` rather than ``List[Detail]`` because non-LLM
models (utility / guardrail assets) return it as a dict; see
`_decode_details`.

### StreamChunk Objects

```python
@dataclass
class StreamChunk()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L256)

A chunk of streamed response data.

**Attributes**:

- `status` - The current status of the streaming operation (IN_PROGRESS,
  SUCCESS, or FAILED when the stream reported an error)
- `data` - The content/token of this chunk
- `reasoning_content` - Reasoning-model chain-of-thought text delta, when provided
- `tool_calls` - Tool call deltas when stream uses OpenAI-style chunk format
- `usage` - Usage payload when provided in a stream chunk
- `finish_reason` - Completion reason for the current choice, when provided
- `error_message` - The error reported by the stream, when status is FAILED

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L278)

Ensure data remains a text chunk.

### ModelResponseStreamer Objects

```python
class ModelResponseStreamer(Iterator[StreamChunk])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L355)

A streamer for model responses that yields chunks as they arrive.

This class provides an iterator interface for streaming model responses.
It handles the conversion of Server-Sent Events (SSE) into StreamChunk objects
and manages the response status.

A backend that answers a streaming request with a plain JSON document
instead of an SSE body (a model whose record omits ``supportsStreaming``
may simply not stream) is detected on the first ``next()`` and yielded as a
single complete ``StreamChunk`` with ``status=SUCCESS``, rather than being
fed line by line to the SSE parser — which used to surface the raw JSON
text as ``chunk.data`` and end at ``status=FAILED``.

``status`` only becomes ``SUCCESS`` once the stream terminates cleanly — a
``[DONE]`` marker, a terminal ``finish_reason`` or a terminal ``status``
envelope. An error event, or a stream cut before any of those, leaves
``status`` at ``FAILED``, so a truncated generation is never reported as a
complete one. Error events also yield a final ``StreamChunk`` with
``status=FAILED`` and ``error_message`` set, rather than raising, so
existing ``for chunk in stream`` loops keep working.

The streamer can be used directly in a for loop or as a context manager
for proper resource cleanup.

**Example**:

  
```python
>>> model = aix.Model.get("69b7e5f1b2fe44704ab0e7d0")  # GPT-5.4
>>> for chunk in model.run(text="Explain LLMs", stream=True):
...     print(chunk.data, end="", flush=True)

>>> # With context manager for proper cleanup
>>> with model.run_stream(text="Hello") as stream:
...     for chunk in stream:
...         print(chunk.data, end="", flush=True)
```
  
  

#### \_\_init\_\_

```python
def __init__(response: "requests.Response")
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L391)

Initialize a new ModelResponseStreamer instance.

**Arguments**:

- `response` - A requests.Response object with streaming enabled

#### \_\_iter\_\_

```python
def __iter__() -> Iterator[StreamChunk]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L408)

Return the iterator for the ModelResponseStreamer.

#### \_\_next\_\_

```python
def __next__() -> StreamChunk
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L476)

Return the next chunk of the response.

**Returns**:

- `StreamChunk` - A StreamChunk object containing the next chunk of the response.
  

**Raises**:

- `StopIteration` - When the stream is complete

#### close

```python
def close() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L637)

Close the underlying response connection.

#### \_\_enter\_\_

```python
def __enter__() -> "ModelResponseStreamer"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L642)

Context manager entry.

#### \_\_exit\_\_

```python
def __exit__(exc_type, exc_val, exc_tb) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L646)

Context manager exit - ensures response is closed.

#### find\_function\_by\_id

```python
def find_function_by_id(function_id: str) -> Optional[Function]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L674)

Find function enum by ID.

Handles both SDK-style identifiers (``TEXT_GENERATION``) and the
kebab-case identifiers returned by the backend API
(``text-generation``).

### Parameter Objects

```python
@dataclass_json

@dataclass
class Parameter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L698)

Common parameter structure from the API response.

### Version Objects

```python
@dataclass_json

@dataclass
class Version()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L714)

Version structure from the API response.

### Pricing Objects

```python
@dataclass_json

@dataclass
class Pricing()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L723)

Pricing structure from the API response.

### VendorInfo Objects

```python
@dataclass_json

@dataclass
class VendorInfo()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L733)

Supplier information structure from the API response.

### ModelSearchParams Objects

```python
class ModelSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L741)

Search parameters for model queries.

#### q

Search query parameter as per Swagger spec

#### host

Filter by host (e.g., "openai", "aiXplain")

#### developer

Filter by developer (e.g., "OpenAI")

#### path

Filter by path prefix (e.g., "openai/gpt-4")

### ModelRunParams Objects

```python
class ModelRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L757)

Parameters for running models.

**Attributes**:

- `stream` - If True, returns a ModelResponseStreamer for streaming responses.
  The model must support streaming (check supports_streaming attribute).
- `session_id` - Conversation this run belongs to, emitted as the
  ``x-session-id`` header so downstream services can correlate the call
  with the session that triggered it. Header-only — stripped from the
  model/action input payload and the run URL, exactly like
  ``identifier`` (→ ``x-user-id``). Omit it (or pass ``None``) to send
  no header.
- `agent_name` - Name of the agent making this call, emitted as the ``x-agent``
  header so downstream services can attribute it to the calling agent.
  In a team run this is whichever agent actually issued the call: the
  sub-agent for a delegated call, but the orchestrator's own name for a
  tool it calls directly — so consumers should not assume the value is
  always a sub-agent, nor always the team root. Header-only, on the same
  terms as ``session_id``, and must be ASCII (see ``_headers_for_run``).

### Model Objects

```python
@dataclass_json

@dataclass(repr=False)
class Model(BaseResource, SearchResourceMixin[ModelSearchParams, "Model"],
            GetResourceMixin[BaseGetParams, "Model"],
            RunnableResourceMixin[ModelRunParams, ModelResult], ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L785)

Resource for models.

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L834)

Initialize dynamic attributes based on backend parameters.

#### get\_attribute

```python
def get_attribute(key: str, default: Any = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L841)

Return an attribute value from the backend attribute map.

#### actions

```python
@property
def actions() -> Actions
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L848)

Actions available on this model (always a single ``"run"`` action).

#### supports\_tool\_calling

```python
@property
def supports_tool_calling() -> Optional[bool]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L890)

Return whether this LLM supports tool calling, inferred from backend params.

#### supports\_structured\_output

```python
@property
def supports_structured_output() -> Optional[bool]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L905)

Return whether this LLM supports structured output, inferred from backend params.

#### is\_sync\_only

```python
@property
def is_sync_only() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L920)

Check if the model only supports synchronous execution.

**Returns**:

- `bool` - True if the model only supports synchronous execution

#### is\_async\_capable

```python
@property
def is_async_capable() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L931)

Check if the model supports asynchronous execution.

**Returns**:

- `bool` - True if the model supports asynchronous execution

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L941)

Handle bulk assignment to inputs.

#### build\_run\_payload

```python
def build_run_payload(**kwargs: Unpack[ModelRunParams]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L970)

Build the JSON payload for a model execution request.

Strips SDK-only orchestration params (``timeout``, ``wait_time``,
``show_progress``, ``progress_*``, ``stream``, ``run_retries``,
``run_retry_wait``), the request-dispatch params (``api_key``,
``resource_path``) and the header-only run metadata (``identifier``,
``session_id``, ``agent_name``) so they are never forwarded to the
backend API.

#### build\_run\_url

```python
def build_run_url(**kwargs: Unpack[ModelRunParams]) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L983)

Build the URL for running the model.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L988)

Mark the model as deleted by setting status to DELETED and calling parent method.

#### get

```python
@classmethod
def get(cls: type["Model"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Model"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L996)

Get a model by ID.

#### search

```python
@classmethod
def search(cls: type["Model"],
           query: Optional[str] = None,
           **kwargs: Unpack[ModelSearchParams]) -> Page["Model"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L1005)

Search with optional query and filtering.

**Arguments**:

- `query` - Optional search query string
- `**kwargs` - Additional search parameters (functions, suppliers, etc.)
  

**Returns**:

  Page of items matching the search criteria

#### run

```python
def run(
    **kwargs: Unpack[ModelRunParams]
) -> Union[ModelResult, "ModelResponseStreamer"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L1026)

Run the model with dynamic parameter validation and default handling.

This method routes the execution based on the model's connection type:
- Sync models: Uses V2 endpoint directly (returns result immediately)
- Async models: Uses V2 endpoint and polls until completion

**Returns**:

  ModelResult, or a `ModelResponseStreamer` when ``stream=True``
  — the flag selects the streaming path rather than being silently
  dropped (BUG-1091). A model whose backend record omits
  ``supportsStreaming`` still takes the streaming path; if it answers
  with a complete JSON body instead of an SSE stream, the streamer
  yields that body as a single successful chunk.

#### run\_async

```python
def run_async(**kwargs: Unpack[ModelRunParams]) -> ModelResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L1089)

Run the model asynchronously.

This method routes the execution based on the model's connection type:
- Sync models: Falls back to V1 endpoint (V2 doesn't support async for sync models)
- Async models: Uses V2 endpoint directly (returns polling URL)

**Returns**:

- `ModelResult` - Result with polling URL for async models,
  or immediate result via V1 for sync-only models

#### run\_stream

```python
def run_stream(**kwargs: Unpack[ModelRunParams]) -> ModelResponseStreamer
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L1192)

Run the model with streaming response.

This method executes the model and returns a streamer that yields response
chunks as they are generated. This is useful for real-time output display
or processing large responses incrementally.

**Arguments**:

- `**kwargs` - Model-specific parameters (same as run() without stream parameter)
  

**Returns**:

- `ModelResponseStreamer` - A streamer that yields StreamChunk objects. Can be
  iterated directly or used as a context manager. When the model
  answers with a complete JSON body rather than an SSE stream —
  which a model whose record omits ``supportsStreaming`` may well
  do — the streamer yields that response as a single chunk.
  

**Raises**:

- `ValidationError` - If the model explicitly does not support streaming
  (supports_streaming is False)
- `ValueError` - If required parameters are missing or have invalid types
  

**Example**:

  
```python
>>> model = aix.Model.get("69b7e5f1b2fe44704ab0e7d0")  # GPT-5.4
>>> with model.run_stream(text="Explain quantum computing") as stream:
...     for chunk in stream:
...         print(chunk.data, end="", flush=True)

>>> # Or without context manager
>>> for chunk in model.run_stream(text="Hello"):
...     print(chunk.data, end="", flush=True)
```
  
  

#### as\_tool

```python
def as_tool() -> ToolDict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L1344)

Serialize this model as a tool for agent creation.

This method converts the model into a dictionary format that can be used
as a tool when creating agents. The format matches what the agent factory
expects for model tools.

**Returns**:

- `dict` - A dictionary representing this model as a tool with the following structure:
  - id: The model's ID
  - name: The model's name
  - description: The model's description
  - supplier: The supplier code
  - parameters: Current parameter values
  - function: The model's function type
  - type: Always "model"
  - version: The model's version
  - asset_id: The model's ID (same as id)
  

**Example**:

  
```python
>>> model = aix.Model.get("some-model-id")
>>> agent = aix.Agent(..., tools=[model.as_tool()])
```
  
  

#### get\_parameters

```python
def get_parameters() -> List[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L1402)

Get current parameter values for this model.

**Returns**:

- `List[dict]` - List of parameter dictionaries with current values

