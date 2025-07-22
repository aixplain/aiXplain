from dataclasses import dataclass
from typing import Optional, List
from dataclasses_json import dataclass_json

from .resource import (
    BaseResource,
    PlainListResourceMixin,
    GetResourceMixin,
    DeleteResourceMixin,
    RunnableResourceMixin,
    BaseListParams,
    BareGetParams,
    BareDeleteParams,
    BareRunParams,
    BaseResult,
)


class ToolListParams(BaseListParams):
    """Parameters for listing tools."""

    pass


class ToolRunParams(BareRunParams):
    """Parameters for running a tool."""

    pass


@dataclass_json
@dataclass
class ToolResult(BaseResult):
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
    integration_id: Optional[str] = None
    config: Optional[dict] = None
    code: Optional[str] = None
    allowed_actions: Optional[List[str]] = None

    def __post_init__(self):
        if not self.id:
            if self.integration_id is None:
                assert self.code is not None, "Code is required to create a Tool"
                # Use default integration ID for utility tools
                self.integration_id = self.DEFAULT_INTEGRATION_ID
                self.config = {
                    "code": self.code,
                }
            # Auto-connect for integration tools
            self.connect()

    def connect(self, name: Optional[str] = None, **kwargs) -> ToolResult:
        """Connect to the integration if one is set.

        This method creates a connection to the integration and sets the tool ID
        to the connection ID.

        Args:
            name: Optional name for the connection
            **kwargs: Additional connection parameters (token, client_id,
                     client_secret, etc.)

        Returns:
            Result: The connection result
        """
        if not self.integration_id:
            raise ValueError("No integration ID set for this tool")

        # Get the integration object and connect
        integration_obj = self.context.Integration.get(self.integration_id)
        response = integration_obj.connect(name=name, **kwargs)

        # Handle the response properly
        if response.completed and response.status == "SUCCESS":
            if (
                response.data
                and isinstance(response.data, dict)
                and "id" in response.data
            ):
                self.id = response.data["id"]
            elif hasattr(response, "id") and response.id:
                self.id = response.id
            else:
                # If no ID in response, use the integration ID as a fallback
                self.id = self.integration_id
        else:
            # Connection failed, but don't raise exception
            print(
                f"Warning: Connection failed with status {response.status}: "
                f"{response.error_message}"
            )
            # Use integration ID as fallback
            self.id = self.integration_id

        return response
