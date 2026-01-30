---
sidebar_label: parameters
title: aixplain.base.parameters
---

### Parameter Objects

```python
@dataclass
class Parameter()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L6)

A class representing a single parameter with its properties.

**Attributes**:

- `name` _str_ - The name of the parameter.
- `required` _bool_ - Whether the parameter is required or optional.
- `value` _Optional[Any]_ - The value of the parameter. Defaults to None.
- `is_fixed` _bool_ - Whether the parameter value is fixed. Defaults to False.
- `values` _List[Dict[str, Any]]_ - Pre-set values for the parameter. Defaults to empty list.
- `default_values` _List[Any]_ - Default values for the parameter. Defaults to empty list.
- `available_options` _List[Dict[str, Any]]_ - Available options for selection. Defaults to empty list.
- `data_type` _Optional[str]_ - The data type of the parameter (e.g., &#x27;text&#x27;, &#x27;number&#x27;).
- `data_sub_type` _Optional[str]_ - The sub-type of the data (e.g., &#x27;json&#x27;, &#x27;text&#x27;).
- `multiple_values` _bool_ - Whether multiple values are allowed. Defaults to False.

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L33)

Initialize mutable default values.

### BaseParameters Objects

```python
class BaseParameters()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L43)

A base class for managing a collection of parameters.

This class provides functionality to store, access, and manipulate parameters
in a structured way. Parameters can be accessed using attribute syntax or
dictionary-style access.

**Attributes**:

- `parameters` _Dict[str, Parameter]_ - Dictionary storing Parameter objects.

#### \_\_init\_\_

```python
def __init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L54)

Initialize the BaseParameters class.

The initialization creates an empty dictionary to store parameters.

#### get\_parameter

```python
def get_parameter(name: str) -> Optional[Parameter]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L61)

Get a parameter by name.

**Arguments**:

- `name` _str_ - Name of the parameter
  

**Returns**:

- `Optional[Parameter]` - Parameter object if found, None otherwise

#### to\_dict

```python
def to_dict() -> Dict[str, Dict[str, Any]]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L72)

Convert parameters back to dictionary format.

**Returns**:

  Dict[str, Dict[str, Any]]: Dictionary representation of parameters

#### to\_list

```python
def to_list() -> List[str]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L94)

Convert parameters to a list format.

This method creates a list of dictionaries containing the name and value
of each parameter that has a value set.

**Returns**:

- `List[str]` - A list of dictionaries, each containing &#x27;name&#x27; and &#x27;value&#x27;
  keys for parameters that have values set.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L110)

Create a pretty string representation of the parameters.

**Returns**:

- `str` - Formatted string showing all parameters

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L136)

Allow setting parameters using attribute syntax.

This special method enables setting parameter values using attribute syntax
(e.g., params.text = &quot;Hello&quot;). It only works for parameters that have been
previously defined.

**Arguments**:

- `name` _str_ - Name of the parameter to set.
- `value` _Any_ - Value to assign to the parameter.
  

**Raises**:

- `AttributeError` - If attempting to set a parameter that hasn&#x27;t been defined.

#### \_\_getattr\_\_

```python
def __getattr__(name: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/base/parameters.py#L159)

Allow getting parameter values using attribute syntax.

This special method enables accessing parameter values using attribute syntax
(e.g., params.text). It only works for parameters that have been previously
defined.

**Arguments**:

- `name` _str_ - Name of the parameter to access.
  

**Returns**:

- `Any` - The value of the requested parameter.
  

**Raises**:

- `AttributeError` - If attempting to access a parameter that hasn&#x27;t been defined.

