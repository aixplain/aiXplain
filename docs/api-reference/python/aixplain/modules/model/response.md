---
sidebar_label: response
title: aixplain.modules.model.response
---

### ModelResponse Objects

```python
class ModelResponse()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L6)

ModelResponse class to store the response of the model run.

This class provides a structured way to store and manage the response from model runs.
It includes fields for status, data, details, completion status, error messages,
usage information, and additional metadata.

#### \_\_init\_\_

```python
def __init__(status: ResponseStatus,
             data: Text = "",
             details: Optional[Union[Dict, List]] = {},
             completed: bool = False,
             error_message: Text = "",
             used_credits: float = 0.0,
             run_time: float = 0.0,
             usage: Optional[Dict] = None,
             url: Optional[Text] = None,
             error_code: Optional[ErrorCode] = None,
             **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L14)

Initialize a new ModelResponse instance.

**Arguments**:

- `status` _ResponseStatus_ - The status of the response.
- `data` _Text_ - The data returned by the model.
- `details` _Optional[Union[Dict, List]]_ - Additional details about the response.
- `completed` _bool_ - Whether the response is complete.
- `error_message` _Text_ - The error message if the response is not successful.
- `used_credits` _float_ - The amount of credits used for the response.
- `run_time` _float_ - The time taken to generate the response.
- `usage` _Optional[Dict]_ - Usage information about the response.
- `url` _Optional[Text]_ - The URL of the response.
- `error_code` _Optional[ErrorCode]_ - The error code if the response is not successful.
- `data`0 - Additional keyword arguments.

#### \_\_getitem\_\_

```python
def __getitem__(key: Text) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L59)

Get an item from the ModelResponse.

**Arguments**:

- `key` _Text_ - The key to get the value for.
  

**Returns**:

- `Any` - The value associated with the key.
  

**Raises**:

- `KeyError` - If the key is not found in the ModelResponse.

#### get

```python
def get(key: Text, default: Optional[Any] = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L81)

Get an item from the ModelResponse with a default value.

**Arguments**:

- `key` _Text_ - The key to get the value for.
- `default` _Optional[Any]_ - The default value to return if the key is not found.
  

**Returns**:

- `Any` - The value associated with the key or the default value if the key is not found.

#### \_\_setitem\_\_

```python
def __setitem__(key: Text, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L96)

Set an item in the ModelResponse.

**Arguments**:

- `key` _Text_ - The key to set the value for.
- `value` _Any_ - The value to set.
  

**Raises**:

- `KeyError` - If the key is not found in the ModelResponse.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L117)

Return a string representation of the ModelResponse.

**Returns**:

- `str` - A string representation of the ModelResponse.

#### \_\_contains\_\_

```python
def __contains__(key: Text) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L148)

Check if a key is in the ModelResponse.

**Arguments**:

- `key` _Text_ - The key to check for.
  

**Returns**:

- `bool` - True if the key is in the ModelResponse, False otherwise.

#### to\_dict

```python
def to_dict() -> Dict[Text, Any]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/response.py#L163)

Convert the ModelResponse to a dictionary.

**Returns**:

  Dict[Text, Any]: A dictionary representation of the ModelResponse.

