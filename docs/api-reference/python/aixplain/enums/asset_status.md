---
sidebar_label: asset_status
title: aixplain.enums.asset_status
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

### AssetStatus Objects

```python
class AssetStatus(Text, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/asset_status.py#L28)

Enumeration of possible status values for an asset in the aiXplain system.

This enum defines all possible states that an asset can be in throughout its lifecycle,
from creation to deletion. Each enum value corresponds to a specific state in the
asset&#x27;s lifecycle.

**Attributes**:

- `DRAFT` _str_ - Initial state for a newly created asset.
- `HIDDEN` _str_ - Asset is hidden from public view.
- `SCHEDULED` _str_ - Asset is scheduled for processing.
- `ONBOARDING` _str_ - Asset is in the process of being onboarded.
- `ONBOARDED` _str_ - Asset has been successfully onboarded.
- `PENDING` _str_ - Asset is waiting for processing.
- `FAILED` _str_ - Asset processing has failed.
- `TRAINING` _str_ - Asset is currently in training.
- `REJECTED` _str_ - Asset has been rejected.
- `ENABLING` _str_ - Asset is in the process of being enabled.
- `HIDDEN`0 _str_ - Asset is in the process of being deleted.
- `HIDDEN`1 _str_ - Asset has been disabled.
- `HIDDEN`2 _str_ - Asset has been deleted.
- `HIDDEN`3 _str_ - Asset is currently being processed.
- `HIDDEN`4 _str_ - Asset has completed processing.
- `HIDDEN`5 _str_ - Asset operation is being canceled.
- `HIDDEN`6 _str_ - Asset operation has been canceled.
- `HIDDEN`7 _str_ - Draft state that has been deprecated.

