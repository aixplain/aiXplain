---
sidebar_label: onboard_status
title: aixplain.enums.onboard_status
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
    Onboard Status Enum

### OnboardStatus Objects

```python
class OnboardStatus(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/onboard_status.py#L27)

Enumeration of possible onboarding status values.

This enum defines all possible states that an onboarding process can be in,
from initial onboarding to completed or failed states.

**Attributes**:

- `ONBOARDING` _str_ - Initial onboarding state.
- `ONBOARDED` _str_ - Successful onboarding state.
- `FAILED` _str_ - Failed onboarding state.
- `DELETED` _str_ - Deleted onboarding state.

