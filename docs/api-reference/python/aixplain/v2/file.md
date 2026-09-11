---
sidebar_label: file
title: aixplain.v2.file
---

Unified File asset resource for files and directories.

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

### File Objects

```python
@dataclass_json

@dataclass(repr=False, init=False)
class File(BaseResource)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L44)

A persisted aiXplain file or folder.

**Arguments**:

- `source` - A local file, local directory, or HTTP(S) URL.
- `name` - Optional name overriding the name inferred from ``source``.
- `is_temp` - Whether the source is still transient. A successful save sets this to ``False``.
- `kwargs` - Backend metadata used when hydrating an existing File.

#### \_\_init\_\_

```python
def __init__(source: Optional[Union[str, os.PathLike[str]]] = None,
             name: Optional[str] = None,
             is_temp: bool = True,
             **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L72)

Initialize a File without performing network writes.

#### is\_dir

```python
@property
def is_dir() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L157)

Whether this File represents a directory.

#### file\_path

```python
@property
def file_path() -> Optional[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L162)

Return the original local path for compatibility with the early Resource API.

#### create\_from\_file

```python
@classmethod
def create_from_file(cls,
                     file_path: str,
                     is_temp: bool = True,
                     **kwargs: Any) -> "File"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L167)

Create a File from a local path.

#### save

```python
def save(**_: Any) -> "File"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L299)

Upload the source and persist it as a backend File asset.

**Raises**:

- `ResourceError` - If the file has been deleted.

#### get

```python
@classmethod
def get(cls, identifier: str, recursive: bool = True) -> "File"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L345)

Retrieve a File by ID, encoded asset path, or instance ID.

#### search

```python
@classmethod
def search(cls,
           query: Optional[str] = None,
           page_number: int = 0,
           page_size: int = 20,
           sort: Optional[List[Dict[str, Any]]] = None,
           **filters: Any) -> Page["File"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L382)

Search top-level File assets.

#### download

```python
def download(destination: Union[str, os.PathLike[str]]) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L406)

Stream this File to disk, safely extracting folders from one ZIP request.

