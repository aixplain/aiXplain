"""Pre-defined agent for inspecting the data flow within a team agent.

Example usage:

inspector = InspectorAgent(
    name="my_inspector",
    model_id="my_model",
    model_config={"prompt": "Check if the data is safe to use."},
    policy=InspectorPolicy.ADAPTIVE
)

team = TeamAgent(
    name="team"
    agents=agents,
    description="team description",
    llm_id="xyz",
    use_mentalist=True,
    inspectors=[inspector],
)
"""

from enum import Enum
from typing import Dict, Optional, Text

from pydantic import field_validator

from aixplain.modules.agent.model_with_params import ModelWithParams


class InspectorPolicy(str, Enum):
    """Which action to take if the inspector gives negative feedback."""

    WARN = "warn"  # log only, continue execution
    ABORT = "abort"  # stop execution
    ADAPTIVE = "adaptive"  # adjust execution according to feedback


class Inspector(ModelWithParams):
    """Pre-defined agent for inspecting the data flow within a team agent.

    The model should be onboarded before using it as an inspector.

    Attributes:
        model_id: The ID of the model to wrap.
        model_config: The configuration for the model.
        policy: The policy for the inspector. Default is ADAPTIVE.
    """

    name: Text
    model_config: Optional[Dict] = None
    policy: InspectorPolicy = InspectorPolicy.ADAPTIVE

    @field_validator("policy")
    def validate_policy(cls, v: InspectorPolicy) -> InspectorPolicy:
        if v not in InspectorPolicy:
            raise ValueError(f"Invalid policy: {v}")
        return v
