from typing import Optional, List, Any, Dict, TYPE_CHECKING
import json
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from functools import cached_property

from .resource import BaseSearchParams, BaseResult
from .model import Model
from .enums import AuthenticationScheme

if TYPE_CHECKING:
    from .tool import Tool


class ActionInputsProxy:
    """Proxy object that provides both dict-like and dot notation access to action input parameters.

    This proxy dynamically fetches action input specifications from the container resource
    when needed, allowing for runtime discovery and validation of action inputs.
    """

    def __init__(self, container, action_name: str):
        self._container = container
        self._action_name = action_name
        self._inputs = {}
        self._inputs_fetched = False

    def _ensure_inputs_fetched(self):
        """Ensure action inputs have been fetched from the backend."""
        if not self._inputs_fetched:
            self._fetch_action_inputs()
            self._inputs_fetched = True

    def _fetch_action_inputs(self):
        """Fetch action input specifications from the backend."""
        actions = self._container.list_inputs(self._action_name)
        
        if not actions:
            raise ValueError(f"Action '{self._action_name}' not found or has no input parameters defined.")

        action = actions[0]
        if not action.inputs:
            raise ValueError(f"Action '{self._action_name}' found but has no input parameters defined.")

        # Setup inputs with defaults
        for input_param in action.inputs:
            input_code = input_param.code or input_param.name.lower().replace(" ", "_")
            self._inputs[input_code] = {
                "value": input_param.defaultValue[0] if input_param.defaultValue else None,
                "input": input_param
            }

    def _get_input_info(self, key: str):
        """Get input info, ensuring inputs are fetched."""
        self._ensure_inputs_fetched()
        if key not in self._inputs:
            raise KeyError(f"Input parameter '{key}' not found")
        return self._inputs[key]

    def _set_input_value(self, key: str, value):
        """Set input value with validation."""
        input_info = self._get_input_info(key)
        input_param = input_info["input"]
        
        if not self._validate_input_type(value, input_param.datatype):
            raise ValueError(
                f"Invalid value type for input '{key}'. "
                f"Expected {input_param.datatype}, got {type(value).__name__}"
            )
        
        input_info["value"] = value

    def _validate_input_type(self, value, expected_type: str) -> bool:
        """Validate input type based on the input definition."""
        if value is None or expected_type is None:
            return True
        
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected = type_map.get(expected_type)
        return expected and isinstance(value, expected)

    # Dict-like interface
    def __getitem__(self, key: str):
        return self._get_input_info(key)["value"]

    def __setitem__(self, key: str, value):
        self._set_input_value(key, value)

    def __contains__(self, key: str) -> bool:
        try:
            self._get_input_info(key)
            return True
        except KeyError:
            return False

    def __len__(self) -> int:
        self._ensure_inputs_fetched()
        return len(self._inputs)

    def __iter__(self):
        self._ensure_inputs_fetched()
        return iter(self._inputs.keys())

    # Attribute access
    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(f"Input parameter '{name}' not found") from e

    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            try:
                self[name] = value
            except KeyError as e:
                raise AttributeError(f"Input parameter '{name}' not found") from e

    # Utility methods
    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, **kwargs):
        """Update multiple inputs at once."""
        for key, value in kwargs.items():
            self[key] = value

    def keys(self):
        """Get input parameter codes."""
        self._ensure_inputs_fetched()
        return list(self._inputs.keys())

    def values(self):
        """Get input parameter values."""
        self._ensure_inputs_fetched()
        return [info["value"] for info in self._inputs.values()]

    def items(self):
        """Get input parameter code-value pairs."""
        self._ensure_inputs_fetched()
        return [(name, info["value"]) for name, info in self._inputs.items()]

    def get_input_codes(self) -> list:
        """Get a list of all available input parameter codes."""
        return self.keys()

    def get_all_inputs(self) -> dict:
        """Get all current input values."""
        return dict(self.items())

    def reset_input(self, input_code: str):
        """Reset an input parameter to its backend default value."""
        input_info = self._get_input_info(input_code)
        input_param = input_info["input"]
        input_info["value"] = input_param.defaultValue[0] if input_param.defaultValue else None

    def reset_all_inputs(self):
        """Reset all input parameters to their backend default values."""
        for input_code in self._inputs:
            self.reset_input(input_code)

    def __repr__(self):
        self._ensure_inputs_fetched()
        return f"ActionInputsProxy(action='{self._action_name}', inputs={self.get_all_inputs()})"


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

    def get_inputs_proxy(self, container) -> ActionInputsProxy:
        """Get an ActionInputsProxy for this action from a container.

        Args:
            container: The container resource (Tool or Integration) that can fetch action specs

        Returns:
            ActionInputsProxy: A proxy object for accessing action inputs
        """
        return ActionInputsProxy(container, self.name or self.slug or "")


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


class IntegrationSearchParams(BaseSearchParams):
    """Parameters for listing integrations."""

    pass


