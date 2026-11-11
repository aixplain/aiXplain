---
sidebar_label: upload_utils
title: aixplain.v2.upload_utils
---

`from aixplain import FileUploader, upload_file, validate_file_for_upload`


File upload utilities for v2 Resource system.

This module provides comprehensive file upload functionality that ports the exact
logic from the legacy FileFactory while maintaining a clean, modular architecture.

### FileValidator Objects

```python
class FileValidator()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L28)

Handles file validation logic.

#### validate\_file\_exists

```python
@classmethod
def validate_file_exists(cls, file_path: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L42)

Validate that the file exists.

#### validate\_file\_size

```python
@classmethod
def validate_file_size(cls, file_path: str, file_type: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L48)

Validate file size against type-specific limits.

#### get\_file\_size\_mb

```python
@classmethod
def get_file_size_mb(cls, file_path: str) -> float
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L59)

Get file size in MB.

### MimeTypeDetector Objects

```python
class MimeTypeDetector()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L64)

Handles MIME type detection with fallback support.

#### detect\_mime\_type

```python
@classmethod
def detect_mime_type(cls, file_path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L86)

Detect MIME type with fallback support.

#### classify\_file\_type

```python
@classmethod
def classify_file_type(cls, file_path: str, mime_type: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L103)

Classify file type for size limit enforcement.

### RequestManager Objects

```python
class RequestManager()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L119)

Handles HTTP requests with retry logic.

#### create\_session

```python
@classmethod
def create_session(cls) -> requests.Session
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L131)

Return the shared retry session, creating it on first use.

#### request\_with\_retry

```python
@classmethod
def request_with_retry(cls, method: str, url: str,
                       **kwargs) -> requests.Response
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L142)

Make HTTP request with retry logic.

A default ``(connect, read)`` timeout is applied when the caller doesn't
pass one: without it ``requests`` waits forever, so a peer that accepts
the connection and then goes silent pins the calling thread with no upper
bound. The read timeout only starts once the request body has been sent;
while it is being sent the socket is held to the *connect* timeout, so
an upload passes its own ``timeout=upload_timeout()`` (see
`aixplain.v2.client.upload_timeout`). Override per call with
``timeout=`` or globally via ``AIXPLAIN_HTTP_CONNECT_TIMEOUT`` /
``AIXPLAIN_HTTP_READ_TIMEOUT`` / ``AIXPLAIN_HTTP_UPLOAD_TIMEOUT``.

### PresignedUrlManager Objects

```python
class PresignedUrlManager()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L162)

Handles pre-signed URL requests to aiXplain backend.

#### get\_temp\_upload\_url

```python
@classmethod
def get_temp_upload_url(cls, backend_url: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L166)

Get temporary upload URL endpoint.

#### get\_perm\_upload\_url

```python
@classmethod
def get_perm_upload_url(cls, backend_url: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L171)

Get permanent upload URL endpoint.

#### build\_temp\_payload

```python
@classmethod
def build_temp_payload(cls, content_type: str,
                       file_name: str) -> Dict[str, str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L176)

Build payload for temporary upload request.

#### build\_perm\_payload

```python
@classmethod
def build_perm_payload(cls, content_type: str, file_path: str, tags: List[str],
                       license: str) -> Dict[str, str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L184)

Build payload for permanent upload request.

#### request\_presigned\_url

```python
@classmethod
def request_presigned_url(cls, url: str, payload: Dict[str, str],
                          api_key: str) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L194)

Request pre-signed URL from backend.

#### upload\_body

```python
def upload_body(handle: BinaryIO) -> Union[BinaryIO, bytes]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L206)

Return what to send as the body of a presigned upload PUT for *handle*.

The open handle itself, so the file is streamed, except for an empty file:
``requests`` cannot take a length from an empty handle and falls back to
``Transfer-Encoding: chunked``, which a presigned S3 PUT rejects. An empty
``bytes`` body is sent with ``Content-Length: 0`` instead.

**Arguments**:

- `handle` - The file, opened in binary mode and positioned at its start.
  

**Returns**:

  *handle*, or ``b""`` when the file is empty.

### S3Uploader Objects

```python
class S3Uploader()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L223)

