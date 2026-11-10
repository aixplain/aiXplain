---
sidebar_label: config
title: aixplain.utils.config
---

Copyright 2022 The aiXplain SDK authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

#### ensure\_config\_urls\_safe

```python
def ensure_config_urls_safe() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/config.py#L57)

Raise if a configured endpoint failed the policy at import time.

Kept as an explicit call for anyone reading configuration through this
module; the v1 request choke point that called it automatically went with v1
in 0.3.0. ``Aixplain()`` validates its own three URLs directly.

**Raises**:

- `UnsafeURLError` - If ``BACKEND_URL`` or ``MODELS_RUN_URL`` is not allowed.

#### validate\_api\_keys

```python
def validate_api_keys()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/config.py#L109)

Centralized eager API key validation - normalize, then require a key.

This function handles all API key validation logic:
1. Auto-normalizes AIXPLAIN_API_KEY to TEAM_API_KEY if needed
2. Prevents conflicting API keys
3. Ensures at least one API key is provided

It is no longer called at import time (see `_normalize_api_keys`), but
is kept for callers that want the eager, all-or-nothing check.

**Raises**:

- `Exception` - If no API keys are provided or if conflicting keys are detected

#### check\_api\_keys\_available

```python
def check_api_keys_available()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/config.py#L127)

Runtime check to ensure API keys are available.

This is used by decorators and other runtime validation.
Uses the same validation logic as the module-level check.

**Raises**:

- `Exception` - If no valid API keys are available

