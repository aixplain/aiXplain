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
from .integration import Integration, Action, Input, ActionMixin


@dataclass_json
@dataclass
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass
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
    asset_id: Optional[str] = field(
        default=None, metadata=dj_config(field_name="assetId")
    )
    integration: Optional[Union[Integration, str]] = field(
        default=None, metadata=dj_config(exclude=lambda x: True)
    )
    config: Optional[dict] = field(
        default=None, metadata=dj_config(exclude=lambda x: True)
    )
    code: Optional[str] = field(
        default=None, metadata=dj_config(exclude=lambda x: True)
    )
    allowed_actions: Optional[List[str]] = field(
        default_factory=list, metadata=dj_config(field_name="allowedActions")
    )
    auth_scheme: Optional[Integration.AuthenticationScheme] = field(
        default=Integration.AuthenticationScheme.NO_AUTH,
        metadata=dj_config(exclude=lambda x: True),
    )

    def __post_init__(self) -> None:
        if not self.id:
            if self.integration is None:
                assert self.code is not None, "Code is required to create a Tool"
                # Use default integration ID for utility tools
                self.integration = self.context.Integration.get(
                    self.DEFAULT_INTEGRATION_ID
                )
                self.config = {
                    "code": self.code,
                }
                self.auth_scheme = Integration.AuthenticationScheme.NO_AUTH
            else:
                if isinstance(self.integration, str):
                    self.integration = self.context.Integration.get(self.integration)

                assert isinstance(
                    self.integration, Integration
                ), "Integration must be an Integration object or a string"

            connection = self.integration.connect(
                authScheme=self.auth_scheme, data=self.config
            )
            self.id = self.asset_id = connection.id
            self.function = self.integration.function
            self.function_type = self.integration.function_type

    def validate_allowed_actions(self) -> None:
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
        """Validate parameters for the tool."""
        errors = super()._validate_params(**kwargs)
        if "action" not in kwargs:
            errors.append("action is required")

        self.validate_allowed_actions()

        action = kwargs["action"]
        if action not in self.allowed_actions:
            errors.append(f"Action {action} is not allowed for this tool")

        return errors

    def run(self, *args: Any, **kwargs: Unpack[ModelRunParams]) -> ToolResult:
        """Run the tool."""
        if len(args) > 0:
            kwargs["data"] = args[0]
            args = args[1:]

        # If no action is provided and we have allowed actions, use the first one
        if "action" not in kwargs:
            if self.allowed_actions and len(self.allowed_actions) == 1:
                kwargs["action"] = self.allowed_actions[0]

        if "action" not in kwargs:
            raise ValueError("No action provided")

        return super().run(*args, **kwargs)

    def _merge_with_dynamic_attrs(self, **kwargs) -> dict:
        """Override to handle tool-specific parameter merging.

        Tools don't have the standard 'inputs' attribute like models do,
        so we need to handle parameter merging differently.
        """
        # Start with current tool parameters
        merged = {}

        # For tools, we need to get the current action input values from the actions
        if hasattr(self, "actions") and self.allowed_actions:
            # Get the first allowed action (or use the one specified in kwargs)
            action_name = kwargs.get("action", self.allowed_actions[0])

            try:
                # Get the action proxy to access current input values
                action_proxy = self.actions[action_name]

                # Extract all current input values
                for input_code in action_proxy.keys():
                    value = action_proxy.get(input_code)
                    if value is not None:
                        merged[input_code] = value

            except (ValueError, KeyError) as e:
                # If we can't get the action proxy, just continue with empty merged
                pass

        # Add any additional kwargs
        merged.update(kwargs)

        # Ensure the action parameter is preserved
        if "action" in kwargs:
            merged["action"] = kwargs["action"]

        return merged
