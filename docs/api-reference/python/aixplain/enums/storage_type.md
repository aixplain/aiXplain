---
sidebar_label: storage_type
title: aixplain.enums.storage_type
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
    Storage Type Enum

### StorageType Objects

```python
class StorageType(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/storage_type.py#L27)

Enumeration of possible storage types.

This enum defines the different types of storage that can be used to store
assets, including text, URL, and file.

**Attributes**:

- `TEXT` _str_ - Text storage type.
- `URL` _str_ - URL storage type.
- `FILE` _str_ - File storage type.

#### \_\_str\_\_

```python
def __str__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/storage_type.py#L42)

Return the string representation of the storage type.

**Returns**:

- `str` - The storage type value as a string.

