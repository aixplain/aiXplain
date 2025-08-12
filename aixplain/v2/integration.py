from typing import Optional, List, Any, Dict, TYPE_CHECKING
import json
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

from .resource import BaseListParams, BaseResult
from .model import Model
from .enums import AuthenticationScheme

if TYPE_CHECKING:
    from .tool import Tool


class ActionInputsProxy:
    """Proxy object that provides both dict-like and dot notation access to action input parameters."""

    def __init__(self, action):
        self._action = action
        self._dynamic_inputs = {}
        self._setup_dynamic_inputs()

    def _setup_dynamic_inputs(self):
        """Create dynamic inputs for all action input parameters."""
        if self._action.inputs:
            for input_param in self._action.inputs:
                # Create a dynamic input for each parameter
                input_code = input_param.code or input_param.name.lower().replace(
                    " ", "_"
                )

                # Set initial value from backend defaults if available
                initial_value = None
                if input_param.defaultValue:
                    initial_value = (
                        input_param.defaultValue[0]
                        if input_param.defaultValue
                        else None
                    )

                # Store the input parameter metadata and value
                self._dynamic_inputs[input_code] = {
                    "value": initial_value,
                    "input": input_param,
                    "required": input_param.required,
                    "datatype": input_param.datatype,
                    "allowMulti": input_param.allowMulti,
                    "supportsVariables": input_param.supportsVariables,
                    "fixed": input_param.fixed,
                    "description": input_param.description,
                }

    def __getitem__(self, key: str):
        """Dict-like access: inputs['channels']"""
        if key in self._dynamic_inputs:
            return self._dynamic_inputs[key]["value"]
        raise KeyError(f"Input parameter '{key}' not found")

    def __setitem__(self, key: str, value):
        """Dict-like assignment: inputs['channels'] = 'general'"""
        if key in self._dynamic_inputs:
            # Validate the value against the input definition
            input_info = self._dynamic_inputs[key]
            input_param = input_info["input"]

            if not self._validate_input_type(value, input_param.datatype):
                raise ValueError(
                    f"Invalid value type for input '{key}'. "
                    f"Expected {input_param.datatype}, got {type(value).__name__}"
                )

            # Store the value
            self._dynamic_inputs[key]["value"] = value
        else:
            raise KeyError(f"Input parameter '{key}' not found")

    def __getattr__(self, name: str):
        """Dot notation access: inputs.channels"""
        if name in self._dynamic_inputs:
            return self._dynamic_inputs[name]["value"]
        raise AttributeError(f"Input parameter '{name}' not found")

    def __setattr__(self, name: str, value):
        """Dot notation assignment: inputs.channels = 'general'"""
        if name == "_action" or name == "_dynamic_inputs":
            super().__setattr__(name, value)
        elif name == "action_inputs" and isinstance(value, dict):
            # Handle bulk assignment to action_inputs
            self.update(**value)
        elif name in self._dynamic_inputs:
            # Validate the value against the input definition
            input_info = self._dynamic_inputs[name]
            input_param = input_info["input"]

            if not self._validate_input_type(value, input_param.datatype):
                raise ValueError(
                    f"Invalid value type for input '{name}'. "
                    f"Expected {input_param.datatype}, got {type(value).__name__}"
                )

            # Store the value
            self._dynamic_inputs[name]["value"] = value
        else:
            raise AttributeError(f"Input parameter '{name}' not found")

    def __contains__(self, key: str) -> bool:
        """Check if input parameter exists: 'channels' in inputs"""
        return key in self._dynamic_inputs

    def __len__(self) -> int:
        """Number of input parameters"""
        return len(self._dynamic_inputs)

    def __iter__(self):
        """Iterate over input parameter codes"""
        return iter(self._dynamic_inputs.keys())

    def keys(self):
        """Get input parameter codes"""
        return list(self._dynamic_inputs.keys())

    def values(self):
        """Get input parameter values"""
        return [info["value"] for info in self._dynamic_inputs.values()]

    def items(self):
        """Get input parameter code-value pairs"""
        return [(name, info["value"]) for name, info in self._dynamic_inputs.items()]

    def get(self, key: str, default=None):
        """Get input parameter value with default"""
        if key in self._dynamic_inputs:
            return self._dynamic_inputs[key]["value"]
        return default

    def update(self, **kwargs):
        """Update multiple inputs at once"""
        for key, value in kwargs.items():
            if key in self._dynamic_inputs:
                self[key] = value  # This will trigger validation
            else:
                raise KeyError(f"Input '{key}' not found")

    def set_input(self, input_name: str, value: Any, **kwargs):
        """Set a single input parameter.

        Args:
            input_name: Name of the input parameter
            value: Value to set
            **kwargs: Optional metadata like description, dtype, etc.
        """
        if input_name in self._dynamic_inputs:
            # Set the value (this will trigger validation)
            self[input_name] = value

            # Update metadata if provided
            if kwargs:
                input_info = self._dynamic_inputs[input_name]
                for key, val in kwargs.items():
                    if key in input_info:
                        input_info[key] = val
        else:
            raise KeyError(f"Input '{input_name}' not found")

    def set_inputs(self, inputs_dict: Dict[str, Dict[str, Any]]):
        """Set multiple input parameters in bulk.

        Args:
            inputs_dict: Dictionary in the format:
                {
                    "input_name_1": {
                        "value": "...",  # optional
                        "description": "..."  # optional
                    }
                }
        """
        for input_name, input_data in inputs_dict.items():
            if input_name in self._dynamic_inputs:
                # Extract value and metadata
                value = input_data.get("value")
                if value is not None:
                    self[input_name] = value

                # Update metadata
                input_info = self._dynamic_inputs[input_name]
                for key, val in input_data.items():
                    if key != "value" and key in input_info:
                        input_info[key] = val
            else:
                raise KeyError(f"Input '{input_name}' not found")

    def clear(self):
        """Reset all inputs to backend defaults"""
        for input_name in self._dynamic_inputs:
            self.reset_input(input_name)

    def copy(self):
        """Get a copy of current input parameter values"""
        return {name: info["value"] for name, info in self._dynamic_inputs.items()}

    def has_input(self, input_code: str) -> bool:
        """Check if an input parameter exists."""
        return input_code in self._dynamic_inputs

    def get_input_codes(self) -> list:
        """Get a list of all available input parameter codes."""
        return list(self._dynamic_inputs.keys())

    def get_required_inputs(self) -> list:
        """Get a list of required input parameter codes."""
        return [name for name, info in self._dynamic_inputs.items() if info["required"]]

    def get_input_info(self, input_code: str):
        """Get information about a specific input parameter."""
        if input_code in self._dynamic_inputs:
            return self._dynamic_inputs[input_code].copy()
        return None

    def get_all_inputs(self) -> dict:
        """Get all current input values."""
        return {name: info["value"] for name, info in self._dynamic_inputs.items()}

    def reset_input(self, input_code: str):
        """Reset an input parameter to its backend default value."""
        if input_code in self._dynamic_inputs:
            input_info = self._dynamic_inputs[input_code]
            input_param = input_info["input"]

            if input_param.defaultValue:
                self._dynamic_inputs[input_code]["value"] = (
                    input_param.defaultValue[0] if input_param.defaultValue else None
                )
            else:
                self._dynamic_inputs[input_code]["value"] = None

    def reset_all_inputs(self):
        """Reset all input parameters to their backend default values."""
        for input_code in self._dynamic_inputs:
            self.reset_input(input_code)

    def _validate_input_type(self, value, expected_type: str) -> bool:
        """Validate input type based on the input definition."""
        # Allow None values for all inputs
        if value is None:
            return True

        # If datatype is not specified, accept any value
        if expected_type is None:
            return True

        # Check datatype
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        else:
            # For unknown types, accept any value
            return True

    def __repr__(self):
        inputs = self.get_all_inputs()
        return f"ActionInputsProxy({inputs})"


