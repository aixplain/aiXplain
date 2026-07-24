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

### TriggerTypeSpec Objects

```python
@dataclass_json

@dataclass
class TriggerTypeSpec()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L95)

Backend spec for an available external trigger type (deserialization only).

### TriggerEventOption Objects

```python
class TriggerEventOption()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L106)

A selectable external event option (e.g. ``gmail.triggers[&quot;NEW_EMAIL&quot;]``).

Carries the event ``slug`` and its config schema. When sourced from a
*connected* tool it also carries ``connection_id`` (the tool id), which is
required to activate the trigger. Pass it to ``aix.Trigger(event=...)``.

#### \_\_init\_\_

```python
def __init__(slug: str,
             name: Optional[str] = None,
             description: Optional[str] = None,
             config: Optional[Any] = None,
             connection_id: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L114)

Initialize an event option.

#### configure

```python
def configure(**values: Any) -> "TriggerEventOption"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L130)

Set config values passed to the trigger on activation.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L135)

Return a concise representation.

### TriggerTypes Objects

```python
class TriggerTypes()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L141)

Browsable collection of :class:`TriggerEventOption` for an integration/tool.

Supports ``integration.triggers[&quot;NEW_EMAIL&quot;]`` (case-insensitive), iteration,
``in``, and ``len``.

#### \_\_init\_\_

```python
def __init__(specs: List[TriggerTypeSpec],
             connection_id: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L148)

Initialize from backend specs and an optional connection id.

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> TriggerEventOption
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L164)

Return the :class:`TriggerEventOption` for *key* (case-insensitive).

#### \_\_contains\_\_

```python
def __contains__(key: object) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L178)

Return whether *key* matches an available trigger event.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L182)

Iterate over available trigger event slugs.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L186)

Return the number of available trigger events.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L190)

Return ``TriggerTypes([&#x27;SLUG&#x27;, ...])``.

### ActionMixin Objects

```python
@dataclass
class ActionMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L196)

Mixin class providing action-related functionality for integrations and tools.

#### list\_actions

```python
def list_actions() -> List[ActionSpec]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L218)

List available actions for the integration.

**Returns**:

  List of :class:`ActionSpec` objects from the backend.

#### list\_inputs

```python
def list_inputs(*actions: str) -> List[ActionSpec]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L270)

List available inputs for the integration.

.. deprecated::
    Use ``tool.actions[&#x27;action_name&#x27;].inputs`` to discover and configure
    action inputs instead.

#### actions

```python
@cached_property
def actions() -> Actions
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L286)

Collection of actions with their inputs.

**Returns**:

  :class:`Actions` collection.  Access individual actions via
  ``tool.actions[&#x27;ACTION_NAME&#x27;]`` which returns an :class:`Action`
  whose ``.inputs`` property lazily fetches input specs.

#### list\_trigger\_types

```python
def list_trigger_types() -> List[TriggerTypeSpec]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L325)

List available external event trigger types for the integration/tool.

Uses the same model-execute mechanism as :meth:`list_actions`.

**Returns**:

  List of :class:`TriggerTypeSpec` objects from the backend.

#### triggers

```python
@cached_property
def triggers() -> TriggerTypes
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L350)

Browsable collection of external event options (like :attr:`actions`).

Pick an option and pass it to ``aix.Trigger(event=...)``. When accessed on
a *connected* tool, each option carries the connection id needed to
activate the trigger; on an unconnected integration it is discovery-only.

**Returns**:

  :class:`TriggerTypes` collection (e.g. ``gmail.triggers[&quot;NEW_EMAIL&quot;]``).

#### set\_inputs

```python
def set_inputs(inputs_dict: Dict[str, Dict[str, Any]]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L366)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L400)

Resource for integrations.

Integrations are a subtype of models with Function.CONNECTOR.
All connection logic is centralized here.

#### run

```python
def run(**kwargs: Any) -> IntegrationResult
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L425)

Run the integration with validation.

#### connect

```python
def connect(**kwargs: Any) -> "Tool"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L429)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/integration.py#L456)

Handle the response from the integration.

