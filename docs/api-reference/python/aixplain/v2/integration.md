---
sidebar_label: integration
title: aixplain.v2.integration
---

Integration module for managing external service integrations.

### ActionInputsProxy Objects

```python
class ActionInputsProxy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L17)

Proxy object that provides both dict-like and dot notation access to action input parameters.

This proxy dynamically fetches action input specifications from the container resource
when needed, allowing for runtime discovery and validation of action inputs.

#### \_\_init\_\_

```python
def __init__(container, action_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L24)

Initialize ActionInputsProxy with container and action name.

#### \_\_getitem\_\_

```python
def __getitem__(key: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L93)

Get input value by key.

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L97)

Set input value by key.

#### \_\_contains\_\_

```python
def __contains__(key: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L101)

Check if input parameter exists.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L109)

Return the number of input parameters.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L114)

Iterate over input parameter keys.

#### \_\_getattr\_\_

```python
def __getattr__(name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L120)

Get input value by attribute name.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L127)

Set input value by attribute name.

#### get

```python
def get(key: str, default=None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L138)

Get input value with optional default.

#### update

```python
def update(**kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L145)

Update multiple inputs at once.

#### keys

```python
def keys()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L150)

Get input parameter codes.

#### values

```python
def values()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L155)

Get input parameter values.

#### items

```python
def items()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L160)

Get input parameter code-value pairs.

#### reset\_input

```python
def reset_input(input_code: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L169)

Reset an input parameter to its backend default value.

#### reset\_all\_inputs

```python
def reset_all_inputs()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L175)

Reset all input parameters to their backend default values.

#### \_\_repr\_\_

```python
def __repr__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L180)

Return string representation of the proxy.

### Input Objects

```python
@dataclass_json

@dataclass
class Input()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L188)

Input parameter for an action.

### Action Objects

```python
@dataclass_json

@dataclass(repr=False)
class Action()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L206)

Container for tool action information and inputs.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L224)

Return a string representation showing name and input parameters.

#### get\_inputs\_proxy

```python
def get_inputs_proxy(container) -> ActionInputsProxy
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L240)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L254)

Result for tool operations.

### IntegrationResult Objects

```python
@dataclass_json

@dataclass
class IntegrationResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L263)

Result for connection operations.

The backend returns the connection ID in data.id.

### IntegrationSearchParams Objects

```python
class IntegrationSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L272)

Parameters for listing integrations.

### ActionMixin Objects

```python
class ActionMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L278)

Mixin class providing action-related functionality for integrations and tools.

#### list\_actions

```python
def list_actions() -> List[Action]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L284)

List available actions for the integration.

#### list\_inputs

```python
def list_inputs(*actions: str) -> List[Action]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L311)

List available inputs for the integration.

#### actions

```python
@cached_property
def actions()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L336)

Get a proxy object that provides access to actions with their inputs.

This enables the syntax: mytool.actions[&#x27;ACTION_NAME&#x27;].channel = &#x27;value&#x27;

**Returns**:

- `ActionsProxy` - A proxy object for accessing actions and their inputs

#### set\_inputs

```python
def set_inputs(inputs_dict: Dict[str, Dict[str, Any]]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L346)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L412)

Proxy object that provides access to actions with their inputs.

This enables the syntax: mytool.actions[&#x27;ACTION_NAME&#x27;].channel = &#x27;value&#x27;

#### \_\_init\_\_

```python
def __init__(container)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L418)

Initialize ActionsProxy with container resource.

#### \_\_getitem\_\_

```python
def __getitem__(action_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L446)

Get an action with its inputs proxy.

Converts action name to lowercase for consistent lookup.

#### \_\_getattr\_\_

```python
def __getattr__(attr_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L466)

Get an action with its inputs proxy using attribute notation.

Converts attribute name to lowercase for consistent lookup.

#### \_\_contains\_\_

```python
def __contains__(action_name: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L480)

Check if an action exists.

#### get\_available\_actions

```python
def get_available_actions() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L489)

Get a list of available action names.

#### refresh\_cache

```python
def refresh_cache()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L494)

Clear the actions cache to force re-fetching.

### Integration Objects

```python
class Integration(Model, ActionMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L500)

Resource for integrations.

Integrations are a subtype of models with Function.CONNECTOR.
All connection logic is centralized here.

#### run

```python
def run(**kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L526)

Run the integration with validation.

#### connect

```python
def connect(**kwargs: Any) -> "Tool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L530)

Connect the integration.

For OAuth-based integrations, the backend may return a redirect URL
that the user must visit to complete authentication before using the tool.

**Returns**:

- `Tool` - The created tool. If OAuth authentication is required,
  ``tool.redirect_url`` will contain the URL the user must visit.

#### handle\_run\_response

```python
def handle_run_response(response: dict, **kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L549)

Handle the response from the integration.

