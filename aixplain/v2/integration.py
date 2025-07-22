from typing_extensions import Unpack
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from typing import Optional

from .model import Model, ModelRunParams
from .resource import (
    BaseListParams,
    BaseResult,
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
class Integration(Model):
    """Resource for integrations.

    Integrations are a subtype of models with Function.CONNECTOR.
    """

    TOOL_TYPE = ToolType.INTEGRATION
    RESPONSE_CLASS = IntegrationResult

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BaseListParams]) -> "Integration":
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

    def build_run_payload(self, **kwargs: Unpack[ModelRunParams]) -> dict:
        """
        Build the payload for running the integration.

        For connections, we want to preserve the exact payload structure
        without the Model's restructuring.
        """
        # If this is a connection call (has authScheme), preserve the payload
        if "authScheme" in kwargs:
            return kwargs

        # Otherwise, use the parent's method for regular model runs
        result = super().build_run_payload(**kwargs)
        return result

    def connect(self, name: Optional[str] = None, **kwargs) -> IntegrationResult:
        """Connect to the integration.

        This method creates a connection to the integration using OAuth2
        by default. For other authentication methods, additional parameters
        can be passed.

        Args:
            name: Optional name for the connection
            **kwargs: Additional connection parameters (token, client_id, client_secret, etc.)

        Returns:
            Result: The connection result with ID if successful
        """
        # Determine authentication scheme based on provided parameters
        auth_scheme = "OAUTH2"  # Default
        if "token" in kwargs:
            auth_scheme = "BEARER_TOKEN"
        elif "client_id" in kwargs and "client_secret" in kwargs:
            auth_scheme = "OAUTH"

        # Build the connection payload based on authentication scheme
        if auth_scheme == "BEARER_TOKEN":
            payload = {
                "name": name or "Connection",
                "authScheme": auth_scheme,
                "data": {
                    "token": kwargs["token"],
                },
            }
        elif auth_scheme == "OAUTH":
            payload = {
                "name": name or "Connection",
                "authScheme": auth_scheme,
                "data": {
                    "client_id": kwargs["client_id"],
                    "client_secret": kwargs["client_secret"],
                },
            }
        else:  # OAUTH2
            payload = {
                "name": name or "Connection",
                "authScheme": auth_scheme,
            }

        # Call the run method with the payload as the data parameter
        return self.run(data=payload)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> IntegrationResult:
        return super().run(**kwargs)
