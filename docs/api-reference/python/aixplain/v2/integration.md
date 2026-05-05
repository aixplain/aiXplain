---
sidebar_label: integration
title: aixplain.v2.integration
---

Integration module for managing external service integrations.

### ActionInputSpec Objects

```python
@dataclass_json

@dataclass
class ActionInputSpec()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L20)

Backend input-parameter specification for an action (deserialization only).

### ActionSpec Objects

```python
@dataclass_json

@dataclass(repr=False)
class ActionSpec()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L38)

Backend action specification (deserialization only).

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L56)

Return a concise representation of the action spec.

### ToolId Objects

```python
@dataclass_json

@dataclass
class ToolId()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L69)

Result for tool operations.

### IntegrationResult Objects

```python
@dataclass_json

@dataclass
class IntegrationResult(Result)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L78)

Result for connection operations.

The backend returns the connection ID in data.id.

### IntegrationSearchParams Objects

```python
class IntegrationSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L87)

Parameters for listing integrations.

### ActionMixin Objects

```python
@dataclass
class ActionMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L94)

Mixin class providing action-related functionality for integrations and tools.

#### list\_actions

```python
def list_actions() -> List[ActionSpec]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L116)

List available actions for the integration.

**Returns**:

  List of :class:`ActionSpec` objects from the backend.

#### list\_inputs

```python
def list_inputs(*actions: str) -> List[ActionSpec]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L168)

List available inputs for the integration.

.. deprecated::
    Use ``tool.actions[&#x27;action_name&#x27;].inputs`` to discover and configure
    action inputs instead.

#### actions

```python
@cached_property
def actions() -> Actions
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L184)

Collection of actions with their inputs.

**Returns**:

  :class:`Actions` collection.  Access individual actions via
  ``tool.actions[&#x27;ACTION_NAME&#x27;]`` which returns an :class:`Action`
  whose ``.inputs`` property lazily fetches input specs.

#### set\_inputs

```python
def set_inputs(inputs_dict: Dict[str, Dict[str, Any]]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L223)

Set multiple action inputs in bulk using a dictionary tree structure.

**Arguments**:

- `inputs_dict` - ``\{&quot;ACTION_NAME&quot;: \{&quot;input_param&quot;: &quot;value&quot;, ...}, ...}``
  

**Raises**:

- `ValueError` - If an action name is not found or invalid.
- `KeyError` - If an input parameter is not found for an action.

### Integration Objects

```python
@dataclass_json

@dataclass
class Integration(Model, ActionMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L257)

Resource for integrations.

Integrations are a subtype of models with Function.CONNECTOR.
All connection logic is centralized here.

#### run

```python
def run(**kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L282)

Run the integration with validation.

#### connect

```python
def connect(**kwargs: Any) -> "Tool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L286)

Connect the integration.

For OAuth-based integrations, the backend may return a redirect URL
that the user must visit to complete authentication before using the tool.

**Returns**:

- `Tool` - The created tool. If OAuth authentication is required,
  ``tool.redirect_url`` will contain the URL the user must visit.
  

**Raises**:

- `ValueError` - If the connection fails (e.g., name already exists).

#### handle\_run\_response

```python
def handle_run_response(response: dict, **kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L313)

Handle the response from the integration.

