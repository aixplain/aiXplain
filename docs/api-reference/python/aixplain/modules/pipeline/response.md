---
sidebar_label: response
title: aixplain.modules.pipeline.response
---

### PipelineResponse Objects

```python
@dataclass
class PipelineResponse()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/response.py#L7)

A response object for pipeline operations.

This class encapsulates the response from pipeline operations, including
status, error information, timing data, and any additional fields.

**Attributes**:

- `status` _ResponseStatus_ - The status of the pipeline operation.
- `error` _Optional[Dict[str, Any]]_ - Error details if operation failed.
- `elapsed_time` _Optional[float]_ - Time taken to complete the operation.
- `data` _Optional[Text]_ - The main response data.
- `url` _Optional[Text]_ - URL for polling or accessing results.
- `additional_fields` _Dict[str, Any]_ - Any extra fields provided.

#### \_\_init\_\_

```python
def __init__(status: ResponseStatus,
             error: Optional[Dict[str, Any]] = None,
             elapsed_time: Optional[float] = 0.0,
             data: Optional[Text] = None,
             url: Optional[Text] = "",
             **kwargs)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/response.py#L22)

Initialize a new PipelineResponse instance.

**Arguments**:

- `status` _ResponseStatus_ - The status of the pipeline operation.
- `error` _Optional[Dict[str, Any]], optional_ - Error details if operation
  failed. Defaults to None.
- `elapsed_time` _Optional[float], optional_ - Time taken to complete the
  operation in seconds. Defaults to 0.0.
- `data` _Optional[Text], optional_ - The main response data.
  Defaults to None.
- `url` _Optional[Text], optional_ - URL for polling or accessing results.
  Defaults to &quot;&quot;.
- `**kwargs` - Additional fields to store in the response.

#### \_\_getattr\_\_

```python
def __getattr__(key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/response.py#L52)

Get an attribute from additional_fields if it exists.

This method is called when an attribute lookup has not found the
attribute in the usual places (i.e., it is not an instance attribute
nor found through the __mro__ chain).

**Arguments**:

- `key` _str_ - The name of the attribute to get.
  

**Returns**:

- `Any` - The value from additional_fields.
  

**Raises**:

- `AttributeError` - If the key is not found in additional_fields.

#### get

```python
def get(key: str, default: Any = None) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/response.py#L73)

Get an attribute value with a default if not found.

**Arguments**:

- `key` _str_ - The name of the attribute to get.
- `default` _Any, optional_ - Value to return if key is not found.
  Defaults to None.
  

**Returns**:

- `Any` - The attribute value or default if not found.

#### \_\_getitem\_\_

```python
def __getitem__(key: str) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/response.py#L86)

Get an attribute value using dictionary-style access.

This method enables dictionary-style access to attributes
(e.g., response[&quot;status&quot;]).

**Arguments**:

- `key` _str_ - The name of the attribute to get.
  

**Returns**:

- `Any` - The attribute value.
  

**Raises**:

- `AttributeError` - If the key is not found.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/response.py#L103)

Return a string representation of the PipelineResponse.

**Returns**:

- `str` - A string in the format &quot;PipelineResponse(status=X, error=Y, ...)&quot;
  containing all non-empty fields.

#### \_\_contains\_\_

```python
def __contains__(key: str) -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/pipeline/response.py#L123)

Check if an attribute exists using &#x27;in&#x27; operator.

This method enables using the &#x27;in&#x27; operator to check for attribute
existence (e.g., &quot;status&quot; in response).

**Arguments**:

- `key` _str_ - The name of the attribute to check.
  

**Returns**:

- `bool` - True if the attribute exists, False otherwise.

