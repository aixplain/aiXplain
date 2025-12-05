---
sidebar_label: utility
title: aixplain.v2.utility
---

### UtilitySearchParams Objects

```python
class UtilitySearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L21)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L35)

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

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L47)

Resource for utilities.

Utilities are standalone assets that can be created and managed
independently of models. They represent custom functions that can be
executed on the platform.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L93)

Build the payload for the save action.

#### search

```python
@classmethod
def search(cls: type["Utility"],
           query: Optional[str] = None,
           **kwargs: Unpack[UtilitySearchParams]) -> "Page[Utility]"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/utility.py#L112)

Search utilities with optional query and filtering.

**Arguments**:

- `query` - Optional search query string
- `**kwargs` - Additional search parameters (function, status, etc.)
  

**Returns**:

  Page of utilities matching the search criteria