Handles S3 file uploads using pre-signed URLs.

#### upload\_file

```python
@classmethod
def upload_file(cls, file_path: str, presigned_url: str,
                content_type: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L227)

Upload file to S3 using pre-signed URL.

**Raises**:

- `UnsafeURLError` - If ``presigned_url`` does not point at an allowed
  upload host. The check sits *outside* the ``try`` below so the
  generic ``FileUploadError`` wrapper cannot mask why the upload
  was refused (BUG-939).

#### construct\_s3\_url

```python
@classmethod
def construct_s3_url(cls, presigned_url: str, path: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L274)

Construct an ``s3://`` URL from a pre-signed upload URL and object key.

Handles both S3 addressing styles (and regional hosts):

* virtual-hosted-style: ``https://<bucket>.s3[.<region>].amazonaws.com/<key>``
* path-style:           ``https://s3[.<region>].amazonaws.com/<bucket>/<key>``

The previous implementation only recognised virtual-hosted-style URLs and
silently fell back to a hardcoded ``aixplain-uploads`` bucket for anything
else (e.g. the path-style URLs returned by some backends), producing links
that point at the wrong bucket.

### ConfigManager Objects

```python
class ConfigManager()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L303)

Handles configuration and environment variables.

#### get\_backend\_url

```python
@classmethod
def get_backend_url(cls, custom_url: Optional[str] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L309)

Resolve the backend URL and apply the config-URL policy.

The upload helpers send ``Authorization: token <key>`` to this URL, so
it gets the same check ``Aixplain()`` applies to ``BACKEND_URL``
(BUG-1451): https only unless ``AIXPLAIN_ALLOW_INSECURE_URLS=1``, no
userinfo, and a one-time WARNING for a non-aiXplain host.

**Arguments**:

- `custom_url` - Explicit backend URL; falls back to ``BACKEND_URL`` and
  then to the public aiXplain platform.
  

**Returns**:

- `str` - The validated backend URL.
  

**Raises**:

- `UnsafeURLError` - If the resolved URL fails the policy.

#### get\_api\_key

```python
@classmethod
def get_api_key(cls,
                custom_key: Optional[str] = None,
                required: bool = True) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L331)

Get API key from custom value or environment.

Resolution order matches ``Aixplain()``: explicit key, then
``TEAM_API_KEY``, then ``AIXPLAIN_API_KEY``. ``Aixplain(api_key=...)``
does not export its key to the environment, so callers holding a client
should pass ``api_key=aix.api_key`` explicitly.

### FileUploader Objects

```python
class FileUploader()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L348)

Main file upload orchestrator.

#### \_\_init\_\_

```python
def __init__(backend_url: Optional[str] = None,
             api_key: Optional[str] = None,
             require_api_key: bool = True)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L351)

Initialize file uploader with configuration.

**Raises**:

- `UnsafeURLError` - If the resolved backend URL fails the config-URL
  policy (for example plain ``http://`` without
  ``AIXPLAIN_ALLOW_INSECURE_URLS=1``). Raised here, before any
  request carries the API key.

#### upload

```python
def upload(file_path: str,
           tags: Optional[List[str]] = None,
           license: str = "MIT",
           is_temp: bool = True,
           return_download_link: bool = False) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L368)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L429)

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
  

**Raises**:

- `UnsafeURLError` - If the backend URL (``backend_url`` or ``BACKEND_URL``)
  fails the config-URL policy; raised before any request is sent.

#### validate\_file\_for\_upload

```python
def validate_file_for_upload(file_path: str) -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/upload_utils.py#L466)

Validate a file for upload without actually uploading.

**Arguments**:

- `file_path` - Path to the file to validate
  

**Returns**:

  Dictionary with validation results
  

**Raises**:

- `FileUploadError` - If validation fails

