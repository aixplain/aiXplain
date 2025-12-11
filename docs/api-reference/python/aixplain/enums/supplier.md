---
sidebar_label: supplier
title: aixplain.enums.supplier
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
Date: September 25th 2023
Description:
    Supplier Enum

#### clean\_name

```python
def clean_name(name: str) -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/supplier.py#L33)

Clean a supplier name by replacing spaces and special characters with underscores.

This function takes a supplier name and performs the following transformations:
1. Replaces spaces and hyphens with underscores.
2. Removes any non-alphanumeric characters.
3. Removes any leading numbers.

**Arguments**:

- `name` _str_ - The supplier name to clean.
  

**Returns**:

- `str` - The cleaned supplier name.

#### load\_suppliers

```python
def load_suppliers() -> Enum
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/supplier.py#L53)

Load suppliers from the backend or cache.

This function fetches supplier information from the backend API and creates
an Enum class with supplier names as keys.

**Returns**:

- `Enum` - An Enum class with supplier names as keys.
  

**Raises**:

- `Exception` - If suppliers cannot be loaded due to invalid API key or other errors.

