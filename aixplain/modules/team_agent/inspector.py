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
from typing import Dict, Optional, Text, Union, Callable, Any, List

import textwrap
from pydantic import BaseModel, field_validator, Field

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
    EDIT = "edit"


class InspectorSeverity(str, Enum):
    """Severity levels for inspector findings."""

    CRITICAL = "critical"  
    HIGH = "high"        
    MEDIUM = "medium"      
    LOW = "low"          
    INFO = "info"       


class InspectorActionConfig(BaseModel):
    """
    Configuration for what the inspector should do when a violation is detected.
    """

    type: InspectorAction
    max_retries: Optional[int] = None    
    on_exhaust: Optional[Text] = "abort"   
    editors: Optional[List[Any]] = None      

    @classmethod
    def continue_(cls) -> "InspectorActionConfig":
        return cls(type=InspectorAction.CONTINUE)

    @classmethod
    def abort(cls) -> "InspectorActionConfig":
        return cls(type=InspectorAction.ABORT)

    @classmethod
    def rerun(
        cls,
        max_retries: int = 3,
        on_exhaust: Text = "abort",
    ) -> "InspectorActionConfig":
        return cls(
            type=InspectorAction.RERUN,
            max_retries=max_retries,
            on_exhaust=on_exhaust,
        )

    @classmethod
    def edit(cls, editors: Union[Any, List[Any]]) -> "InspectorActionConfig":
        if not isinstance(editors, list):
            editors = [editors]
        return cls(type=InspectorAction.EDIT, editors=editors)



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


def callable_to_code_string(func: Callable) -> str:
    """Convert a callable policy function to a code string for serialization."""
    try:
        if hasattr(func, "_source_code"):
            source_code = func._source_code
        else:
            source_code = inspect.getsource(func)
        source_code = textwrap.dedent(source_code)
        return source_code
    except (OSError, TypeError):
        sig = inspect.signature(func)
        return f"def {func.__name__}{str(sig)}:\n    # Function source not available\n    pass"
    

