---
sidebar_label: data_factory
title: aixplain.factories.data_factory
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
Date: May 15th 2023
Description:
    Data Factory Class

### DataFactory Objects

```python
class DataFactory(AssetFactory)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/data_factory.py#L38)

Factory class for creating and managing data assets.

This class provides functionality for creating, retrieving, and managing
data assets in the aiXplain platform. Data assets represent individual
pieces of data (e.g., text, audio) that can be used in corpora or
directly with models.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### get

```python
@classmethod
def get(cls, data_id: Text) -> Data
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/data_factory.py#L95)

Retrieve a data asset by its ID.

This method fetches a data asset from the platform using its unique
identifier.

**Arguments**:

- `data_id` _Text_ - Unique identifier of the data asset to retrieve.
  

**Returns**:

- `Data` - Retrieved data asset object with its configuration.
  

**Raises**:

- `Exception` - If:
  - Data asset ID is invalid or not found
  - Authentication fails
  - Service is unavailable

