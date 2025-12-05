---
sidebar_label: api_key_checker
title: aixplain.decorators.api_key_checker
---

API key validation decorator for aiXplain SDK.

#### check\_api\_key

```python
def check_api_key(method)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/decorators/api_key_checker.py#L6)

Decorator to verify that an API key is set before executing the method.

This decorator uses the centralized API key validation logic from config.py
to ensure consistent behavior across the entire SDK.

**Arguments**:

- `method` _callable_ - The method to be decorated.
  

**Returns**:

- `callable` - The wrapped method that includes API key verification.
  

**Raises**:

- `Exception` - If neither TEAM_API_KEY nor AIXPLAIN_API_KEY is set.
  

**Example**:

  @check_api_key
  def my_api_method():
  # Method implementation
  pass

