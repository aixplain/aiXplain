---
sidebar_label: status
title: aixplain.enums.status
---

### Status Objects

```python
class Status(Text, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/status.py#L5)

Enumeration of possible status values.

This enum defines the different statuses that a task or operation can be in,
including failed, in progress, and success.

**Attributes**:

- `FAILED` _str_ - Task failed.
- `IN_PROGRESS` _str_ - Task is in progress.
- `SUCCESS` _str_ - Task was successful.

