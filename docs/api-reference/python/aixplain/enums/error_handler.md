---
sidebar_label: error_handler
title: aixplain.enums.error_handler
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
Date: May 26th 2023
Description:
    Error Handler Enum

### ErrorHandler Objects

```python
class ErrorHandler(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/error_handler.py#L27)

Enumeration class defining different error handler strategies.

**Attributes**:

- `SKIP` _str_ - skip failed rows.
- `FAIL` _str_ - raise an exception.

