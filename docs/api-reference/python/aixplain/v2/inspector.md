---
sidebar_label: inspector
title: aixplain.v2.inspector
---

`from aixplain import AUTO_DEFAULT_MODEL_ID, Inspector`


Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

The public surface is intentionally tiny: construct an `Inspector` with
plain strings for ``action`` / ``targets`` / ``severity`` and an ``aix.Metric``
(the universal judge) for ``metric``. No enums or config classes to import.

### \_ActionConfig Objects

```python
@dataclass
class _ActionConfig()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L53)

Internal, normalized action policy.

Users never import or construct this — they pass ``action="abort"`` (a string)
or ``action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"}`` (a
dict) and `coerce` builds this.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L65)

Normalize/validate the action policy.

#### coerce

```python
@classmethod
def coerce(cls, value: Any) -> "_ActionConfig"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L85)

Build an action config from a string, dict, or existing config.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L99)

Convert the action config to a dictionary for API serialization.

### \_Judge Objects

```python
@dataclass
class _Judge()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L110)

Internal, normalized judge (evaluator or editor).

Users never import or construct this — they pass a Metric, an asset-id string,
or a Python callable and `coerce` builds this. It serializes to the same
backend shape the platform has always accepted (``type`` = ``asset`` |
``function``).

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L123)

Convert callable functions to source and validate the judge has a target.

#### type

```python
@property
def type() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L131)

``"function"`` for callable judges, otherwise ``"asset"``.

#### coerce

```python
@classmethod
def coerce(cls,
           value: Any,
           *,
           prompt: Optional[str] = None) -> Optional["_Judge"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L136)

Build a judge from a Metric, asset-id string, callable, dict, or judge.

Accepts:
- an ``aix.Metric`` (or any asset-backed object exposing ``id``) — the
  universal judge; its id and prompt flow into the evaluator payload;
- a plain asset-id ``str``;
- a Python ``callable`` (or its source) — a custom function judge;
- a ``dict`` in either snake_case or the backend's camelCase.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L172)

Convert to a dictionary for API serialization.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "_Judge"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L184)

Create a judge from a backend (or user) dict.

### Inspector Objects

```python
@dataclass(repr=False)
class Inspector(BaseResource, GetResourceMixin[BaseGetParams, "Inspector"],
                SearchResourceMixin[BaseSearchParams, "Inspector"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L275)

Inspector v2 configuration object.

An ``Inspector`` is the single type the ``aix.Agent(inspectors=[...])`` slot
accepts — whether it is hand-built or retrieved from the marketplace via
`get` / `search`. Prebuilt guards are ordinary marketplace assets
under the ``guardrails`` `Function`; retrieving one
returns a fully-configured ``Inspector`` whose ``metric`` points at the guard
model, so a fetched guard and a custom inspector are indistinguishable to the
agent.

Configuration is plain data — no enums or config classes to import:

- ``action``: a string (``"continue" | "rerun" | "abort" | "edit"``) or, when
you need retry parameters, a dict
``{"type": "rerun", "max_retries": 2, "on_exhaust": "abort"}``.
- ``targets``: a list of strings (``"input" | "steps" | "output"`` or a
sub-agent name).
- ``severity``: a string (``"low" | "medium" | "high" | "critical"``).
- ``metric``: the universal judge — an ``aix.Metric``, an asset-id string, or
a Python callable. Required.
- ``editor``: required when ``action`` is ``"edit"``; same accepted types as
``metric``.

**Example**:

  
```python
from aixplain import Aixplain

aix = Aixplain(api_key="<KEY>")

# A custom inspector judged by a Metric (the universal judge)
inspector = aix.Inspector(
    name="grounded_output",
    severity="high",
    targets=["output"],
    action="abort",
    metric=aix.Metric.create(
        name="grounded",
        llm_path="<LLM_ID>",
        prompt_template="Abort if the answer is not grounded in the context.",
    ),
)

# Discover and retrieve prebuilt guards like any other asset
aix.Inspector.search("guard")
guard = aix.Inspector.get("aws/detect-prompt-attacks-guardrail/aws")
redactor = aix.Inspector.get("aws/sensitive-information-guardrail/aws")
redactor.targets = ["output"]            # config as an inspectable attribute

team = aix.Agent(name="team", agents=[...], inspectors=[guard, inspector])
```
  
  

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L345)

Normalize and validate inspector configuration after initialization.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L368)

Convert the inspector to a dictionary for API serialization.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Inspector"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L388)

Create an Inspector from an inspector-shaped dictionary.

#### from\_guard\_model

```python
@classmethod
def from_guard_model(cls,
                     payload: Dict[str, Any],
                     requested_path: Optional[str] = None) -> "Inspector"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L409)

Adapt a ``guardrails`` marketplace model payload into a configured Inspector.

The guard model becomes the inspector's ``metric`` (``asset`` judge), and
sensible default ``action`` / ``targets`` are applied based on the guard's
canonical path slug (see `_GUARD_CONFIG_DEFAULTS`). Unknown guards
fall back to a safe ``abort`` on ``input`` default, so future guards need
no SDK change.

**Arguments**:

- `payload` - The guard-model dict returned by the marketplace.
- `requested_path` - The path/id the caller passed to `get`, used to
  resolve default config when the payload omits a path.
  

**Returns**:

  A fully-configured Inspector ready to attach to an agent.

#### get

```python
@classmethod
def get(cls, id: Any, **kwargs: Any) -> "Inspector"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L455)

Retrieve a prebuilt guard by human-readable path (IDs also accepted).

**Arguments**:

- `id` - The guard's marketplace path (e.g.
  ``"aws/sensitive-information-guardrail/aws"``) or its asset id.
- `**kwargs` - Additional request parameters (e.g. ``resource_path``)
  forwarded to the underlying client call.
  

**Returns**:

  A fully-configured Inspector backed by the guard model.

#### search

```python
@classmethod
def search(cls,
           query: Optional[str] = None,
           **kwargs: Any) -> Page["Inspector"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L481)

Search available guards, returning the standard paginated shape.

**Arguments**:

- `query` - Optional free-text query (e.g. ``"guard"``).
- `**kwargs` - Additional pagination/search parameters.
  

**Returns**:

  A ``Page`` of configured Inspectors.

