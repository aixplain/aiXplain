---
sidebar_label: model
title: aixplain.v2.model
---

Model resource for v2 API.

### Message Objects

```python
@dataclass_json

@dataclass
class Message()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L36)

Message structure from the API response.

### Detail Objects

```python
@dataclass_json

@dataclass
class Detail()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L48)

Detail structure from the API response.

### Usage Objects

```python
@dataclass_json

@dataclass
class Usage()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L89)

Usage structure from the API response.

Token counts are nullable because some model providers (GPT-5.4, Claude,
Mistral Large) return ``&quot;NaN&quot;`` or ``null`` instead of integers.

### ModelResult Objects

```python
@dataclass_json

@dataclass
class ModelResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L112)

Result for model runs with specific fields from the backend response.

### StreamChunk Objects

```python
@dataclass
class StreamChunk()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L123)

A chunk of streamed response data.

**Attributes**:

- `status` - The current status of the streaming operation (IN_PROGRESS or SUCCESS)
- `data` - The content/token of this chunk
- `tool_calls` - Tool call deltas when stream uses OpenAI-style chunk format
- `usage` - Usage payload when provided in a stream chunk
- `finish_reason` - Completion reason for the current choice, when provided

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L140)

Ensure data remains a text chunk.

### ModelResponseStreamer Objects

```python
class ModelResponseStreamer(Iterator[StreamChunk])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L146)

A streamer for model responses that yields chunks as they arrive.

This class provides an iterator interface for streaming model responses.
It handles the conversion of Server-Sent Events (SSE) into StreamChunk objects
and manages the response status.

The streamer can be used directly in a for loop or as a context manager
for proper resource cleanup.

**Example**:

  &gt;&gt;&gt; model = aix.Model.get(&quot;69b7e5f1b2fe44704ab0e7d0&quot;)  # GPT-5.4
  &gt;&gt;&gt; for chunk in model.run(text=&quot;Explain LLMs&quot;, stream=True):
  ...     print(chunk.data, end=&quot;&quot;, flush=True)
  
  &gt;&gt;&gt; # With context manager for proper cleanup
  &gt;&gt;&gt; with model.run_stream(text=&quot;Hello&quot;) as stream:
  ...     for chunk in stream:
  ...         print(chunk.data, end=&quot;&quot;, flush=True)

#### \_\_init\_\_

```python
def __init__(response: "requests.Response")
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L167)

Initialize a new ModelResponseStreamer instance.

**Arguments**:

- `response` - A requests.Response object with streaming enabled

#### \_\_iter\_\_

```python
def __iter__() -> Iterator[StreamChunk]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L179)

Return the iterator for the ModelResponseStreamer.

#### \_\_next\_\_

```python
def __next__() -> StreamChunk
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L183)

Return the next chunk of the response.

**Returns**:

- `StreamChunk` - A StreamChunk object containing the next chunk of the response.
  

**Raises**:

- `StopIteration` - When the stream is complete

#### close

```python
def close() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L298)

Close the underlying response connection.

#### \_\_enter\_\_

```python
def __enter__() -> "ModelResponseStreamer"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L303)

Context manager entry.

#### \_\_exit\_\_

```python
def __exit__(exc_type, exc_val, exc_tb) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L307)

Context manager exit - ensures response is closed.

#### find\_supplier\_by\_id

```python
def find_supplier_by_id(supplier_id: Union[str, int]) -> Optional[Supplier]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L315)

Find supplier enum by ID.

#### find\_function\_by\_id

```python
def find_function_by_id(function_id: str) -> Optional[Function]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L324)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L348)

Common parameter structure from the API response.

### Version Objects

```python
@dataclass_json

@dataclass
class Version()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L364)

Version structure from the API response.

### Pricing Objects

```python
@dataclass_json

@dataclass
class Pricing()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L373)

Pricing structure from the API response.

### VendorInfo Objects

```python
@dataclass_json

@dataclass
class VendorInfo()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L383)

Supplier information structure from the API response.

### ModelSearchParams Objects

```python
class ModelSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L391)

Search parameters for model queries.

#### q

Search query parameter as per Swagger spec

#### host

Filter by host (e.g., &quot;openai&quot;, &quot;aiXplain&quot;)

#### developer

Filter by developer (e.g., &quot;OpenAI&quot;)

#### path

Filter by path prefix (e.g., &quot;openai/gpt-4&quot;)

### ModelRunParams Objects

```python
class ModelRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L407)

Parameters for running models.

**Attributes**:

- `stream` - If True, returns a ModelResponseStreamer for streaming responses.
  The model must support streaming (check supports_streaming attribute).

### Model Objects

```python
@dataclass_json

@dataclass(repr=False)
class Model(BaseResource, SearchResourceMixin[ModelSearchParams, "Model"],
            GetResourceMixin[BaseGetParams, "Model"],
            RunnableResourceMixin[ModelRunParams, ModelResult], ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L420)

Resource for models.

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L469)

Initialize dynamic attributes based on backend parameters.

#### get\_attribute

