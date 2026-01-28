"""Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"


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
    INFO = "info"
    CRITICAL = "critical"


@dataclass
class InspectorActionConfig:
    """Inspector action configuration (nested under Inspector.action)."""

    actionType: InspectorAction
    maxRetries: Optional[int] = None
    onExhaust: Optional[InspectorOnExhaust] = None
    evaluator: Optional[str] = None
    evaluator_prompt: Optional[str] = None
    edit_fn: Optional[str] = None
    edit_evaluator_fn: Optional[str] = None

    def __post_init__(self) -> None:
        """Convert callable edit functions to source strings after initialization."""
        if callable(self.edit_fn):
            self.edit_fn = self._callable_to_string(self.edit_fn)
        if callable(self.edit_evaluator_fn):
            self.edit_evaluator_fn = self._callable_to_string(self.edit_evaluator_fn)

    @staticmethod
    def _callable_to_string(fn) -> str:
        import inspect
        import textwrap

        try:
            return textwrap.dedent(inspect.getsource(fn)).strip()
        except (OSError, IOError, TypeError):
            return f"{fn.__module__}.{fn.__qualname__}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the action config to a dictionary for API serialization."""
        d: Dict[str, Any] = {
            "actionType": self.actionType.value,
        }
        if self.maxRetries is not None:
            if self.maxRetries < 0:
                raise ValueError("max_retries must be >= 0")
            d["maxRetries"] = self.maxRetries
        if self.onExhaust is not None:
            d["onExhaust"] = self.onExhaust.value
        if self.evaluator is not None:
            d["evaluator"] = self.evaluator
        if self.evaluator_prompt is not None:
            d["evaluatorPrompt"] = self.evaluator_prompt
        if self.edit_fn is not None:
            d["editFn"] = self.edit_fn
        if self.edit_evaluator_fn is not None:
            d["editEvaluatorFn"] = self.edit_evaluator_fn
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InspectorActionConfig":
        """Create an InspectorActionConfig from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("action must be a dict")

        # Accept both evaluatorPrompt and evaluator_prompt
        evaluator_prompt = data.get("evaluatorPrompt", data.get("evaluator_prompt"))

        return cls(
            actionType=InspectorAction(data["actionType"]),
            maxRetries=data.get("maxRetries"),
            onExhaust=InspectorOnExhaust(data["onExhaust"]) if data.get("onExhaust") else None,
            evaluator=data.get("evaluator"),
            evaluator_prompt=evaluator_prompt,
        )


@dataclass
class Inspector:
    """Inspector v2 configuration object."""

    name: str
    action: InspectorActionConfig

    description: Optional[str] = None
    severity: Optional[InspectorSeverity] = None
    targets: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate inspector name and normalize targets after initialization."""
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")
        self.targets = [t for t in (self.targets or []) if t and str(t).strip()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the inspector to a dictionary for API serialization."""
        d: Dict[str, Any] = {
            "name": self.name,
            "targets": list(self.targets),
            "action": self.action.to_dict(),
        }
        if self.description is not None:
            d["description"] = self.description
        if self.severity is not None:
            d["severity"] = self.severity.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Inspector":
        """Create an Inspector from a dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Inspector data must be a dict")

        severity = data.get("severity")
        return cls(
            name=data["name"],
            description=data.get("description"),
            severity=InspectorSeverity(severity) if severity else None,
            targets=data.get("targets") or [],
            action=InspectorActionConfig.from_dict(data.get("action") or {}),
        )


__all__ = [
    "Inspector",
    "InspectorTarget",
    "InspectorAction",
    "InspectorOnExhaust",
    "InspectorSeverity",
    "InspectorActionConfig",
]
