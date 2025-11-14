---
sidebar_label: asset_factory
title: aixplain.factories.asset_factory
---

#### \_\_author\_\_

Copyright 2022 The aiXplain SDK authors

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
Date: December 27th 2022
Description:
    Asset Factory Class

### AssetFactory Objects

```python
class AssetFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/asset_factory.py#L30)

Base class for asset factories.

This class provides a common interface for creating and retrieving assets
from the aiXplain platform. Subclasses should implement the abstract methods
to define specific asset types.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### get

```python
@abstractmethod
def get(asset_id: Text) -> Asset
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/asset_factory.py#L43)

Create a &#x27;Asset&#x27; object from id

**Arguments**:

- `asset_id` _str_ - ID of required asset.
  

**Returns**:

- `Asset` - Created &#x27;Asset&#x27; object

