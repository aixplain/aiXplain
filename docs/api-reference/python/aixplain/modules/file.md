---
sidebar_label: file
title: aixplain.modules.file
---

#### \_\_author\_\_

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

Author: aiXplain team
Date: March 20th 2023
Description:
    File Class

### File Objects

```python
class File()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/file.py#L31)

A class representing a file in the aiXplain platform.

This class provides functionality for managing files, which are used to store
data samples in the platform. It supports various file types, compression formats,
and data splits.

**Attributes**:

- `path` _Union[Text, pathlib.Path]_ - File path
- `extension` _Union[Text, FileType]_ - File extension (e.g. CSV, TXT, etc.)
- `data_split` _Optional[DataSplit]_ - Data split of the file.
- `compression` _Optional[Text]_ - Compression extension (e.g., .gz).

#### \_\_init\_\_

```python
def __init__(path: Union[Text, pathlib.Path],
             extension: Union[Text, FileType],
             data_split: Optional[DataSplit] = None,
             compression: Optional[Text] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/file.py#L44)

Initialize a new File instance.

**Arguments**:

- `path` _Union[Text, pathlib.Path]_ - File path
- `extension` _Union[Text, FileType]_ - File extension (e.g. CSV, TXT, etc.)
- `data_split` _Optional[DataSplit], optional_ - Data split of the file. Defaults to None.
- `compression` _Optional[Text], optional_ - Compression extension (e.g., .gz). Defaults to None.

