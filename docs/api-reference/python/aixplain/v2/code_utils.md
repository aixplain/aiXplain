---
sidebar_label: code_utils
title: aixplain.v2.code_utils
---

`from aixplain import UtilityModelInput, UtilityModelInputDict`


Code parsing utilities for v2 utility models.

Adapted from aixplain.modules.model.utils to avoid v1 import chain
that triggers env var validation.

### UtilityModelInputDict Objects

```python
class UtilityModelInputDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/code_utils.py#L31)

The dict form of `UtilityModelInput`, on the same field names.

``total=True``: ``name`` and ``description`` have no default on the struct,
so marking them optional would let a dict type-check and then fail at
runtime. Only ``type`` defaults.

### UtilityModelInput Objects

```python
@dataclass
class UtilityModelInput()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/code_utils.py#L45)

Input parameter for a utility model.

**Attributes**:

- `name` - The name of the input parameter.
- `description` - A description of what this input parameter represents.
- `type` - The data type of the input parameter -- a `DataType` or its
  string value (``"text"``, ``"boolean"``, ``"number"``).

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/code_utils.py#L59)

Coerce a string ``type`` into a `DataType` on every assignment.

``to_dict`` reads ``self.type.value``, so a plain string left as-is would
reach the wire as an ``AttributeError``. Coercing on assignment (not only
in ``__post_init__``) keeps construction and later assignment identical.

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/code_utils.py#L74)

Validate that the input type is one of TEXT, BOOLEAN, or NUMBER.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/code_utils.py#L79)

Convert to dictionary representation.

#### parse\_code

```python
def parse_code(
        code: Union[Text, Callable],
        api_key: Optional[Text] = None,
        backend_url: Optional[Text] = None) -> Tuple[Text, List, Text, Text]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/code_utils.py#L176)

Parse and process code for utility model creation.

**Arguments**:

- `code` - The code to parse (callable, file path, URL, or raw code string).
- `api_key` - API key for authentication when uploading code.
- `backend_url` - Backend URL for file upload.
  

**Returns**:

  Tuple of (code_url, inputs, description, name).

#### parse\_code\_decorated

```python
def parse_code_decorated(
        code: Union[Text, Callable],
        api_key: Optional[Text] = None,
        backend_url: Optional[Text] = None) -> Tuple[Text, List, Text, Text]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/code_utils.py#L242)

Parse and process code that may be decorated with @utility_tool.

**Arguments**:

- `code` - The code to parse (decorated/non-decorated callable, file path, URL, or raw string).
- `api_key` - API key for authentication when uploading code.
- `backend_url` - Backend URL for file upload.
  

**Returns**:

  Tuple of (code_url, inputs, description, name).

