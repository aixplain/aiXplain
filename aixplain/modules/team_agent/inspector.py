"""Pre-defined agent for inspecting the data flow within a team agent.

Example usage:

inspector = Inspector(
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


AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"  # GPT-4.1 Nano


class InspectorAuto(str, Enum):
    """A list of keywords for inspectors configured automatically in the backend."""

    CORRECTNESS = "correctness"

    def get_name(self) -> Text:
        return "inspector_" + self.value


class InspectorPolicy(str, Enum):
    """Which action to take if the inspector gives negative feedback."""

    WARN = "warn"  # log only, continue execution
    ABORT = "abort"  # stop execution
    ADAPTIVE = "adaptive"  # adjust execution according to feedback


class Inspector(ModelWithParams):
    """Pre-defined agent for inspecting the data flow within a team agent.

    The model should be onboarded before using it as an inspector.

    Attributes:
        name: The name of the inspector.
        model_id: The ID of the model to wrap.
        model_params: The configuration for the model.
        policy: The policy for the inspector. Default is ADAPTIVE.
    """

    name: Text
    model_params: Optional[Dict] = None
    auto: Optional[InspectorAuto] = None
    policy: InspectorPolicy = InspectorPolicy.ADAPTIVE

    def __init__(self, *args, **kwargs):
        if kwargs.get("auto"):
            kwargs["model_id"] = AUTO_DEFAULT_MODEL_ID
        super().__init__(*args, **kwargs)

    @field_validator("name")
    def validate_name(cls, v: Text) -> Text:
        if v == "":
            raise ValueError("name cannot be empty")
        return v
