# Copyright 2024 aiXplain, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unified Actions / Inputs hierarchy for models and tools.

Object Hierarchy::

    Actions                    — collection of Action objects
      Action                   — metadata + owns its inputs
        Inputs                 — collection of Input objects
          Input                — individual input with schema + current value

Models have a single implicit "run" action. The ``model.inputs`` shorthand
skips the actions layer since there is nothing to disambiguate.

Tools have multiple actions, so the full path is always used.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Parameter
    from .integration import ActionInputSpec


class Input:
    """Individual input with schema and current value.

    Attributes:
        name: The input parameter name.
        required: Whether this input is required.
        type: The data type (e.g. ``"text"``, ``"number"``, ``"string"``).
        value: The current value (mutable).
        description: Human-readable description.
    """

    def __init__(
        self,
        name: str,
        required: bool = False,
        type: Optional[str] = None,
        value: Any = None,
        description: str = "",
        *,
        _validator: Optional[Callable[[Any], bool]] = None,
        _metadata: Optional[Any] = None,
    ) -> None:
        """Initialize an Input with schema metadata and an optional validator."""
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_required", required)
        object.__setattr__(self, "_type", type)
        object.__setattr__(self, "_value", value)
        object.__setattr__(self, "_description", description or "")
        object.__setattr__(self, "_validator", _validator)
        object.__setattr__(self, "_metadata", _metadata)

    @property
    def name(self) -> str:
        """The input parameter name."""
        return self._name

    @property
    def required(self) -> bool:
        """Whether this input is required."""
        return self._required

    @property
    def type(self) -> Optional[str]:
        """The data type string (e.g. ``"text"``, ``"number"``)."""
        return self._type

    @property
    def value(self) -> Any:
        """The current value."""
        return self._value

    @value.setter
    def value(self, val: Any) -> None:
        """Set the value, running the validator if one was provided."""
        if self._validator is not None and val is not None:
            if not self._validator(val):
                raise ValueError(
                    f"Invalid value type for input '{self._name}'. Expected {self._type}, got {type(val).__name__}"
                )
        object.__setattr__(self, "_value", val)

    @property
    def description(self) -> str:
        """Human-readable description of the input."""
        return self._description

    def reset(self, default: Any = None) -> None:
        """Reset the value to the given default (bypasses validation)."""
        object.__setattr__(self, "_value", default)

    def __eq__(self, other: object) -> bool:
        """Compare by value so ``inputs['temperature'] == 0.7`` works."""
        if isinstance(other, Input):
            return self._name == other._name and self._value == other._value
        return self._value == other

    def __hash__(self) -> int:
        """Return an identity-based hash."""
        return hash((self._name, id(self)))

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        parts = [
            f"name='{self._name}'",
            f"required={self._required}",
            f"type='{self._type}'",
            f"value={self._value!r}",
        ]
        if self._description:
            parts.append(f"description='{self._description}'")
        return f"Input({', '.join(parts)})"

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_parameter(cls, param: "Parameter") -> "Input":
        """Build an ``Input`` from a model ``Parameter``."""
        initial_value = None
        if param.default_values:
            first = param.default_values[0]
            if isinstance(first, dict):
                initial_value = first.get("value")
            else:
                initial_value = first

        default_for_reset = initial_value

        def _make_validator(p: "Parameter") -> Callable[[Any], bool]:
            def _validate(value: Any) -> bool:
                if value is None or p.data_type is None:
                    return True
                _type_map: dict[str, Any] = {
                    "text": str,
                    "json": (dict, list, str),
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "label": (str, type(None)),
                    "audio": (str, type(None)),
                }
                if p.data_type == "text" and p.data_sub_type == "json":
                    return isinstance(value, (dict, list, str))
                if p.data_type == "text" and p.data_sub_type == "number":
                    return isinstance(value, (int, float, str))
                expected = _type_map.get(p.data_type)
                if expected is None:
                    return True
                return isinstance(value, expected)

            return _validate

        inp = cls(
            name=param.name,
            required=param.required,
            type=param.data_type,
            value=initial_value,
            description="",
            _validator=_make_validator(param),
            _metadata=param,
        )
        object.__setattr__(inp, "_default_value", default_for_reset)
        return inp

    @classmethod
    def from_action_input_spec(cls, spec: "ActionInputSpec") -> "Input":
        """Build an ``Input`` from a tool ``ActionInputSpec``."""
        code = spec.code or spec.name.lower().replace(" ", "_")
        initial_value = spec.default_value[0] if spec.default_value else None
        default_for_reset = initial_value

        def _make_validator(s: "ActionInputSpec") -> Callable[[Any], bool]:
            def _validate(value: Any) -> bool:
                if value is None or s.datatype is None:
                    return True
                _type_map: dict[str, Any] = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }
                expected = _type_map.get(s.datatype)
                if expected is None:
                    return True
                return isinstance(value, expected)

            return _validate

        inp = cls(
            name=code,
            required=spec.required,
            type=spec.datatype,
            value=initial_value,
            description=spec.description or "",
            _validator=_make_validator(spec),
            _metadata=spec,
        )
        object.__setattr__(inp, "_default_value", default_for_reset)
        return inp


