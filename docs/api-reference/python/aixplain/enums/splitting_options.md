---
sidebar_label: splitting_options
title: aixplain.enums.splitting_options
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
Date: May 30th 2025
Description:
    Splitting Options Enum

### SplittingOptions Objects

```python
class SplittingOptions(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/splitting_options.py#L27)

Enumeration of possible splitting options.

This enum defines the different ways that text can be split into chunks,
including by word, sentence, passage, page, and line.

**Attributes**:

- `WORD` _str_ - Split by word.
- `SENTENCE` _str_ - Split by sentence.
- `PASSAGE` _str_ - Split by passage.
- `PAGE` _str_ - Split by page.
- `LINE` _str_ - Split by line.

#### \_\_str\_\_

```python
def __str__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/splitting_options.py#L46)

Return the string representation of the splitting option.

**Returns**:

- `str` - The splitting option value as a string.

