"""
Shared authentication utilities for v2 implementation.

This module contains shared utility functions to eliminate redundancy
and break circular dependencies between Tool and Integration classes.
"""

from typing import Optional, Union
from enum import Enum


class AuthenticationScheme(Enum):
    """Authentication schemes supported by tools."""

    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH = "OAUTH"
    OAUTH2 = "OAUTH2"


def build_connection_payload_from_kwargs(name: Optional[str] = None, **kwargs) -> dict:
    """Build connection payload from keyword arguments.

    This is a shared utility function to eliminate redundancy between
    Tool and Integration classes.
    """
    # Determine authentication scheme from kwargs
    if "token" in kwargs:
        # Bearer token authentication
        auth_scheme = AuthenticationScheme.BEARER_TOKEN
        payload = {
            "name": name or "Connection",
            "authScheme": auth_scheme.value,
            "data": {
                "token": kwargs["token"],
            },
        }
    elif "client_id" in kwargs and "client_secret" in kwargs:
        # OAuth authentication
        auth_scheme = AuthenticationScheme.OAUTH
        payload = {
            "name": name or "Connection",
            "authScheme": auth_scheme.value,
            "data": {
                "client_id": kwargs["client_id"],
                "client_secret": kwargs["client_secret"],
            },
        }
    else:
        # OAuth2 authentication (default)
        auth_scheme = AuthenticationScheme.OAUTH2
        payload = {
            "name": name or "Connection",
            "authScheme": auth_scheme.value,
        }

    return payload


def build_connection_payload_from_auth(authentication) -> dict:
    """Build connection payload from authentication dataclass.

    This is a shared utility function to eliminate redundancy between
    Tool and Integration classes.
    """
    payload = {
        "name": authentication.name or "Connection",
        "authScheme": authentication.scheme.value,
    }

    if authentication.scheme == AuthenticationScheme.BEARER_TOKEN:
        payload["data"] = {
            "token": authentication.token,
        }
    elif authentication.scheme == AuthenticationScheme.OAUTH:
        payload["data"] = {
            "client_id": authentication.client_id,
            "client_secret": authentication.client_secret,
        }
    elif authentication.scheme == AuthenticationScheme.OAUTH2:
        # OAuth2 doesn't need additional data
        pass

    return payload


def handle_connection_response(response: dict, response_class) -> any:
    """Handle connection response with standard pattern.

    This is a shared utility function to eliminate redundancy between
    Tool and Integration classes.
    """
    status = response.get("status", "IN_PROGRESS")
    data = response.get("data", None)

    if status == "IN_PROGRESS":
        if data is not None:
            # This is the polling URL case
            return response_class.from_dict(
                {"status": status, "url": data, "completed": True}
            )
        else:
            return response_class.from_dict(
                {
                    "status": "FAILED",
                    "completed": True,
                    "error_message": "No polling URL found",
                }
            )
    else:
        # Direct response case
        return response_class.from_dict(response)
