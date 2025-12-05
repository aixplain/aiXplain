---
sidebar_label: data_type
title: aixplain.enums.data_type
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
    Data Type Enum

### DataType Objects

```python
class DataType(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/data_type.py#L27)

Enumeration of supported data types in the aiXplain system.

This enum defines all the data types that can be processed by the system,
including various media types and basic data types.

**Attributes**:

- `AUDIO` _str_ - Audio data type.
- `FLOAT` _str_ - Floating-point number data type.
- `IMAGE` _str_ - Image data type.
- `INTEGER` _str_ - Integer number data type.
- `LABEL` _str_ - Label/category data type.
- `TENSOR` _str_ - Tensor/multi-dimensional array data type.
- `TEXT` _str_ - Text data type.
- `VIDEO` _str_ - Video data type.
- `EMBEDDING` _str_ - Vector embedding data type.
- `NUMBER` _str_ - Generic number data type.
- `FLOAT`0 _str_ - Boolean data type.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/data_type.py#L58)

Return the string representation of the data type.

**Returns**:

- `str` - The data type value as a string.

