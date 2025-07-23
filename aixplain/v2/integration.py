"""
Integration resource for v2 implementation.

Integrations handle all connection logic and provide a clean interface
for tools to connect without knowing implementation details.
"""

from typing import Optional, Union
from typing_extensions import Unpack
from dataclasses_json import dataclass_json
from dataclasses import dataclass
from enum import Enum

from .resource import (
    BaseListParams,
    BaseResult
)
from .model import Model, ModelRunParams
from .enums import Function, ToolType


class AuthenticationScheme(Enum):
    """Authentication schemes supported by integrations."""

    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH = "OAUTH"
    OAUTH2 = "OAUTH2"


@dataclass_json
@dataclass
class IntegrationResult(BaseResult):
    """Result for connection operations."""

    connection_id: Optional[str] = None
    polling_url: Optional[str] = None


class IntegrationListParams(BaseListParams):
    """Parameters for listing integrations."""

    pass


class Integration(Model):
    """Resource for integrations.

    Integrations are a subtype of models with Function.CONNECTOR.
    All connection logic is centralized here.
    """

    TOOL_TYPE = ToolType.INTEGRATION
    RESPONSE_CLASS = IntegrationResult

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BaseListParams]) -> "Integration":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[IntegrationListParams]) -> "Page[Integration]":
        return super().list(**kwargs)

    @classmethod
    def _populate_filters(cls, params: BaseListParams) -> dict:
        """Populate the filters for pagination."""
        filters = super()._populate_filters(params)
        filters["functions"] = [Function.CONNECTOR]
        return filters

    def build_run_payload(
        self,
        name: Optional[str],
        auth_scheme: Optional[AuthenticationScheme],
        **auth_params
    ) -> dict:
        """Build the connection payload based on authentication parameters."""
        # Determine authentication scheme from parameters if not provided
        if auth_scheme is None:
            if "token" in auth_params:
                auth_scheme = AuthenticationScheme.BEARER_TOKEN
            elif "client_id" in auth_params and "client_secret" in auth_params:
                auth_scheme = AuthenticationScheme.OAUTH
            else:
                auth_scheme = AuthenticationScheme.OAUTH2

        # Build base payload
        payload = {
            "name": name or "Connection",
            "authScheme": auth_scheme.value,
        }

        # Add authentication data based on scheme
        if auth_scheme == AuthenticationScheme.BEARER_TOKEN:
            payload["data"] = {
                "token": auth_params["token"],
            }
        elif auth_scheme == AuthenticationScheme.OAUTH:
            payload["data"] = {
                "client_id": auth_params["client_id"],
                "client_secret": auth_params["client_secret"],
            }
        elif auth_scheme == AuthenticationScheme.OAUTH2:
            # OAuth2 doesn't need additional data
            pass

        return payload