class Inputs:
    """Ordered collection of :class:`Input` objects.

    Supports dict-like access (``inputs["key"]``, ``inputs["key"] = val``)
    and dot-notation (``inputs.key``, ``inputs.key = val``).

    Iterating, ``.keys()``, ``.values()``, and ``.items()`` operate on
    *raw values* so that ``dict(inputs.items())`` gives a plain ``{name: value}``
    mapping suitable for API payloads.
    """

    def __init__(self, inputs: Optional[Dict[str, Input]] = None) -> None:
        """Initialize from an optional ordered dict of :class:`Input` objects."""
        object.__setattr__(self, "_inputs", inputs or {})

    # ------------------------------------------------------------------
    # Dict-like interface
    # ------------------------------------------------------------------

    def __getitem__(self, key: str) -> Input:
        """Return the :class:`Input` for *key*."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        if key in inputs:
            return inputs[key]
        raise KeyError(f"Input '{key}' not found")

    def __setitem__(self, key: str, value: Any) -> None:
        """Set the *value* on the :class:`Input` identified by *key*."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        if key in inputs:
            inputs[key].value = value
        else:
            raise KeyError(f"Input '{key}' not found")

    def __contains__(self, key: object) -> bool:
        """Return whether *key* is a known input name."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        return key in inputs

    def __len__(self) -> int:
        """Return the number of inputs."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        return len(inputs)

    def __iter__(self):
        """Iterate over input names."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        return iter(inputs.keys())

    # ------------------------------------------------------------------
    # Dot-notation interface
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Input:
        """Dot-notation read: ``inputs.temperature``."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        if name in inputs:
            return inputs[name]
        raise AttributeError(f"Input '{name}' not found")

    def __setattr__(self, name: str, value: Any) -> None:
        """Dot-notation write: ``inputs.temperature = 0.7``."""
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        if name in inputs:
            inputs[name].value = value
        else:
            raise AttributeError(f"Input '{name}' not found")

    # ------------------------------------------------------------------
    # Value-oriented helpers (backward-compatible with internal code)
    # ------------------------------------------------------------------

    def keys(self) -> List[str]:
        """Return input names."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        return list(inputs.keys())

    def values(self) -> List[Any]:
        """Return raw values for all inputs."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        return [inp.value for inp in inputs.values()]

    def items(self) -> List[tuple[str, Any]]:
        """Return ``(name, value)`` pairs."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        return [(name, inp.value) for name, inp in inputs.items()]

    def get(self, key: str, default: Any = None) -> Any:
        """Return the *raw value* for *key*, or *default*."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        if key in inputs:
            return inputs[key].value
        return default

    def update(self, **kwargs: Any) -> None:
        """Update multiple input values at once."""
        for key, value in kwargs.items():
            self[key] = value

    def reset(self, key: Optional[str] = None) -> None:
        """Reset one or all inputs to their default values."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        if key is not None:
            if key not in inputs:
                raise KeyError(f"Input '{key}' not found")
            inp = inputs[key]
            default = getattr(inp, "_default_value", None)
            inp.reset(default)
        else:
            for inp in inputs.values():
                default = getattr(inp, "_default_value", None)
                inp.reset(default)

    def copy(self) -> Dict[str, Any]:
        """Return a shallow copy of ``{name: value}``."""
        return dict(self.items())

    def validate(self, data: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate *data* (or current values) against input specs.

        Returns a list of error strings (empty means valid).
        """
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        errors: List[str] = []
        values_to_check = data if data is not None else {name: inp.value for name, inp in inputs.items()}

        for name, inp in inputs.items():
            if inp.required and values_to_check.get(name) is None:
                errors.append(f"Required input '{name}' is missing")

        return errors

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def required(self) -> List[str]:
        """Names of all required inputs."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        return [name for name, inp in inputs.items() if inp.required]

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return ``Inputs({'key': value, ...})``."""
        inputs: Dict[str, Input] = object.__getattribute__(self, "_inputs")
        inner = ", ".join(f"'{k}': {v.value!r}" for k, v in inputs.items())
        return f"Inputs({{{inner}}})"

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_parameters(cls, params: Optional[list]) -> "Inputs":
        """Build from a list of model ``Parameter`` objects."""
        if not params:
            return cls()
        inputs: Dict[str, Input] = {}
        for param in params:
            inp = Input.from_parameter(param)
            inputs[inp.name] = inp
        return cls(inputs)

    @classmethod
    def from_action_input_specs(cls, specs: Optional[list]) -> "Inputs":
        """Build from a list of tool ``ActionInputSpec`` objects."""
        if not specs:
            return cls()
        inputs: Dict[str, Input] = {}
        for spec in specs:
            inp = Input.from_action_input_spec(spec)
            inputs[inp.name] = inp
        return cls(inputs)