class ActionMixin:

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

    @cached_property
    def actions(self):
        """Get a proxy object that provides access to actions with their inputs.

        This enables the syntax: mytool.actions['ACTION_NAME'].channel = 'value'

        Returns:
            ActionsProxy: A proxy object for accessing actions and their inputs
        """
        return ActionsProxy(self)

    def set_inputs(self, inputs_dict: Dict[str, Dict[str, Any]]) -> None:
        """Set multiple action inputs in bulk using a dictionary tree structure.
        
        This method allows you to set inputs for multiple actions at once.
        Action names are automatically converted to lowercase for consistent lookup.
        
        Args:
            inputs_dict: Dictionary in the format:
                {
                    "ACTION_NAME": {
                        "input_param1": "value1",
                        "input_param2": "value2",
                        ...
                    },
                    "ANOTHER_ACTION": {
                        "input_param1": "value1",
                        ...
                    }
                }
        
        Example:
            tool.set_inputs({
                'slack_send_message': {  # Will work regardless of case
                    'channel': '#general',
                    'text': 'Hello from bulk set!',
                    'username': 'MyBot'
                },
                'SLACK_SEND_MESSAGE': {  # Will also work
                    'channel': '#general',
                    'text': 'Hello from bulk set!',
                    'username': 'MyBot'
                },
                'uploadFile': {  # Will also work
                    'channels': '#general',
                    'file': 'document.pdf'
                }
            })
        
        Raises:
            ValueError: If an action name is not found or invalid
            KeyError: If an input parameter is not found for an action
        """
        for action_name, input_values in inputs_dict.items():
            if not isinstance(input_values, dict):
                raise ValueError(
                    f"Input values for action '{action_name}' must be a dictionary, "
                    f"got {type(input_values).__name__}"
                )
            
            # Get the action proxy - the actions proxy will handle case conversion
            try:
                action_proxy = self.actions[action_name]
            except ValueError as e:
                raise ValueError(f"Action '{action_name}' not found: {e}")
            
            # Set all inputs for this action
            try:
                action_proxy.update(**input_values)
            except KeyError as e:
                raise KeyError(
                    f"Input parameter {e} not found for action '{action_name}'. "
                    f"Available inputs: {action_proxy.get_input_codes()}"
                )
            except Exception as e:
                raise ValueError(
                    f"Error setting inputs for action '{action_name}': {e}"
                )


class ActionsProxy:
    """Proxy object that provides access to actions with their inputs.

    This enables the syntax: mytool.actions['ACTION_NAME'].channel = 'value'
    """

    def __init__(self, container):
        self._container = container
        self._actions_cache = {}

    def __getitem__(self, action_name: str):
        """Get an action with its inputs proxy: actions['SLACK_SEND_MESSAGE'] or actions['slack_send_message']
        
        Converts action name to lowercase for consistent lookup.
        """
        # Convert action name to lowercase for consistent lookup
        normalized_name = action_name.lower()
        
        if normalized_name not in self._actions_cache:
            # Create an action object and get its inputs proxy
            # For backend calls, we need to determine the actual action name
            # Let's try to find it from available actions first
            available_actions = self._container.list_actions()
            actual_action_name = None
            
            # Look for exact match first
            for action in available_actions:
                if action.name and action.name.lower() == normalized_name:
                    actual_action_name = action.name
                    break
            
            # If no exact match, try to find by slug
            if not actual_action_name:
                for action in available_actions:
                    if action.slug and action.slug.lower() == normalized_name:
                        actual_action_name = action.slug
                        break
            
            # If still no match, use the original name as fallback
            if not actual_action_name:
                actual_action_name = action_name
            
            action = Action(name=actual_action_name)
            proxy = action.get_inputs_proxy(self._container)
            # Store the proxy in cache - errors will be raised when inputs are first accessed
            self._actions_cache[normalized_name] = proxy

        return self._actions_cache[normalized_name]

    def __getattr__(self, attr_name: str):
        """Get an action with its inputs proxy using attribute notation: actions.slack_send_message
        
        Converts attribute name to lowercase for consistent lookup.
        """
        try:
            return self[attr_name]
        except ValueError as e:
            raise AttributeError(
                f"Action '{attr_name}' not found. "
                f"Available actions: {self.get_available_actions()}. "
                f"Use actions['ACTION_NAME'] or check the action name spelling."
            ) from e

    def __contains__(self, action_name: str) -> bool:
        """Check if an action exists: 'SLACK_SEND_MESSAGE' in actions"""
        try:
            # Try to access the action to see if it exists
            self[action_name]
            return True
        except ValueError:
            return False

    def get_available_actions(self) -> List[str]:
        """Get a list of available action names."""
        actions = self._container.list_actions()
        return [action.name for action in actions if action.name]

    def refresh_cache(self):
        """Clear the actions cache to force re-fetching."""
        self._actions_cache.clear()


class Integration(Model, ActionMixin):
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

    def connect(self, **kwargs: Any) -> "Tool":
        """Connect the integration."""
        response = self.run(**kwargs)
        tool_id = response.data.id
        return self.context.Tool.get(tool_id)
