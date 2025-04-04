"""
Error handling manager for aiXplain SDK.

This module provides centralized error handling for the aiXplain SDK,
particularly focused on agent operations.
"""

import logging
from typing import Dict, Any, Type

from aixplain.exceptions import (
    AixplainBaseException,
    AgentError,
    AgentTimeoutError,
    ValidationError,
    AuthenticationError,
    BillingError,
    SupplierError,
    NetworkError,
    ServiceError,
    InternalError,
)

from aixplain.exceptions.registry import ErrorRegistry
from aixplain.exceptions import ErrorCategory


class ErrorHandler:
    """
    Centralized error handler for the aiXplain SDK.

    This class provides error handling functionality for agent operations,
    including retry logic for recoverable errors and proper error classification.
    """

    def __init__(self, max_retries: int = 3, log_level: int = logging.INFO):
        self.max_retries = max_retries
        self.retry_count = 0
        self.log_level = log_level
        self.logger = logging.getLogger("aixplain.error_handler")

        # Common categories of recoverable errors
        self.recoverable_error_types = [
            "supplier_error",
            "quota_limit_exceeded",
            "rate_limit_exceeded",
            "timeout",
            "connection_error",
        ]

    def handle_error(self, error: Exception, operation: str = "operation", context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an exception, deciding whether to retry or propagate.

        Args:
            error (Exception): The exception to handle
            operation (str): The name of the operation that failed
            context (Dict[str, Any]): Additional context about the operation

        Returns:
            Dict[str, Any]: Response containing handling decision
        """
        context = context or {}
        agent_id = context.get("agent_id", "unknown")

        # Log the error
        self._log_error(error, operation, agent_id)

        # Check if error is non-recoverable first
        if self._is_non_recoverable_error(error):
            self.logger.error(
                f"Non-recoverable error encountered in {operation} ({error.__class__.__name__}): {str(error)}. Breaking process."
            )
            # Signal that we should not retry and process should be broken
            return {"break_process": True, "should_retry": False, "error": error}

        # Check if error is recoverable and we have retries left
        if self._is_recoverable_error(error) and self.retry_count < self.max_retries:
            self.retry_count += 1
            retry_after = min(2**self.retry_count, 30)  # Exponential backoff with 30s max

            self.logger.warning(
                f"Recoverable error in {operation} ({error.__class__.__name__}): {str(error)}. "
                f"Retry {self.retry_count}/{self.max_retries} scheduled in {retry_after}s."
            )

            return {
                "break_process": False,
                "should_retry": True,
                "retry_after": retry_after,
                "error": error,
            }

        # If we've used all retries or it's not recoverable
        self.logger.error(
            f"Error in {operation} ({error.__class__.__name__}): {str(error)}. "
            f"No more retries available ({self.retry_count}/{self.max_retries})."
        )

        return {"break_process": False, "should_retry": False, "error": error}

    def reset_retries(self) -> None:
        """Reset the retry counter."""
        self.retry_count = 0

    def _log_error(self, error: Exception, operation: str, agent_id: str) -> None:
        """Log the error with appropriate detail level."""
        error_message = str(error)
        if isinstance(error, AixplainBaseException):
            error_message = f"{error.__class__.__name__}: {error.message}"

        self.logger.error(f"{operation} for agent {agent_id} encountered an error: {error_message}")

    def _is_non_recoverable_error(self, error: Exception) -> bool:
        """Determine if an error is non-recoverable."""
        # Authentication errors are non-recoverable during a session
        if isinstance(error, AuthenticationError):
            return True

        # Validation errors are non-recoverable (input won't change)
        if isinstance(error, ValidationError):
            return True

        # Billing errors are generally non-recoverable without user intervention
        if isinstance(error, BillingError):
            return True

        # Check message for keywords indicating non-recoverable errors
        error_str = str(error).lower()
        if any(kw in error_str for kw in ["invalid key", "unauthorized", "permission denied", "not found"]):
            return True

        # All other errors are potentially recoverable
        return False

    def _is_supplier_or_quota_error(self, error: Exception) -> bool:
        """Check if the error is related to supplier issues or quota limits."""
        if isinstance(error, SupplierError):
            return True

        error_str = str(error).lower()
        return any(keyword in error_str for keyword in ["supplier", "quota", "rate limit", "too many requests", "capacity"])

    def _is_unspecified_error(self, error: Exception) -> bool:
        """Check if this is an unspecified or unknown error type."""
        # If it's non-recoverable or a supplier/quota error, it's not unspecified
        if self._is_non_recoverable_error(error) or self._is_supplier_or_quota_error(error):
            return False

        # AgentExecutionError is considered unspecified unless it's more specific
        if error.__class__.__name__ == "AgentExecutionError":
            # If the error message already indicates it's an unspecified error, return True
            if "unspecified error" in str(error).lower():
                return True
            # Otherwise check if it has a specific categorization
            return not any(
                keyword in str(error).lower()
                for keyword in [
                    "validation",
                    "authentication",
                    "billing",
                    "subscription",
                    "supplier",
                    "quota",
                    "timeout",
                    "iteration limit",
                ]
            )

        # Generic exceptions without specific handling should be treated as unspecified
        if not isinstance(error, AixplainBaseException):
            return True

        # InternalError is considered unspecified
        if isinstance(error, InternalError):
            return True

        # Check if the error message contains generic error indicators
        error_str = str(error).lower()
        return (
            any(keyword in error_str for keyword in ["unknown", "unspecified", "internal server error", "unexpected"])
            or error.category == ErrorCategory.UNKNOWN  # noqa: W503
        )

    def _is_recoverable_error(self, error: Exception) -> bool:
        """Determine if an error is recoverable through retrying."""
        # Network and service errors are generally recoverable
        if isinstance(error, (NetworkError, ServiceError)):
            return True

        # Supplier errors are generally recoverable
        if isinstance(error, SupplierError):
            return True

        # Timeouts are recoverable
        if isinstance(error, AgentTimeoutError):
            return True

        # Check for specific error messages
        error_str = str(error).lower()
        return any(
            keyword in error_str
            for keyword in [
                "timeout",
                "connection",
                "retry",
                "temporary",
                "service unavailable",
                "too many requests",
                "rate limit",
                "quota",
                "capacity",
                "busy",
                "overloaded",
            ]
        )


# Global error handler instance for convenience
default_error_handler = ErrorHandler()


def handle_error(error: Exception, operation: str = "operation", context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to handle errors using the default error handler."""
    return default_error_handler.handle_error(error, operation, context)


def raise_error(error_code: str, exception_class: Type[AixplainBaseException] = None, **kwargs) -> None:
    """
    Create and raise an exception from the error registry.

    Args:
        error_code (str): The error code to use from the registry.
        exception_class (Type[AixplainBaseException], optional): The exception class to instantiate.
        **kwargs: Additional parameters for the exception constructor and message formatting.

    Raises:
        AixplainBaseException: An exception of the specified class.
    """
    if exception_class is None:
        # Determine exception class from error code prefix
        prefix = error_code.split(".")[0]

        if prefix == "auth":
            exception_class = AuthenticationError
        elif prefix == "validation":
            exception_class = ValidationError
        elif prefix == "resource":
            exception_class = ValidationError
        elif prefix == "billing":
            exception_class = BillingError
        elif prefix == "supplier":
            exception_class = SupplierError
        elif prefix == "network":
            exception_class = NetworkError
        elif prefix == "service":
            exception_class = ServiceError
        elif prefix == "agent":
            exception_class = AgentError
        else:
            exception_class = InternalError

    exception = ErrorRegistry.create_exception(error_code, exception_class, **kwargs)
    raise exception
