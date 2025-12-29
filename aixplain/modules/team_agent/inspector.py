"""Pre-defined agent for inspecting the data flow within a team agent.
WARNING: This feature is currently in private beta.

WARNING: This feature is currently in private beta.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Text, Set

from pydantic import BaseModel, Field, field_validator, model_validator


AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"  # GPT-4.1 Nano


class InspectorActionType(str, Enum):
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


# Keep this close to the agentification contract you pasted
_ALLOWED_ACTIONS_BY_SEVERITY: Dict[str, Set[InspectorActionType]] = {
    "critical": {InspectorActionType.ABORT, InspectorActionType.EDIT},
    "high": {InspectorActionType.ABORT, InspectorActionType.EDIT},
    "medium": {InspectorActionType.RERUN, InspectorActionType.EDIT},
    "low": {InspectorActionType.CONTINUE, InspectorActionType.RERUN},
    "info": {InspectorActionType.CONTINUE},
}


class InspectorActionConfig(BaseModel):
    """
    Configuration for what an inspector should do when it finds issues.

    LLM-style actions (continue/rerun/abort):
      - evaluator + evaluator_prompt
      - (rerun only) max_retries/on_exhaust

    EDIT action:
      - edit_fn (required)
      - edit_evaluator_fn (optional gate)
    """

    action_type: InspectorActionType

    # RERUN-only controls
    max_retries: Optional[int] = Field(default=None, ge=0)
    on_exhaust: Optional[InspectorOnExhaust] = None

    evaluator: Optional[Text] = None
    evaluator_prompt: Optional[Text] = None

    edit_fn: Optional[Text] = None
    edit_evaluator_fn: Optional[Text] = None

    @field_validator("evaluator_prompt")
    @classmethod
    def _validate_evaluator_prompt(cls, v: Optional[Text], info) -> Optional[Text]:
        return v

    @model_validator(mode="after")
    def _validate_action_contract(self) -> "InspectorActionConfig":
        is_edit = self.action_type == InspectorActionType.EDIT

        if is_edit:
            if not self.edit_fn or not str(self.edit_fn).strip():
                raise ValueError("edit_fn is required when action_type='edit'")

            if self.evaluator is not None or self.evaluator_prompt is not None:
                raise ValueError("EDIT action must not include evaluator/evaluator_prompt")
            if self.max_retries is not None or self.on_exhaust is not None:
                raise ValueError("EDIT action must not include max_retries/on_exhaust")
        else:
            if self.edit_fn is not None or self.edit_evaluator_fn is not None:
                raise ValueError("Only EDIT action may include edit_fn/edit_evaluator_fn")

            if self.action_type != InspectorActionType.RERUN:
                if self.max_retries is not None or self.on_exhaust is not None:
                    raise ValueError("max_retries/on_exhaust are only valid for action_type='rerun'")

        return self

    def to_backend_dict(self) -> Dict[str, Any]:
        d = self.model_dump(exclude_none=True)

        if "evaluator_prompt" in d:
            d["evaluatorPrompt"] = d.pop("evaluator_prompt")

        return d


class Inspector(BaseModel):
    """
    Inspector config object (SDK-side).
    """

    name: Text
    description: Optional[Text] = None
    severity: Optional[InspectorSeverity] = None
    targets: List[Text] = Field(default_factory=list)
    action: InspectorActionConfig

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Text) -> Text:
        if not v or not str(v).strip():
            raise ValueError("name cannot be empty")
        return v

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: List[Text]) -> List[Text]:
        if v is None:
            return []
        return [t for t in v if t and str(t).strip()]

    @model_validator(mode="after")
    def _validate_severity_action(self) -> "Inspector":
        if self.severity is None:
            return self

        sev = self.severity.value if isinstance(self.severity, Enum) else str(self.severity)
        allowed = _ALLOWED_ACTIONS_BY_SEVERITY.get(sev)

        if not allowed:
            return self

        if self.action.action_type not in allowed:
            raise ValueError(
                f"Action '{self.action.action_type.value}' is not allowed for severity '{sev}'. "
                f"Allowed: {[a.value for a in sorted(allowed, key=lambda x: x.value)]}"
            )
        return self

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        base = super().model_dump(*args, **kwargs)
        base["action"] = self.action.to_backend_dict()
        if isinstance(base.get("severity"), Enum):
            base["severity"] = base["severity"].value
        return base

    def to_backend_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class VerificationInspector(Inspector):
    """
    Convenience inspector for rerun-based verification.
    """

    def __init__(
        self,
        *,
        evaluator: Text,
        evaluator_prompt: Text = "Check the output against the plan",
        targets: Optional[List[Text]] = None,
        max_retries: int = 2,
        on_exhaust: InspectorOnExhaust = InspectorOnExhaust.CONTINUE,
        severity: InspectorSeverity = InspectorSeverity.MEDIUM,
        name: Text = "VerificationInspector",
        description: Text = "Checks output against the plan and requests rerun on mismatch",
        **kwargs: Any,
    ):
        super().__init__(
            name=name,
            description=description,
            severity=severity,
            targets=targets or [],
            action=InspectorActionConfig(
                action_type=InspectorActionType.RERUN,
                max_retries=max_retries,
                on_exhaust=on_exhaust,
                evaluator=evaluator,
                evaluator_prompt=evaluator_prompt,
            ),
            **kwargs,
        )
