---
sidebar_label: asset
title: aixplain.modules.asset
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
    Asset Class

### Asset Objects

```python
class Asset()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/asset.py#L29)

A class representing an aiXplain Asset.

This class provides functionality to create and manage assets in the aiXplain platform.
Assets can be models, datasets, or other resources with associated metadata like
supplier information, version, license, privacy settings, and cost.

**Attributes**:

- `id` _Text_ - The unique identifier of the asset.
- `name` _Text_ - The name of the asset.
- `description` _Text_ - A detailed description of the asset.
- `supplier` _Union[Dict, Text, Supplier, int]_ - The supplier of the asset.
- `version` _Text_ - The version of the asset.
- `license` _Optional[License]_ - The license associated with the asset.
- `privacy` _Privacy_ - The privacy setting of the asset.
- `cost` _Optional[Union[Dict, float]]_ - The cost associated with the asset.

#### \_\_init\_\_

```python
def __init__(id: Text,
             name: Text,
             description: Text,
             supplier: Union[Dict, Text, Supplier, int] = Supplier.AIXPLAIN,
             version: Text = "1.0",
             license: Optional[License] = None,
             privacy: Privacy = Privacy.PRIVATE,
             cost: Optional[Union[Dict, float]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/asset.py#L47)

Initialize a new Asset instance.

**Arguments**:

- `id` _Text_ - Unique identifier of the asset.
- `name` _Text_ - Name of the asset.
- `description` _Text_ - Detailed description of the asset.
- `supplier` _Union[Dict, Text, Supplier, int], optional_ - Supplier of the asset.
  Can be a Supplier enum, dictionary, text, or integer. Defaults to Supplier.AIXPLAIN.
- `version` _Text, optional_ - Version of the asset. Defaults to &quot;1.0&quot;.
- `license` _Optional[License], optional_ - License associated with the asset. Defaults to None.
- `privacy` _Privacy, optional_ - Privacy setting of the asset. Defaults to Privacy.PRIVATE.
- `cost` _Optional[Union[Dict, float]], optional_ - Cost of the asset. Can be a dictionary
  with pricing details or a float value. Defaults to None.

#### to\_dict

```python
def to_dict() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/asset.py#L95)

Convert the Asset instance to a dictionary representation.

This method serializes all attributes of the Asset instance into a dictionary
format, which can be useful for data transmission or storage.

**Returns**:

- `dict` - A dictionary containing all attributes of the Asset instance.
  Keys are attribute names and values are their corresponding values.

