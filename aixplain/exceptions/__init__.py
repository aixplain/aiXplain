"""
Error handling system for aiXplain SDK.

This module provides a hierarchy of exceptions for the aiXplain ecosystem.
Errors are categorized to allow for appropriate handling at different levels.
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorSeverity(Enum):
    """Defines the severity level of errors."""

    DEBUG = "debug"  # Internal debugging only
    INFO = "info"  # Informational, non-critical
    WARNING = "warning"  # Potentially problematic but operation can continue
    ERROR = "error"  # Operation cannot continue but system remains stable
    CRITICAL = "critical"  # System stability might be compromised


class ErrorCategory(Enum):
    """Categorizes errors by their domain."""

    AUTHENTICATION = "authentication"  # API keys, permissions
    VALIDATION = "validation"  # Input validation
    RESOURCE = "resource"  # Resource availability
    BILLING = "billing"  # Credits, payment
    SUPPLIER = "supplier"  # External supplier issues
    NETWORK = "network"  # Network connectivity
    SERVICE = "service"  # Service availability
    INTERNAL = "internal"  # Internal system errors
    AGENT = "agent"  # Agent-specific errors
    UNKNOWN = "unknown"  # Uncategorized errors


class AixplainBaseException(Exception):
    """Base exception class for all aiXplain exceptions."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        retry_recommended: bool = False,
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.status_code = status_code
        self.details = details or {}
        self.retry_recommended = retry_recommended
        super().__init__(self.message)

    def __str__(self):
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "status_code": self.status_code,
            "details": self.details,
            "retry_recommended": self.retry_recommended,
        }


# Authentication Errors
class AuthenticationError(AixplainBaseException):
    """Raised when authentication fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.ERROR,
            **kwargs,
        )


# Validation Errors
class ValidationError(AixplainBaseException):
    """Raised when input validation fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            **kwargs,
        )


# Resource Errors
class ResourceError(AixplainBaseException):
    """Raised when a resource is unavailable."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.ERROR,
            **kwargs,
        )


# Billing Errors
class BillingError(AixplainBaseException):
    """Raised when there are billing issues."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.BILLING,
            severity=ErrorSeverity.ERROR,
            **kwargs,
        )


# Supplier Errors
class SupplierError(AixplainBaseException):
    """Raised when there are issues with external suppliers."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SUPPLIER,
            severity=ErrorSeverity.ERROR,
            retry_recommended=True,
            **kwargs,
        )


# Network Errors
class NetworkError(AixplainBaseException):
    """Raised when there are network connectivity issues."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            retry_recommended=True,
            **kwargs,
        )


# Service Errors
class ServiceError(AixplainBaseException):
    """Raised when a service is unavailable."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SERVICE,
            severity=ErrorSeverity.ERROR,
            retry_recommended=True,
            **kwargs,
        )


# Internal Errors
class InternalError(AixplainBaseException):
    """Raised when there is an internal system error."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.ERROR,
            **kwargs,
        )


# Agent-specific Errors
class AgentError(AixplainBaseException):
    """Base class for agent-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, category=ErrorCategory.AGENT, severity=ErrorSeverity.ERROR, **kwargs)


class AgentExecutionError(AgentError):
    """Raised when an agent execution fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, **kwargs)


class AgentTimeoutError(AgentError):
    """Raised when an agent execution times out."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message=message, retry_recommended=True, **kwargs)


class AgentIterationLimitError(AgentError):
    """Raised when an agent reaches its iteration limit."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            retry_recommended=True,
            **kwargs,
        )


# HTTP status code to error category mapping
def get_error_from_status_code(status_code: int, default_message: str = None) -> AixplainBaseException:
    """Map HTTP status codes to appropriate exception types."""
    if status_code == 401:
        return AuthenticationError(message=default_message or "Unauthorized API key", status_code=status_code)
    elif 460 <= status_code < 470:
        return ResourceError(message=default_message or "Subscription-related error", status_code=status_code)
    elif 470 <= status_code < 480:
        return BillingError(message=default_message or "Billing-related error", status_code=status_code)
    elif 480 <= status_code < 490:
        return SupplierError(message=default_message or "Supplier-related error", status_code=status_code)
    elif 490 <= status_code < 500:
        return ValidationError(message=default_message or "Validation-related error", status_code=status_code)
    else:
        return InternalError(message=default_message or f"Unspecified error (Status {status_code})", status_code=status_code)
