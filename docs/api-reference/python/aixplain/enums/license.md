---
sidebar_label: license
title: aixplain.enums.license
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
    License Enum

### LicenseMetadata Objects

```python
@dataclass
class LicenseMetadata()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/license.py#L34)

Metadata container for license information.

This class holds metadata about a license including its identifier, name,
description, URL, and custom URL settings.

**Attributes**:

- `id` _str_ - ID of the license.
- `name` _str_ - Name of the license.
- `description` _str_ - Description of the license terms.
- `url` _str_ - URL to the license text or details.
- `allowCustomUrl` _bool_ - Whether custom URLs are allowed for this license.

#### to\_dict

```python
def to_dict() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/license.py#L53)

Convert the license metadata to a dictionary.

**Returns**:

- `dict` - Dictionary representation of the license metadata.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: dict) -> "LicenseMetadata"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/license.py#L68)

Create a LicenseMetadata instance from a dictionary.

**Arguments**:

- `data` _dict_ - Dictionary containing license metadata.
  

**Returns**:

- `LicenseMetadata` - New instance created from the dictionary data.

#### load\_licenses

```python
def load_licenses() -> Enum
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/license.py#L86)

Load license definitions from the backend or cache.

This function attempts to load license definitions from the cache first.
If the cache is invalid or doesn&#x27;t exist, it fetches the data from the
backend API. It creates a dynamic Enum class containing all available
licenses.

**Returns**:

- `Enum` - Dynamically created License enum class with license identifiers.
  

**Raises**:

- `Exception` - If licenses cannot be loaded due to invalid API key or other errors.

