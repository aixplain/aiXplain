---
sidebar_label: utility
title: aixplain.v2.utility
---

Utility resource module for managing custom Python code utilities.

### UtilitySearchParams Objects

```python
class UtilitySearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L23)

Parameters for listing utilities.

**Attributes**:

- `function` - Function: The function of the utility (should be UTILITIES).
- `status` - str: The status of the utility.
- `query` - str: Search query for utilities.
- `ownership` - Tuple[OwnershipType, List[OwnershipType]]: Ownership filter.

### UtilityRunParams Objects

```python
class UtilityRunParams(BaseRunParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L37)

Parameters for running utilities.

**Attributes**:

- `data` - str: The data to run the utility on.

### Utility Objects

```python
@dataclass_json

@dataclass(repr=False)
class Utility(BaseResource, SearchResourceMixin[UtilitySearchParams,
                                                "Utility"],
              GetResourceMixin[BaseGetParams, "Utility"],
              DeleteResourceMixin[BaseDeleteParams, "Utility"],
              RunnableResourceMixin[UtilityRunParams, Result])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L49)

Resource for utilities.

Utilities are standalone assets that can be created and managed
independently of models. They represent custom functions that can be
executed on the platform.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L69)

Parse code and validate description for new utility instances.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L91)

Build the payload for the save action.

#### get

```python
@classmethod
def get(cls: type["Utility"], id: str,
        **kwargs: Unpack[BaseGetParams]) -> "Utility"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L98)

Get a utility by ID.

**Arguments**:

- `id` - The utility ID.
- `**kwargs` - Additional parameters for the get request.
  

**Returns**:

  The retrieved Utility instance.

#### run

```python
@classmethod
def run(cls: type["Utility"], **kwargs: Unpack[UtilityRunParams]) -> Result
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L111)

Run the utility with provided parameters.

**Arguments**:

- `**kwargs` - Run parameters including data to process.
  

**Returns**:

  Result of the utility execution.

#### search

```python
@classmethod
def search(cls: type["Utility"],
           query: Optional[str] = None,
           **kwargs: Unpack[UtilitySearchParams]) -> "Page[Utility]"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L123)

Search utilities with optional query and filtering.

**Arguments**:

- `query` - Optional search query string
- `**kwargs` - Additional search parameters (function, status, etc.)
  

**Returns**:

  Page of utilities matching the search criteria