@dataclass_json
@dataclass
class Input:
    """Input parameter for an action."""

    name: str
    code: Optional[str] = None
    value: List[Any] = field(default_factory=list)
    availableOptions: List[Any] = field(default_factory=list)
    datatype: str = "string"
    allowMulti: bool = False
    supportsVariables: bool = False
    defaultValue: List[Any] = field(default_factory=list)
    required: bool = False
    fixed: bool = False
    description: str = ""


@dataclass_json
@dataclass
class Action:
    """Container for tool action information and inputs."""

    name: Optional[str] = None
    description: Optional[str] = None
    displayName: Optional[str] = None
    slug: Optional[str] = None
    available_versions: Optional[List[str]] = None
    version: Optional[str] = None
    toolkit: Optional[Dict[str, Any]] = None
    input_parameters: Optional[Dict[str, Any]] = None
    output_parameters: Optional[Dict[str, Any]] = None
    scopes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    no_auth: Optional[bool] = None
    deprecated: Optional[Dict[str, Any]] = None
    inputs: Optional[List[Input]] = None

    # Dynamic inputs proxy for convenient access
    _inputs_proxy: Optional[ActionInputsProxy] = field(default=None, init=False)

    def __post_init__(self):
        """Initialize the inputs proxy after the action is created."""
        if self.inputs:
            self._inputs_proxy = ActionInputsProxy(self)

    @property
    def action_inputs(self):
        """Get the inputs proxy for this action."""
        if not self._inputs_proxy and self.inputs:
            self._inputs_proxy = ActionInputsProxy(self)
        return self._inputs_proxy

    def __setattr__(self, name: str, value):
        """Handle bulk assignment to action_inputs."""
        if name == "action_inputs" and isinstance(value, dict):
            # Handle bulk assignment to action_inputs
            if hasattr(self, "_inputs_proxy") and self._inputs_proxy:
                self._inputs_proxy.update(**value)
            else:
                # If inputs proxy doesn't exist yet, create it
                if self.inputs:
                    self._inputs_proxy = ActionInputsProxy(self)
                    self._inputs_proxy.update(**value)
        else:
            # Handle regular attributes
            super().__setattr__(name, value)

