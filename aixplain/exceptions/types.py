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


class ErrorCode(str, Enum):
    """Standard error codes for aiXplain exceptions.

    The format is AX-<CATEGORY>-<ID>, where <CATEGORY> is a short identifier
    derived from the ErrorCategory (e.g., AUTH, VAL, RES) and <ID> is a
    unique sequential number within that category, starting from 1000.

    How to Add a New Error Code:
    1.  Identify the appropriate `ErrorCategory` for the new error.
    2.  Determine the next available sequential ID within that category.
        For example, if `AX-AUTH-1000` exists, the next authentication-specific
        error could be `AX-AUTH-1001`.
    3.  Define the new enum member using the format `AX-<CATEGORY_ABBR>-<ID>`.
        Use a concise abbreviation for the category (e.g., AUTH, VAL, RES, BIL,
        SUP, NET, SVC, INT).
    4.  Assign the string value (e.g., `"AX-AUTH-1001"`).
    5.  Add a clear docstring explaining the specific condition that triggers
        this error code.
    6.  (Optional but recommended) Consider creating a more specific exception
        class inheriting from the corresponding category exception (e.g.,
        `class InvalidApiKeyError(AuthenticationError): ...`) and assign the
        new error code to it.
    """

    AX_AUTH_ERROR = "AX-AUTH-1000"  # General authentication error. Use for issues like invalid API keys, insufficient permissions, or failed login attempts.
    AX_VAL_ERROR = "AX-VAL-1000"  # General validation error. Use when user-provided input fails validation checks (e.g., incorrect data type, missing required fields, invalid format.
    AX_RES_ERROR = "AX-RES-1000"  # General resource error. Use for issues related to accessing or managing resources, such as a requested model being unavailable or quota limits exceeded.
    AX_BIL_ERROR = "AX-BIL-1000"  # General billing error. Use for problems related to billing, payments, or credits (e.g., insufficient funds, expired subscription.
    AX_SUP_ERROR = "AX-SUP-1000"  # General supplier error. Use when an error originates from an external supplier or third-party service integrated with aiXplain.
    AX_NET_ERROR = "AX-NET-1000"  # General network error. Use for issues related to network connectivity, such as timeouts, DNS resolution failures, or unreachable services.
    AX_SVC_ERROR = "AX-SVC-1000"  # General service error. Use when a specific aiXplain service or endpoint is unavailable or malfunctioning (e.g., service downtime, internal component failure.
    AX_INT_ERROR = "AX-INT-1000"  # General internal error. Use for unexpected server-side errors that are not covered by other categories. This often indicates a bug or an issue within the aiXplain platform itself.

    def __str__(self):
        return self.value


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
        error_code: Optional[ErrorCode] = None,
    ):
        self.message = message
        self.category = category
        self.severity = severity
        self.status_code = status_code
        self.details = details or {}
        self.retry_recommended = retry_recommended
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        error_code_str = f" [{self.error_code}]" if self.error_code else ""
        return f"{self.__class__.__name__}{error_code_str}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "status_code": self.status_code,
            "details": self.details,
            "retry_recommended": self.retry_recommended,
            "error_code": self.error_code.value if self.error_code else None,
        }


class AuthenticationError(AixplainBaseException):
    """Raised when authentication fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.ERROR,
            retry_recommended=kwargs.pop("retry_recommended", False),
            error_code=ErrorCode.AX_AUTH_ERROR,
            **kwargs,
        )


class ValidationError(AixplainBaseException):
    """Raised when input validation fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            retry_recommended=kwargs.pop("retry_recommended", False),
            error_code=ErrorCode.AX_VAL_ERROR,
            **kwargs,
        )


class ResourceError(AixplainBaseException):
    """Raised when a resource is unavailable."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.ERROR,
            retry_recommended=kwargs.pop("retry_recommended", False),
            error_code=ErrorCode.AX_RES_ERROR,
            **kwargs,
        )


class BillingError(AixplainBaseException):
    """Raised when there are billing issues."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.BILLING,
            severity=ErrorSeverity.ERROR,
            retry_recommended=kwargs.pop("retry_recommended", False),
            error_code=ErrorCode.AX_BIL_ERROR,
            **kwargs,
        )


class SupplierError(AixplainBaseException):
    """Raised when there are issues with external suppliers."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SUPPLIER,
            severity=ErrorSeverity.ERROR,
            retry_recommended=kwargs.pop("retry_recommended", True),
            error_code=ErrorCode.AX_SUP_ERROR,
            **kwargs,
        )


class NetworkError(AixplainBaseException):
    """Raised when there are network connectivity issues."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.ERROR,
            retry_recommended=kwargs.pop("retry_recommended", True),
            error_code=ErrorCode.AX_NET_ERROR,
            **kwargs,
        )


class ServiceError(AixplainBaseException):
    """Raised when a service is unavailable."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SERVICE,
            severity=ErrorSeverity.ERROR,
            retry_recommended=kwargs.pop("retry_recommended", True),
            error_code=ErrorCode.AX_SVC_ERROR,
            **kwargs,
        )


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
            error_code=ErrorCode.AX_INT_ERROR,
            **kwargs,
        )
