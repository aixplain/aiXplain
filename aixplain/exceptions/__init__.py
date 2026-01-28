"""Error message registry for aiXplain SDK.

This module maintains a centralized registry of error messages used throughout the aiXplain ecosystem.
It allows developers to look up existing error messages and reuse them instead of creating new ones.
"""

from aixplain.exceptions.types import (
    AixplainBaseException,
    AuthenticationError,
    ValidationError,
    AlreadyDeployedError,
    ResourceError,
    BillingError,
    SupplierError,
    NetworkError,
    ServiceError,
    InternalError,
    AlreadyDeployedError,
)

__all__ = [
    "AixplainBaseException",
    "AuthenticationError",
    "ValidationError",
    "ResourceError",
    "BillingError",
    "SupplierError",
    "NetworkError",
    "ServiceError",
    "InternalError",
    "AlreadyDeployedError",
]


def get_error_from_status_code(status_code: int, error_details: str = None) -> AixplainBaseException:
    """Map HTTP status codes to appropriate exception types.

    Args:
        status_code (int): The HTTP status code to map.
        error_details (str, optional): Additional error details to include in the message.

    Returns:
        AixplainBaseException: An exception of the appropriate type.
    """
    try:
        if isinstance(status_code, str):
            status_code = int(status_code)
    except Exception as e:
        raise InternalError(f"Failed to get status code from {status_code}: {e}") from e

    error_details = f"Details: {error_details}" if error_details else ""
    if status_code == 400:
        return ValidationError(
            message=f"Bad request: Please verify the request payload and ensure it is correct. {error_details}".strip(),
            status_code=status_code,
        )
    elif status_code == 401:
        return AuthenticationError(
            message=f"Unauthorized API key: Please verify the spelling of the API key and its current validity. {error_details}".strip(),
            status_code=status_code,
        )
    elif status_code == 402:
        return BillingError(
            message=f"Payment required: Please ensure you have enough credits to run this asset. {error_details}".strip(),
            status_code=status_code,
        )
    elif status_code == 403:
        # 403 could be auth or resource, using ResourceError as a general 'forbidden'
        return ResourceError(
            message=f"Forbidden access: Please verify the API key and its current validity. {error_details}".strip(),
            status_code=status_code,
        )
    elif status_code == 404:
        # Added 404 mapping
        return ResourceError(
            message=f"Resource not found: Please verify the spelling of the resource and its current availability. {error_details}".strip(),
            status_code=status_code,
        )
    elif status_code == 429:
        # Using SupplierError for rate limiting as per your original function
        return SupplierError(
            message=f"Rate limit exceeded: Please try again later. {error_details}".strip(),
            status_code=status_code,
            retry_recommended=True,
        )
    elif status_code == 500:
        return InternalError(
            message=f"Internal server error: Please try again later. {error_details}".strip(),
            status_code=status_code,
            retry_recommended=True,
        )
    elif status_code == 503:
        return ServiceError(
            message=f"Service unavailable: Please try again later. {error_details}".strip(),
            status_code=status_code,
            retry_recommended=True,
        )
    elif status_code == 504:
        return NetworkError(
            message=f"Gateway timeout: Please try again later. {error_details}".strip(),
            status_code=status_code,
            retry_recommended=True,
        )
    elif 460 <= status_code < 470:
        return ResourceError(
            message=f"Subscription-related error: Please ensure that your subscription is active and has not expired. {error_details}".strip(),
            status_code=status_code,
        )
    elif 470 <= status_code < 480:
        return BillingError(
            message=f"Billing-related error: Please ensure you have enough credits to run this asset. {error_details}".strip(),
            status_code=status_code,
        )
    elif 480 <= status_code < 490:
        return SupplierError(
            message=f"Supplier-related error: Please ensure that the selected supplier provides the asset you are trying to access. {error_details}".strip(),
            status_code=status_code,
        )
    elif 490 <= status_code < 500:
        return ValidationError(
            message=f"Validation-related error: Please verify the request payload and ensure it is correct. {error_details}".strip(),
            status_code=status_code,
        )
    else:
        # Catch-all for other client/server errors
        category = "Client" if 400 <= status_code < 500 else "Server"
        return InternalError(
            message=f"Unspecified {category} Error (Status {status_code}) {error_details}".strip(),
            status_code=status_code,
        )
