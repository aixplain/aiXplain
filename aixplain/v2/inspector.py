"""Inspector module for v2 API - Team agent inspection and validation.

This module provides inspector functionality for validating team agent operations
at different stages (input, steps, output) with custom policies.

Example usage:
    ```python
    from aixplain.v2 import Inspector, InspectorTarget, InspectorPolicy, InspectorAction, InspectorOutput

    # Using built-in policy
    inspector = Inspector(
        name="my_inspector",
        model_id="model_id_here",
        model_params={"prompt": "Check if the data is safe to use."},
        policy=InspectorPolicy.ADAPTIVE
    )

    # Using custom policy
    def process_response(model_response, input_content: str) -> InspectorOutput:
        # Custom logic here
        return InspectorOutput(
            critiques="...",
            content_edited="...",
            action=InspectorAction.CONTINUE
        )

    inspector = Inspector(
        name="custom_inspector",
        model_id="model_id_here",
        model_params={"prompt": "Custom inspection prompt"},
        policy=process_response
    )

    # Use with team agent
    team_agent = Agent(
        name="team",
        subagents=[agent1, agent2],
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.STEPS]
    )
    ```
"""

import inspect
import textwrap
from enum import Enum
from typing import Dict, Optional, Union, Callable, Any
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config


AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"  # GPT-4.1 Nano


class InspectorTarget(str, Enum):
    """Target stages for inspector validation in the team agent pipeline.

    This enumeration defines the stages where inspectors can be applied to
    validate and ensure quality of the team agent's operation.

    Attributes:
        INPUT: Validates the input data before processing.
        STEPS: Validates intermediate steps during processing.
        OUTPUT: Validates the final output before returning.
    """

    INPUT = "input"
    STEPS = "steps"
    OUTPUT = "output"

    def __str__(self):
        """Return the string value of the enum member.

        Returns:
            str: The string value associated with the enum member.
        """
        return self._value_


class InspectorAction(str, Enum):
    """Inspector's decision on the next action.

    Attributes:
        CONTINUE: Continue execution normally.
        RERUN: Rerun the current step.
        ABORT: Stop execution completely.
    """

    CONTINUE = "continue"
    RERUN = "rerun"
    ABORT = "abort"


class InspectorPolicy(str, Enum):
    """Which action to take if the inspector gives negative feedback.

    Attributes:
        WARN: Log only, continue execution.
        ABORT: Stop execution immediately.
        ADAPTIVE: Adjust execution according to feedback.
    """

    WARN = "warn"
    ABORT = "abort"
    ADAPTIVE = "adaptive"


class InspectorAuto(str, Enum):
    """A list of keywords for inspectors configured automatically in the backend.

    Attributes:
        CORRECTNESS: Automatic correctness validation.
    """

    CORRECTNESS = "correctness"

    def get_name(self) -> str:
        """Get the standardized name for this inspector type.

        Returns:
            str: The inspector name in the format "inspector_<type>".
        """
        return "inspector_" + self.value


@dataclass_json
@dataclass
class InspectorOutput:
    """Inspector's output after validation.

    Attributes:
        critiques: Feedback text from the inspector.
        content_edited: Modified content (if any).
        action: The action to take next (CONTINUE, RERUN, or ABORT).
    """

    critiques: str
    content_edited: str
    action: InspectorAction


# Helper class to represent model response (mimicking legacy ModelResponse structure)
@dataclass_json
@dataclass
class ModelResponse:
    """Model response structure for inspector policy functions.

    This is a simplified version that captures the essential fields needed
    by inspector policy functions.

    Attributes:
        data: The response data from the model.
        error_message: Any error message from the model.
        status: Status of the response (e.g., "SUCCESS", "FAILED").
    """

    data: str = ""
    error_message: str = ""
    status: str = "SUCCESS"


