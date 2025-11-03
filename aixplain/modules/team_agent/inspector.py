"""Pre-defined agent for inspecting the data flow within a team agent.
WARNING: This feature is currently in private beta.

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
    inspectors=[inspector],
)
"""

import inspect
from enum import Enum
from typing import Dict, Optional, Text, Union, Callable

import textwrap
from pydantic import BaseModel, field_validator

from aixplain.modules.agent.model_with_params import ModelWithParams
from aixplain.modules.model.response import ModelResponse


AUTO_DEFAULT_MODEL_ID = "67fd9e2bef0365783d06e2f0"  # GPT-4.1 Nano


class InspectorAction(str, Enum):
    """
    Inspector's decision on the next action.
    """

    CONTINUE = "continue"
    RERUN = "rerun"
    ABORT = "abort"


class InspectorOutput(BaseModel):
    """
    Inspector's output.
    """

    critiques: Text
    content_edited: Text
    action: InspectorAction


class InspectorAuto(str, Enum):
    """A list of keywords for inspectors configured automatically in the backend."""
    ALIGNMENT = "alignment" 
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


def validate_policy_callable(policy_func: Callable) -> bool:
    """Validate that the policy callable meets the required constraints."""
    # Check function name
    if policy_func.__name__ != "process_response":
        return False

    # Get function signature
    sig = inspect.signature(policy_func)
    params = list(sig.parameters.keys())

    # Check arguments - should have exactly 2 parameters: model_response and input_content
    if len(params) != 2 or params[0] != "model_response" or params[1] != "input_content":
        return False

    # Check return type annotation - should return InspectorOutput
    return_annotation = sig.return_annotation
    if return_annotation != InspectorOutput:
        return False

    return True


def callable_to_code_string(policy_func: Callable) -> str:
    """Convert a callable policy function to a code string for serialization."""
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
    """Convert a code string back to a callable function for deserialization."""
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
            "dir": dir,
            "type": type,
            "id": id,
            "hash": hash,
            "repr": repr,
            "str": str,
            "format": format,
            "ord": ord,
            "chr": chr,
            "bin": bin,
            "oct": oct,
            "hex": hex,
            "pow": pow,
            "divmod": divmod,
            "complex": complex,
            "bytes": bytes,
            "bytearray": bytearray,
            "memoryview": memoryview,
            "slice": slice,
            "property": property,
            "staticmethod": staticmethod,
            "classmethod": classmethod,
            "super": super,
            "object": object,
            "Exception": Exception,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "AttributeError": AttributeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "RuntimeError": RuntimeError,
            "AssertionError": AssertionError,
            "ImportError": ImportError,
            "ModuleNotFoundError": ModuleNotFoundError,
            "NameError": NameError,
            "SyntaxError": SyntaxError,
            "IndentationError": IndentationError,
            "TabError": TabError,
            "UnboundLocalError": UnboundLocalError,
            "UnicodeError": UnicodeError,
            "UnicodeDecodeError": UnicodeDecodeError,
            "UnicodeEncodeError": UnicodeEncodeError,
            "UnicodeTranslateError": UnicodeTranslateError,
            "OSError": OSError,
            "FileNotFoundError": FileNotFoundError,
            "PermissionError": PermissionError,
            "ProcessLookupError": ProcessLookupError,
            "TimeoutError": TimeoutError,
            "ConnectionError": ConnectionError,
            "BrokenPipeError": BrokenPipeError,
            "ConnectionAbortedError": ConnectionAbortedError,
            "ConnectionRefusedError": ConnectionRefusedError,
            "ConnectionResetError": ConnectionResetError,
            "BlockingIOError": BlockingIOError,
            "ChildProcessError": ChildProcessError,
            "NotADirectoryError": NotADirectoryError,
            "IsADirectoryError": IsADirectoryError,
            "InterruptedError": InterruptedError,
            "EnvironmentError": EnvironmentError,
            "IOError": IOError,
            "EOFError": EOFError,
            "MemoryError": MemoryError,
            "RecursionError": RecursionError,
            "SystemError": SystemError,
            "ReferenceError": ReferenceError,
            "FloatingPointError": FloatingPointError,
            "OverflowError": OverflowError,
            "ZeroDivisionError": ZeroDivisionError,
            "ArithmeticError": ArithmeticError,
            "BufferError": BufferError,
            "LookupError": LookupError,
            "StopIteration": StopIteration,
            "GeneratorExit": GeneratorExit,
            "KeyboardInterrupt": KeyboardInterrupt,
            "SystemExit": SystemExit,
            "BaseException": BaseException,
        }

        # Execute the code string in the namespace
        exec(code_string, namespace)

        # Get the function from the namespace
        if "process_response" not in namespace:
            raise ValueError("Code string must define a function named 'process_response'")

        func = namespace["process_response"]

        # Store the original source code as an attribute for later retrieval
        func._source_code = code_string

        # Validate the function
        if not validate_policy_callable(func):
            raise ValueError("Deserialized function does not meet the required constraints")

        return func
    except Exception as e:
        raise ValueError(f"Failed to deserialize code string to callable: {e}")


