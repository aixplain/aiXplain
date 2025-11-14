---
sidebar_label: record
title: aixplain.modules.model.record
---

### Record Objects

```python
class Record()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/record.py#L6)

A class representing a record in an index.

This class defines the structure of a record with its value, type, ID, URI,
and attributes.

#### \_\_init\_\_

```python
def __init__(value: str = "",
             value_type: DataType = DataType.TEXT,
             id: Optional[str] = None,
             uri: str = "",
             attributes: dict = {})
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/record.py#L12)

Initialize a new Record instance.

**Arguments**:

- `value` _str_ - The value of the record.
- `value_type` _DataType_ - The type of the value.
- `id` _Optional[str]_ - The ID of the record. Defaults to a random UUID.
- `uri` _str_ - The URI of the record.
- `attributes` _dict_ - The attributes of the record.

#### to\_dict

```python
def to_dict()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/record.py#L35)

Convert the record to a dictionary.

**Returns**:

- `dict` - A dictionary containing the record&#x27;s value, type, ID, URI, and attributes.

#### validate

```python
def validate()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/model/record.py#L49)

Validate the record.

**Raises**:

- `AssertionError` - If the value type is invalid or if the URI is required for image records.

