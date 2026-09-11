---
sidebar_label: exceptions
title: aixplain.v2.exceptions
---

Unified error hierarchy for v2 system.

This module provides a comprehensive set of error types for consistent
error handling across all v2 components.

### AixplainV2Error Objects

```python
class AixplainV2Error(Exception)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L10)

Base exception for all v2 errors.

#### \_\_init\_\_

```python
def __init__(message: Union[str, List[str]],
             details: Optional[Dict[str, Any]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L13)

Initialize the exception with a message and optional details.

**Arguments**:

- `message` - Error message string or list of error messages.
- `details` - Optional dictionary with additional error details.

### ResourceError Objects

```python
class ResourceError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L27)

Raised when resource operations fail.

### APIError Objects

```python
class APIError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L33)

Raised when API calls fail.

#### \_\_init\_\_

```python
def __init__(message: Union[str, List[str]],
             status_code: int = 0,
             response_data: Optional[Dict[str, Any]] = None,
             error: Optional[str] = None,
             retryable: Optional[bool] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L36)

Initialize APIError with HTTP status and response details.

**Arguments**:

- `message` - Error message string or list of error messages.
- `status_code` - HTTP status code from the API response.
- `response_data` - Optional dictionary containing the raw API response.
- `error` - Optional error string override.
- `retryable` - Explicit retry signal, tri-state. ``None`` (the default)
  means &quot;no opinion&quot; — callers fall back to the status-code
  heuristic, where ``0`` stands for &quot;no HTTP response at all&quot;.
  ``False`` marks a deterministic failure that re-submitting
  cannot fix; a business ``FAILED`` response is the motivating
  case, because its usually-absent ``statusCode`` collapses onto
  that same ``0`` transport sentinel.

### AixplainIssueError Objects

```python
class AixplainIssueError(APIError)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L74)

Raised when SDK issue reporting fails.

### ValidationError Objects

```python
class ValidationError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L80)

Raised when validation fails.

### TimeoutError Objects

```python
class TimeoutError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L86)

Raised when operations timeout.

### FileUploadError Objects

```python
class FileUploadError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L92)

Raised when file upload operations fail.

### UntrustedURLError Objects

```python
class UntrustedURLError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L98)

Raised when a credentialed request targets a host outside the trusted set.

Not an :class:`APIError`: no request is made, so there is no status code to
report. Poll URLs come from response bodies, so this is the SDK refusing to
hand the team API key to a host a body asked it to talk to.

#### create\_operation\_failed\_error

```python
def create_operation_failed_error(response: Dict[str, Any]) -> APIError
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L128)

Create an operation failed error from API response.

The error is always marked non-retryable: a ``FAILED`` body reports a
*business* outcome, and its ``statusCode`` (usually absent, hence ``0``) is
not a transport code. Without the explicit flag it would be indistinguishable
from a connection failure and re-POSTed, billing the customer again for the
same deterministic failure (BUG-1090).

