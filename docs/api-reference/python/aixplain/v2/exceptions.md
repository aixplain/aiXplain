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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L11)

Base exception for all v2 errors.

### ResourceError Objects

```python
class ResourceError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L24)

Raised when resource operations fail.

### APIError Objects

```python
class APIError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L30)

Raised when API calls fail.

### ValidationError Objects

```python
class ValidationError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L53)

Raised when validation fails.

### TimeoutError Objects

```python
class TimeoutError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L59)

Raised when operations timeout.

### FileUploadError Objects

```python
class FileUploadError(AixplainV2Error)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L65)

Raised when file upload operations fail.

#### create\_operation\_failed\_error

```python
def create_operation_failed_error(response: Dict[str, Any]) -> APIError
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/exceptions.py#L72)

Create an operation failed error from API response.

