---
sidebar_label: file
title: aixplain.v2.file
---

Simple Resource class for file handling and S3 uploads.

### ResourceGetParams Objects

```python
@dataclass_json

@dataclass
class ResourceGetParams()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L21)

Parameters for getting resources.

### Resource Objects

```python
@dataclass_json

@dataclass(repr=False)
class Resource(BaseResource)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L30)

Simple resource class for file handling and S3 uploads.

This class provides the basic functionality needed for the requirements:
- File path handling
- S3 upload via save()
- URL access after upload

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L49)

Initialize the resource.

#### build\_save\_payload

```python
def build_save_payload(**kwargs) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L79)

Build the payload for saving the resource.

#### save

```python
def save(is_temp: Optional[bool] = None, **kwargs) -> "Resource"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L93)

Save the resource, uploading file to S3 if needed.

**Arguments**:

- `is_temp` - Whether this is a temporary upload. If None, uses the resource&#x27;s is_temp setting.
- `**kwargs` - Additional parameters for saving.

#### url

```python
@property
def url() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L130)

Get the presigned/public URL of the uploaded file.

#### create\_from\_file

```python
@classmethod
def create_from_file(cls,
                     file_path: str,
                     is_temp: bool = True,
                     **kwargs) -> "Resource"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L135)

Create a resource from a file path.

**Arguments**:

- `file_path` - Path to the file to upload.
- `is_temp` - Whether this is a temporary upload (default: True).
- `**kwargs` - Additional parameters for initialization.

#### \_\_init\_\_

```python
def __init__(file_path: Optional[str] = None, is_temp: bool = True, **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L147)

Initialize the resource with file path.

**Arguments**:

- `file_path` - Path to the file to upload.
- `is_temp` - Whether this is a temporary upload (default: True).
- `**kwargs` - Additional parameters for initialization.

