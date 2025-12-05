---
sidebar_label: integration
title: aixplain.v2.integration
---

### ActionInputsProxy Objects

```python
class ActionInputsProxy()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L15)

Proxy object that provides both dict-like and dot notation access to action input parameters.

This proxy dynamically fetches action input specifications from the container resource
when needed, allowing for runtime discovery and validation of action inputs.

#### \_\_contains\_\_

```python
def __contains__(key: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L103)

Check if input parameter exists: &#x27;channels&#x27; in inputs

#### update

```python
def update(**kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L142)

Update multiple inputs at once.

#### keys

```python
def keys()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L147)

Get input parameter codes.

#### values

```python
def values()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L152)

Get input parameter values.

#### items

```python
def items()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L157)

Get input parameter code-value pairs.

#### reset\_input

```python
def reset_input(input_code: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L166)

Reset an input parameter to its backend default value.

#### reset\_all\_inputs

```python
def reset_all_inputs()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L174)

Reset all input parameters to their backend default values.

### Input Objects

```python
@dataclass_json

@dataclass
class Input()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L186)

Input parameter for an action.

### Action Objects

```python
@dataclass_json

@dataclass(repr=False)
class Action()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L204)

Container for tool action information and inputs.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L222)

Return a string representation showing name and input parameters.

#### get\_inputs\_proxy

```python
def get_inputs_proxy(container) -> ActionInputsProxy
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L238)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L252)

Result for tool operations.

### IntegrationResult Objects

```python
@dataclass_json

@dataclass
class IntegrationResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L260)

Result for connection operations.

The backend returns the connection ID in data.id.

### IntegrationSearchParams Objects

```python
class IntegrationSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L269)

Parameters for listing integrations.

### ActionMixin Objects

```python
class ActionMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L275)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L311)

List available inputs for the integration.

#### actions

```python
@cached_property
def actions()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L331)

Get a proxy object that provides access to actions with their inputs.

This enables the syntax: mytool.actions[&#x27;ACTION_NAME&#x27;].channel = &#x27;value&#x27;

**Returns**:

- `ActionsProxy` - A proxy object for accessing actions and their inputs

#### set\_inputs

```python
def set_inputs(inputs_dict: Dict[str, Dict[str, Any]]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L341)

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

#### \_\_getitem\_\_

```python
def __getitem__(action_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L443)

Get an action with its inputs proxy: actions[&#x27;SLACK_SEND_MESSAGE&#x27;] or actions[&#x27;slack_send_message&#x27;]

Converts action name to lowercase for consistent lookup.

#### \_\_getattr\_\_

```python
def __getattr__(attr_name: str)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L463)

Get an action with its inputs proxy using attribute notation: actions.slack_send_message

Converts attribute name to lowercase for consistent lookup.

#### \_\_contains\_\_

```python
def __contains__(action_name: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L477)

Check if an action exists: &#x27;SLACK_SEND_MESSAGE&#x27; in actions

#### get\_available\_actions

```python
def get_available_actions() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L486)

Get a list of available action names.

#### refresh\_cache

```python
def refresh_cache()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L491)

Clear the actions cache to force re-fetching.

### Integration Objects

```python
class Integration(Model, ActionMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L497)

Resource for integrations.

Integrations are a subtype of models with Function.CONNECTOR.
All connection logic is centralized here.

#### auth\_schemes

```python
@property
def auth_schemes() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L512)

Get authentication schemes for integrations.

#### get\_auth\_inputs

```python
def get_auth_inputs(auth_scheme: Optional[str] = None) -> List[Dict[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L530)

Get authentication inputs for a specific auth scheme.

#### run

```python
def run(**kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L636)

Run the integration with validation.

#### connect

```python
def connect(**kwargs: Any) -> "Tool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L640)

Connect the integration.

#### handle\_run\_response

```python
def handle_run_response(response: dict, **kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L646)

Handle the response from the integration.

