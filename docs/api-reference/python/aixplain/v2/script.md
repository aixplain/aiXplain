---
sidebar_label: script
title: aixplain.v2.script
---

### Script Objects

```python
class Script(BaseResource)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/script.py#L4)

#### upload

```python
@classmethod
def upload(cls, script_path: str) -> "Script"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/script.py#L6)

Upload a script to the server.

**Arguments**:

- `script_path` - str: The path to the script.
  

**Returns**:

- `Script` - The script.

