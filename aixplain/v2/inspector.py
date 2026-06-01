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


PROMPT_INJECTION_GUARDRAIL_ASSET_ID = "69a9974367d506543103ca18"
PII_REDACTION_GUARDRAIL_ASSET_ID = "69cbf63cd74e334a6bacfeb1"
HALLUCINATION_GUARD_ASSET_ID = "69a9a38967d506543103ca1d"

_PREBUILT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "prompt_injection_guard": {
        "name": "Prompt Injection Guard",
        "category": "protection",
        "description": "Detects prompt attacks before they influence planning or execution.",
        "default_targets": [InspectorTarget.INPUT.value],
        "default_action": {"type": InspectorAction.ABORT.value},
        "evaluator_asset_id": PROMPT_INJECTION_GUARDRAIL_ASSET_ID,
        "supported_actions": [
            InspectorAction.CONTINUE.value,
            InspectorAction.RERUN.value,
            InspectorAction.ABORT.value,
        ],
        "vendor": "aws",
    },
    "pii_redaction": {
        "name": "PII Redaction",
        "category": "redaction",
        "description": "Finds sensitive information and returns redacted content from the guardrail evaluator.",
        "default_targets": [InspectorTarget.INPUT.value],
        "default_action": {"type": InspectorAction.EDIT.value},
        "evaluator_asset_id": PII_REDACTION_GUARDRAIL_ASSET_ID,
        "supported_actions": [
            InspectorAction.CONTINUE.value,
            InspectorAction.EDIT.value,
            InspectorAction.ABORT.value,
        ],
        "vendor": "aws",
    },
    "hallucination_guard": {
        "name": "Hallucination Guard",
        "category": "quality",
        "description": "Detects hallucinations in the agent's final response by verifying it against the intermediate step results and the original user query.",
        "default_targets": [InspectorTarget.OUTPUT.value],
        "default_action": {"type": InspectorAction.RERUN.value, "maxRetries": 2, "onExhaust": "abort"},
        "evaluator_asset_id": HALLUCINATION_GUARD_ASSET_ID,
        "supported_actions": [
            InspectorAction.CONTINUE.value,
            InspectorAction.RERUN.value,
            InspectorAction.ABORT.value,
        ],
        "vendor": None,
    },
}


