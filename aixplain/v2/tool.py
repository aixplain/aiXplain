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
from .auth_utils import AuthenticationScheme
from .integration import Integration


@dataclass_json
@dataclass
class BearerTokenAuthentication:
    """Bearer token authentication."""

    token: str
    name: Optional[str] = None
    scheme: AuthenticationScheme = AuthenticationScheme.BEARER_TOKEN


@dataclass_json
@dataclass
class OAuthAuthentication:
    """OAuth authentication with client credentials."""

    client_id: str
    client_secret: str
    name: Optional[str] = None
    scheme: AuthenticationScheme = AuthenticationScheme.OAUTH


@dataclass_json
@dataclass
class OAuth2Authentication:
    """OAuth2 authentication (default, no additional credentials needed)."""

    name: Optional[str] = None
    scheme: AuthenticationScheme = AuthenticationScheme.OAUTH2


# Union type for all authentication types
Authentication = Union[
    BearerTokenAuthentication, OAuthAuthentication, OAuth2Authentication
]


class ToolListParams(BaseListParams):
    """Parameters for listing tools."""

    pass


class ToolRunParams(BareRunParams):
    """Parameters for running tools."""

    action: str
    params: dict


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
    authentication: Optional[Authentication] = None

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
            if self.authentication:
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

        if not self.authentication:
            raise ValueError("No authentication provided for this tool")

        # Build the connection payload based on authentication type
        payload = self._build_connection_payload()
        result = self.integration.connect(**payload)
        self.id = result["id"]
        return result

    def _build_connection_payload(self) -> dict:
        """Build the connection payload based on authentication type."""
        from .auth_utils import build_connection_payload_from_auth

        return build_connection_payload_from_auth(self.authentication)

    def build_run_url(self, **kwargs: Unpack[ToolRunParams]) -> str:
        """
        Build the URL for running the tool.

        Tools use the same MODELS_RUN_URL as connections for execution.
        """
        return f"{self.context.MODELS_RUN_URL}/{self.id}"
