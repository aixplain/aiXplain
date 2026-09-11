---
sidebar_label: request_utils
title: aixplain.utils.request_utils
---

#### get\_session

```python
def get_session() -> requests.Session
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/request_utils.py#L35)

Return this thread&#x27;s session, creating it on first use.

**Returns**:

- `requests.Session` - A session owned exclusively by the calling thread.

