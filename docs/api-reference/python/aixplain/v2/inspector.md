---
sidebar_label: inspector
title: aixplain.v2.inspector
---

Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

The public surface is intentionally tiny: construct an :class:`Inspector` with
plain strings for ``action`` / ``targets`` / ``severity`` and an ``aix.Metric``
(the universal judge) for ``metric``. No enums or config classes to import.

### \_ActionConfig Objects

```python
@dataclass
class _ActionConfig()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/inspector.py#L53)

Internal, normalized action policy.

Users never import or construct this — they pass ``action=&quot;abort&quot;`` (a string)
or ``action=\{&quot;type&quot;: &quot;rerun&quot;, &quot;max_retries&quot;: 2, &quot;on_exhaust&quot;: &quot;abort&quot;}`` (a
dict) and :meth:`coerce` builds this.

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
or a Python callable and :meth:`coerce` builds this. It serializes to the same
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

``&quot;function&quot;`` for callable judges, otherwise ``&quot;asset&quot;``.

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
- a ``dict`` in either snake_case or the backend&#x27;s camelCase.

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
:meth:`get` / :meth:`search`. Prebuilt guards are ordinary marketplace assets
under the ``guardrails`` :class:`~aixplain.v2.enums.Function`; retrieving one
returns a fully-configured ``Inspector`` whose ``metric`` points at the guard
model, so a fetched guard and a custom inspector are indistinguishable to the
agent.

Configuration is plain data — no enums or config classes to import:

- ``action``: a string (``&quot;continue&quot; | &quot;rerun&quot; | &quot;abort&quot; | &quot;edit&quot;``) or, when
you need retry parameters, a dict
``\{&quot;type&quot;: &quot;rerun&quot;, &quot;max_retries&quot;: 2, &quot;on_exhaust&quot;: &quot;abort&quot;}``.
- ``targets``: a list of strings (``&quot;input&quot; | &quot;steps&quot; | &quot;output&quot;`` or a
sub-agent name).
- ``severity``: a string (``&quot;low&quot; | &quot;medium&quot; | &quot;high&quot; | &quot;critical&quot;``).
- ``metric``: the universal judge — an ``aix.Metric``, an asset-id string, or
a Python callable. Required.
- ``editor``: required when ``action`` is ``&quot;edit&quot;``; same accepted types as
``metric``.

Example::

from aixplain import Aixplain

aix = Aixplain(api_key=&quot;&lt;KEY&gt;&quot;)

# A custom inspector judged by a Metric (the universal judge)
inspector = aix.Inspector(
name=&quot;grounded_output&quot;,
severity=&quot;high&quot;,
targets=[&quot;output&quot;],
action=&quot;abort&quot;,
metric=aix.Metric.create(
name=&quot;grounded&quot;,
llm_path=&quot;&lt;LLM_ID&gt;&quot;,
prompt_template=&quot;Abort if the answer is not grounded in the context.&quot;,
),
)

# Discover and retrieve prebuilt guards like any other asset
aix.Inspector.search(&quot;guard&quot;)
guard = aix.Inspector.get(&quot;aws/detect-prompt-attacks-guardrail/aws&quot;)
redactor = aix.Inspector.get(&quot;aws/sensitive-information-guardrail/aws&quot;)
redactor.targets = [&quot;output&quot;]            # config as an inspectable attribute

team = aix.Agent(name=&quot;team&quot;, agents=[...], inspectors=[guard, inspector])

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

The guard model becomes the inspector&#x27;s ``metric`` (``asset`` judge), and
sensible default ``action`` / ``targets`` are applied based on the guard&#x27;s
canonical path slug (see :data:``0). Unknown guards
fall back to a safe ``abort`` on ``input`` default, so future guards need
no SDK change.

**Arguments**:

- ``5 - The guard-model dict returned by the marketplace.
- ``6 - The path/id the caller passed to :meth:``7, used to
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

- `id` - The guard&#x27;s marketplace path (e.g.
  ``&quot;aws/sensitive-information-guardrail/aws&quot;``) or its asset id.
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

- `query` - Optional free-text query (e.g. ``&quot;guard&quot;``).
- `**kwargs` - Additional pagination/search parameters.
  

**Returns**:

  A ``Page`` of configured Inspectors.

