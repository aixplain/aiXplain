"""Coercion of plain dicts into the v2 config structs (PROD-2921).

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
"""

from dataclasses import fields as dataclass_fields
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Type, TypeVar

from .exceptions import ValidationError

T = TypeVar("T")


def struct_fields(cls: type) -> Tuple[str, ...]:
    """Return the user-facing field names of a config dataclass, in order.

    Read off the dataclass rather than hardcoded, so a field added to the struct
    is accepted -- and named in the error for an unknown key -- without a second
    edit here.

    Args:
        cls: The dataclass to inspect.

    Returns:
        Tuple[str, ...]: Its field names, excluding private ones.
    """
    return tuple(f.name for f in dataclass_fields(cls) if not f.name.startswith("_"))


def coerce_struct(
    value: Any,
    cls: Type[T],
    *,
    label: str,
    aliases: Optional[Mapping[str, str]] = None,
) -> Optional[T]:
    """Coerce ``value`` into an instance of ``cls``, raising on unknown keys.

    Args:
        value: ``None``, an instance of *cls* (returned unchanged), or a dict on
            *cls*'s field names.
        cls: The config dataclass to build.
        label: How to name the thing in an error message, e.g. ``"budget"``.
        aliases: Extra accepted keys mapped onto field names -- the wire
            spellings a backend response carries, so the same entry point decodes
            both what a caller writes and what the API sends back.

    Returns:
        Optional[T]: The coerced instance, or ``None`` for ``None``.

    Raises:
        ValidationError: If *value* is neither ``None``, an instance, nor a dict,
            or if a dict carries a key that is neither a field nor an alias.
    """
    if value is None or isinstance(value, cls):
        return value
    accepted = struct_fields(cls)
    if not isinstance(value, Mapping):
        raise ValidationError(
            f"{label} must be a {cls.__name__} or a dict, got {type(value).__name__}. "
            f"Accepted dict fields: {', '.join(accepted)}."
        )

    alias_map = dict(aliases or {})
    kwargs: Dict[str, Any] = {}
    unknown: List[str] = []
    for key, item in value.items():
        field_name = key if key in accepted else alias_map.get(key)
        if field_name is None:
            unknown.append(str(key))
            continue
        kwargs[field_name] = item
    if unknown:
        raise ValidationError(
            f"Unknown {label} field(s): {', '.join(sorted(unknown))}. Accepted fields: {', '.join(accepted)}."
        )
    return cls(**kwargs)


def coerce_struct_list(
    value: Any,
    cls: Type[T],
    *,
    label: str,
    aliases: Optional[Mapping[str, str]] = None,
) -> List[T]:
    """Coerce a sequence of dicts and/or instances into a list of ``cls``.

    Args:
        value: ``None``, or an iterable of dicts and/or *cls* instances.
        cls: The config dataclass to build.
        label: How to name the thing in an error message, e.g. ``"tasks"``.
        aliases: Extra accepted keys, as in :func:`coerce_struct`.

    Returns:
        List[T]: One entry per element; empty for ``None``.

    Raises:
        ValidationError: If *value* is a single struct rather than a sequence of
            them -- a dict iterates as its keys, so without this the mistake
            surfaces as a list of unknown single-character fields.
    """
    if value is None:
        return []
    if isinstance(value, (Mapping, cls)) or isinstance(value, (str, bytes)):
        raise ValidationError(f"{label} must be a list of {cls.__name__}, not a single one. Wrap it in a list.")
    if not isinstance(value, Iterable):
        raise ValidationError(f"{label} must be a list of {cls.__name__}, got {type(value).__name__}.")
    coerced = [coerce_struct(entry, cls, label=label, aliases=aliases) for entry in value]
    return [entry for entry in coerced if entry is not None]