@dataclass
class PrebuiltInspector:
    """A lightweight preset reference that the backend resolves into a full Inspector.

    Instead of manually configuring an evaluator, action, and editor, users can
    reference one of the platform's pre-built inspector presets by ID.  The
    backend's ``normalize_prebuilt_inspectors`` validator expands the reference
    before the agent graph is constructed.

    Example::

        from aixplain.v2 import PrebuiltInspector, InspectorTarget

        team = client.Agent(
            name="Safe Agent",
            agents=[agent1, agent2],
            inspectors=[
                PrebuiltInspector.prompt_injection_guard(),
                PrebuiltInspector.pii_redaction(targets=[InspectorTarget.OUTPUT]),
            ],
        )
    """

    preset_id: str
    targets: Optional[List[str]] = None
    action: Optional[Dict[str, Any]] = None
    severity: Optional[InspectorSeverity] = None
    description: Optional[str] = None
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate the inspector configuration after initialization."""
        if self.preset_id not in _PREBUILT_REGISTRY:
            available = ", ".join(sorted(_PREBUILT_REGISTRY))
            raise ValueError(f"Unknown inspector preset '{self.preset_id}'. Available presets: {available}")
        if self.targets is not None:
            self.targets = [t.value if isinstance(t, InspectorTarget) else str(t).lower() for t in self.targets]
        if self.action is not None:
            action_type = self.action.get("type", "")
            supported = _PREBUILT_REGISTRY[self.preset_id]["supported_actions"]
            if str(action_type).lower() not in supported:
                raise ValueError(
                    f"Action '{action_type}' is not supported by preset '{self.preset_id}'. "
                    f"Supported actions: {supported}"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the lightweight reference format expected by the backend."""
        d: Dict[str, Any] = {"presetId": self.preset_id}
        if self.name is not None:
            d["name"] = self.name
        if self.description is not None:
            d["description"] = self.description
        if self.targets is not None:
            d["targets"] = list(self.targets)
        if self.action is not None:
            d["action"] = dict(self.action)
        if self.severity is not None:
            d["severity"] = self.severity.value
        if self.config is not None:
            d["config"] = dict(self.config)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrebuiltInspector":
        """Create a PrebuiltInspector from a dictionary."""
        severity_raw = data.get("severity")
        return cls(
            preset_id=data["presetId"],
            name=data.get("name"),
            description=data.get("description"),
            targets=data.get("targets"),
            action=data.get("action"),
            severity=InspectorSeverity(severity_raw) if severity_raw else None,
            config=data.get("config"),
        )

    @staticmethod
    def prompt_injection_guard(
        *,
        targets: Optional[List[Any]] = None,
        action: Optional[Dict[str, Any]] = None,
        severity: Optional[InspectorSeverity] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PrebuiltInspector":
        """Create a Prompt Injection Guard inspector.

        Detects prompt injection attacks before they influence planning or
        execution.  Defaults to ``ABORT`` on ``INPUT``.

        Args:
            targets: Override default targets (default: ``[InspectorTarget.INPUT]``).
            action: Override default action dict (default: ``{"type": "abort"}``).
            severity: Optional severity level.
            name: Optional custom name for the inspector node.
            description: Optional custom description.

        Returns:
            A PrebuiltInspector configured for prompt injection detection.
        """
        return PrebuiltInspector(
            preset_id="prompt_injection_guard",
            targets=targets,
            action=action,
            severity=severity,
            name=name,
            description=description,
        )

    @staticmethod
    def pii_redaction(
        *,
        targets: Optional[List[Any]] = None,
        action: Optional[Dict[str, Any]] = None,
        severity: Optional[InspectorSeverity] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PrebuiltInspector":
        """Create a PII Redaction inspector.

        Finds sensitive information (PII) and returns redacted content from the
        guardrail evaluator.  Defaults to ``EDIT`` on ``INPUT``.

        Args:
            targets: Override default targets (default: ``[InspectorTarget.INPUT]``).
            action: Override default action dict (default: ``{"type": "edit"}``).
            severity: Optional severity level.
            name: Optional custom name for the inspector node.
            description: Optional custom description.

        Returns:
            A PrebuiltInspector configured for PII redaction.
        """
        return PrebuiltInspector(
            preset_id="pii_redaction",
            targets=targets,
            action=action,
            severity=severity,
            name=name,
            description=description,
        )

    @staticmethod
    def hallucination_guard(
        *,
        targets: Optional[List[Any]] = None,
        action: Optional[Dict[str, Any]] = None,
        severity: Optional[InspectorSeverity] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PrebuiltInspector":
        """Create a Hallucination Guard inspector.

        Detects hallucinations in the agent's final response by verifying it
        against the intermediate step results and the original user query.
        Defaults to ``RERUN`` (max 2 retries, abort on exhaust) on ``OUTPUT``.

        Args:
            targets: Override default targets (default: ``[InspectorTarget.OUTPUT]``).
            action: Override default action dict (default: ``{"type": "rerun", "maxRetries": 2, "onExhaust": "abort"}``).
            severity: Optional severity level.
            name: Optional custom name for the inspector node.
            description: Optional custom description.

        Returns:
            A PrebuiltInspector configured for hallucination detection.
        """
        return PrebuiltInspector(
            preset_id="hallucination_guard",
            targets=targets,
            action=action,
            severity=severity,
            name=name,
            description=description,
        )

    @staticmethod
    def list_presets() -> Dict[str, Dict[str, Any]]:
        """Return metadata for all available pre-built inspector presets.

        Returns:
            A dict mapping preset IDs to their metadata (name, category,
            description, default targets/action, supported actions, vendor).
        """
        return {
            pid: {
                "name": meta["name"],
                "category": meta["category"],
                "description": meta["description"],
                "default_targets": list(meta["default_targets"]),
                "default_action": dict(meta["default_action"]),
                "supported_actions": list(meta["supported_actions"]),
                "vendor": meta.get("vendor"),
            }
            for pid, meta in _PREBUILT_REGISTRY.items()
        }


def is_prebuilt_inspector(obj: Any) -> bool:
    """Return True if *obj* is a PrebuiltInspector or a dict preset reference."""
    if isinstance(obj, PrebuiltInspector):
        return True
    return isinstance(obj, dict) and isinstance(obj.get("presetId"), str)


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
    "PrebuiltInspector",
    "is_prebuilt_inspector",
]
