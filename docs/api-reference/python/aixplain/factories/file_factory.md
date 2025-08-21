---
sidebar_label: file_factory
title: aixplain.factories.file_factory
---

#### \_\_author\_\_

Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain team
Date: March 20th 2023
Description:
    File Factory Class

### FileFactory Objects

```python
class FileFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/file_factory.py#L39)

Factory class for managing file uploads and storage in the aiXplain platform.

This class provides functionality for uploading files to S3 storage,
checking storage types, and managing file links. It supports various file
types with different size limits and handles both temporary and permanent
storage.

#### upload

```python
@classmethod
def upload(cls,
           local_path: Text,
           tags: Optional[List[Text]] = None,
           license: Optional[License] = None,
           is_temp: bool = True,
           return_download_link: bool = False) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/file_factory.py#L49)

Upload a file to the aiXplain S3 storage.

This method uploads a file to S3 storage with size limits based on file type:
- Audio: 50MB
- Application: 25MB
- Video: 300MB
- Image: 25MB
- Database: 300MB
- Other: 50MB

**Arguments**:

- `local_path` _Text_ - Path to the file to upload.
- `tags` _Optional[List[Text]], optional_ - Tags to associate with the file.
  Defaults to None.
- `license` _Optional[License], optional_ - License type for the file.
  Required for non-temporary files. Defaults to None.
- `is_temp` _bool, optional_ - Whether this is a temporary upload.
  Defaults to True.
- `return_download_link` _bool, optional_ - Whether to return a download
  link instead of S3 path. Only valid for temporary files.
  Defaults to False.
  

**Returns**:

- `Text` - Either:
  - S3 path where the file was uploaded (if return_download_link=False)
  - Download URL for the file (if return_download_link=True)
  

**Raises**:

- `FileNotFoundError` - If the local file doesn&#x27;t exist.
- `Exception` - If:
  - File size exceeds the type-specific limit
  - Requesting download link for non-temporary file
- `AssertionError` - If requesting download link for non-temporary file.

#### check\_storage\_type

```python
@classmethod
def check_storage_type(cls, input_link: Any) -> StorageType
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/file_factory.py#L137)

Determine the storage type of a given input.

This method checks whether the input is a local file path, a URL
(including S3 and HTTP/HTTPS links), or raw text content.

**Arguments**:

- `input_link` _Any_ - Input to check. Can be a file path, URL, or text.
  

**Returns**:

- `StorageType` - Storage type enum value:
  - StorageType.FILE: Local file path
  - StorageType.URL: S3 or HTTP/HTTPS URL
  - StorageType.TEXT: Raw text content

#### to\_link

```python
@classmethod
def to_link(cls, data: Union[Text, Dict], **kwargs) -> Union[Text, Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/file_factory.py#L165)

Convert local file paths to aiXplain platform links.

This method checks if the input contains local file paths and uploads
them to the platform, replacing the paths with the resulting URLs.
Other types of input (URLs, text) are left unchanged.

**Arguments**:

- `data` _Union[Text, Dict]_ - Input data to process. Can be:
  - Text: Single file path, URL, or text content
  - Dict: Dictionary with string values that may be file paths
- `**kwargs` - Additional arguments passed to upload() method.
  

**Returns**:

  Union[Text, Dict]: Processed input where any local file paths have
  been replaced with platform URLs. Structure matches input type.

#### create

```python
@classmethod
def create(cls,
           local_path: Text,
           tags: Optional[List[Text]] = None,
           license: Optional[License] = None,
           is_temp: bool = False) -> Text
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/file_factory.py#L193)

Create a permanent or temporary file asset in the platform.

This method is similar to upload() but with a focus on creating file
assets. For permanent assets (is_temp=False), a license is required.

**Arguments**:

- `local_path` _Text_ - Path to the file to upload.
- `tags` _Optional[List[Text]], optional_ - Tags to associate with the file.
  Defaults to None.
- `license` _Optional[License], optional_ - License type for the file.
  Required for non-temporary files. Defaults to None.
- `is_temp` _bool, optional_ - Whether this is a temporary upload.
  Defaults to False.
  

**Returns**:

- `Text` - Either:
  - S3 path for permanent files (is_temp=False)
  - Download URL for temporary files (is_temp=True)
  

**Raises**:

- `FileNotFoundError` - If the local file doesn&#x27;t exist.
- `Exception` - If file size exceeds the type-specific limit.
- `AssertionError` - If license is not provided for non-temporary files.