@dataclass_json
@dataclass
class ToolId:
    """Result for tool operations."""

    id: str


class IntegrationResult(BaseResult):
    """Result for connection operations.

    The backend returns the connection ID in data.id.
    """

    data: ToolId


class IntegrationListParams(BaseListParams):
    """Parameters for listing integrations."""

    pass


class Integration(Model):
    """Resource for integrations.

    Integrations are a subtype of models with Function.CONNECTOR.
    All connection logic is centralized here.
    """

    RESOURCE_PATH = "v2/integrations"
    RESPONSE_CLASS = IntegrationResult

    # Make AuthenticationScheme accessible
    AuthenticationScheme = AuthenticationScheme

    # Integration-specific properties
    @property
    def auth_schemes(self) -> List[str]:
        """Get authentication schemes for integrations."""
        if not self.attributes:
            return []

        auth_schemes_attr = next(
            (attr for attr in self.attributes if attr.name == "auth_schemes"), None
        )

        if not auth_schemes_attr:
            return []

        try:
            return json.loads(auth_schemes_attr.code)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_auth_inputs(
        self, auth_scheme: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get authentication inputs for a specific auth scheme."""
        if not self.attributes or not auth_scheme:
            return []

        inputs_attr = next(
            (attr for attr in self.attributes if attr.name == f"{auth_scheme}-inputs"),
            None,
        )

        if not inputs_attr:
            return []

        try:
            return json.loads(inputs_attr.code)
        except (json.JSONDecodeError, TypeError):
            return []

    def _validate_params(self, **kwargs) -> List[str]:
        """Validate all provided parameters against the model's expected
        parameters and integration-specific auth requirements."""
        # Call parent validation first
        errors = super()._validate_params(**kwargs)

        auth_scheme = kwargs["authScheme"]
        if auth_scheme not in self.auth_schemes:
            errors.append(
                f"Invalid auth_scheme '{auth_scheme}'. "
                f"Available schemes: {self.auth_schemes}"
            )

        data = kwargs["data"]
        data_errors = self._validate_data_params(data, auth_scheme)

        if data_errors:
            errors.extend(data_errors)

        return errors

    def _validate_data_params(
        self, data: Optional[Dict[str, Any]], auth_scheme: Optional[str] = None
    ) -> List[str]:
        """Validate data parameter against expected auth inputs for the auth
        scheme."""
        errors = []

        # Handle None data
        if data is None:
            data = {}

        # Get expected auth inputs for the auth scheme
        expected_inputs = self.get_auth_inputs(auth_scheme)
        if not expected_inputs:
            return errors

        # Validate each required input
        for expected_input in expected_inputs:
            input_name = expected_input.get("name")
            required = expected_input.get("required", False)

            if required and input_name not in data:
                errors.append(
                    f"Required auth input '{input_name}' is missing for "
                    f"auth scheme '{auth_scheme}'"
                )

            # Validate input type if specified
            if input_name in data and "type" in expected_input:
                expected_type = expected_input["type"]
                actual_value = data[input_name]

                if not self._validate_input_type(actual_value, expected_type):
                    errors.append(
                        f"Auth input '{input_name}' has invalid type. "
                        f"Expected {expected_type}, got "
                        f"{type(actual_value).__name__}"
                    )

        return errors

    def _validate_input_type(self, value: Any, expected_type: str) -> bool:
        """Validate input type based on expected type."""
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "number": lambda v: isinstance(v, (int, float)),
            "boolean": lambda v: isinstance(v, bool),
            "object": lambda v: isinstance(v, dict),
            "array": lambda v: isinstance(v, list),
        }

        validator = type_validators.get(expected_type)
        return validator(value) if validator else True

    def run(self, **kwargs: Any) -> IntegrationResult:
        """Run the integration with validation."""
        return super().run(**kwargs)

    def list_actions(self) -> List[Action]:
        """List available actions for the integration."""
        run_url = self.build_run_url()
        response = self.context.client.request(
            "post", run_url, json={"action": "LIST_ACTIONS", "data": {}}
        )

        # Handle the response data
        if "data" not in response:
            return []

        actions = []
        for action_data in response["data"]:
            try:
                # Handle case where action_data might be a string or other format
                if isinstance(action_data, dict):
                    actions.append(Action.from_dict(action_data))
                else:
                    # Skip invalid action data
                    continue
            except Exception:
                # Skip invalid action data
                continue

        return actions

    def list_inputs(self, *actions: str) -> List[Action]:
        """List available inputs for the integration."""
        run_url = self.build_run_url()
        response = self.context.client.request(
            "post",
            run_url,
            json={"action": "LIST_INPUTS", "data": {"actions": actions}},
        )

        # Handle the response data
        if "data" not in response:
            return []

        actions = []
        for input_data in response["data"]:
            actions.append(Action.from_dict(input_data))

        return actions

    def connect(self, **kwargs: Any) -> "Tool":
        """Connect the integration."""
        response = self.run(**kwargs)
        tool_id = response.data.id
        return self.context.Tool.get(tool_id)
