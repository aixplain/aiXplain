---
sidebar_label: file_utils
title: aixplain.utils.file_utils
---

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#### save\_file

```python
def save_file(
        download_url: Text,
        download_file_path: Optional[Union[str,
                                           Path]] = None) -> Union[str, Path]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/file_utils.py#L32)

Download and save a file from a given URL.

This function downloads a file from the specified URL and saves it either
to a specified path or to a generated path in the &#x27;aiXplain&#x27; directory.

**Arguments**:

- `download_url` _Text_ - URL of the file to download.
- `download_file_path` _Optional[Union[str, Path]], optional_ - Path where the
  downloaded file should be saved. If None, generates a folder &#x27;aiXplain&#x27;
  in the current working directory and saves the file there with a UUID
  name. Defaults to None.
  

**Returns**:

  Union[str, Path]: Path where the file was downloaded.
  

**Notes**:

  If download_file_path is None, the file will be saved with a UUID name
  and the original file extension in the &#x27;aiXplain&#x27; directory.

#### download\_data

```python
def download_data(url_link: str, local_filename: Optional[str] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/file_utils.py#L64)

Download a file from a URL with streaming support.

This function downloads a file from the specified URL using streaming to
handle large files efficiently. The file is downloaded in chunks to
minimize memory usage.

**Arguments**:

- `url_link` _str_ - URL of the file to download.
- `local_filename` _Optional[str], optional_ - Local path where the file
  should be saved. If None, uses the last part of the URL as the
  filename. Defaults to None.
  

**Returns**:

- `str` - Path to the downloaded file.
  

**Raises**:

- `requests.exceptions.RequestException` - If the download fails or the
  server returns an error status.

#### upload\_data

```python
def upload_data(file_name: Union[Text, Path],
                tags: Optional[List[Text]] = None,
                license: Optional[License] = None,
                is_temp: bool = True,
                content_type: Text = "text/csv",
                content_encoding: Optional[Text] = None,
                nattempts: int = 2,
                return_download_link: bool = False) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/file_utils.py#L97)

Upload a file to S3 using pre-signed URLs with retry support.

This function handles file uploads to S3 by first obtaining a pre-signed URL
from the aiXplain backend and then using it to upload the file. It supports
both temporary and permanent storage with optional metadata like tags and
license information.

**Arguments**:

- `file_name` _Union[Text, Path]_ - Local path of the file to upload.
- `tags` _Optional[List[Text]], optional_ - List of tags to associate with
  the file. Only used when is_temp is False. Defaults to None.
- `license` _Optional[License], optional_ - License to associate with the file.
  Only used when is_temp is False. Defaults to None.
- `is_temp` _bool, optional_ - Whether to upload as a temporary file.
  Temporary files have different handling and URL generation.
  Defaults to True.
- `content_type` _Text, optional_ - MIME type of the content being uploaded.
  Defaults to &quot;text/csv&quot;.
- `content_encoding` _Optional[Text], optional_ - Content encoding of the file
  (e.g., &#x27;gzip&#x27;). Defaults to None.
- `nattempts` _int, optional_ - Number of retry attempts for upload failures.
  Defaults to 2.
- `return_download_link` _bool, optional_ - If True, returns a direct download
  URL instead of the S3 path. Defaults to False.
  

**Returns**:

- `str` - Either an S3 path (s3://bucket/key) or a download URL, depending
  on return_download_link parameter.
  

**Raises**:

- `Exception` - If the upload fails after all retry attempts.
  

**Notes**:

  The function will automatically retry failed uploads up to nattempts
  times before raising an exception.

#### s3\_to\_csv

```python
def s3_to_csv(
    s3_url: Text,
    aws_credentials: Optional[Dict[Text, Text]] = {
        "AWS_ACCESS_KEY_ID": None,
        "AWS_SECRET_ACCESS_KEY": None
    }
) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/file_utils.py#L207)

Convert S3 directory contents to a CSV file with file listings.

This function takes an S3 URL and creates a CSV file containing listings
of all files in that location. It handles both single files and directories,
with special handling for directory structures.

**Arguments**:

- `s3_url` _Text_ - S3 URL in the format &#x27;s3://bucket-name/path&#x27;.
- `aws_credentials` _Optional[Dict[Text, Text]], optional_ - AWS credentials
  dictionary with &#x27;AWS_ACCESS_KEY_ID&#x27; and &#x27;AWS_SECRET_ACCESS_KEY&#x27;.
  If not provided or values are None, uses environment variables.
  Defaults to \{&quot;AWS_ACCESS_KEY_ID&quot;: None, &quot;AWS_SECRET_ACCESS_KEY&quot;: None}.
  

**Returns**:

- `str` - Path to the generated CSV file. The file contains listings of
  all files found in the S3 location.
  

**Raises**:

- `Exception` - If:
  - boto3 is not installed
  - Invalid S3 URL format
  - AWS credentials are missing
  - Bucket doesn&#x27;t exist
  - No files found
  - Files are at bucket root
  - Directory structure is invalid (unequal file counts or mismatched names)
  

**Notes**:

  - The function requires the boto3 package to be installed
  - The generated CSV will have a UUID as filename
  - For directory structures, all subdirectories must have the same
  number of files with matching prefixes

