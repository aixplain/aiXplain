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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L27)

Message structure from the API response.

### Detail Objects

```python
@dataclass_json

@dataclass
class Detail()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L38)

Detail structure from the API response.

### Usage Objects

```python
@dataclass_json

@dataclass
class Usage()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L49)

Usage structure from the API response.

### ModelResult Objects

```python
@dataclass_json

@dataclass
class ModelResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L59)

Result for model runs with specific fields from the backend response.

### InputsProxy Objects

```python
class InputsProxy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L68)

Proxy object that provides both dict-like and dot notation access to model parameters.

#### \_\_init\_\_

```python
def __init__(model)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L71)

Initialize InputsProxy with a model instance.

#### \_\_getitem\_\_

```python
def __getitem__(key: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L98)

Dict-like access: inputs[&#x27;temperature&#x27;].

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L104)

Dict-like assignment: inputs[&#x27;temperature&#x27;] = 0.7.

#### \_\_getattr\_\_

```python
def __getattr__(name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L121)

Dot notation access: inputs.temperature.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L127)

Dot notation assignment: inputs.temperature = 0.7.

#### \_\_contains\_\_

```python
def __contains__(key: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L146)

Check if parameter exists: &#x27;temperature&#x27; in inputs.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L150)

Number of parameters.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L154)

Iterate over parameter names.

#### keys

```python
def keys()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L158)

Get parameter names.

#### values

```python
def values()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L162)

Get parameter values.

#### items

```python
def items()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L166)

Get parameter name-value pairs.

#### get

```python
def get(key: str, default=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L170)

Get parameter value with default.

#### update

```python
def update(**kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L176)

Update multiple parameters at once.

#### clear

```python
def clear()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L184)

Reset all parameters to backend defaults.

#### copy

```python
def copy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L189)

Get a copy of current parameter values.

#### has\_parameter

```python
def has_parameter(param_name: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L193)

Check if a parameter exists.

#### get\_parameter\_names

```python
def get_parameter_names() -> list
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L197)

Get a list of all available parameter names.

#### get\_required\_parameters

```python
def get_required_parameters() -> list
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L201)

Get a list of required parameter names.

#### get\_parameter\_info

```python
def get_parameter_info(param_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L205)

Get information about a specific parameter.

#### get\_all\_parameters

```python
def get_all_parameters() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L211)

Get all current parameter values.

#### reset\_parameter

```python
def reset_parameter(param_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L215)

Reset a parameter to its backend default value.

#### reset\_all\_parameters

```python
def reset_all_parameters()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L226)

Reset all parameters to their backend default values.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L271)

Return string representation of InputsProxy.

#### find\_supplier\_by\_id

```python
def find_supplier_by_id(supplier_id: Union[str, int]) -> Optional[Supplier]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L277)

Find supplier enum by ID.

#### find\_function\_by\_id

```python
def find_function_by_id(function_id: str) -> Optional[Function]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L286)

Find function enum by ID.

### Attribute Objects

```python
@dataclass_json

@dataclass
class Attribute()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L296)

Common attribute structure from the API response.

### Parameter Objects

```python
@dataclass_json

@dataclass
class Parameter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L305)

Common parameter structure from the API response.

### Version Objects

```python
@dataclass_json

@dataclass
class Version()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L321)

Version structure from the API response.

### Pricing Objects

```python
@dataclass_json

@dataclass
class Pricing()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L330)

Pricing structure from the API response.

### VendorInfo Objects

```python
@dataclass_json

@dataclass
class VendorInfo()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L340)

Supplier information structure from the API response.

### ModelSearchParams Objects

```python
class ModelSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L348)

Search parameters for model queries.

#### q

Search query parameter as per Swagger spec

### ModelRunParams Objects

```python
class ModelRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L361)

Parameters for running models.

This class is intentionally empty to allow dynamic validation
based on each model&#x27;s specific parameters from the backend.

### Model Objects

```python
@dataclass_json

@dataclass(repr=False)
class Model(BaseResource, SearchResourceMixin[ModelSearchParams, "Model"],
            GetResourceMixin[BaseGetParams, "Model"],
            RunnableResourceMixin[ModelRunParams, ModelResult], ToolableMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L373)

Resource for models.

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L421)

Initialize dynamic attributes based on backend parameters.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L426)

Handle bulk assignment to inputs.

#### build\_run\_url

```python
def build_run_url(**kwargs: Unpack[ModelRunParams]) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L435)

Build the URL for running the model.

#### mark\_as\_deleted

```python
def mark_as_deleted() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L440)

Mark the model as deleted by setting status to DELETED and calling parent method.

#### get

```python
@classmethod
def get(cls: type["Model"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Model"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L448)

Get a model by ID.

#### search

```python
@classmethod
def search(cls: type["Model"],
           query: Optional[str] = None,
           **kwargs: Unpack[ModelSearchParams]) -> Page["Model"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L457)

Search models with optional query and filtering.

**Arguments**:

- `query` - Optional search query string
- `**kwargs` - Additional search parameters (functions, suppliers, etc.)
  

**Returns**:

  Page of models matching the search criteria

#### run

```python
def run(**kwargs: Unpack[ModelRunParams]) -> ModelResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L482)

Run the model with dynamic parameter validation and default handling.

#### as\_tool

```python
def as_tool() -> ToolDict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L568)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L626)

Get current parameter values for this model.

**Returns**:

- `List[dict]` - List of parameter dictionaries with current values

