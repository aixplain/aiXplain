from typing import Union, List, Optional, Any
from typing_extensions import Unpack
from dataclasses_json import dataclass_json, config as dj_config
from dataclasses import dataclass, field

from .resource import (
    BaseListParams,
    BaseRunParams,
    Result,
    DeleteResourceMixin,
    BaseDeleteParams,
    BaseGetParams,
    GetResourceMixin,
    BaseResource,
    RunnableResourceMixin,
    ToolMixin,
)
from .model import ModelRunParams
from .integration import Integration


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

    data: dict
    action: Optional[str] = None


@dataclass_json
@dataclass
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass
class Tool(
    BaseResource,
    GetResourceMixin[BaseGetParams, "Model"],
    RunnableResourceMixin[ModelRunParams, Result],
    DeleteResourceMixin[BaseDeleteParams, "Tool"],
    ToolMixin,
):

    RESOURCE_PATH = "sdk/models"
    RESPONSE_CLASS = ToolResult
    DEFAULT_INTEGRATION_ID = "686432941223092cb4294d3f"  # Script integration

    supplier: str = field(
        default="aixplain",  # Use lowercase to match working
        metadata=dj_config(field_name="supplier"),
    )
    function: Optional[str] = field(
        default=None,  # Use None to match working
        metadata=dj_config(field_name="function"),
    )
    type: str = field(default="model", metadata=dj_config(field_name="type"))
    version: Optional[str] = field(
        default=None, metadata=dj_config(field_name="version")
    )
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
            else:
                if isinstance(self.integration, str):
                    self.integration = self.context.Integration.get(self.integration)

                assert isinstance(
                    self.integration, Integration
                ), "Integration must be an Integration object or a string"

            self.validate_allowed_actions()

            # Auto-connect for integration tools
            self.connect()
            self.parameters = self.get_parameters()

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

    def validate_auth_credentials(self) -> dict:
        """Validate and extract authentication credentials based on auth scheme."""
        # Scheme to required fields mapping
        scheme_fields = {
            Integration.AuthenticationScheme.NO_AUTH: [],
            Integration.AuthenticationScheme.BEARER_TOKEN: ["token"],
            Integration.AuthenticationScheme.OAUTH2: ["client_id", "client_secret"],
            Integration.AuthenticationScheme.OAUTH1: [
                "consumer_key",
                "consumer_secret",
            ],
            Integration.AuthenticationScheme.API_KEY: ["api_key"],
            Integration.AuthenticationScheme.BASIC: ["username", "password"],
        }

        if self.auth_scheme not in scheme_fields:
            raise ValueError(f"Unsupported authentication scheme: {self.auth_scheme}")

        required_fields = scheme_fields[self.auth_scheme]

        # Validate all required fields are present
        for field_name in required_fields:
            if field_name not in self.config:
                raise AssertionError(
                    f"{field_name.replace('_', ' ').title()} is required "
                    f"for this tool"
                )

        # Extract and return credentials
        credentials = {}
        for field_name in required_fields:
            credentials[field_name] = self.config.pop(field_name)

        return credentials

    def connect(self) -> ToolResult:
        """Connect the tool using validated authentication credentials."""
        # Validate and extract authentication credentials
        auth_credentials = self.validate_auth_credentials()

        # Build the connection payload based on authentication type
        result = self.integration.run(
            name=self.name,
            auth_scheme=self.auth_scheme,
            data=auth_credentials,
        )
        self.id = result.data["id"]
        self.asset_id = self.id

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

    def run(self, *args: Any, **kwargs: Unpack[ToolRunParams]) -> ToolResult:
        """Run the tool."""
        if len(args) > 0:
            kwargs["data"] = args[0]
            args = args[1:]

        if "action" not in kwargs and self.allowed_actions:
            kwargs["action"] = self.allowed_actions[0]
        else:
            raise ValueError("No action provided")

        return super().run(*args, **kwargs)

    def build_run_url(self, **kwargs: Unpack[ModelRunParams]) -> str:
        # Use api/v2/execute instead of api/v1/execute
        url = f"{self.context.model_url}/{self.id}"
        return url.replace("/api/v1/execute", "/api/v2/execute")
