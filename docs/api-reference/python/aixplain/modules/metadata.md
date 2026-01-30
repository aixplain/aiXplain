---
sidebar_label: metadata
title: aixplain.modules.metadata
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
    Meta-data Class

### MetaData Objects

```python
class MetaData()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/metadata.py#L33)

A class representing metadata for data in the aiXplain platform.

This class provides functionality for managing metadata, which is used to store
information about data in the platform. It supports various data types, languages,
and storage formats.

**Attributes**:

- `name` _Text_ - Name of the data.
- `dtype` _DataType_ - Type of data.
- `storage_type` _StorageType_ - Storage type of the data.
- `data_column` _Optional[Text]_ - Column index/name where the data is on a structured file.
- `start_column` _Optional[Text]_ - Column index/name where the start indexes is on a structured file.
- `end_column` _Optional[Text]_ - Column index/name where the end indexes is on a structured file.
- `privacy` _Optional[Privacy]_ - Privacy of data.
- `file_extension` _Optional[FileType]_ - File extension (e.g. CSV, TXT, etc.).
- `languages` _List[Language]_ - List of languages which the data consists of.
- `dsubtype` _DataSubtype_ - Data subtype (e.g., age, topic, race, split, etc.), used in datasets metadata.
- `dtype`0 _Optional[Text]_ - Data ID.
- `dtype`1 _dict_ - Additional keyword arguments for extensibility.

#### \_\_init\_\_

```python
def __init__(name: Text,
             dtype: DataType,
             storage_type: StorageType,
             data_column: Optional[Text] = None,
             start_column: Optional[Text] = None,
             end_column: Optional[Text] = None,
             privacy: Optional[Privacy] = None,
             file_extension: Optional[FileType] = None,
             languages: List[Language] = [],
             dsubtype: DataSubtype = DataSubtype.OTHER,
             id: Optional[Text] = None,
             **kwargs) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/metadata.py#L54)

Initialize a new MetaData instance.

**Arguments**:

- `name` _Text_ - Data Name
- `dtype` _DataType_ - Data Type
- `storage_type` _StorageType_ - Data Storage (e.g. text, local file, web link)
- `data_column` _Optional[Text], optional_ - Column index/name where the data is on a structured file (e.g. CSV). Defaults to None.
- `start_column` _Optional[Text], optional_ - Column index/name where the start indexes is on a structured file (e.g. CSV). Defaults to None.
- `end_column` _Optional[Text], optional_ - Column index/name where the end indexes is on a structured file (e.g. CSV). Defaults to None.
- `privacy` _Optional[Privacy], optional_ - Privacy of data. Defaults to None.
- `file_extension` _Optional[FileType], optional_ - File extension (e.g. CSV, TXT, etc.). Defaults to None.
- `languages` _List[Language], optional_ - List of languages which the data consists of. Defaults to [].
- `dsubtype` _DataSubtype, optional_ - Data subtype (e.g., age, topic, race, split, etc.), used in datasets metadata. Defaults to Other.
- `dtype`0 _Optional[Text], optional_ - Data ID. Defaults to None.

