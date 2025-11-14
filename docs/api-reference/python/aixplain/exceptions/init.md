---
sidebar_label: exceptions
title: aixplain.exceptions
---

Error message registry for aiXplain SDK.

This module maintains a centralized registry of error messages used throughout the aiXplain ecosystem.
It allows developers to look up existing error messages and reuse them instead of creating new ones.

#### get\_error\_from\_status\_code

```python
def get_error_from_status_code(status_code: int,
                               error_details: str = None
                               ) -> AixplainBaseException
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/exceptions/__init__.py#L35)

Map HTTP status codes to appropriate exception types.

**Arguments**:

- `status_code` _int_ - The HTTP status code to map.
- `error_details` _str, optional_ - Additional error details to include in the message.
  

**Returns**:

- `AixplainBaseException` - An exception of the appropriate type.

