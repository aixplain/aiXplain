---
sidebar_label: evolve_param
title: aixplain.modules.agent.evolve_param
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

Author: aiXplain Team
Date: December 2024
Description:
    EvolveParam Base Model Class for Agent and TeamAgent evolve functionality

### EvolveParam Objects

```python
@dataclass
class EvolveParam()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/evolve_param.py#L29)

Base model for evolve parameters used in Agent and TeamAgent evolution.

**Attributes**:

- `to_evolve` _bool_ - Whether to enable evolution. Defaults to False.
- `evolve_type` _Optional[EvolveType]_ - Type of evolve.
- `max_successful_generations` _int_ - Maximum number of successful generations.
- `max_failed_generation_retries` _int_ - Maximum number of failed generation retries.
- `max_iterations` _int_ - Maximum number of iterations.
- `max_non_improving_generations` _Optional[int]_ - Maximum number of non-improving generations.
- `llm` _Optional[Dict[str, Any]]_ - LLM configuration with all parameters.
- `additional_params` _Optional[Dict[str, Any]]_ - Additional parameters.

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/evolve_param.py#L52)

Validate parameters after initialization.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/evolve_param.py#L56)

Validate evolve parameters.

**Raises**:

- `ValueError` - If any parameter is invalid.

#### from\_dict

```python
@classmethod
def from_dict(cls, data: Union[Dict[str, Any], None]) -> "EvolveParam"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/evolve_param.py#L107)

Create EvolveParam instance from dictionary.

**Arguments**:

- `data` _Union[Dict[str, Any], None]_ - Dictionary containing evolve parameters.
  

**Returns**:

- `EvolveParam` - Instance with parameters set from dictionary.
  

**Raises**:

- `ValueError` - If data format is invalid.

#### to\_dict

```python
def to_dict() -> Dict[str, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/evolve_param.py#L160)

Convert EvolveParam instance to dictionary for API calls.

**Returns**:

  Dict[str, Any]: Dictionary representation with API-compatible keys.

#### merge

```python
def merge(other: Union[Dict[str, Any], "EvolveParam"]) -> "EvolveParam"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/evolve_param.py#L188)

Merge this EvolveParam with another set of parameters.

**Arguments**:

- `other` _Union[Dict[str, Any], EvolveParam]_ - Other parameters to merge.
  

**Returns**:

- `EvolveParam` - New instance with merged parameters.

#### validate\_evolve\_param

```python
def validate_evolve_param(
        evolve_param: Union[Dict[str, Any], EvolveParam, None]) -> EvolveParam
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/agent/evolve_param.py#L242)

Utility function to validate and convert evolve parameters.

**Arguments**:

- `evolve_param` _Union[Dict[str, Any], EvolveParam, None]_ - Input evolve parameters.
  

**Returns**:

- `EvolveParam` - Validated EvolveParam instance.
  

**Raises**:

- `ValueError` - If parameters are invalid.

