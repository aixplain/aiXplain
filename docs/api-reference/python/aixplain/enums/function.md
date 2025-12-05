---
sidebar_label: function
title: aixplain.enums.function
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
    Function Enum

### FunctionMetadata Objects

```python
@dataclass
class FunctionMetadata()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/function.py#L40)

Metadata container for function information.

This class holds metadata about a function including its identifier, name,
description, parameters, outputs, and additional metadata.

**Attributes**:

- `id` _str_ - ID of the function.
- `name` _str_ - Name of the function.
- `description` _Optional[str]_ - Description of what the function does.
- `params` _List[Dict[str, Any]]_ - List of parameter specifications.
- `output` _List[Dict[str, Any]]_ - List of output specifications.
- `metadata` _Dict[str, Any]_ - Additional metadata about the function.

#### to\_dict

```python
def to_dict() -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/function.py#L61)

Convert the function metadata to a dictionary.

**Returns**:

- `dict` - Dictionary representation of the function metadata.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: dict) -> "FunctionMetadata"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/function.py#L77)

Create a FunctionMetadata instance from a dictionary.

**Arguments**:

- `data` _dict_ - Dictionary containing function metadata.
  

**Returns**:

- `FunctionMetadata` - New instance created from the dictionary data.

#### load\_functions

```python
def load_functions() -> Tuple[Enum, Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/function.py#L96)

Load function definitions from the backend or cache.

This function attempts to load function definitions from the cache first.
If the cache is invalid or doesn&#x27;t exist, it fetches the data from the
backend API.

**Returns**:

  Tuple[Function, Dict]: A tuple containing:
  - Function: Dynamically created Function enum class
  - Dict: Dictionary mapping function IDs to their input/output specifications
  

**Raises**:

- `Exception` - If functions cannot be loaded due to invalid API key or other errors.

### FunctionParameters Objects

```python
class FunctionParameters(BaseParameters)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/function.py#L203)

Class to store and manage function parameters

#### \_\_init\_\_

```python
def __init__(input_params: Dict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/function.py#L206)

Initialize FunctionParameters with input parameters

**Arguments**:

- `input_params` _Dict_ - Dictionary of input parameters

