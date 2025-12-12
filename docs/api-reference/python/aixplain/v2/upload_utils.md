---
sidebar_label: upload_utils
title: aixplain.v2.upload_utils
---

File upload utilities for v2 Resource system.

This module provides comprehensive file upload functionality that ports the exact
logic from the legacy FileFactory while maintaining a clean, modular architecture.

### FileValidator Objects

```python
class FileValidator()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L18)

Handles file validation logic.

#### validate\_file\_exists

```python
@classmethod
def validate_file_exists(cls, file_path: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L32)

Validate that the file exists.

#### validate\_file\_size

```python
@classmethod
def validate_file_size(cls, file_path: str, file_type: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L40)

Validate file size against type-specific limits.

#### get\_file\_size\_mb

```python
@classmethod
def get_file_size_mb(cls, file_path: str) -> float
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L52)

Get file size in MB.

### MimeTypeDetector Objects

```python
class MimeTypeDetector()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L57)

Handles MIME type detection with fallback support.

#### detect\_mime\_type

```python
@classmethod
def detect_mime_type(cls, file_path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L79)

Detect MIME type with fallback support.

#### classify\_file\_type

```python
@classmethod
def classify_file_type(cls, file_path: str, mime_type: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L96)

Classify file type for size limit enforcement.

### RequestManager Objects

```python
class RequestManager()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L112)

Handles HTTP requests with retry logic.

#### create\_session

```python
@classmethod
def create_session(cls) -> requests.Session
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L116)

Create a requests session with retry configuration.

#### request\_with\_retry

```python
@classmethod
def request_with_retry(cls, method: str, url: str,
                       **kwargs) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L123)

Make HTTP request with retry logic.

### PresignedUrlManager Objects

```python
class PresignedUrlManager()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L129)

Handles pre-signed URL requests to aiXplain backend.

#### get\_temp\_upload\_url

```python
@classmethod
def get_temp_upload_url(cls, backend_url: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L133)

Get temporary upload URL endpoint.

#### get\_perm\_upload\_url

```python
@classmethod
def get_perm_upload_url(cls, backend_url: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L138)

Get permanent upload URL endpoint.

#### build\_temp\_payload

```python
@classmethod
def build_temp_payload(cls, content_type: str,
                       file_name: str) -> Dict[str, str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L143)

Build payload for temporary upload request.

#### build\_perm\_payload

```python
@classmethod
def build_perm_payload(cls, content_type: str, file_path: str, tags: List[str],
                       license: str) -> Dict[str, str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L151)

Build payload for permanent upload request.

#### request\_presigned\_url

```python
@classmethod
def request_presigned_url(cls, url: str, payload: Dict[str, str],
                          api_key: str) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L163)

Request pre-signed URL from backend.

### S3Uploader Objects

```python
class S3Uploader()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L181)

Handles S3 file uploads using pre-signed URLs.

#### upload\_file

```python
@classmethod
def upload_file(cls, file_path: str, presigned_url: str,
                content_type: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L185)

Upload file to S3 using pre-signed URL.

#### construct\_s3\_url

```python
@classmethod
def construct_s3_url(cls, presigned_url: str, path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L206)

Construct S3 URL from pre-signed URL and path.

### ConfigManager Objects

```python
class ConfigManager()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L218)

Handles configuration and environment variables.

#### get\_backend\_url

```python
@classmethod
def get_backend_url(cls, custom_url: Optional[str] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L222)

Get backend URL from custom value or environment.

#### get\_api\_key

```python
@classmethod
def get_api_key(cls,
                custom_key: Optional[str] = None,
                required: bool = True) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L229)

Get API key from custom value or environment.

### FileUploader Objects

```python
class FileUploader()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L241)

Main file upload orchestrator.

#### \_\_init\_\_

```python
def __init__(backend_url: Optional[str] = None,
             api_key: Optional[str] = None,
             require_api_key: bool = True)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L244)

Initialize file uploader with configuration.

#### upload

```python
def upload(file_path: str,
           tags: Optional[List[str]] = None,
           license: str = "MIT",
           is_temp: bool = True,
           return_download_link: bool = False) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L254)

Upload a file to S3 using the same logic as legacy FileFactory.

**Arguments**:

- `file_path` - Path to the file to upload
- `tags` - Tags to associate with the file
- `license` - License type for the file
- `is_temp` - Whether this is a temporary upload
- `return_download_link` - Whether to return download link instead of S3 path
  

**Returns**:

  S3 path (s3://bucket/key) or download URL
  

**Raises**:

- `FileUploadError` - If upload fails

#### upload\_file

```python
def upload_file(file_path: str,
                tags: Optional[List[str]] = None,
                license: str = "MIT",
                is_temp: bool = True,
                return_download_link: bool = False,
                backend_url: Optional[str] = None,
                api_key: Optional[str] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L322)

Convenience function to upload a file.

**Arguments**:

- `file_path` - Path to the file to upload
- `tags` - Tags to associate with the file
- `license` - License type for the file
- `is_temp` - Whether this is a temporary upload
- `return_download_link` - Whether to return download link instead of S3 path
- `backend_url` - Custom backend URL (optional)
- `api_key` - Custom API key (optional)
  

**Returns**:

  S3 path (s3://bucket/key) or download URL

#### validate\_file\_for\_upload

```python
def validate_file_for_upload(file_path: str) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L356)

Validate a file for upload without actually uploading.

**Arguments**:

- `file_path` - Path to the file to validate
  

**Returns**:

  Dictionary with validation results
  

**Raises**:

- `FileUploadError` - If validation fails

