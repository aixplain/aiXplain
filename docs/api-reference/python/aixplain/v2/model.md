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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L35)

Message structure from the API response.

### Detail Objects

```python
@dataclass_json

@dataclass
class Detail()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L46)

Detail structure from the API response.

### Usage Objects

```python
@dataclass_json

@dataclass
class Usage()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L57)

Usage structure from the API response.

### ModelResult Objects

```python
@dataclass_json

@dataclass
class ModelResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L67)

Result for model runs with specific fields from the backend response.

### StreamChunk Objects

```python
@dataclass
class StreamChunk()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L77)

A chunk of streamed response data.

**Attributes**:

- `status` - The current status of the streaming operation (IN_PROGRESS or SUCCESS)
- `data` - The content/token of this chunk

### ModelResponseStreamer Objects

```python
class ModelResponseStreamer(Iterator[StreamChunk])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L89)

A streamer for model responses that yields chunks as they arrive.

This class provides an iterator interface for streaming model responses.
It handles the conversion of Server-Sent Events (SSE) into StreamChunk objects
and manages the response status.

The streamer can be used directly in a for loop or as a context manager
for proper resource cleanup.

**Example**:

  &gt;&gt;&gt; model = aix.Model.get(&quot;669a63646eb56306647e1091&quot;)  # GPT-4o Mini
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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L110)

Initialize a new ModelResponseStreamer instance.

**Arguments**:

- `response` - A requests.Response object with streaming enabled

#### \_\_iter\_\_

```python
def __iter__() -> Iterator[StreamChunk]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L121)

Return the iterator for the ModelResponseStreamer.

#### \_\_next\_\_

```python
def __next__() -> StreamChunk
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L125)

Return the next chunk of the response.

**Returns**:

- `StreamChunk` - A StreamChunk object containing the next chunk of the response.
  

**Raises**:

- `StopIteration` - When the stream is complete

#### close

```python
def close() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L176)

Close the underlying response connection.

#### \_\_enter\_\_

```python
def __enter__() -> "ModelResponseStreamer"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L181)

Context manager entry.

#### \_\_exit\_\_

```python
def __exit__(exc_type, exc_val, exc_tb) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L185)

Context manager exit - ensures response is closed.

### InputsProxy Objects

```python
class InputsProxy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L190)

Proxy object that provides both dict-like and dot notation access to model parameters.

#### \_\_init\_\_

```python
def __init__(model)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L193)

Initialize InputsProxy with a model instance.

#### \_\_getitem\_\_

```python
def __getitem__(key: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L220)

Dict-like access: inputs[&#x27;temperature&#x27;].

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L226)

Dict-like assignment: inputs[&#x27;temperature&#x27;] = 0.7.

#### \_\_getattr\_\_

```python
def __getattr__(name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L243)

Dot notation access: inputs.temperature.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L249)

Dot notation assignment: inputs.temperature = 0.7.

#### \_\_contains\_\_

```python
def __contains__(key: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L268)

Check if parameter exists: &#x27;temperature&#x27; in inputs.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L272)

Number of parameters.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L276)

Iterate over parameter names.

#### keys

```python
def keys()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L280)

Get parameter names.

#### values

```python
def values()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L284)

Get parameter values.

#### items

```python
def items()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L288)

Get parameter name-value pairs.

#### get

```python
def get(key: str, default=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L292)

Get parameter value with default.

#### update

```python
def update(**kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L298)

Update multiple parameters at once.

#### clear

```python
def clear()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L306)

Reset all parameters to backend defaults.

#### copy

```python
def copy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L311)

Get a copy of current parameter values.

#### has\_parameter

```python
def has_parameter(param_name: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L315)

Check if a parameter exists.

#### get\_parameter\_names

```python
def get_parameter_names() -> list
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L319)

Get a list of all available parameter names.

#### get\_required\_parameters

```python
def get_required_parameters() -> list
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L323)

Get a list of required parameter names.

#### get\_parameter\_info

```python
def get_parameter_info(param_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L327)

Get information about a specific parameter.

#### get\_all\_parameters

```python
def get_all_parameters() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L333)

Get all current parameter values.

#### reset\_parameter

```python
def reset_parameter(param_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L337)

Reset a parameter to its backend default value.

#### reset\_all\_parameters

```python
def reset_all_parameters()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L348)

Reset all parameters to their backend default values.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L393)

Return string representation of InputsProxy.

#### find\_supplier\_by\_id

```python
def find_supplier_by_id(supplier_id: Union[str, int]) -> Optional[Supplier]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L399)

Find supplier enum by ID.

#### find\_function\_by\_id

```python
def find_function_by_id(function_id: str) -> Optional[Function]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L408)

Find function enum by ID.

### Attribute Objects

```python
@dataclass_json

@dataclass
class Attribute()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L418)

Common attribute structure from the API response.

### Parameter Objects

```python
@dataclass_json

@dataclass
class Parameter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L428)

Common parameter structure from the API response.

### Version Objects

```python
@dataclass_json

@dataclass
class Version()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L444)

Version structure from the API response.

### Pricing Objects

```python
@dataclass_json

@dataclass
class Pricing()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L453)

Pricing structure from the API response.

### VendorInfo Objects

```python
@dataclass_json

@dataclass
class VendorInfo()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L463)

Supplier information structure from the API response.

### ModelSearchParams Objects

```python
class ModelSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L471)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L487)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L500)

Resource for models.

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L552)

Initialize dynamic attributes based on backend parameters.

#### is\_sync\_only

```python
@property
def is_sync_only() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L558)

Check if the model only supports synchronous execution.

**Returns**:

- `bool` - True if the model only supports synchronous execution

#### is\_async\_capable

```python
@property
def is_async_capable() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L569)

Check if the model supports asynchronous execution.

**Returns**:

- `bool` - True if the model supports asynchronous execution

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L579)

Handle bulk assignment to inputs.

#### build\_run\_url

```python
def build_run_url(**kwargs: Unpack[ModelRunParams]) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L588)

Build the URL for running the model.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L593)

Mark the model as deleted by setting status to DELETED and calling parent method.

#### get

```python
@classmethod
def get(cls: type["Model"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Model"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L601)

Get a model by ID.

#### search

```python
@classmethod
def search(cls: type["Model"],
           query: Optional[str] = None,
           **kwargs: Unpack[ModelSearchParams]) -> Page["Model"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L610)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L631)

Run the model with dynamic parameter validation and default handling.

This method routes the execution based on the model&#x27;s connection type:
- Sync models: Uses V2 endpoint directly (returns result immediately)
- Async models: Uses V2 endpoint and polls until completion

#### run\_async

```python
def run_async(**kwargs: Unpack[ModelRunParams]) -> ModelResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L672)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L768)

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
  

**Example**:

  &gt;&gt;&gt; model = aix.Model.get(&quot;669a63646eb56306647e1091&quot;)  # GPT-4o Mini
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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L898)

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
  - assetId: The model&#x27;s ID (same as id)
  

**Example**:

  &gt;&gt;&gt; model = aix.Model.get(&quot;some-model-id&quot;)
  &gt;&gt;&gt; agent = aix.Agent(..., tools=[model.as_tool()])

#### get\_parameters

```python
def get_parameters() -> List[dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L956)

Get current parameter values for this model.

**Returns**:

- `List[dict]` - List of parameter dictionaries with current values

