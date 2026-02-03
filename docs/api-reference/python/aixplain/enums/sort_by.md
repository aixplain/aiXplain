---
sidebar_label: sort_by
title: aixplain.enums.sort_by
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
    Sort By Enum

### SortBy Objects

```python
class SortBy(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/sort_by.py#L27)

Enumeration of possible sorting criteria.

This enum defines the different criteria that can be used to sort assets,
including creation date, price, and popularity.

**Attributes**:

- `CREATION_DATE` _str_ - Sort by creation date.
- `PRICE` _str_ - Sort by normalized price.
- `POPULARITY` _str_ - Sort by total number of subscriptions.