def validate_policy_callable(policy_func: Callable) -> bool:
    """Validate that the policy callable meets the required constraints.

    A valid policy function must:
    - Be named 'process_response'
    - Have exactly 2 parameters: 'model_response' and 'input_content'
    - Return InspectorOutput

    Args:
        policy_func: The policy function to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    # Check function name
    if policy_func.__name__ != "process_response":
        return False

    # Get function signature
    sig = inspect.signature(policy_func)
    params = list(sig.parameters.keys())

    # Check arguments - should have exactly 2 parameters
    if (
        len(params) != 2
        or params[0] != "model_response"
        or params[1] != "input_content"
    ):
        return False

    # Check return type annotation - should return InspectorOutput
    return_annotation = sig.return_annotation
    if return_annotation != InspectorOutput:
        return False

    return True


def callable_to_code_string(policy_func: Callable) -> str:
    """Convert a callable policy function to a code string for serialization.

    Args:
        policy_func: The policy function to convert.

    Returns:
        str: The source code of the function as a string.
    """
    try:
        source_code = get_policy_source(policy_func)
        if source_code is None:
            # If we can't get the source code, create a minimal representation
            sig = inspect.signature(policy_func)
            return f"def process_response{str(sig)}:\n    # Function source not available\n    pass"

        # Dedent the source code to remove leading whitespace
        source_code = textwrap.dedent(source_code)
        return source_code
    except (OSError, TypeError):
        # If we can't get the source code, create a minimal representation
        sig = inspect.signature(policy_func)
        return f"def process_response{str(sig)}:\n    # Function source not available\n    pass"


def code_string_to_callable(code_string: str) -> Callable:
    """Convert a code string back to a callable function for deserialization.

    Args:
        code_string: The source code string to execute.

    Returns:
        Callable: The deserialized function.

    Raises:
        ValueError: If the code string is invalid or doesn't define process_response.
    """
    try:
        # Create a namespace to execute the code
        namespace = {
            "InspectorAction": InspectorAction,
            "InspectorOutput": InspectorOutput,
            "ModelResponse": ModelResponse,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "len": len,
            "print": print,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "any": any,
            "all": all,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "sorted": sorted,
            "reversed": reversed,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "setattr": setattr,
        }

        # Execute the code string in the namespace
        exec(code_string, namespace)

        # Get the function from the namespace
        if "process_response" not in namespace:
            raise ValueError(
                "Code string must define a function named 'process_response'"
            )

        func = namespace["process_response"]

        # Store the original source code as an attribute for later retrieval
        func._source_code = code_string

        # Validate the function
        if not validate_policy_callable(func):
            raise ValueError(
                "Deserialized function does not meet the required constraints"
            )

        return func
    except Exception as e:
        raise ValueError(f"Failed to deserialize code string to callable: {e}")


def get_policy_source(func: Callable) -> Optional[str]:
    """Get the source code of a policy function.

    This function tries to retrieve the source code of a policy function.
    It first checks if the function has a stored _source_code attribute (for functions
    created via code_string_to_callable), then falls back to inspect.getsource().

    Args:
        func: The function to get source code for.

    Returns:
        Optional[str]: The source code string if available, None otherwise.
    """
    if hasattr(func, "_source_code"):
        return func._source_code
    try:
        return inspect.getsource(func)
    except (OSError, TypeError):
        return None


@dataclass
class Inspector:
    """Inspector for validating team agent operations.

    An inspector validates the behavior of team agents at different stages
    (input, steps, output) and can enforce policies to ensure quality,
    safety, or correctness.

    NOTE: This class does not use @dataclass_json because we need custom
    serialization for callable policies.

    Attributes:
        name: The name of the inspector.
        model: The model to use for inspection. Can be a model ID (str) or Model object.
        model_params: Configuration parameters for the model (e.g., prompts).
        auto: Optional automatic configuration type.
        policy: The policy for the inspector. Can be InspectorPolicy enum or
               a callable function. If callable, must be named 'process_response',
               have arguments 'model_response' and 'input_content', and return
               InspectorOutput. Defaults to ADAPTIVE.

    Example:
        ```python
        # Using model ID
        inspector = Inspector(
            name="safety_check",
            model="model_id",
            model_params={"prompt": "Check for safety issues"},
            policy=InspectorPolicy.ABORT
        )

        # Using Model object with params set on model
        model = aix.Model("model_id")
        model.inputs.query = "Check for safety issues"
        inspector = Inspector(
            name="safety_check",
            model=model,
            policy=InspectorPolicy.ABORT
        )

        # Using custom callable policy
        def process_response(model_response, input_content: str) -> InspectorOutput:
            if "unsafe" in model_response.data:
                return InspectorOutput(
                    critiques="Unsafe content detected",
                    content_edited="",
                    action=InspectorAction.ABORT
                )
            return InspectorOutput(
                critiques="Content is safe",
                content_edited=input_content,
                action=InspectorAction.CONTINUE
            )

        inspector = Inspector(
            name="custom_safety",
            model="model_id",
            model_params={"prompt": "Check for safety"},
            policy=process_response
        )
        ```
    """

    name: str
    model: Union[str, Any]  # Can be model ID string or Model object
    model_params: Optional[Dict[str, Any]] = None
    auto: Optional[InspectorAuto] = None
    policy: Union[InspectorPolicy, Callable] = InspectorPolicy.ADAPTIVE

    # Internal field to store model_id
    model_id: Optional[str] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Validate name
        if not self.name or self.name == "":
            raise ValueError("name cannot be empty")

        # Handle model field - extract model ID from Model object or use string directly
        if hasattr(self.model, "id"):
            # It's a Model object
            self.model_id = self.model.id
            # If model has inputs configured and no model_params, extract them
            if (
                not self.model_params
                and hasattr(self.model, "inputs")
                and hasattr(self.model.inputs, "__dict__")
            ):
                # Convert model inputs to dict for model_params
                inputs_dict = {
                    k: v
                    for k, v in vars(self.model.inputs).items()
                    if not k.startswith("_")
                }
                if inputs_dict:
                    self.model_params = inputs_dict
        elif isinstance(self.model, str):
            # It's a model ID string
            self.model_id = self.model
        else:
            raise ValueError(
                f"model must be a model ID (str) or Model object, got {type(self.model)}"
            )

        # If auto is set, use default model ID
        if self.auto and not self.model_id:
            self.model_id = AUTO_DEFAULT_MODEL_ID

        # Validate policy
        if callable(self.policy):
            if not validate_policy_callable(self.policy):
                raise ValueError(
                    "Policy callable must have name 'process_response', "
                    "arguments 'model_response' and 'input_content' (both strings), "
                    "and return InspectorOutput"
                )
        elif not isinstance(self.policy, InspectorPolicy):
            raise ValueError(
                f"Policy must be InspectorPolicy enum or a valid callable function, "
                f"got {type(self.policy)}"
            )

    def to_dict(self, encode_json=False) -> Dict[str, Any]:
        """Convert inspector to dictionary with proper policy serialization.

        Args:
            encode_json: If True, encodes the dict to JSON format.

        Returns:
            Dict[str, Any]: The inspector as a dictionary.
        """
        # Use dataclass_json's to_dict for base serialization
        data = (
            super().to_dict(encode_json=encode_json)
            if hasattr(super(), "to_dict")
            else {}
        )

        # Manually construct the dict to ensure proper field names
        data = {
            "modelId": self.model_id,
            "name": self.name,
            "modelParams": self.model_params,
            "auto": self.auto.value if self.auto else None,
        }

        # Handle callable policy serialization
        if callable(self.policy):
            data["policy"] = callable_to_code_string(self.policy)
            data["policy_type"] = "callable"
        elif isinstance(self.policy, InspectorPolicy):
            data["policy"] = self.policy.value
            data["policy_type"] = "enum"
        else:
            data["policy"] = str(self.policy)
            data["policy_type"] = "unknown"

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Inspector":
        """Create an Inspector from a dictionary with policy deserialization.

        Args:
            data: Dictionary containing inspector data.

        Returns:
            Inspector: The deserialized inspector instance.
        """
        # Handle callable policy deserialization
        if isinstance(data, dict) and data.get("policy_type") == "callable":
            policy_code = data.get("policy")
            if isinstance(policy_code, str):
                try:
                    data["policy"] = code_string_to_callable(policy_code)
                except Exception:
                    # If deserialization fails, fall back to default policy
                    data["policy"] = InspectorPolicy.ADAPTIVE
            data.pop("policy_type", None)  # Remove the type indicator

        # Convert camelCase to snake_case for dataclass fields
        converted_data = {
            "name": data.get("name"),
            "model": data.get("modelId", data.get("model_id", data.get("model"))),
            "model_params": data.get("modelParams", data.get("model_params")),
            "auto": data.get("auto"),
            "policy": data.get("policy", InspectorPolicy.ADAPTIVE),
        }

        return cls(**{k: v for k, v in converted_data.items() if v is not None})


__all__ = [
    "Inspector",
    "InspectorTarget",
    "InspectorAction",
    "InspectorPolicy",
    "InspectorAuto",
    "InspectorOutput",
    "ModelResponse",
]
