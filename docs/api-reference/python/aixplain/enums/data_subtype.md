---
sidebar_label: data_subtype
title: aixplain.enums.data_subtype
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
Date: May 3rd 2023
Description:
    Data Subtype Enum

### DataSubtype Objects

```python
class DataSubtype(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/data_subtype.py#L27)

Enumeration of data subtypes for categorizing and organizing data.

This enum defines various subtypes that can be used to further categorize
data points within the system, particularly useful for demographic and
content-based categorization.

**Attributes**:

- `AGE` _str_ - Age category subtype.
- `GENDER` _str_ - Gender category subtype.
- `INTERVAL` _str_ - Time interval subtype.
- `OTHER` _str_ - Miscellaneous/other subtype.
- `RACE` _str_ - Race/ethnicity category subtype.
- `SPLIT` _str_ - Data split category subtype.
- `TOPIC` _str_ - Content topic subtype.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/data_subtype.py#L51)

Return the string representation of the data subtype.

**Returns**:

- `str` - The data subtype value as a string.

