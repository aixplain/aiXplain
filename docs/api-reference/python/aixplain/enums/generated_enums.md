---
sidebar_label: generated_enums
title: aixplain.enums.generated_enums
---

### Function Objects

```python
class Function(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L10)

#### get\_input\_output\_params

```python
def get_input_output_params() -> Tuple[Dict, Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L139)

Gets the input and output parameters for this function

**Returns**:

  Tuple[Dict, Dict]: A tuple containing (input_params, output_params)

#### get\_parameters

```python
def get_parameters() -> "FunctionParameters"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L156)

Gets a FunctionParameters object for this function

**Returns**:

- `FunctionParameters` - Object containing the function&#x27;s parameters

### FunctionParameters Objects

```python
class FunctionParameters(BaseParameters)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L5022)

Class to store and manage function parameters

#### \_\_init\_\_

```python
def __init__(input_params: Dict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L5025)

Initialize FunctionParameters with input parameters

**Arguments**:

- `input_params` _Dict_ - Dictionary of input parameters

