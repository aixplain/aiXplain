"""Pre-defined agent for inspecting the data flow within a team agent.

WARNING: This feature is currently in private beta.

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
        """Get the standardized name for this inspector type.

        This method generates a consistent name for the inspector by prefixing
        the enum value with "inspector_".

        Returns:
            Text: The inspector name in the format "inspector_<type>".
        """
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
        """Initialize an Inspector instance.

        This method initializes an inspector with either a custom model or an
        automatic configuration. If auto is specified, it uses the default
        auto model ID.

        Args:
            *args: Variable length argument list passed to parent class.
            **kwargs: Arbitrary keyword arguments. Supported keys:
                - name (Text): The inspector's name
                - model_id (Text): The model ID to use
                - model_params (Dict, optional): Model configuration
                - auto (InspectorAuto, optional): Auto configuration type
                - policy (InspectorPolicy, optional): Inspector policy

        Note:
            If auto is specified in kwargs, model_id is automatically set to
            AUTO_DEFAULT_MODEL_ID.
        """
        if kwargs.get("auto"):
            kwargs["model_id"] = AUTO_DEFAULT_MODEL_ID
        super().__init__(*args, **kwargs)

    @field_validator("name")
    def validate_name(cls, v: Text) -> Text:
        """Validate the inspector name field.

        This validator ensures that the inspector's name is not empty.

        Args:
            v (Text): The name value to validate.

        Returns:
            Text: The validated name value.

        Raises:
            ValueError: If the name is an empty string.
        """
        if v == "":
            raise ValueError("name cannot be empty")
        return v
