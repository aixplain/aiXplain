---
sidebar_label: file
title: aixplain.v2.file
---

`from aixplain import File`


Unified File asset resource for files and directories.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

### FileSearchParams Objects

```python
class FileSearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L56)

Search parameters for File assets.

**Attributes**:

- `file_type` - Filter by structural type (``file`` or ``folder``).
- `parent_type` - Filter by the parent asset's type.
- `parent_id` - Filter by parent folder id.
  ownership, sort_by, sort_order: Inherited from `BaseSearchParams`
  like every other resource. ``sort_by`` accepts ``SortBy.NAME`` /
  ``SortBy.CREATED_AT`` / ``SortBy.UPDATED_AT`` or a raw backend field
  name; defaults to newest-created first.

### File Objects

```python
@dataclass_json

@dataclass(repr=False, init=False)
class File(BaseResource, SearchResourceMixin[FileSearchParams, "File"],
           DeleteResourceMixin[BaseDeleteParams, "File"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L76)

A persisted aiXplain file or folder.

**Arguments**:

- `source` - A local file, local directory, or HTTP(S) URL.
- `name` - Optional name overriding the name inferred from ``source``.
- `kwargs` - Backend metadata used when hydrating an existing File.

#### \_\_init\_\_

```python
def __init__(source: Optional[Union[str, os.PathLike[str]]] = None,
             name: Optional[str] = None,
             **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L115)

Initialize a File without performing network writes.

#### is\_dir

```python
@property
def is_dir() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L207)

Whether this File represents a directory.

#### save

```python
def save(**_: Any) -> "File"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L395)

Upload the source and persist it as a backend File asset.

**Raises**:

- `ResourceError` - If the file has been deleted.

#### get\_signed\_url

```python
def get_signed_url(expires_in: Optional[int] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L440)

Return a short-lived signed URL for this file's bytes.

The backend's file-asset responses (create/get/paginate) never carry a
stable ``url`` — it must be requested on demand through the same
signed-URL endpoint the platform UI uses to render media inline. The
endpoint is ``{rootAssetId}/file/{fileId}/url``: a standalone root file
addresses itself both ways, but a child (from ``folder.children``)
must address its parent folder's asset id, tracked in ``_root_id``.

**Arguments**:

- `expires_in` - Signed URL lifetime in seconds (backend default: 1
  hour; capped at 7 days).
  

**Raises**:

- `ValidationError` - If the File is unsaved or is a folder (a folder
  has no single downloadable object — use `download`).

#### build\_delete\_url

```python
def build_delete_url(**kwargs: Any) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L468)

Refuse to delete a non-root child node; there is no documented endpoint for one.

Only the root asset (a standalone File, or a folder as a whole) has a
confirmed delete endpoint (``DELETE {RESOURCE_PATH}/{id}``). A node
from ``folder.children`` carries a ``_root_id`` different from its own
``id`` — deleting the *folder* removes it along with the rest of the
tree; there is no separate per-child delete to fall back on here.

#### get

```python
@classmethod
def get(cls, identifier: str, recursive: bool = True) -> "File"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L485)

Retrieve a File by ID, encoded asset path, or instance ID.

#### download

```python
def download(
        destination: Optional[Union[str, os.PathLike[str]]] = None) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L612)

Stream this File to disk, safely extracting folders from one ZIP request.

**Arguments**:

- `destination` - Where to write the file (or extract the folder). Defaults
  to ``self.name`` in the current directory.

#### \_\_getattr\_\_

```python
def __getattr__(name: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/file.py#L667)

PEP 562: warn on the deprecated ``Resource`` alias, matching ``Aixplain().Resource``.

``Resource`` is deliberately not a plain module attribute: importing this
module — including transitively, through ``aixplain.v2`` — must never warn
by itself. Only an actual access to the deprecated name does.

