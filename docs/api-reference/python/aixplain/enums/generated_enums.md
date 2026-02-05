---
sidebar_label: generated_enums
title: aixplain.enums.generated_enums
---

Auto-generated enum module containing static values from the backend API.

### Function Objects

```python
class Function(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L12)

Enum representing available functions in the aiXplain platform.

#### get\_input\_output\_params

```python
def get_input_output_params() -> Tuple[Dict, Dict]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L143)

Get the input and output parameters for this function.

**Returns**:

  Tuple[Dict, Dict]: A tuple containing (input_params, output_params).

#### get\_parameters

```python
def get_parameters() -> "FunctionParameters"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L156)

Get a FunctionParameters object for this function.

**Returns**:

- `FunctionParameters` - Object containing the function&#x27;s parameters.

### FunctionParameters Objects

```python
class FunctionParameters(BaseParameters)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L4504)

Class to store and manage function parameters.

#### \_\_init\_\_

```python
def __init__(input_params: Dict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L4507)

Initialize FunctionParameters with input parameters.

**Arguments**:

- `input_params` _Dict_ - Dictionary of input parameters.

### Supplier Objects

```python
class Supplier(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L4522)

Enum representing available suppliers in the aiXplain platform.

#### \_\_str\_\_

```python
def __str__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L4606)

Return the supplier name.

### Language Objects

```python
class Language(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L4611)

Enum representing available languages in the aiXplain platform.

### License Objects

```python
class License(str, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/generated_enums.py#L4900)

Enum representing available licenses in the aiXplain platform.

