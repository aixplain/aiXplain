---
sidebar_label: data
title: aixplain.modules.data
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
    Data Class

### Data Objects

```python
class Data()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/data.py#L33)

A class representing a collection of data samples of the same type and genre.

This class provides functionality for managing data in the aiXplain platform,
supporting various data types, languages, and storage formats. It can handle
both structured (e.g., CSV) and unstructured data files.

**Attributes**:

- `id` _Text_ - ID of the data collection.
- `name` _Text_ - Name of the data collection.
- `dtype` _DataType_ - Type of data (e.g., text, audio, image).
- `privacy` _Privacy_ - Privacy settings for the data.
- `onboard_status` _OnboardStatus_ - Current onboarding status.
- `data_column` _Optional[Any]_ - Column identifier where data is stored in structured files.
- `start_column` _Optional[Any]_ - Column identifier for start indexes in structured files.
- `end_column` _Optional[Any]_ - Column identifier for end indexes in structured files.
- `files` _List[File]_ - List of files containing the data instances.
- `languages` _List[Language]_ - List of languages present in the data.
- `name`0 _DataSubtype_ - Subtype categorization of the data.
- `name`1 _Optional[int]_ - Number of samples/rows in the data collection.
- `name`2 _dict_ - Additional keyword arguments for extensibility.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             dtype: DataType,
             privacy: Privacy,
             onboard_status: OnboardStatus,
             data_column: Optional[Any] = None,
             start_column: Optional[Any] = None,
             end_column: Optional[Any] = None,
             files: List[File] = [],
             languages: List[Language] = [],
             dsubtype: DataSubtype = DataSubtype.OTHER,
             length: Optional[int] = None,
             **kwargs) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/data.py#L56)

Initialize a new Data instance.

**Arguments**:

- `id` _Text_ - ID of the data collection.
- `name` _Text_ - Name of the data collection.
- `dtype` _DataType_ - Type of data (e.g., text, audio, image).
- `privacy` _Privacy_ - Privacy settings for the data.
- `onboard_status` _OnboardStatus_ - Current onboarding status of the data.
- `data_column` _Optional[Any], optional_ - Column identifier where data is stored in
  structured files (e.g., CSV). If None, defaults to the value of name.
- `start_column` _Optional[Any], optional_ - Column identifier where start indexes are
  stored in structured files. Defaults to None.
- `end_column` _Optional[Any], optional_ - Column identifier where end indexes are
  stored in structured files. Defaults to None.
- `files` _List[File], optional_ - List of files containing the data instances.
  Defaults to empty list.
- `languages` _List[Language], optional_ - List of languages present in the data.
  Can be provided as Language enums or language codes. Defaults to empty list.
- `name`0 _DataSubtype, optional_ - Subtype categorization of the data
  (e.g., age, topic, race, split). Defaults to DataSubtype.OTHER.
- `name`1 _Optional[int], optional_ - Number of samples/rows in the data collection.
  Defaults to None.
- `name`2 - Additional keyword arguments for extensibility.

