"""Pre-defined agent for inspecting the data flow within a team agent.

WARNING: This feature is currently in private beta.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Text, Set

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Union, Callable
import inspect
import textwrap

AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"  # GPT-4.1 Nano


class Inspectoraction_type(str, Enum):
    """Enum defining the types of actions an inspector can take."""

    CONTINUE = "continue"
    RERUN = "rerun"
    ABORT = "abort"
    EDIT = "edit"


class InspectorOnExhaust(str, Enum):
    """Enum defining behavior when inspector retries are exhausted."""

    CONTINUE = "continue"
    ABORT = "abort"


class InspectorSeverity(str, Enum):
    """Enum defining the severity levels for inspector findings."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


EditFnType = Union[str, Callable[[str], str]]
GateFnType = Union[str, Callable[[str], bool]]


class InspectorActionConfig(BaseModel):
    """Configuration for what an inspector should do when it finds issues.

    LLM-style actions (continue/rerun/abort):
      - evaluator + evaluator_prompt
      - (rerun only) max_retries/on_exhaust

    EDIT action:
      - edit_fn (required)
      - edit_evaluator_fn (optional gate)
    """

    actionType: Inspectoraction_type

    # RERUN-only controls
    maxRetries: Optional[int] = Field(default=None, ge=0)
    onExhaust: Optional[InspectorOnExhaust] = None

    evaluator: Optional[Text] = None
    evaluator_prompt: Optional[Text] = None

    edit_fn: Optional[EditFnType] = None
    edit_evaluator_fn: Optional[GateFnType] = None

    @field_validator("evaluator_prompt")
    @classmethod
    def _validate_evaluator_prompt(cls, v: Optional[Text], info) -> Optional[Text]:
        return v

    @staticmethod
    def _callable_to_string(fn: Callable) -> str:
        try:
            src = inspect.getsource(fn)
            return textwrap.dedent(src).strip()
        except (OSError, IOError, TypeError):
            # fallback: stable identifier
            return f"{fn.__module__}.{fn.__qualname__}"

    @field_validator("edit_fn", "edit_evaluator_fn", mode="before")
    @classmethod
    def _normalize_edit_functions(cls, v):
        if v is None:
            return None

        if callable(v):
            return cls._callable_to_string(v)

        if isinstance(v, str):
            return v

        raise TypeError("edit_fn / edit_evaluator_fn must be a string or a callable")

    @model_validator(mode="after")
    def _validate_action_contract(self) -> "InspectorActionConfig":
        is_edit = self.actionType == Inspectoraction_type.EDIT

        if is_edit:
            if not self.edit_fn or not str(self.edit_fn).strip():
                raise ValueError("edit_fn is required when actionType='edit'")

            if self.evaluator is not None or self.evaluator_prompt is not None:
                raise ValueError("EDIT action must not include evaluator/evaluator_prompt")
            if self.maxRetries is not None or self.onExhaust is not None:
                raise ValueError("EDIT action must not include max_retries/on_exhaust")
        else:
            if self.edit_fn is not None or self.edit_evaluator_fn is not None:
                raise ValueError("Only EDIT action may include edit_fn/edit_evaluator_fn")

            if self.actionType != Inspectoraction_type.RERUN:
                if self.maxRetries is not None or self.onExhaust is not None:
                    raise ValueError("max_retries/on_exhaust are only valid for actionType='rerun'")

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert the action config to a dictionary for serialization.

        Returns:
            Dict[str, Any]: Dictionary representation with camelCase keys.
        """
        d = self.model_dump(exclude_none=True)

        if "evaluator_prompt" in d:
            d["evaluatorPrompt"] = d.pop("evaluator_prompt")

        return d


class Inspector(BaseModel):
    """Inspector config object (SDK-side)."""

    name: Text
    description: Optional[Text] = None
    severity: Optional[InspectorSeverity] = None
    targets: List[Text] = Field(default_factory=list)
    action: InspectorActionConfig

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Text) -> Text:
        """Validate that the inspector name is not empty.

        Args:
            v: The name value to validate.

        Returns:
            The validated name.

        Raises:
            ValueError: If the name is empty or whitespace-only.
        """
        if not v or not str(v).strip():
            raise ValueError("name cannot be empty")
        return v

    @field_validator("targets")
    @classmethod
    def validate_targets(cls, v: List[Text]) -> List[Text]:
        """Validate and filter the targets list.

        Args:
            v: The list of target names to validate.

        Returns:
            A filtered list containing only non-empty target names.
        """
        if v is None:
            return []
        return [t for t in v if t and str(t).strip()]

    def model_dump(self, *args, **kwargs) -> Dict[str, Any]:
        """Serialize the inspector to a dictionary.

        Args:
            *args: Positional arguments passed to parent model_dump.
            **kwargs: Keyword arguments passed to parent model_dump.

        Returns:
            Dict[str, Any]: Dictionary representation of the inspector.
        """
        base = super().model_dump(*args, **kwargs)
        base["action"] = self.action.to_dict()
        if isinstance(base.get("severity"), Enum):
            base["severity"] = base["severity"].value
        return base

    def to_dict(self) -> Dict[str, Any]:
        """Convert the inspector to a dictionary for serialization.

        Returns:
            Dict[str, Any]: Dictionary representation excluding None values.
        """
        return self.model_dump(exclude_none=True)


class VerificationInspector(Inspector):
    """Convenience inspector for rerun-based verification."""

    def __init__(
        self,
        *,
        evaluator: Text,
        evaluator_prompt: Text = "Check the output against the plan",
        targets: Optional[List[Text]] = None,
        maxRetries: int = 2,
        onExhaust: InspectorOnExhaust = InspectorOnExhaust.CONTINUE,
        severity: InspectorSeverity = InspectorSeverity.MEDIUM,
        name: Text = "VerificationInspector",
        description: Text = "Checks output against the plan and requests rerun on mismatch",
        **kwargs: Any,
    ):
        """Initialize a verification inspector with rerun-based verification.

        Args:
            evaluator: The evaluator model ID to use for verification.
            evaluator_prompt: The prompt for the evaluator.
            targets: List of target agent names to inspect.
            maxRetries: Maximum number of rerun attempts.
            onExhaust: Behavior when retries are exhausted.
            severity: The severity level of this inspector.
            name: The name of the inspector.
            description: Description of the inspector's purpose.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(
            name=name,
            description=description,
            severity=severity,
            targets=targets or [],
            action=InspectorActionConfig(
                actionType=Inspectoraction_type.RERUN,
                maxRetries=maxRetries,
                onExhaust=onExhaust,
                evaluator=evaluator,
                evaluator_prompt=evaluator_prompt,
            ),
            **kwargs,
        )
