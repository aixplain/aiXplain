---
sidebar_label: database_source
title: aixplain.enums.database_source
---

#### \_\_author\_\_

Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Lucas Pavanelli and Thiago Castro Ferreira and Ahmet Gunduz
Date: March 7th 2025
Description:
    Database Source Type Enum

### DatabaseSourceType Objects

```python
class DatabaseSourceType(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/database_source.py#L27)

Enumeration of supported database source types.

This enum defines the different types of database sources that can be used
for data storage and retrieval in the system.

**Attributes**:

- `POSTGRESQL` _str_ - PostgreSQL database source type.
- `SQLITE` _str_ - SQLite database source type.
- `CSV` _str_ - CSV file source type.

#### from\_string

```python
@classmethod
def from_string(cls, source_type: str) -> "DatabaseSourceType"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/database_source.py#L44)

Convert string to DatabaseSourceType enum

**Arguments**:

- `source_type` _str_ - Source type string
  

**Returns**:

- `DatabaseSourceType` - Corresponding enum value

