"""
Standardized error hierarchy for v2 resource system.

This module provides a consistent error handling framework across all
v2 resources and mixins.
"""

from typing import Optional, Any, Dict


class AixplainV2Error(Exception):
    """Base exception for all v2 errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ResourceError(AixplainV2Error):
    """Base exception for resource-related errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Raised when a resource is not found."""
    pass


class ResourceValidationError(ResourceError):
    """Raised when resource validation fails."""
    pass


class ResourceOperationError(ResourceError):
    """Raised when a resource operation fails."""
    pass


class ResourceContextError(ResourceError):
    """Raised when resource context is invalid or missing."""
    pass


class ResourceConfigurationError(ResourceError):
    """Raised when resource configuration is invalid."""
    pass


class AuthenticationError(AixplainV2Error):
    """Raised when authentication fails."""
    pass


class AuthorizationError(AixplainV2Error):
    """Raised when authorization fails."""
    pass


class APIError(AixplainV2Error):
    """Raised when API calls fail."""
    
    def __init__(self, message: str, status_code: int, response_data: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(message, {"status_code": status_code, "response_data": response_data})


class OperationFailedError(APIError):
    """Raised when an operation fails with specific error details."""
    
    def __init__(self, error_message: str, supplier_error: Optional[str] = None, **kwargs):
        self.supplier_error = supplier_error
        details = {"supplier_error": supplier_error, **kwargs}
        super().__init__(f"Operation failed: {error_message}", 0, details)


class TimeoutError(AixplainV2Error):
    """Raised when operations timeout."""
    pass


class ValidationError(AixplainV2Error):
    """Raised when validation fails."""
    pass


# Error factory functions for consistent error creation
def create_resource_error(error_type: str, message: str, **details) -> ResourceError:
    """Create a resource error with consistent formatting."""
    error_map = {
        "not_found": ResourceNotFoundError,
        "validation": ResourceValidationError,
        "operation": ResourceOperationError,
        "context": ResourceContextError,
        "configuration": ResourceConfigurationError,
    }
    
    error_class = error_map.get(error_type, ResourceError)
    return error_class(message, details)


def create_api_error(message: str, status_code: int, response_data: Optional[Dict[str, Any]] = None) -> APIError:
    """Create an API error with consistent formatting."""
    return APIError(message, status_code, response_data)


def create_operation_failed_error(response: Dict[str, Any]) -> OperationFailedError:
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
    
    return OperationFailedError(
        error_message=error_msg,
        supplier_error=response.get("supplierError") or response.get("supplier_error"),
        status=response.get("status"),
        response_data=response
    ) 