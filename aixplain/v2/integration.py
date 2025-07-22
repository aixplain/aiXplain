from typing_extensions import Unpack
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Optional

from .resource import (
    BaseListParams,
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    Page,
    RunnableResourceMixin,
    BareRunParams,
    BaseResult,
    ToolMixin,
)
from .enums import Function, ToolType


class IntegrationListParams(BaseListParams):
    """Parameters for listing integrations.

    Integrations are models with Function.CONNECTOR, so we use the models
    endpoint and filter by function.
    """

    pass


@dataclass_json
@dataclass
class IntegrationResult(BaseResult):
    """Result for integration operations."""

    pass


@dataclass_json
@dataclass
class Integration(
    BaseResource,
    PagedListResourceMixin[IntegrationListParams, "Integration"],
    GetResourceMixin[BareGetParams, "Integration"],
    RunnableResourceMixin[BareRunParams, IntegrationResult],
    ToolMixin,
):
    """Resource for integrations."""

    RESOURCE_PATH = "sdk/models"  # Use models endpoint like legacy
    TOOL_TYPE = ToolType.INTEGRATION
    RESPONSE_CLASS = IntegrationResult

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Integration":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[IntegrationListParams]) -> "Page[Integration]":
        # Add the function filter for CONNECTOR
        kwargs["function"] = Function.CONNECTOR
        return super().list(**kwargs)

    @classmethod
    def _populate_filters(cls, params):
        """Override to handle function filter for integrations."""
        filters = super()._populate_filters(params)

        # Handle function filter (for integrations)
        if params.get("function") is not None:
            if "functions" not in filters:
                filters["functions"] = []
            filters["functions"].append(params["function"].value)

        return filters

    def connect(self, name: Optional[str] = None, **kwargs) -> IntegrationResult:
        """Connect to the integration.

        This method creates a connection to the integration using OAuth2
        by default. For other authentication methods, additional parameters
        can be passed.

        Args:
            name: Optional name for the connection
            **kwargs: Additional connection parameters

        Returns:
            Result: The connection result with ID if successful
        """
        # Build the connection payload5
        payload = {
            "name": name or "Connection",
            "authScheme": "OAUTH2",
        }

        # Add any additional data if provided
        if kwargs:
            payload["data"] = kwargs

        # Use the run method to create the connection
        return self.run(**payload)

    def run(self, **kwargs: Unpack[BareRunParams]) -> IntegrationResult:
        return super().run(**kwargs)
