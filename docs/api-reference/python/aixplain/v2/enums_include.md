---
sidebar_label: enums_include
title: aixplain.v2.enums_include
---

### ErrorHandler Objects

```python
class ErrorHandler(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/enums_include.py#L54)

Enumeration class defining different error handler strategies.

**Attributes**:

- `SKIP` _str_ - skip failed rows.
- `FAIL` _str_ - raise an exception.

