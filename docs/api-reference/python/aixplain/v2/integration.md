---
sidebar_label: integration
title: aixplain.v2.integration
---

Integration module for managing external service integrations.

### ActionInputsProxy Objects

```python
class ActionInputsProxy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L16)

Proxy object that provides both dict-like and dot notation access to action input parameters.

This proxy dynamically fetches action input specifications from the container resource
when needed, allowing for runtime discovery and validation of action inputs.

#### \_\_init\_\_

```python
def __init__(container, action_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L23)

Initialize ActionInputsProxy with container and action name.

#### \_\_getitem\_\_

```python
def __getitem__(key: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L92)

Get input value by key.

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L96)

Set input value by key.

#### \_\_contains\_\_

```python
def __contains__(key: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L100)

Check if input parameter exists.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L108)

Return the number of input parameters.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L113)

Iterate over input parameter keys.

#### \_\_getattr\_\_

```python
def __getattr__(name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L119)

Get input value by attribute name.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L126)

Set input value by attribute name.

#### get

```python
def get(key: str, default=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L137)

Get input value with optional default.

#### update

```python
def update(**kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L144)

Update multiple inputs at once.

#### keys

```python
def keys()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L149)

Get input parameter codes.

#### values

```python
def values()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L154)

Get input parameter values.

#### items

```python
def items()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L159)

Get input parameter code-value pairs.

#### reset\_input

```python
def reset_input(input_code: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L168)

Reset an input parameter to its backend default value.

#### reset\_all\_inputs

```python
def reset_all_inputs()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L174)

Reset all input parameters to their backend default values.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L179)

Return string representation of the proxy.

### Input Objects

```python
@dataclass_json

@dataclass
class Input()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L187)

Input parameter for an action.

### Action Objects

```python
@dataclass_json

@dataclass(repr=False)
class Action()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L205)

Container for tool action information and inputs.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L223)

Return a string representation showing name and input parameters.

#### get\_inputs\_proxy

```python
def get_inputs_proxy(container) -> ActionInputsProxy
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L239)

Get an ActionInputsProxy for this action from a container.

**Arguments**:

- `container` - The container resource (Tool or Integration) that can fetch action specs
  

**Returns**:

- `ActionInputsProxy` - A proxy object for accessing action inputs

### ToolId Objects

```python
@dataclass_json

@dataclass
class ToolId()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L253)

Result for tool operations.

### IntegrationResult Objects

```python
@dataclass_json

@dataclass
class IntegrationResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L261)

Result for connection operations.

The backend returns the connection ID in data.id.

### IntegrationSearchParams Objects

```python
class IntegrationSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L270)

Parameters for listing integrations.

### ActionMixin Objects

```python
class ActionMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L276)

Mixin class providing action-related functionality for integrations and tools.

#### list\_actions

```python
def list_actions() -> List[Action]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L282)

List available actions for the integration.

#### list\_inputs

```python
def list_inputs(*actions: str) -> List[Action]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L309)

List available inputs for the integration.

#### actions

```python
@cached_property
def actions()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L334)

Get a proxy object that provides access to actions with their inputs.

This enables the syntax: mytool.actions[&#x27;ACTION_NAME&#x27;].channel = &#x27;value&#x27;

**Returns**:

- `ActionsProxy` - A proxy object for accessing actions and their inputs

#### set\_inputs

```python
def set_inputs(inputs_dict: Dict[str, Dict[str, Any]]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L344)

Set multiple action inputs in bulk using a dictionary tree structure.

This method allows you to set inputs for multiple actions at once.
Action names are automatically converted to lowercase for consistent lookup.

**Arguments**:

- `inputs_dict` - Dictionary in the format:
  \{
- `"ACTION_NAME"` - \{
- `"input_param1"` - &quot;value1&quot;,
- `"input_param2"` - &quot;value2&quot;,
  ...
  },
- `"ANOTHER_ACTION"` - \{
- `"input_param1"` - &quot;value1&quot;,
  ...
  }
  }
  

**Example**:

  tool.set_inputs(\{
- `'slack_send_message'` - \{  # Will work regardless of case
- `'channel'` - &#x27;`general`&#x27;,
- `'text'` - &#x27;Hello from bulk set!&#x27;,
- `"ACTION_NAME"`0 - &#x27;MyBot&#x27;
  },
- `"ACTION_NAME"`1 - \{  # Will also work
- `'channel'` - &#x27;`general`&#x27;,
- `'text'` - &#x27;Hello from bulk set!&#x27;,
- `"ACTION_NAME"`0 - &#x27;MyBot&#x27;
  },
- `"ACTION_NAME"`6 - \{  # Will also work
- `"ACTION_NAME"`7 - &#x27;`general`&#x27;,
- `"ACTION_NAME"`9 - &#x27;document.pdf&#x27;
  }
  })
  

**Raises**:

- `"input_param1"`0 - If an action name is not found or invalid
- `"input_param1"`1 - If an input parameter is not found for an action

### ActionsProxy Objects

```python
class ActionsProxy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L410)

Proxy object that provides access to actions with their inputs.

This enables the syntax: mytool.actions[&#x27;ACTION_NAME&#x27;].channel = &#x27;value&#x27;

#### \_\_init\_\_

```python
def __init__(container)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L416)

Initialize ActionsProxy with container resource.

#### \_\_getitem\_\_

```python
def __getitem__(action_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L444)

Get an action with its inputs proxy.

Converts action name to lowercase for consistent lookup.

#### \_\_getattr\_\_

```python
def __getattr__(attr_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L464)

Get an action with its inputs proxy using attribute notation.

Converts attribute name to lowercase for consistent lookup.

#### \_\_contains\_\_

```python
def __contains__(action_name: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L478)

Check if an action exists.

#### get\_available\_actions

```python
def get_available_actions() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L487)

Get a list of available action names.

#### refresh\_cache

```python
def refresh_cache()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L492)

Clear the actions cache to force re-fetching.

### Integration Objects

```python
class Integration(Model, ActionMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L498)

Resource for integrations.

Integrations are a subtype of models with Function.CONNECTOR.
All connection logic is centralized here.

#### run

```python
def run(**kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L524)

Run the integration with validation.

#### connect

```python
def connect(**kwargs: Any) -> "Tool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L528)

Connect the integration.

#### handle\_run\_response

```python
def handle_run_response(response: dict, **kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L534)

Handle the response from the integration.

