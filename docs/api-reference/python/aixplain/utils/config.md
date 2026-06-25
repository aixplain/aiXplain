---
sidebar_label: config
title: aixplain.utils.config
---

Copyright 2022 The aiXplain SDK authors.

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#### validate\_api\_keys

```python
def validate_api_keys()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/config.py#L31)

Centralized API key validation function - single source of truth.

This function handles all API key validation logic:
1. Ensures at least one API key is provided
2. Prevents conflicting API keys
3. Auto-normalizes AIXPLAIN_API_KEY to TEAM_API_KEY if needed

**Raises**:

- `Exception` - If no API keys are provided or if conflicting keys are detected

#### check\_api\_keys\_available

```python
def check_api_keys_available()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/config.py#L58)

Runtime check to ensure API keys are available.

This is used by decorators and other runtime validation.
Uses the same validation logic as the module-level check.

**Raises**:

- `Exception` - If no valid API keys are available

