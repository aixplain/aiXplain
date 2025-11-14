---
sidebar_label: response_status
title: aixplain.enums.response_status
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

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: February 21st 2024
Description:
    Asset Enum

### ResponseStatus Objects

```python
class ResponseStatus(Text, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/response_status.py#L28)

Enumeration of possible response status values.

This enum defines the different statuses that a response can be in, including
in progress, success, and failure.

**Attributes**:

- `IN_PROGRESS` _str_ - Response is in progress.
- `SUCCESS` _str_ - Response was successful.
- `FAILED` _str_ - Response failed.

#### \_\_str\_\_

```python
def __str__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/response_status.py#L43)

Return the string representation of the response status.

**Returns**:

- `str` - The response status value as a string.

