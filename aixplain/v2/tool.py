"""Tool resource module for managing tools and their integrations."""

import warnings
from typing import Union, List, Optional, Any
from typing_extensions import Unpack
from dataclasses_json import dataclass_json, config as dj_config
from dataclasses import dataclass, field

from .resource import (
    Result,
    DeleteResourceMixin,
    BaseDeleteParams,
    DeleteResult,
)
from .model import Model, ModelRunParams
from .integration import Integration, Action, ActionMixin


@dataclass_json
@dataclass(repr=False)
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass(repr=False)
class Tool(Model, DeleteResourceMixin[BaseDeleteParams, DeleteResult], ActionMixin):
    """Resource for tools.

    This class represents a tool resource that matches the backend structure.
    Tools can be integrations, utilities, or other specialized resources.
    Inherits from Model to reuse shared attributes and functionality.
    """

    RESOURCE_PATH = "v2/tools"
    RESPONSE_CLASS = ToolResult
    DEFAULT_INTEGRATION_ID = "686432941223092cb4294d3f"  # Script integration

    # Tool-specific fields
    asset_id: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))
    subscriptions: Optional[Any] = field(default=None)
    integration: Optional[Union[Integration, str]] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    config: Optional[dict] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    code: Optional[str] = field(default=None, metadata=dj_config(exclude=lambda x: True))
    allowed_actions: Optional[List[str]] = field(default_factory=list, metadata=dj_config(field_name="allowedActions"))

    def __post_init__(self) -> None:
        """Initialize tool after dataclass creation.

        Sets up default integration for utility tools if no integration is provided.
        Validates integration type if provided.
        """
        if not self.id:
            if self.integration is None:
                code = self.code or (
                    self.config.pop("code", None) if self.config else None
                )
                assert code is not None, "Code is required to create a (script) Tool"
                # Use default integration ID for utility tools (store as string, will be fetched on save)
                self.integration = self.DEFAULT_INTEGRATION_ID
                self.config = {
                    "code": code,
                }
            else:
                # Allow integration to be a string or Integration instance
                # String will be resolved to Integration instance during save operation
                if isinstance(self.integration, str):
                    # Keep as string - will be fetched during save
                    pass
                elif not isinstance(self.integration, Integration):
                    raise ValueError(
                        "Integration must be an Integration object or a string"
                    )

    def _ensure_integration(self, required: bool = False) -> bool:
        """Ensure integration is resolved to an Integration instance.

        Args:
            required: If True, raise ValueError if integration is missing or cannot be resolved.

        Returns:
            True if integration is available and resolved, False otherwise.

        Raises:
            ValueError: If required=True and integration is missing or cannot be resolved.
        """
        if not self.integration:
            if required:
                raise ValueError("Integration is required")
            return False

        # Resolve integration string to Integration instance if needed
        if isinstance(self.integration, str):
            try:
                self.integration = self.context.Integration.get(self.integration)
            except Exception as e:
                if required:
                    raise ValueError(f"Failed to resolve integration: {e}") from e
                return False

        if not isinstance(self.integration, Integration):
            if required:
                raise ValueError(
                    "Integration must be an Integration object or a string"
                )
            return False

        return True

    def list_actions(self) -> List[Action]:
        """List available actions for the tool.

        Overrides parent method to add fallback to base integration.

        Returns:
            List of Action objects available for this tool. Falls back to
            integration's list_actions() if tool's own method fails.
        """
        try:
            actions = super().list_actions()
            return actions
        except Exception as e:
            warnings.warn(
                f"Error listing actions: {e}. Using integration.list_actions() instead."
            )
            if self._ensure_integration():
                return self.integration.list_actions()

            return []

    def list_inputs(self, *actions: str) -> List["Action"]:
        """List available inputs for specified actions.

        Overrides parent method to add fallback to base integration.

        Args:
            *actions: Variable number of action names to get inputs for.

        Returns:
            List of Action objects with their input specifications. Falls back to
            integration's list_inputs() if tool's own method fails.
        """
        try:
            inputs = super().list_inputs(*actions)
            return inputs
        except Exception as e:
            warnings.warn(
                f"Error listing inputs: {e}. Using integration.list_inputs() instead."
            )
            if self._ensure_integration():
                try:
                    return self.integration.list_inputs(*actions)
                except Exception:
                    pass

            return []

    def _create(self, resource_path: str, payload: dict) -> None:
        """Create the tool by connecting to the integration."""
        self._ensure_integration(required=True)

        payload = {}

        if self.name:
            payload["name"] = self.name
        if self.description:
            payload["description"] = self.description

        if self.config:
            data = self.config.pop("data", {})
            data.update(self.config)
            payload["data"] = data

        connection = self.integration.connect(**payload)

        self.id = connection.id

        # Map attributes from connection to tool if they are None
        for attr_name in self.__dataclass_fields__:
            if not getattr(self, attr_name) and getattr(connection, attr_name, None):
                setattr(self, attr_name, getattr(connection, attr_name))

    def _update(self, resource_path: str, payload: dict) -> None:
        raise NotImplementedError("Updating a tool is not supported yet")

    def _is_utility_model_without_integration(self) -> bool:
        """Check if this is a utility model accessed via Tool.get() without real integration.

        This distinguishes between:
        1. Real tools (created via Tool() with actual integrations)
        2. Utility models (accessed via Tool.get() that are just models exposed through tools endpoint)
        """
        from .enums import Function

        # Must be a utility function
        if not (self.function_type == "ai" and self.function == Function.UTILITIES):
            return False

        # Must NOT have a real integration object (created tools have integrations)
        if hasattr(self, "integration") and self.integration is not None:
            return False

        # Must have been retrieved (has ID) but not created locally
        if not self.id:
            return False

        # Check if actions_available field suggests it should have actions but doesn't
        actions_available = getattr(self, "actions_available", None)
        if hasattr(actions_available, "__class__") and "Field" in str(
            type(actions_available)
        ):
            # Field deserialization issue - assume True for utility models
            actions_available = True

        return bool(actions_available)

    def validate_allowed_actions(self) -> None:
        """Validate that all allowed actions are available for this tool.

        Checks that:
        - Integration is available
        - All actions in allowed_actions list exist in the integration

        Raises:
            AssertionError: If validation fails.
        """
        if self.allowed_actions:
            assert (
                self.integration is not None
            ), "Integration is required to validate allowed actions"

            available_actions = [action.name for action in self.list_actions()]
            assert (
                available_actions is not None
            ), "Integration must have available actions"
            assert all(
                action in available_actions for action in self.allowed_actions
            ), "All allowed actions must be available"

    def get_parameters(self) -> List[dict]:
        """Get parameters for the tool in the format expected by agent saving.

        This method includes both static backend values and dynamically set values
        from the ActionInputsProxy instances, ensuring agents get the current
        configured action inputs.
        """
        self.validate_allowed_actions()

        parameters = []

        # Get all actions at once to avoid multiple API calls
        actions = self.list_inputs(*self.allowed_actions)

        for action in actions:
            # Convert action inputs to the expected parameter format
            action_inputs = {}

            # Get the current action proxy to access dynamically set values
            action_proxy = None
            action_name = action.name or action.slug or ""
            if action_name:
                try:
                    action_proxy = self.actions[action_name]
                except (ValueError, KeyError):
                    # If we can't get the action proxy, skip this action
                    continue

            for input_param in action.inputs:
                input_code = input_param.code or input_param.name.lower().replace(
                    " ", "_"
                )

                # Get the current value from the action proxy if available
                current_value = None
                if action_proxy:
                    current_value = action_proxy.get(input_code)

                # Fall back to backend default if no current value
                if current_value is None and input_param.defaultValue:
                    current_value = (
                        input_param.defaultValue[0]
                        if input_param.defaultValue
                        else None
                    )

                action_inputs[input_code] = {
                    "name": input_param.name,
                    "value": current_value,
                    "required": input_param.required,
                    "datatype": input_param.datatype,
                    "allowMulti": input_param.allowMulti,
                    "supportsVariables": input_param.supportsVariables,
                    "fixed": input_param.fixed,
                    "description": input_param.description,
                }

            parameters.append(
                {
                    "code": action.slug,
                    "name": action_name,
                    "description": action.description or "",
                    "inputs": action_inputs,
                }
            )

        return parameters

    def _validate_params(self, **kwargs: Any) -> List[str]:
        """Validate parameters for the tool.

        Tool validation uses ACTION-based validation (via ActionInputsProxy),
        NOT model parameter validation. This is because tools run actions with
        action-specific inputs, not direct model parameters.
        """
        errors = []

        # For utility models without integration, use model validation
        if (
            self._is_utility_model_without_integration()
            and "data" in kwargs
            and isinstance(kwargs["data"], dict)
        ):
            # Validate the parameters inside the data field
            model_kwargs = kwargs["data"]
            errors = super()._validate_params(**model_kwargs)
            return errors

        # For regular tools with integrations, use ACTION validation
        # 1. Check action is provided
        action = kwargs.get("action")
        if not action:
            errors.append("action is required")
            return errors

        # 2. Validate allowed actions
        try:
            self.validate_allowed_actions()
        except AssertionError as e:
            errors.append(str(e))
            return errors

        if self.allowed_actions and action not in self.allowed_actions:
            errors.append(
                f"Action '{action}' is not allowed for this tool. Allowed actions: {self.allowed_actions}"
            )
            return errors

        # 3. Validate action inputs using ActionInputsProxy
        # This uses the integration's action spec, not self.params
        try:
            action_proxy = self.actions[action]
            data = kwargs.get("data", {})

            # Use ActionInputsProxy.validate() for action input validation
            action_errors = action_proxy.validate(data)
            errors.extend(action_errors)
        except Exception:
            # If we can't get action spec or validate, skip validation
            # Let the backend handle it - this is a fallback for edge cases
            pass

        return errors

    def run(self, *args: Any, **kwargs: Unpack[ModelRunParams]) -> ToolResult:
        """Run the tool."""
        self._ensure_valid_state()

        if len(args) > 0:
            kwargs["data"] = args[0]
            args = args[1:]

        # If no action is provided and we have allowed actions, use the first one
        if "action" not in kwargs:
            if self.allowed_actions and len(self.allowed_actions) == 1:
                kwargs["action"] = self.allowed_actions[0]
            else:
                available_actions = [action.name for action in self.list_actions()]
                if available_actions and len(available_actions) == 1:
                    kwargs["action"] = available_actions[0]
                else:
                    raise ValueError("No action provided")

        if "action" not in kwargs:
            raise ValueError("No action provided")

        return super().run(*args, **kwargs)

    def _merge_with_dynamic_attrs(self, **kwargs) -> dict:
        """Override to handle tool-specific parameter merging.

        Tools don't have the standard 'inputs' attribute like models do,
        so we need to handle parameter merging differently.
        """
        # Original tool logic for real integration-based tools
        merged = {}
        action_name = kwargs.get("action")
        if not action_name and len(self.allowed_actions) == 1:
            action_name = self.allowed_actions[0]

        if not action_name:
            raise ValueError("No action provided")

        action_proxy = self.actions[action_name]

        # Extract all current input values
        for input_code in action_proxy.keys():
            value = action_proxy.get(input_code)
            if value is not None:
                merged[input_code] = value

        kwargs.setdefault("data", {})

        # Handle both string and dict data
        if isinstance(kwargs["data"], str):
            # For string data (like AIXplain Search), pass it directly
            # Include all other parameters (like dataType) in the request
            result = {
                "action": action_name,
                "data": kwargs["data"],
            }
            # Add all other parameters except 'data' and 'action'
            for key, value in kwargs.items():
                if key not in ["data", "action"]:
                    result[key] = value
            return result
        elif isinstance(kwargs["data"], list):
            return {
                "action": action_name,
                "data": kwargs["data"],
            }
        else:
            # For dict data, merge with merged parameters
            return {
                "action": action_name,
                "data": {
                    **merged,
                    **kwargs["data"],
                },
            }
