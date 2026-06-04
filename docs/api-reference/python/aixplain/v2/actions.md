---
sidebar_label: actions
title: aixplain.v2.actions
---

Unified Actions / Inputs hierarchy for models and tools.

Object Hierarchy::

    Actions                    — collection of Action objects
      Action                   — metadata + owns its inputs
        Inputs                 — collection of Input objects
          Input                — individual input with schema + current value

Models have a single implicit &quot;run&quot; action. The ``model.inputs`` shorthand
skips the actions layer since there is nothing to disambiguate.

Tools have multiple actions, so the full path is always used.

### Input Objects

```python
class Input()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L25)

Individual input with schema and current value.

**Attributes**:

- `name` - The input parameter name.
- `required` - Whether this input is required.
- `type` - The data type (e.g. ``&quot;text&quot;``, ``&quot;number&quot;``, ``&quot;string&quot;``).
- `value` - The current value (mutable).
- `required`0 - Human-readable description.

#### \_\_init\_\_

```python
def __init__(name: str,
             required: bool = False,
             type: Optional[str] = None,
             value: Any = None,
             description: str = "",
             *,
             _validator: Optional[Callable[[Any], bool]] = None,
             _metadata: Optional[Any] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L36)

Initialize an Input with schema metadata and an optional validator.

#### name

```python
@property
def name() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L57)

The input parameter name.

#### required

```python
@property
def required() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L62)

Whether this input is required.

#### type

```python
@property
def type() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L67)

The data type string (e.g. ``&quot;text&quot;``, ``&quot;number&quot;``).

#### value

```python
@property
def value() -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L72)

The current value.

#### value

```python
@value.setter
def value(val: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L77)

Set the value, running the validator if one was provided.

#### description

```python
@property
def description() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L87)

Human-readable description of the input.

#### reset

```python
def reset(default: Any = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L91)

Reset the value to the given default (bypasses validation).

#### \_\_eq\_\_

```python
def __eq__(other: object) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L95)

Compare by value so ``inputs[&#x27;temperature&#x27;] == 0.7`` works.

#### \_\_hash\_\_

```python
def __hash__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L101)

Return an identity-based hash.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L105)

Return a developer-friendly representation.

#### from\_parameter

```python
@classmethod
def from_parameter(cls, param: "Parameter") -> "Input"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L122)

Build an ``Input`` from a model ``Parameter``.

#### from\_action\_input\_spec

```python
@classmethod
def from_action_input_spec(cls, spec: "ActionInputSpec") -> "Input"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L171)

Build an ``Input`` from a tool ``ActionInputSpec``.

### Inputs Objects

```python
class Inputs()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L215)

Ordered collection of :class:`Input` objects.

Supports dict-like access (``inputs[&quot;key&quot;]``, ``inputs[&quot;key&quot;] = val``)
and dot-notation (``inputs.key``, ``inputs.key = val``).

Iterating, ``.keys()``, ``.values()``, and ``.items()`` operate on
*raw values* so that ``dict(inputs.items())`` gives a plain ``\{name: value}``
mapping suitable for API payloads.

#### \_\_init\_\_

```python
def __init__(inputs: Optional[Dict[str, Input]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L226)

Initialize from an optional ordered dict of :class:`Input` objects.

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> Input
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L234)

Return the :class:`Input` for *key*.

#### \_\_setitem\_\_

```python
def __setitem__(key: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L241)

Set the *value* on the :class:`Input` identified by *key*.

#### \_\_contains\_\_

```python
def __contains__(key: object) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L249)

Return whether *key* is a known input name.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L254)

Return the number of inputs.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L259)

Iterate over input names.

#### \_\_getattr\_\_

```python
def __getattr__(name: str) -> Input
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L268)

Dot-notation read: ``inputs.temperature``.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L275)

Dot-notation write: ``inputs.temperature = 0.7``.

#### keys

```python
def keys() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L290)

Return input names.

#### values

```python
def values() -> List[Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L295)

Return raw values for all inputs.

#### items

```python
def items() -> List[tuple[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L300)

Return ``(name, value)`` pairs.

#### get

```python
def get(key: str, default: Any = None) -> Optional[Input]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L305)

Return the :class:`Input` for *key*, or *default*.

#### update

```python
def update(**kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L312)

Update multiple input values at once.

#### reset

```python
def reset(key: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L317)

Reset one or all inputs to their default values.

#### copy

```python
def copy() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L331)

Return a shallow copy of ``\{name: value}``.

#### validate

```python
def validate(data: Optional[Dict[str, Any]] = None) -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L335)

Validate *data* (or current values) against input specs.

Returns a list of error strings (empty means valid).

#### required

```python
@property
def required() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L355)

Names of all required inputs.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L364)

Return ``Inputs(\{&#x27;key&#x27;: value, ...})``.

#### from\_parameters

```python
@classmethod
def from_parameters(cls, params: Optional[list]) -> "Inputs"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L375)

Build from a list of model ``Parameter`` objects.

#### from\_action\_input\_specs

```python
@classmethod
def from_action_input_specs(cls, specs: Optional[list]) -> "Inputs"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L386)

Build from a list of tool ``ActionInputSpec`` objects.

### Action Objects

```python
class Action()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L397)

Metadata for a single action, owning its :class:`Inputs`.

For models the single action is always ``&quot;run&quot;``.
For tools there may be many (e.g. ``&quot;search_agents&quot;``, ``&quot;search_models&quot;``).

#### \_\_init\_\_

```python
def __init__(name: str,
             description: Optional[str] = None,
             *,
             inputs: Optional[Inputs] = None,
             _inputs_loader: Optional[Callable[[], Inputs]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L404)

Initialize an Action with name, description and optional lazy inputs.

#### name

```python
@property
def name() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L420)

The canonical action name.

#### description

```python
@property
def description() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L425)

Human-readable description of the action.

#### inputs

```python
@property
def inputs() -> Inputs
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L430)

The action&#x27;s :class:`Inputs` (lazily loaded for tool actions).

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L440)

Return a multi-line representation showing the action and its inputs.

### Actions Objects

```python
class Actions()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L470)

Ordered collection of :class:`Action` objects.

For models this contains a single ``&quot;run&quot;`` action.
For tools it lazily discovers actions from the backend.

#### \_\_init\_\_

```python
def __init__(
    actions: Optional[Dict[str, Action]] = None,
    *,
    _action_factory: Optional[Callable[[str, Optional[str]], Action]] = None,
    _actions_lister: Optional[Callable[[], List[tuple[str,
                                                      Optional[str]]]]] = None
) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L477)

Initialize with either an eager dict or lazy factory/lister callbacks.

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> Action
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L511)

Return the :class:`Action` for *key* (case-insensitive).

#### \_\_contains\_\_

```python
def __contains__(key: object) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L532)

Return whether *key* matches an available action name.

#### \_\_iter\_\_

```python
def __iter__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L540)

Iterate over available action names.

#### \_\_len\_\_

```python
def __len__() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L545)

Return the number of available actions.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L549)

Return ``Actions([&#x27;action1&#x27;, &#x27;action2&#x27;, ...])``.

#### refresh

```python
def refresh() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/actions.py#L555)

Clear caches and force re-fetch on next access.

