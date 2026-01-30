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
             error: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L36)

Initialize APIError with HTTP status and response details.

**Arguments**:

- `message` - Error message string or list of error messages.
- `status_code` - HTTP status code from the API response.
- `response_data` - Optional dictionary containing the raw API response.
- `error` - Optional error string override.

### ValidationError Objects

```python
class ValidationError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L64)

Raised when validation fails.

### TimeoutError Objects

```python
class TimeoutError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L70)

Raised when operations timeout.

### FileUploadError Objects

```python
class FileUploadError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L76)

Raised when file upload operations fail.

#### create\_operation\_failed\_error

```python
def create_operation_failed_error(response: Dict[str, Any]) -> APIError
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L83)

Create an operation failed error from API response.

