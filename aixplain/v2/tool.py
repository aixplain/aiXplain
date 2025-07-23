from typing import Union, List, Optional
from typing_extensions import Unpack
from dataclasses_json import dataclass_json
from dataclasses import dataclass

from .resource import (
    BaseListParams,
    BaseResource,
    PlainListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    DeleteResourceMixin,
    BareDeleteParams,
    RunnableResourceMixin,
    BareRunParams,
    Result,
)
from .integration import Integration
from .model import Model


class ToolListParams(BaseListParams):
    """Parameters for listing tools."""

    pass


class ToolRunParams(BareRunParams):
    """Parameters for running tools."""

    action: str
    data: dict


@dataclass_json
@dataclass
class ToolResult(Result):
    """Result for a tool."""

    pass


@dataclass_json
@dataclass
class Tool(
    BaseResource,
    PlainListResourceMixin,
    GetResourceMixin[BareGetParams, "Tool"],
    DeleteResourceMixin[BareDeleteParams, "Tool"],
    RunnableResourceMixin[ToolRunParams, ToolResult],
):
    """Convenient wrapper class for tool representations.

    This class automatically creates the appropriate underlying resource
    based on constructor arguments and passes through all args/kwargs.
    """

    # Tools are not standalone resources, so we don't have a direct save
    # endpoint
    # Use models endpoint for getting existing tools
    RESOURCE_PATH = "sdk/models"
    RESPONSE_CLASS = ToolResult

    DEFAULT_INTEGRATION_ID = "686432941223092cb4294d3f"  # Script integration
    integration: Optional[Union[Integration, str]] = None
    config: Optional[dict] = None
    code: Optional[str] = None
    allowed_actions: Optional[List[str]] = None
    auth_scheme: Optional[Integration.AuthenticationScheme] = None
    auth_credentials: Optional[Integration.Credentials] = None
    connection: Optional[Model] = None

    def __post_init__(self):
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

            # Auto-connect for integration tools
            self.connect()

    def connect(self) -> ToolResult:
        """Connect to the integration if one is set.

        This method creates a connection to the integration and sets the tool ID
        to the connection ID.

        Returns:
            Result: The connection result
        """
        if not self.integration:
            raise ValueError("No integration set for this tool")

        if not self.auth_scheme:
            raise ValueError("No authentication provided for this tool")

        if not self.auth_credentials:
            raise ValueError("No authentication credentials provided for this tool")

        # Build the connection payload based on authentication type
        result = self.integration.connect(
            name=self.name,
            auth_scheme=self.auth_scheme,
            data=self.auth_credentials,
        )

        # Set the tool ID to the connection ID
        connection_id = result.data["id"]
        self.connection = self.context.Model.get(connection_id)

    def run(self, **kwargs: Unpack[ToolRunParams]) -> ToolResult:
        """Run the tool."""

        if not self.connection:
            raise ValueError("No connection set for this tool")

        return self.connection.run(**kwargs)
