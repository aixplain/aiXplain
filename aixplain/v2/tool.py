from typing import Union, List, Optional, Any
from typing_extensions import Unpack
from dataclasses_json import dataclass_json
from dataclasses import dataclass

from .resource import (
    BaseListParams,
    BaseRunParams,
    Result,
)
from .integration import Integration
from .model import Model
from .exceptions import ValidationError, ResourceError


@dataclass_json
@dataclass
class InputParameter:
    name: str
    code: str
    value: List[Any]
    availableOptions: List[Any]
    datatype: str
    allowMulti: bool
    supportsVariables: bool
    defaultValue: List[Any]
    required: bool
    fixed: bool
    description: str


@dataclass_json
@dataclass
class ToolAction:
    """Container for tool action information and inputs."""

    slug: str
    name: str
    description: str
    available_versions: List[str]
    version: str
    toolkit: dict
    input_parameters: dict
    output_parameters: dict
    scopes: List[str]
    tags: List[str]
    no_auth: bool
    deprecated: dict
    displayName: str
    inputs: List[InputParameter]


class ToolListParams(BaseListParams):
    """Parameters for listing tools."""

    pass


class ToolRunParams(BaseRunParams):
    """Parameters for running tools."""

    action: Optional[str] = None
    data: dict


@dataclass_json
@dataclass
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass
class Tool(Model):
    RESPONSE_CLASS = ToolResult

    DEFAULT_INTEGRATION_ID = "686432941223092cb4294d3f"  # Script integration
    integration: Optional[Union[Integration, str]] = None
    config: Optional[dict] = None
    code: Optional[str] = None
    allowed_actions: Optional[List[str]] = None
    auth_scheme: Optional[Integration.AuthenticationScheme] = (
        Integration.AuthenticationScheme.BEARER_TOKEN
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
            else:
                if isinstance(self.integration, str):
                    self.integration = self.context.Integration.get(self.integration)

                assert isinstance(
                    self.integration, Integration
                ), "Integration must be an Integration object or a string"

            self.validate_allowed_actions()

            # Auto-connect for integration tools
            self.connect()

    def validate_allowed_actions(self) -> None:
        if self.allowed_actions:
            assert (
                self.integration is not None
            ), "Integration is required to validate allowed actions"
            assert (
                self.integration.get_available_actions() is not None
            ), "Integration must have available actions"
            available_actions = self.integration.get_available_actions()
            assert all(
                action in available_actions for action in self.allowed_actions
            ), "All allowed actions must be available"

    def connect(self) -> ToolResult:
        if not self.integration:
            raise ValidationError("No integration set for this tool")

        if not self.auth_scheme:
            raise ResourceError("No authentication provided for this tool")

        if not self.config:
            raise ResourceError("No authentication credentials provided for this tool")

        auth_credentials = {}
        if "token" in self.config:
            auth_credentials["token"] = self.config.pop("token")
        elif "client_id" in self.config and "client_secret" in self.config:
            auth_credentials["client_id"] = self.config.pop("client_id")
            auth_credentials["client_secret"] = self.config.pop("client_secret")
        else:
            raise ValueError("No authentication credentials provided for this tool")

        # Build the connection payload based on authentication type
        result = self.integration.run(
            name=self.name,
            auth_scheme=self.auth_scheme,
            data=auth_credentials,
        )
        self.id = result.data["id"]

    def _get_actions(self) -> List[ToolAction]:
        """Get input parameters for specific actions."""
        if not self.allowed_actions:
            return []

        response = super().run(
            action="LIST_INPUTS", data={"actions": self.allowed_actions}
        )
        return [ToolAction.from_dict(action_data) for action_data in response.data]

    def get_parameters(self) -> List[dict]:
        """Get parameters for the tool in the format expected by agent saving."""
        parameters = []
        for action in self._get_actions():
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

    def run(self, **kwargs: Unpack[ToolRunParams]) -> ToolResult:
        """Run the tool."""
        kwargs.setdefault("action", self.allowed_actions[0])
        return super().run(**kwargs)
