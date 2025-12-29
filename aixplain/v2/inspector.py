"""Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"  




class InspectorTarget(str, Enum):
    INPUT = "input"
    STEPS = "steps"
    OUTPUT = "output"

    def __str__(self) -> str:
        return self.value


class InspectorAction(str, Enum):
    CONTINUE = "continue"
    RERUN = "rerun"
    ABORT = "abort"
    EDIT = "edit"  

class InspectorOnExhaust(str, Enum):
    CONTINUE = "continue"
    ABORT = "abort"

class InspectorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    INFO = "info"
    CRITICAL = "critical"


@dataclass
class InspectorActionConfig:
    """
    Inspector action configuration (nested under Inspector.action).
    """
    action_type: InspectorAction
    max_retries: Optional[int] = None
    on_exhaust: Optional[InspectorOnExhaust] = None
    evaluator: Optional[str] = None
    evaluator_prompt: Optional[str] = None  
    edit_fn: Optional[str] = None
    edit_evaluator_fn: Optional[str] = None


    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "action_type": self.action_type.value,
        }
        if self.max_retries is not None:
            if self.max_retries < 0:
                raise ValueError("max_retries must be >= 0")
            d["max_retries"] = self.max_retries
        if self.on_exhaust is not None:
            d["on_exhaust"] = self.on_exhaust.value
        if self.evaluator is not None:
            d["evaluator"] = self.evaluator
        if self.evaluator_prompt is not None:
            d["evaluatorPrompt"] = self.evaluator_prompt
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InspectorActionConfig":
        if not isinstance(data, dict):
            raise ValueError("action must be a dict")

        # Accept both evaluatorPrompt and evaluator_prompt
        evaluator_prompt = data.get("evaluatorPrompt", data.get("evaluator_prompt"))

        return cls(
            action_type=InspectorAction(data["action_type"]),
            max_retries=data.get("max_retries"),
            on_exhaust=InspectorOnExhaust(data["on_exhaust"]) if data.get("on_exhaust") else None,
            evaluator=data.get("evaluator"),
            evaluator_prompt=evaluator_prompt,
        )


@dataclass
class Inspector:
    """
    Inspector v2 configuration object.
    """
    name: str
    action: InspectorActionConfig

    description: Optional[str] = None
    severity: Optional[InspectorSeverity] = None
    targets: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise ValueError("name cannot be empty")
        self.targets = [t for t in (self.targets or []) if t and str(t).strip()]

    def to_dict(self) -> Dict[str, Any]:
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