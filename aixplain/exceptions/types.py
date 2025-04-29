from enum import Enum
from typing import Optional, Dict, Any


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""

    INFO = "info"  # Informational, not an error
    WARNING = "warning"  # Warning, operation can continue
    ERROR = "error"  # Error, operation cannot continue
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
        return f"{self.__class__.__name__}: {self.message}"

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
            retry_recommended=kwargs.pop("retry_recommended", False),
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
            retry_recommended=kwargs.pop("retry_recommended", False),
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
            retry_recommended=kwargs.pop("retry_recommended", False),
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
            retry_recommended=kwargs.pop("retry_recommended", False),
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
            retry_recommended=kwargs.pop("retry_recommended", True),
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
            retry_recommended=kwargs.pop("retry_recommended", True),
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
            retry_recommended=kwargs.pop("retry_recommended", True),
            **kwargs,
        )


# Internal Errors
class InternalError(AixplainBaseException):
    """Raised when there is an internal system error."""

    def __init__(self, message: str, **kwargs):
        # Server errors (5xx) should generally be retryable
        status_code = kwargs.get("status_code")
        retry_recommended = kwargs.pop("retry_recommended", False)
        if status_code and status_code in [500, 502, 503, 504]:
            retry_recommended = True

        super().__init__(
            message=message,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.ERROR,
            retry_recommended=retry_recommended,
            **kwargs,
        )
