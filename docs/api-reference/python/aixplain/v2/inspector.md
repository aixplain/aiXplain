---
sidebar_label: inspector
title: aixplain.v2.inspector
---

Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

The public surface is intentionally tiny: construct an `Inspector` with plain
strings for `action` / `targets` / `severity` and an `aix.Metric` (the universal
judge) for `metric`. No enums or config classes to import.

### Inspector Objects

```python
@dataclass(repr=False)
class Inspector(BaseResource, GetResourceMixin, SearchResourceMixin)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py)

Inspector v2 configuration object.

An `Inspector` is the single type the `aix.Agent(inspectors=[...])` slot accepts —
whether it is hand-built or retrieved from the marketplace via `get` / `search`.
Prebuilt guards are ordinary marketplace assets under the `guardrails` function;
retrieving one returns a fully-configured `Inspector` whose `metric` points at the
guard model, so a fetched guard and a custom inspector are indistinguishable to the
agent.

Configuration is plain data — no enums or config classes to import:

- `action`: a string (`"continue" | "rerun" | "abort" | "edit"`) or, when you need
  retry parameters, a dict `{"type": "rerun", "max_retries": 2, "on_exhaust": "abort"}`.
- `targets`: a list of strings (`"input" | "steps" | "output"` or a sub-agent name).
- `severity`: a string (`"low" | "medium" | "high" | "critical"`).
- `metric`: the universal judge — an `aix.Metric`, an asset-id string, or a Python
  callable. Required.
- `editor`: required when `action` is `"edit"`; same accepted types as `metric`.

Example:

```python
from aixplain import Aixplain

aix = Aixplain(api_key="<KEY>")

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

team = aix.Agent(name="team", agents=[...], inspectors=[guard, inspector])
```

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

Convert the inspector to a dictionary for API serialization. The judge serializes
under the backend's long-standing `evaluator` key.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Inspector"
```

Create an Inspector from an inspector-shaped dictionary.

#### from\_guard\_model

```python
@classmethod
def from_guard_model(cls,
                     payload: Dict[str, Any],
                     requested_path: Optional[str] = None) -> "Inspector"
```

Adapt a `guardrails` marketplace model payload into a configured Inspector. The
guard model becomes the inspector's `metric` (`asset` judge), and sensible default
`action` / `targets` are applied based on the guard's canonical path slug. Unknown
guards fall back to a safe `abort` on `input` default, so future guards need no SDK
change.

#### get

```python
@classmethod
def get(cls, id: Any, **kwargs: Any) -> "Inspector"
```

Retrieve a prebuilt guard by human-readable path (IDs also accepted). Returns a
fully-configured Inspector backed by the guard model.

#### search

```python
@classmethod
def search(cls,
           query: Optional[str] = None,
           **kwargs: Any) -> Page["Inspector"]
```

Search available guards, returning the standard paginated shape.
