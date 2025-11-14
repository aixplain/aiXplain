---
sidebar_label: cost
title: aixplain.modules.finetune.cost
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
Date: June 14th 2023
Description:
    FinetuneCost Class

### FinetuneCost Objects

```python
class FinetuneCost()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/cost.py#L27)

A class representing the cost structure for a fine-tuning job.

This class encapsulates the cost information for training, inference, and hosting
components of a fine-tuning job. It provides methods to convert the cost data
into a dictionary format for serialization.

**Attributes**:

- `training` _Dict_ - Dictionary containing training cost information.
- `inference` _Dict_ - Dictionary containing inference cost information.
- `hosting` _Dict_ - Dictionary containing hosting cost information.

#### \_\_init\_\_

```python
def __init__(training: Dict, inference: Dict, hosting: Dict) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/cost.py#L40)

Create a FinetuneCost object with training, inference, and hosting cost information.

**Arguments**:

- `training` _Dict_ - Dictionary containing training cost information.
- `inference` _Dict_ - Dictionary containing inference cost information.
- `hosting` _Dict_ - Dictionary containing hosting cost information.

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/cost.py#L57)

Convert the FinetuneCost object to a dictionary.

**Returns**:

- `Dict` - A dictionary representation of the FinetuneCost object.