```python
def get_attribute(key: str, default: Any = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L476)

Return an attribute value from the backend attribute map.

#### actions

```python
@property
def actions() -> Actions
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L483)

Actions available on this model (always a single ``&quot;run&quot;`` action).

#### supports\_tool\_calling

```python
@property
def supports_tool_calling() -> Optional[bool]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L525)

Return whether this LLM supports tool calling, inferred from backend params.

#### supports\_structured\_output

```python
@property
def supports_structured_output() -> Optional[bool]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L540)

Return whether this LLM supports structured output, inferred from backend params.

#### is\_sync\_only

```python
@property
def is_sync_only() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L555)

Check if the model only supports synchronous execution.

**Returns**:

- `bool` - True if the model only supports synchronous execution

#### is\_async\_capable

```python
@property
def is_async_capable() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L566)

Check if the model supports asynchronous execution.

**Returns**:

- `bool` - True if the model supports asynchronous execution

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L576)

Handle bulk assignment to inputs.

#### build\_run\_payload

```python
def build_run_payload(**kwargs: Unpack[ModelRunParams]) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L585)

Build the JSON payload for a model execution request.

Strips SDK-only orchestration params (``timeout``, ``wait_time``,
``show_progress``, ``stream``) so they are never forwarded to the
backend API.

#### build\_run\_url

```python
def build_run_url(**kwargs: Unpack[ModelRunParams]) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L595)

Build the URL for running the model.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L600)

Mark the model as deleted by setting status to DELETED and calling parent method.

#### get

```python
@classmethod
def get(cls: type["Model"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Model"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L608)

Get a model by ID.

#### search

```python
@classmethod
def search(cls: type["Model"],
           query: Optional[str] = None,
           **kwargs: Unpack[ModelSearchParams]) -> Page["Model"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L617)

Search with optional query and filtering.

**Arguments**:

- `query` - Optional search query string
- `**kwargs` - Additional search parameters (functions, suppliers, etc.)
  

**Returns**:

  Page of items matching the search criteria

#### run

```python
def run(**kwargs: Unpack[ModelRunParams]) -> ModelResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L638)

Run the model with dynamic parameter validation and default handling.

This method routes the execution based on the model&#x27;s connection type:
- Sync models: Uses V2 endpoint directly (returns result immediately)
- Async models: Uses V2 endpoint and polls until completion

#### run\_async

```python
def run_async(**kwargs: Unpack[ModelRunParams]) -> ModelResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L680)

Run the model asynchronously.

This method routes the execution based on the model&#x27;s connection type:
- Sync models: Falls back to V1 endpoint (V2 doesn&#x27;t support async for sync models)
- Async models: Uses V2 endpoint directly (returns polling URL)

**Returns**:

- `ModelResult` - Result with polling URL for async models,
  or immediate result via V1 for sync-only models

#### run\_stream

```python
def run_stream(**kwargs: Unpack[ModelRunParams]) -> ModelResponseStreamer
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L776)

Run the model with streaming response.

This method executes the model and returns a streamer that yields response
chunks as they are generated. This is useful for real-time output display
or processing large responses incrementally.

**Arguments**:

- `**kwargs` - Model-specific parameters (same as run() without stream parameter)
  

**Returns**:

- `ModelResponseStreamer` - A streamer that yields StreamChunk objects. Can be
  iterated directly or used as a context manager.
  

**Raises**:

- `ValidationError` - If the model explicitly does not support streaming
  (supports_streaming is False)
- `ValueError` - If required parameters are missing or have invalid types
  

**Example**:

  &gt;&gt;&gt; model = aix.Model.get(&quot;69b7e5f1b2fe44704ab0e7d0&quot;)  # GPT-5.4
  &gt;&gt;&gt; with model.run_stream(text=&quot;Explain quantum computing&quot;) as stream:
  ...     for chunk in stream:
  ...         print(chunk.data, end=&quot;&quot;, flush=True)
  
  &gt;&gt;&gt; # Or without context manager
  &gt;&gt;&gt; for chunk in model.run_stream(text=&quot;Hello&quot;):
  ...     print(chunk.data, end=&quot;&quot;, flush=True)

#### as\_tool

```python
def as_tool() -> ToolDict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L909)

Serialize this model as a tool for agent creation.

This method converts the model into a dictionary format that can be used
as a tool when creating agents. The format matches what the agent factory
expects for model tools.

**Returns**:

- `dict` - A dictionary representing this model as a tool with the following structure:
  - id: The model&#x27;s ID
  - name: The model&#x27;s name
  - description: The model&#x27;s description
  - supplier: The supplier code
  - parameters: Current parameter values
  - function: The model&#x27;s function type
  - type: Always &quot;model&quot;
  - version: The model&#x27;s version
  - asset_id: The model&#x27;s ID (same as id)
  

**Example**:

  &gt;&gt;&gt; model = aix.Model.get(&quot;some-model-id&quot;)
  &gt;&gt;&gt; agent = aix.Agent(..., tools=[model.as_tool()])

#### get\_parameters

```python
def get_parameters() -> List[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L967)

Get current parameter values for this model.

**Returns**:

- `List[dict]` - List of parameter dictionaries with current values

