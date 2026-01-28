"""Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

"""

import inspect
import textwrap
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"


def _callable_to_string(fn) -> str:
    """Convert a callable to its source string representation."""
    try:
        return textwrap.dedent(inspect.getsource(fn)).strip()
    except (OSError, IOError, TypeError):
        return f"{fn.__module__}.{fn.__qualname__}"


class InspectorTarget(str, Enum):
    """Target stages for inspector validation in the team agent pipeline."""

    INPUT = "input"
    STEPS = "steps"
    OUTPUT = "output"

    def __str__(self) -> str:
        """Return the string value of the enum."""
        return self.value


class InspectorAction(str, Enum):
    """Actions an inspector can take when evaluating content."""

    CONTINUE = "continue"
    RERUN = "rerun"
    ABORT = "abort"
    EDIT = "edit"


class InspectorOnExhaust(str, Enum):
    """Action to take when max retries are exhausted."""

    CONTINUE = "continue"
    ABORT = "abort"


class InspectorSeverity(str, Enum):
    """Severity level for inspector findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvaluatorType(str, Enum):
    """Type of evaluator or editor."""

    ASSET = "asset"
    FUNCTION = "function"


@dataclass
class InspectorActionConfig:
    """Inspector action configuration."""

    type: InspectorAction
    max_retries: Optional[int] = None
    on_exhaust: Optional[InspectorOnExhaust] = None

    def __post_init__(self) -> None:
        """Validate that max_retries and on_exhaust are only used with RERUN."""
        if self.type != InspectorAction.RERUN:
            if self.max_retries is not None:
                raise ValueError("max_retries is only valid when action type is 'rerun'")
            if self.on_exhaust is not None:
                raise ValueError("on_exhaust is only valid when action type is 'rerun'")
        if self.max_retries is not None and self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the action config to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type.value}
        if self.max_retries is not None:
            d["maxRetries"] = self.max_retries
        if self.on_exhaust is not None:
            d["onExhaust"] = self.on_exhaust.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InspectorActionConfig":
        """Create an InspectorActionConfig from a dictionary."""
        return cls(
            type=InspectorAction(data["type"]),
            max_retries=data.get("maxRetries"),
            on_exhaust=InspectorOnExhaust(data["onExhaust"]) if data.get("onExhaust") else None,
        )


@dataclass
class EvaluatorConfig:
    """Evaluator configuration for an inspector."""

    type: EvaluatorType
    asset_id: Optional[str] = None
    prompt: Optional[str] = None
    function: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and convert callable functions to source strings."""
        if callable(self.function):
            self.function = _callable_to_string(self.function)
        if self.type == EvaluatorType.ASSET and not self.asset_id:
            raise ValueError("asset_id is required when evaluator type is 'asset'")
        if self.type == EvaluatorType.FUNCTION and not self.function:
            raise ValueError("function is required when evaluator type is 'function'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type.value}
        if self.asset_id is not None:
            d["assetId"] = self.asset_id
        if self.prompt is not None:
            d["prompt"] = self.prompt
        if self.function is not None:
            d["function"] = self.function
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluatorConfig":
        """Create an EvaluatorConfig from a dictionary."""
        return cls(
            type=EvaluatorType(data["type"]),
            asset_id=data.get("assetId"),
            prompt=data.get("prompt"),
            function=data.get("function"),
        )


@dataclass
class EditorConfig:
    """Editor configuration for an inspector."""

    type: EvaluatorType
    asset_id: Optional[str] = None
    prompt: Optional[str] = None
    function: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate and convert callable functions to source strings."""
        if callable(self.function):
            self.function = _callable_to_string(self.function)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for API serialization."""
        d: Dict[str, Any] = {"type": self.type.value}
        if self.asset_id is not None:
            d["assetId"] = self.asset_id
        if self.prompt is not None:
            d["prompt"] = self.prompt
        if self.function is not None:
            d["function"] = self.function
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EditorConfig":
        """Create an EditorConfig from a dictionary."""
        return cls(
            type=EvaluatorType(data["type"]),
            asset_id=data.get("assetId"),
            prompt=data.get("prompt"),
            function=data.get("function"),
        )


@dataclass
class Inspector:
    """Inspector v2 configuration object."""

    name: str
    action: InspectorActionConfig
    evaluator: EvaluatorConfig

    description: Optional[str] = None
    severity: Optional[InspectorSeverity] = None
    targets: List[str] = field(default_factory=list)
    editor: Optional[EditorConfig] = None

    def __post_init__(self) -> None:
        """Validate inspector configuration after initialization."""
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")
        self.targets = [t for t in (self.targets or []) if t and str(t).strip()]
        if self.action.type == InspectorAction.EDIT and self.editor is None:
            raise ValueError("editor is required when action type is 'edit'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the inspector to a dictionary for API serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
            "targets": list(self.targets),
            "action": self.action.to_dict(),
            "evaluator": self.evaluator.to_dict(),
        }
        if self.description is not None:
            d["description"] = self.description
        if self.severity is not None:
            d["severity"] = self.severity.value
        if self.editor is not None:
            d["editor"] = self.editor.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Inspector":
        """Create an Inspector from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Inspector data must be a dict")

        severity = data.get("severity")
        editor_data = data.get("editor")
        return cls(
            name=data["name"],
            description=data.get("description"),
            severity=InspectorSeverity(severity) if severity else None,
            targets=data.get("targets") or [],
            action=InspectorActionConfig.from_dict(data.get("action") or {}),
            evaluator=EvaluatorConfig.from_dict(data["evaluator"]),
            editor=EditorConfig.from_dict(editor_data) if editor_data else None,
        )


__all__ = [
    "Inspector",
    "InspectorTarget",
    "InspectorAction",
    "InspectorOnExhaust",
    "InspectorSeverity",
    "InspectorActionConfig",
    "EvaluatorType",
    "EvaluatorConfig",
    "EditorConfig",
]
