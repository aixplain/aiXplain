---
sidebar_label: index_stores
title: aixplain.enums.index_stores
---

### IndexStores Objects

```python
class IndexStores(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/index_stores.py#L4)

Enumeration of available index store providers in the aiXplain system.

This enum defines the different index store providers that can be used for
storing and retrieving indexed data, along with their identifiers.

**Attributes**:

- `AIR` _dict_ - AIR index store configuration with name and ID.
- `VECTARA` _dict_ - Vectara index store configuration with name and ID.
- `GRAPHRAG` _dict_ - GraphRAG index store configuration with name and ID.
- `ZERO_ENTROPY` _dict_ - Zero Entropy index store configuration with name and ID.

#### \_\_str\_\_

```python
def __str__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/index_stores.py#L21)

Return the name of the index store.

**Returns**:

- `str` - The name value from the index store configuration.

#### get\_model\_id

```python
def get_model_id() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/index_stores.py#L29)

Return the model ID of the index store.

**Returns**:

- `str` - The ID value from the index store configuration.

