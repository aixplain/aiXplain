"""Unified error hierarchy for v2 system.

This module provides a comprehensive set of error types for consistent
error handling across all v2 components.
"""

from typing import Optional, Any, Dict, Union, List


class AixplainV2Error(Exception):
    """Base exception for all v2 errors."""

    def __init__(self, message: Union[str, List[str]], details: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the exception with a message and optional details.

        Args:
            message: Error message string or list of error messages.
            details: Optional dictionary with additional error details.
        """
        if isinstance(message, list):
            message = "\n".join(message)
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ResourceError(AixplainV2Error):
    """Raised when resource operations fail."""

    pass


class APIError(AixplainV2Error):
    """Raised when API calls fail."""

    def __init__(
        self,
        message: Union[str, List[str]],
        status_code: int = 0,
        response_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Initialize APIError with HTTP status and response details.

        Args:
            message: Error message string or list of error messages.
            status_code: HTTP status code from the API response.
            response_data: Optional dictionary containing the raw API response.
            error: Optional error string override.
        """
        self.status_code = status_code
        self.response_data = response_data or {}
        self.error = error or message if isinstance(message, str) else str(message)
        super().__init__(
            message,
            {
                "status_code": status_code,
                "response_data": response_data,
                "error": self.error,
            },
        )


class ValidationError(AixplainV2Error):
    """Raised when validation fails."""

    pass


class TimeoutError(AixplainV2Error):
    """Raised when operations timeout."""

    pass


class FileUploadError(AixplainV2Error):
    """Raised when file upload operations fail."""

    pass


# Error factory function for consistent error creation
def create_operation_failed_error(response: Dict[str, Any]) -> APIError:
    """Create an operation failed error from API response."""
    # Extract error message using consistent logic
    error_msg = None
    if response.get("supplierError"):
        error_msg = response["supplierError"]
    elif response.get("supplier_error"):
        error_msg = response["supplier_error"]
    elif response.get("error_message"):
        error_msg = response["error_message"]
    elif response.get("error"):
        error_msg = response["error"]
    else:
        error_msg = "Operation failed"

    return APIError(
        f"Operation failed: {error_msg}",
        status_code=response.get("statusCode", 0),
        response_data=response,
        error=error_msg,
    )
