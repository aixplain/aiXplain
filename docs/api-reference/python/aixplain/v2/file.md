---
sidebar_label: file
title: aixplain.v2.file
---

### FileCreateParams Objects

```python
class FileCreateParams(BaseCreateParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L10)

Parameters for creating a file.

### File Objects

```python
class File(BaseResource, CreateResourceMixin[FileCreateParams, "File"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L19)

Resource for files.

#### create

```python
@classmethod
def create(cls, *args, **kwargs: Unpack[FileCreateParams]) -> "File"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L25)

Create a file.

#### to\_link

```python
@classmethod
def to_link(cls, local_path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L36)

Convert a local path to a link.

**Arguments**:

- `local_path` - str: The local path to the file.
  

**Returns**:

- `str` - The link to the file.

#### upload

```python
@classmethod
def upload(cls,
           local_path: str,
           tags: List[str] = None,
           license: "License" = None,
           is_temp: bool = True) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L50)

Upload a file.

**Arguments**:

- `local_path` - str: The local path to the file.
  

**Returns**:

- `str` - The upload URL.

#### check\_storage\_type

```python
@classmethod
def check_storage_type(cls, upload_url: str) -> "StorageType"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L70)

Check the storage type of a file.

**Arguments**:

- `upload_url` - str: The upload URL.
  

**Returns**:

- `StorageType` - The storage type of the file.

