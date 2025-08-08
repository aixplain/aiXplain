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
from .integration import Integration, Action, Input


@dataclass_json
@dataclass
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass
class Tool(Model, DeleteResourceMixin[BaseDeleteParams, DeleteResult]):
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
    auth_params: Optional[dict] = field(
        default=None, metadata=dj_config(exclude=lambda x: True)
    )
    parameters: Optional[List[dict]] = field(default_factory=list)

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
                authScheme=self.auth_scheme, data=self.auth_params
            )
            self.id = connection.id
            self.validate_allowed_actions()
            self.parameters = self.get_parameters()

    def list_actions(self) -> List[Action]:
        """List available actions for the tool."""
        return self.integration.list_actions()

    def list_inputs(self, *actions: str) -> List[Input]:
        """List available inputs for the tool."""
        return self.integration.list_inputs(*actions)

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
        """Get parameters for the tool in the format expected by agent saving."""
        parameters = []
        for action in self.list_inputs(*self.allowed_actions):
            # Convert action inputs to the expected parameter format
            action_inputs = {}
            for input_param in action.inputs:
                action_inputs[input_param.code] = {
                    "name": input_param.name,
                    "value": (
                        input_param.value[0]
                        if input_param.value
                        else (
                            input_param.defaultValue[0]
                            if input_param.defaultValue
                            else None
                        )
                    ),
                    "required": input_param.required,
                    "datatype": input_param.datatype,
                    "description": input_param.description,
                }

            parameters.append(
                {
                    "code": action.slug,
                    "name": action.name,
                    "description": action.description,
                    "inputs": action_inputs,
                }
            )
        return parameters

    def _validate_params(self, **kwargs: Any) -> List[str]:
        """Validate parameters for the tool."""
        errors = super()._validate_params(**kwargs)
        if "action" not in kwargs:
            errors.append("action is required")

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
