---
sidebar_label: script_factory
title: aixplain.factories.script_factory
---

### ScriptFactory Objects

```python
class ScriptFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/script_factory.py#L10)

A factory class for handling script file operations.

This class provides functionality for uploading script files to the backend
and managing their metadata.

#### upload\_script

```python
@classmethod
def upload_script(cls, script_path: str) -> Tuple[str, str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/script_factory.py#L17)

Uploads a script file to the backend and returns its ID and metadata.

**Arguments**:

- `script_path` _str_ - The file system path to the script file to be uploaded.
  

**Returns**:

  Tuple[str, str]: A tuple containing:
  - file_id (str): The unique identifier assigned to the uploaded file.
  - metadata (str): JSON string containing file metadata (name and size).
  

**Raises**:

- `Exception` - If the upload fails or the file cannot be accessed.

