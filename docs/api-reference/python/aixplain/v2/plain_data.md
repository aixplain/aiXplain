---
sidebar_label: plain_data
title: aixplain.v2.plain_data
---

Coercion of plain dicts into the v2 config structs (PROD-2921).

The rule this module implements: anything a caller has to construct or pass in
accepts plain data, so calling code does not depend on the SDK's module layout.
Anything that only ever comes back from the SDK stays an object and is not
touched. The classification of every v2 enum and dataclass is recorded in
``docs/v2-plain-data.md``.

Each input struct pairs a dataclass with a ``TypedDict`` on the same field names.
The ``TypedDict`` is what a type checker flags a misspelled key against; this
module is what raises on one at runtime, naming the fields that *are* accepted.
Silently dropping an unknown key is the failure mode being removed: a misspelled
``max_iteration`` used to mean "no cap" rather than "you meant max_iterations".

#### struct\_fields

```python
def struct_fields(cls: type) -> Tuple[str, ...]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/plain_data.py#L24)

Return the user-facing field names of a config dataclass, in order.

Read off the dataclass rather than hardcoded, so a field added to the struct
is accepted -- and named in the error for an unknown key -- without a second
edit here.

**Arguments**:

- `cls` - The dataclass to inspect.
  

**Returns**:

  Tuple[str, ...]: Its field names, excluding private ones.

#### coerce\_struct

```python
def coerce_struct(value: Any,
                  cls: Type[T],
                  *,
                  label: str,
                  aliases: Optional[Mapping[str, str]] = None) -> Optional[T]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/plain_data.py#L40)

Coerce ``value`` into an instance of ``cls``, raising on unknown keys.

**Arguments**:

- `value` - ``None``, an instance of *cls* (returned unchanged), or a dict on
  *cls*'s field names.
- `cls` - The config dataclass to build.
- `label` - How to name the thing in an error message, e.g. ``"budget"``.
- `aliases` - Extra accepted keys mapped onto field names -- the wire
  spellings a backend response carries, so the same entry point decodes
  both what a caller writes and what the API sends back.
  

**Returns**:

- `Optional[T]` - The coerced instance, or ``None`` for ``None``.
  

**Raises**:

- `ValidationError` - If *value* is neither ``None``, an instance, nor a dict,
  if a dict carries a key that is neither a field nor an alias, or if
  it omits a field the struct requires.

#### coerce\_struct\_list

```python
def coerce_struct_list(value: Any,
                       cls: Type[T],
                       *,
                       label: str,
                       aliases: Optional[Mapping[str, str]] = None) -> List[T]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/plain_data.py#L103)

Coerce a sequence of dicts and/or instances into a list of ``cls``.

**Arguments**:

- `value` - ``None``, or an iterable of dicts and/or *cls* instances.
- `cls` - The config dataclass to build.
- `label` - How to name the thing in an error message, e.g. ``"tasks"``.
- `aliases` - Extra accepted keys, as in `coerce_struct`.
  

**Returns**:

- `List[T]` - One entry per element; empty for ``None``.
  

**Raises**:

- `ValidationError` - If *value* is a single struct rather than a sequence of
- `them` - a dict iterates as its keys, so without this the mistake
  surfaces as a list of unknown single-character fields.

