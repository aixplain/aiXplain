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
from typing import Dict, Optional, Text, Union, Callable

from pydantic import field_validator

from aixplain.modules.agent.model_with_params import ModelWithParams


AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"  # GPT-4.1 Nano


class InspectorAction(str, Enum):
    """
    Inspector's decision on the next action.
    """

    CONTINUE = "continue"
    RERUN = "rerun"
    ABORT = "abort"


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


def validate_policy_callable(policy_func: Callable) -> bool:
    """Validate that the policy callable meets the required constraints."""
    import inspect

    # Check function name
    if policy_func.__name__ != "process_response":
        return False

    # Get function signature
    sig = inspect.signature(policy_func)
    params = list(sig.parameters.keys())

    # Check arguments
    if len(params) != 2 or params[0] != "model_response" or params[1] != "input_content":
        return False

    # Check return type annotation
    return_annotation = sig.return_annotation
    if return_annotation != InspectorAction:
        return False

    return True


class Inspector(ModelWithParams):
    """Pre-defined agent for inspecting the data flow within a team agent.

    The model should be onboarded before using it as an inspector.

    Attributes:
        name: The name of the inspector.
        model_id: The ID of the model to wrap.
        model_params: The configuration for the model.
        policy: The policy for the inspector. Can be InspectorPolicy enum or a callable function.
               If callable, must have name "process_response", arguments "model_response" and "input_content" (both strings),
               and return InspectorAction. Default is ADAPTIVE.
    """

    name: Text
    model_params: Optional[Dict] = None
    auto: Optional[InspectorAuto] = None
    policy: Union[InspectorPolicy, Callable] = InspectorPolicy.ADAPTIVE

    def __init__(self, *args, **kwargs):
        if kwargs.get("auto"):
            kwargs["model_id"] = AUTO_DEFAULT_MODEL_ID
        super().__init__(*args, **kwargs)

    @field_validator("name")
    def validate_name(cls, v: Text) -> Text:
        if v == "":
            raise ValueError("name cannot be empty")
        return v

    @field_validator("policy")
    def validate_policy(cls, v: Union[InspectorPolicy, Callable]) -> Union[InspectorPolicy, Callable]:
        if callable(v):
            if not validate_policy_callable(v):
                raise ValueError(
                    "Policy callable must have name 'process_response', arguments 'model_response' and 'input_content' (both strings), and return InspectorAction"
                )
        elif not isinstance(v, InspectorPolicy):
            raise ValueError(f"Policy must be InspectorPolicy enum or a valid callable function, got {type(v)}")
        return v