class Action:
    """Metadata for a single action, owning its :class:`Inputs`.

    For models the single action is always ``"run"``.
    For tools there may be many (e.g. ``"search_agents"``, ``"search_models"``).
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        *,
        inputs: Optional[Inputs] = None,
        _inputs_loader: Optional[Callable[[], Inputs]] = None,
    ) -> None:
        """Initialize an Action with name, description and optional lazy inputs."""
        self._name = name
        self._description = description
        self._inputs = inputs
        self._inputs_loader = _inputs_loader
        self._inputs_loaded = inputs is not None

    @property
    def name(self) -> str:
        """The canonical action name."""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """Human-readable description of the action."""
        return self._description

    @property
    def inputs(self) -> Inputs:
        """The action's :class:`Inputs` (lazily loaded for tool actions)."""
        if not self._inputs_loaded:
            if self._inputs_loader is not None:
                self._inputs = self._inputs_loader()
            else:
                self._inputs = Inputs()
            self._inputs_loaded = True
        return self._inputs  # type: ignore[return-value]

    def __repr__(self) -> str:
        """Return a multi-line representation showing the action and its inputs."""
        header = f"Action(name='{self._name}'"
        if self._description:
            header += f", description='{self._description}'"
        header += ")"

        if not self._inputs_loaded and self._inputs_loader is not None:
            return header

        try:
            inputs: Dict[str, Input] = object.__getattribute__(self.inputs, "_inputs")
        except Exception:
            return header

        if not inputs:
            return header

        lines = [header]
        max_name_len = max(len(k) for k in inputs) if inputs else 0
        for key, inp in inputs.items():
            req = "required" if inp.required else "optional"
            type_str = inp.type or "any"
            desc = f" — {inp.description}" if inp.description else ""
            lines.append(f"  {key:<{max_name_len}} ({req}) {type_str}{desc}")
        return "\n".join(lines)


class Actions:
    """Ordered collection of :class:`Action` objects.

    For models this contains a single ``"run"`` action.
    For tools it lazily discovers actions from the backend.
    """

    def __init__(
        self,
        actions: Optional[Dict[str, Action]] = None,
        *,
        _action_factory: Optional[Callable[[str, Optional[str]], Action]] = None,
        _actions_lister: Optional[Callable[[], List[tuple[str, Optional[str]]]]] = None,
    ) -> None:
        """Initialize with either an eager dict or lazy factory/lister callbacks."""
        self._actions: Dict[str, Action] = actions or {}
        self._action_factory = _action_factory
        self._actions_lister = _actions_lister
        self._available_actions: Optional[List[tuple[str, Optional[str]]]] = None
        self._eager = actions is not None and _actions_lister is None

    def _ensure_available(self) -> List[tuple[str, Optional[str]]]:
        """Return list of ``(name, description)`` tuples for available actions."""
        if self._available_actions is None:
            if self._eager:
                self._available_actions = [(name, action.description) for name, action in self._actions.items()]
            elif self._actions_lister is not None:
                self._available_actions = self._actions_lister()
            else:
                self._available_actions = []
        return self._available_actions

    def _resolve_name(self, key: str) -> str:
        """Resolve a user-supplied key to the canonical action name."""
        available = self._ensure_available()
        normalized = key.lower()
        for name, _ in available:
            if name and name.lower() == normalized:
                return name
        return key

    def __getitem__(self, key: str) -> Action:
        """Return the :class:`Action` for *key* (case-insensitive)."""
        resolved = self._resolve_name(key)
        normalized = resolved.lower()

        for k, v in self._actions.items():
            if k.lower() == normalized:
                return v

        if self._action_factory is not None:
            desc = None
            for name, description in self._ensure_available():
                if name and name.lower() == normalized:
                    desc = description
                    break
            action = self._action_factory(resolved, desc)
            self._actions[resolved] = action
            return action

        raise KeyError(f"Action '{key}' not found")

    def __contains__(self, key: object) -> bool:
        """Return whether *key* matches an available action name."""
        if not isinstance(key, str):
            return False
        available = self._ensure_available()
        normalized = str(key).lower()
        return any(name and name.lower() == normalized for name, _ in available)

    def __iter__(self):
        """Iterate over available action names."""
        available = self._ensure_available()
        return iter(name for name, _ in available if name)

    def __len__(self) -> int:
        """Return the number of available actions."""
        return len(self._ensure_available())

    def __repr__(self) -> str:
        """Return ``Actions(['action1', 'action2', ...])``."""
        available = self._ensure_available()
        names = [name for name, _ in available if name]
        return f"Actions({names})"

    def refresh(self) -> None:
        """Clear caches and force re-fetch on next access."""
        self._actions.clear()
        self._available_actions = None