def code_string_to_callable(
    code_string: str,
    func_name: str,
    validator: Optional[Callable[[Callable], bool]] = None,
    extra_namespace: Optional[Dict[str, Any]] = None,
) -> Callable:
    """Convert a code string back to a callable function for deserialization."""

    # Create a namespace to execute the code
    namespace = {
            "InspectorActionConfig": InspectorActionConfig,
            "ModelResponse": ModelResponse,
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

    if extra_namespace:
        namespace.update(extra_namespace)

    try:
        exec(code_string, namespace)
    except Exception as e:
        raise ValueError(f"Failed to execute code_string for {func_name}: {e}")

    if func_name not in namespace or not callable(namespace[func_name]):
        raise ValueError(f"Code string must define a callable named '{func_name}'")

    func = namespace[func_name]
    func._source_code = code_string 

    if validator and not validator(func):
        raise ValueError(f"Deserialized callable '{func_name}' does not meet required constraints")

    return func


def validate_evaluator_callable(func: Callable) -> bool:
    """
    Evaluator must have signature (content: str) -> Any.
    We keep return type flexible (bool/str/dict/etc.).
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    if len(params) != 1:
        return False
    return True


def validate_action_callable(func: Callable) -> bool:
    """
    Action must have signature (evaluation_result, content: str) -> InspectorActionConfig.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    if len(params) != 2:
        return False

    ret = sig.return_annotation
    if ret is not inspect.Signature.empty and ret is not InspectorActionConfig:
        return False

    return True



class Inspector(ModelWithParams):
    """Pre-defined agent for inspecting the data flow within a team agent.

    The model should be onboarded before using it as an inspector.

    Attributes:
        name: The name of the inspector.
        - description (Text):  Human-readable documentation (optional)
        - evaluator:           What checks content:
                               * underlying model (model_id + model_params)
                               * OR a Python callable(content) -> bool | str | dict
                               * OR None for "always edit"
        - evaluator_prompt:    Extra instructions for LLM evaluators (optional)
        - action:              What to do on issues:
                               * InspectorActionConfig
                               * OR callable(evaluation_result, content) -> InspectorActionConfig
        - severity:            Severity level (critical|high|medium|low|info)
        - auto:                Auto inspector type (ALIGNMENT|CORRECTNESS) – keeps v1 behavior
    """

    name: Text
    description: Optional[Text] = None
    evaluator: Optional[Callable[[Text], Union[bool, Text, Dict]]] = None
    evaluator_prompt: Optional[Text] = None
    action: Union[InspectorActionConfig, Callable[[Any, Text], InspectorActionConfig]] = Field(
        default_factory=InspectorActionConfig.rerun  # default RERUN(max_retries=3, on_exhaust="abort")
    )
    severity: Optional[InspectorSeverity] = None
    auto: Optional[InspectorAuto] = None

    model_params: Optional[Dict] = None
   
    def __init__(self, *args, **kwargs):
        """Initialize an Inspector instance.

        This method initializes an inspector with either a custom model or an
        automatic configuration. If auto is specified, it uses the default
        auto model ID.

            If auto is specified in kwargs, model_id is automatically set to
            AUTO_DEFAULT_MODEL_ID.
        """
        if kwargs.get("auto"):
            kwargs["model_id"] = AUTO_DEFAULT_MODEL_ID

        if "model_id" not in kwargs or kwargs["model_id"] is None:
            mp = kwargs.get("model_params") or {}
            if isinstance(mp, dict):
                mp_id = mp.get("model_id") or mp.get("modelId")
                if mp_id:
                    kwargs["model_id"] = mp_id

        if "model_id" not in kwargs or kwargs["model_id"] is None:
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
    
    @field_validator("action")
    def validate_action(
        cls,
        v: Union[InspectorActionConfig, Callable[[Any, Text], InspectorActionConfig]],
    ) -> Union[InspectorActionConfig, Callable[[Any, Text], InspectorActionConfig]]:
        """Ensure action is either a config or a proper callable."""
        if isinstance(v, InspectorActionConfig):
            return v
        if callable(v):
            sig = inspect.signature(v)
            params = list(sig.parameters.keys())
            if len(params) != 2:
                raise ValueError(
                    "Action callable must accept exactly two parameters: "
                    "'evaluation_result' and 'content'"
                )
            return v
        raise ValueError(
            f"action must be InspectorActionConfig or a callable(evaluation_result, content), got {type(v)}"
        )


    def model_dump(self, by_alias: bool = False, **kwargs) -> Dict:
        """Override model_dump to handle callable policy serialization."""
        data = super().model_dump(by_alias=by_alias, **kwargs)

        # ----- evaluator -----
        if callable(self.evaluator):
            data["evaluator"] = callable_to_code_string(self.evaluator)
            data["evaluator_type"] = "callable"
        elif self.evaluator is None:
            data["evaluator_type"] = "none"
        else:
            data["evaluator_type"] = "model"

        # ----- action -----
        if isinstance(self.action, InspectorActionConfig):
            data["action"] = self.action.model_dump()
            data["action_type"] = "config"
        elif callable(self.action):
            data["action"] = callable_to_code_string(self.action)
            data["action_type"] = "callable"

        return data

    @classmethod
    @classmethod
    def model_validate(cls, data: Any) -> "Inspector":
        if isinstance(data, cls):
            return data

        if isinstance(data, dict):
            # ----- evaluator -----
            if data.get("evaluator_type") == "callable":
                code = data.get("evaluator")
                if isinstance(code, str):
                    try:
                        data["evaluator"] = code_string_to_callable(
                            code_string=code,
                            func_name="evaluator_fn",       
                            validator=validate_evaluator_callable,
                        )
                    except Exception:
                        data["evaluator"] = None
                data.pop("evaluator_type", None)

            # ----- action -----
            action_type = data.get("action_type")
            if action_type == "config":
                raw = data.get("action") or {}
                data["action"] = InspectorActionConfig.model_validate(raw)
                data.pop("action_type", None)
            elif action_type == "callable":
                code = data.get("action")
                if isinstance(code, str):
                    try:
                        data["action"] = code_string_to_callable(
                            code_string=code,
                            func_name="action_fn",   
                            validator=validate_action_callable,
                        )
                    except Exception:
                        data["action"] = InspectorActionConfig.rerun()
                data.pop("action_type", None)


        return super().model_validate(data)
    
    @field_validator("evaluator")
    def validate_evaluator(cls, v):
        if v is None:
            return v

        if not callable(v):
            raise ValueError(f"evaluator must be callable or None, got {type(v)}")

        # ensure correct function name
        if v.__name__ != "evaluator_fn":
            raise ValueError(
                f"Evaluator function must be named 'evaluator_fn', got '{v.__name__}'"
            )

        if not validate_evaluator_callable(v):
            raise ValueError(
                "evaluator callable must accept exactly one parameter: 'content'"
            )

        return v


    @field_validator("action")
    def validate_action(cls, v):
        if isinstance(v, InspectorActionConfig):
            return v

        if callable(v):
            if v.__name__ != "action_fn":
                raise ValueError(
                    f"Action function must be named 'action_fn', got '{v.__name__}'"
                )

            if not validate_action_callable(v):
                raise ValueError(
                    "action callable must accept exactly two parameters: "
                    "'evaluation_result' and 'content', and optionally return InspectorActionConfig."
                )
            return v

        raise ValueError(
            f"action must be InspectorActionConfig or a callable(evaluation_result, content), got {type(v)}"
        )



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
        
        resolved_model_id = model_id
        if not resolved_model_id:
            resolved_model_id = "6646261c6eb563165658bbb1"  

        defaults = {
            "name": "verification_inspector",
            "description": "Verifies that the output aligns with the intended plan.",
            "model_id": resolved_model_id,
            "model_params": {
                "prompt": "Check the output against the given plan and return PASS or FAIL with reasons."
            },
            "evaluator": None, 
            "evaluator_prompt": "Evaluate if the response strictly follows the plan.",
            "action": InspectorActionConfig.rerun(max_retries=3, on_exhaust="continue"),
            "severity": InspectorSeverity.MEDIUM,
            "auto": InspectorAuto.ALIGNMENT,
        }

        defaults.update(kwargs)
        super().__init__(**defaults)