def get_policy_source(func: Callable) -> Optional[str]:
    """Get the source code of a policy function.

    This function tries to retrieve the source code of a policy function.
    It first checks if the function has a stored _source_code attribute (for functions
    created via code_string_to_callable), then falls back to inspect.getsource().

    Args:
        func: The function to get source code for

    Returns:
        The source code string if available, None otherwise
    """
    if hasattr(func, "_source_code"):
        return func._source_code
    try:
        return inspect.getsource(func)
    except (OSError, TypeError):
        return None


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

    def model_dump(self, by_alias: bool = False, **kwargs) -> Dict:
        """Override model_dump to handle callable policy serialization."""
        data = super().model_dump(by_alias=by_alias, **kwargs)

        # Handle callable policy serialization
        if callable(self.policy):
            data["policy"] = callable_to_code_string(self.policy)
            data["policy_type"] = "callable"
        elif isinstance(self.policy, InspectorPolicy):
            data["policy"] = self.policy.value
            data["policy_type"] = "enum"

        return data

    @classmethod
    def model_validate(cls, data: Union[Dict, "Inspector"]) -> "Inspector":
        """Override model_validate to handle callable policy deserialization."""
        if isinstance(data, cls):
            return data

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

        return super().model_validate(data)


class VerificationInspector(Inspector):
    """Pre-defined inspector that checks output against the plan.
    
    This inspector is designed to verify that the output aligns with the intended plan
    and provides feedback when discrepancies are found. It uses a RERUN policy by default,
    meaning it will request re-execution when issues are detected.
    
    Example usage:
        from aixplain.modules.team_agent import VerificationInspector
        
        # Use with default model (GPT-4o or resolved_model_id)
        inspector = VerificationInspector()
        
        # Or with custom model
        inspector = VerificationInspector(model_id="your_model_id")
        
        team_agent = TeamAgent(
            name="my_team",
            agents=agents,
            inspectors=[VerificationInspector()],
            inspector_targets=[InspectorTarget.STEPS]
        )
    """
    
    def __init__(self, model_id: Optional[Text] = None, **kwargs):
        """Initialize VerificationInspector with default configuration.
        
        Args:
            model_id (Optional[Text]): Model ID to use. If not provided, uses auto configuration.
            **kwargs: Additional arguments passed to Inspector parent class.
        """
        from aixplain.modules.model.response import ModelResponse
        
        # Replicate resolved_model_id logic from old implementation
        resolved_model_id = model_id
        if not resolved_model_id:
            resolved_model_id = "6646261c6eb563165658bbb1"  # GPT_4o_ID
        
        def process_response(model_response: ModelResponse, input_content: str) -> InspectorOutput:
            """Default policy that always requests rerun for verification."""
            critiques = model_response.data
            action = InspectorAction.RERUN
            return InspectorOutput(critiques=critiques, content_edited=input_content, action=action)
        
        # Exact same default inspector configuration as old implementation
        # Note: When auto=InspectorAuto.ALIGNMENT is set, Inspector.__init__ will override
        # model_id with AUTO_DEFAULT_MODEL_ID
        defaults = {
            "name": "VerificationInspector",
            "model_id": resolved_model_id,
            "model_params": {"prompt": "Check the output against the plan"},
            "policy": process_response,
            "auto": InspectorAuto.ALIGNMENT
        }
        
        # Override defaults with any provided kwargs
        defaults.update(kwargs)
        
        super().__init__(**defaults)
