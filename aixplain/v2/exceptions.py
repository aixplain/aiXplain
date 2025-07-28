"""
Simplified error hierarchy for v2 resource system.

This module provides a minimal set of error types for consistent
error handling across v2 resources.
"""

from typing import Optional, Any, Dict


class AixplainV2Error(Exception):
    """Base exception for all v2 errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
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
        message: str,
        status_code: int = 0,
        response_data: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(
            message, {"status_code": status_code, "response_data": response_data}
        )


class ValidationError(AixplainV2Error):
    """Raised when validation fails."""

    pass


class TimeoutError(AixplainV2Error):
    """Raised when operations timeout."""

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
        f"Operation failed: {error_msg}", status_code=0, response_data=response
    )
