"""
Integration resource for v2 implementation.

Integrations handle all connection logic and provide a clean interface
for tools to connect without knowing implementation details.
"""

from typing import Optional, TypedDict
from typing_extensions import Unpack
from enum import Enum
from dataclasses import dataclass

from .resource import BaseListParams, BaseResult, Page
from .model import Model
from .enums import Function, ToolType


class AuthenticationScheme(str, Enum):
    """Authentication schemes supported by integrations."""

    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH = "OAUTH"
    OAUTH2 = "OAUTH2"


@dataclass
class IntegrationResult(BaseResult):
    """Result for connection operations."""

    connection_id: Optional[str] = None
    polling_url: Optional[str] = None


class IntegrationListParams(BaseListParams):
    """Parameters for listing integrations."""

    pass


class Credentials(TypedDict, total=False):
    """Credentials for integrations."""

    token: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]


class IntegrationRunParams(TypedDict, total=False):
    """Parameters for running integrations (connections).

    Integrations handle authentication and connection setup, so they need
    different parameters than regular models.
    """

    name: Optional[str]
    auth_scheme: Optional[AuthenticationScheme]
    data: Optional[Credentials]
    timeout: Optional[int]
    wait_time: Optional[int]


class Integration(Model):
    """Resource for integrations.

    Integrations are a subtype of models with Function.CONNECTOR.
    All connection logic is centralized here.
    """

    TOOL_TYPE = ToolType.INTEGRATION
    RESPONSE_CLASS = IntegrationResult
    RUN_PARAMS_CLASS = IntegrationRunParams

    # Make AuthenticationScheme accessible
    AuthenticationScheme = AuthenticationScheme
    Credentials = Credentials

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BaseListParams]) -> "Integration":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[IntegrationListParams]) -> "Page[Integration]":
        return super().list(**kwargs)

    def build_run_payload(self, **kwargs) -> dict:
        payload = dict(kwargs)
        # Aliasing for top-level fields
        if "auth_scheme" in payload:
            payload["authScheme"] = payload.pop("auth_scheme")
        if "data" in payload and payload["data"] is not None:
            data = dict(payload["data"])
            if "client_id" in data:
                data["clientId"] = data.pop("client_id")
            if "client_secret" in data:
                data["clientSecret"] = data.pop("client_secret")
            payload["data"] = data
        return payload

    @classmethod
    def _populate_filters(cls, params: BaseListParams) -> dict:
        """Populate the filters for pagination."""
        filters = super()._populate_filters(params)
        filters["functions"] = [Function.CONNECTOR]
        return filters

    def connect(self, **kwargs) -> IntegrationResult:
        """Connect to the integration."""
        return self.run(**kwargs)