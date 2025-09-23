---
sidebar_label: api_key_checker
title: aixplain.decorators.api_key_checker
---

#### check\_api\_key

```python
def check_api_key(method)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/decorators/api_key_checker.py#L4)

Decorator to verify that an API key is set before executing the method.

This decorator checks if either TEAM_API_KEY or AIXPLAIN_API_KEY is set in the
configuration. If neither key is set, it raises an exception.

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

