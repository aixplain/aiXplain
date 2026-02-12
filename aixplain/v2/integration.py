"""Integration module for managing external service integrations."""

from typing import Optional, List, Any, Dict, TYPE_CHECKING
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from functools import cached_property

from .resource import BaseSearchParams, Result
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
        """Initialize ActionInputsProxy with container and action name."""
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
                "value": (input_param.defaultValue[0] if input_param.defaultValue else None),
                "input": input_param,
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
                f"Invalid value type for input '{key}'. Expected {input_param.datatype}, got {type(value).__name__}"
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
            "object": dict,
        }

        expected = type_map.get(expected_type)
        return expected and isinstance(value, expected)

    # Dict-like interface
    def __getitem__(self, key: str):
        """Get input value by key."""
        return self._get_input_info(key)["value"]

    def __setitem__(self, key: str, value):
        """Set input value by key."""
        self._set_input_value(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if input parameter exists."""
        try:
            self._ensure_inputs_fetched()
            return key in self._inputs
        except (ValueError, KeyError):
            return False

    def __len__(self) -> int:
        """Return the number of input parameters."""
        self._ensure_inputs_fetched()
        return len(self._inputs)

    def __iter__(self):
        """Iterate over input parameter keys."""
        self._ensure_inputs_fetched()
        return iter(self._inputs.keys())

    # Attribute access
    def __getattr__(self, name: str):
        """Get input value by attribute name."""
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(f"Input parameter '{name}' not found") from e

    def __setattr__(self, name: str, value):
        """Set input value by attribute name."""
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            try:
                self[name] = value
            except KeyError as e:
                raise AttributeError(f"Input parameter '{name}' not found") from e

    # Utility methods
    def get(self, key: str, default=None):
        """Get input value with optional default."""
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

    # Remove redundant wrapper methods - these just duplicate existing functionality
    # def get_input_codes(self) -> list:  # Just calls self.keys()
    # def get_all_inputs(self) -> dict:  # Just calls dict(self.items())

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
        """Return string representation of the proxy."""
        self._ensure_inputs_fetched()
        return f"ActionInputsProxy(action='{self._action_name}', inputs={dict(self.items())})"


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
@dataclass(repr=False)
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

    def __repr__(self) -> str:
        """Return a string representation showing name and input parameters."""
        name_str = self.name or self.slug or "Unknown"

        # Show input_parameters if available, otherwise show inputs summary
        if self.input_parameters:
            input_params_str = str(self.input_parameters)
        elif self.inputs:
            # Create a summary of input names
            input_names = [inp.name for inp in self.inputs if inp.name]
            input_params_str = f"[{', '.join(input_names)}]" if input_names else "[]"
        else:
            input_params_str = "[]"

        return f"Action(name='{name_str}', input_parameters={input_params_str})"

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


@dataclass_json
@dataclass
class IntegrationResult(Result):
    """Result for connection operations.

    The backend returns the connection ID in data.id.
    """

    data: ToolId


class IntegrationSearchParams(BaseSearchParams):
    """Parameters for listing integrations."""

    pass


class ActionMixin:
    """Mixin class providing action-related functionality for integrations and tools."""

    # Integration-specific fields
    actions_available: Optional[bool] = field(default=None, metadata=config(field_name="actionsAvailable"))

    def list_actions(self) -> List[Action]:
        """List available actions for the integration."""
        if not self.actions_available:
            return []

        run_url = self.build_run_url()
        response = self.context.client.request("post", run_url, json={"action": "LIST_ACTIONS", "data": {}})

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

        data = response["data"]
        if not isinstance(data, list):
            return []

        actions = []
        for input_data in data:
            if isinstance(input_data, dict):
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
                    f"Input values for action '{action_name}' must be a dictionary, got {type(input_values).__name__}"
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
                    f"Available inputs: {list(action_proxy.keys())}"
                )
            except Exception as e:
                raise ValueError(f"Error setting inputs for action '{action_name}': {e}")


class ActionsProxy:
    """Proxy object that provides access to actions with their inputs.

    This enables the syntax: mytool.actions['ACTION_NAME'].channel = 'value'
    """

    def __init__(self, container):
        """Initialize ActionsProxy with container resource."""
        self._container = container
        self._actions_cache = {}
        self._available_actions_cache = None
        self._actions_cache_timestamp = None

    def _get_available_actions(self):
        """Get available actions with caching to avoid redundant API calls."""
        if self._available_actions_cache is None:
            self._available_actions_cache = self._container.list_actions()
        return self._available_actions_cache

    def _resolve_action_name(self, action_name: str) -> str:
        """Resolve the actual backend action name from user input."""
        normalized_name = action_name.lower()
        available_actions = self._get_available_actions()

        # Look for exact match first
        for action in available_actions:
            if action.name and action.name.lower() == normalized_name:
                return action.name
            if action.slug and action.slug.lower() == normalized_name:
                return action.slug

        # If no match found, use the original name as fallback
        return action_name

    def __getitem__(self, action_name: str):
        """Get an action with its inputs proxy.

        Converts action name to lowercase for consistent lookup.
        """
        normalized_name = action_name.lower()

        if normalized_name not in self._actions_cache:
            # Resolve the actual backend action name
            actual_action_name = self._resolve_action_name(action_name)

            # Create action object and get its inputs proxy
            action = Action(name=actual_action_name)
            proxy = action.get_inputs_proxy(self._container)

            # Store the proxy in cache
            self._actions_cache[normalized_name] = proxy

        return self._actions_cache[normalized_name]

    def __getattr__(self, attr_name: str):
        """Get an action with its inputs proxy using attribute notation.

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
        """Check if an action exists."""
        try:
            # Try to access the action to see if it exists
            self[action_name]
            return True
        except ValueError:
            return False

    def get_available_actions(self) -> List[str]:
        """Get a list of available action names."""
        available_actions = self._get_available_actions()
        return [action.name for action in available_actions if action.name]

    def refresh_cache(self):
        """Clear the actions cache to force re-fetching."""
        self._actions_cache.clear()
        self._available_actions_cache = None


class Integration(Model, ActionMixin):
    """Resource for integrations.

    Integrations are a subtype of models with Function.CONNECTOR.
    All connection logic is centralized here.
    """

    RESOURCE_PATH = "v2/integrations"
    RESPONSE_CLASS = IntegrationResult

    # Make AuthenticationScheme accessible
    AuthenticationScheme = AuthenticationScheme

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

    def handle_run_response(self, response: dict, **kwargs: Any) -> IntegrationResult:
        """Handle the response from the integration."""
        try:
            return super().handle_run_response(response)
        except Exception:
            if "data" in response and isinstance(response["data"], str):
                # Create a copy of response and wrap the string ID
                wrapped_response = response.copy()
                wrapped_response["data"] = {"id": response["data"]}
                return super().handle_run_response(wrapped_response)
            else:
                # Re-raise the exception if we can't handle it
                raise
