"""Exception types for the aiXplain SDK.

This module is the non-versioned exceptions path: ``from aixplain.exceptions
import ValidationError`` resolves to the same class the SDK actually raises, so
``except ValidationError`` catches what it looks like it catches. Every name
here is the same object as ``aixplain.<name>`` and ``aixplain.v2.exceptions.<name>``.

The v1-era hierarchy (``AixplainBaseException``, ``AuthenticationError``,
``BillingError``, ..., and ``get_error_from_status_code``) is defined in
``aixplain.exceptions.types``. Its names still resolve here for one release,
with a ``DeprecationWarning``, and are removed from this module in
``V1_EXCEPTIONS_REMOVED_IN``. Nothing in the SDK raises them: an API failure
surfaces as ``aixplain.APIError`` (or a subclass), so handle it with
``except aixplain.APIError as e`` and branch on ``e.status_code`` (for example
``401`` for what ``AuthenticationError`` used to mean).
"""

from aixplain.v2.exceptions import (
    APIError,
    AgentRunFailedError,
    AgentRunNotStartedError,
    AixplainIssueError,
    AixplainV2Error,
    FileUploadError,
    ResourceError,
    TimeoutError,
    UntrustedURLError,
    ValidationError,
)

__all__ = [
    "AixplainV2Error",
    "APIError",
    "AgentRunFailedError",
    "AgentRunNotStartedError",
    "AixplainIssueError",
    "ValidationError",
    "ResourceError",
    "TimeoutError",
    "FileUploadError",
    "UntrustedURLError",
]

#: Release that drops the deprecated v1 names from this module.
V1_EXCEPTIONS_REMOVED_IN = "0.4.0"

_DEPRECATED_V1_NAMES = frozenset(
    {
        "AixplainBaseException",
        "AlreadyDeployedError",
        "AuthenticationError",
        "BillingError",
        "InternalError",
        "NetworkError",
        "ServiceError",
        "SupplierError",
        "get_error_from_status_code",
    }
)


def __getattr__(name: str) -> object:
    """Resolve a deprecated v1 name from ``aixplain.exceptions.types``, with a warning.

    Kept off ``__all__`` and out of the module namespace so only an actual
    access (``from aixplain.exceptions import AuthenticationError``) warns,
    not every ``import aixplain``.
    """
    if name in _DEPRECATED_V1_NAMES:
        import warnings

        from . import types

        if name == "get_error_from_status_code":
            # A helper, not an exception class: there is nothing to `except`.
            hint = (
                "the SDK raises `aixplain.APIError` itself, with the HTTP status on `status_code`; "
                "you should not need to build errors from a status code"
            )
        else:
            hint = (
                f"the SDK never raises it, so `except {name}` will not catch API failures -- "
                f"catch `aixplain.APIError` and check `status_code` instead "
                f"(e.g. `except aixplain.APIError as e: if e.status_code == 401: ...`)"
            )
        warnings.warn(
            f"`aixplain.exceptions.{name}` is deprecated and will be removed in {V1_EXCEPTIONS_REMOVED_IN}: "
            f"{hint}. Until then it stays importable from `aixplain.exceptions.types`.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(types, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
