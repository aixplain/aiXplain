---
sidebar_label: language
title: aixplain.enums.language
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
Date: March 22th 2023
Description:
    Language Enum

### LanguageMetadata Objects

```python
@dataclass
class LanguageMetadata()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/language.py#L34)

Metadata container for language information.

This class holds metadata about a language including its identifier, value,
label, dialects, and supported scripts.

**Attributes**:

- `id` _str_ - ID of the language.
- `value` _str_ - Language code or value.
- `label` _str_ - Label for the language.
- `dialects` _List[Dict[str, str]]_ - List of dialect specifications.
- `scripts` _List[Any]_ - List of supported scripts for the language.

#### to\_dict

```python
def to_dict() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/language.py#L53)

Convert the language metadata to a dictionary.

**Returns**:

- `dict` - Dictionary representation of the language metadata.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: dict) -> "LanguageMetadata"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/language.py#L68)

Create a LanguageMetadata instance from a dictionary.

**Arguments**:

- `data` _dict_ - Dictionary containing language metadata.
  

**Returns**:

- `LanguageMetadata` - New instance created from the dictionary data.

#### load\_languages

```python
def load_languages() -> Enum
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/language.py#L85)

Load language definitions from the backend or cache.

This function attempts to load language definitions from the cache first.
If the cache is invalid or doesn&#x27;t exist, it fetches the data from the
backend API. It creates a dynamic Enum class containing all available
languages and their dialects.

**Returns**:

- `Enum` - Dynamically created Language enum class with language codes and dialects.
  

**Raises**:

- `Exception` - If languages cannot be loaded due to invalid API key or other errors.

