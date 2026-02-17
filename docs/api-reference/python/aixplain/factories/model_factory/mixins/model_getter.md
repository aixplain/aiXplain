---
sidebar_label: model_getter
title: aixplain.factories.model_factory.mixins.model_getter
---

Model getter mixin providing model retrieval functionality.

This module contains the ModelGetterMixin class which provides methods for retrieving
model instances from the backend by ID or name, with support for caching.

### ModelGetterMixin Objects

```python
class ModelGetterMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/mixins/model_getter.py#L18)

Mixin class providing model retrieval functionality.

This mixin provides methods for retrieving model instances from the backend,
with support for caching to improve performance.

#### get

```python
@classmethod
def get(cls,
        model_id: Optional[Text] = None,
        name: Optional[Text] = None,
        api_key: Optional[Text] = None,
        use_cache: bool = False) -> Model
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/mixins/model_getter.py#L26)

Retrieve a model instance by its ID or name.

This method attempts to retrieve a model from the cache if enabled,
falling back to fetching from the backend if necessary.

**Arguments**:

- `model_id` _Optional[Text], optional_ - ID of the model to retrieve.
- `name` _Optional[Text], optional_ - Name of the model to retrieve.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
- `use_cache` _bool, optional_ - Whether to attempt retrieving from cache.
  Defaults to False.
  

**Returns**:

- `Model` - Retrieved model instance.
  

**Raises**:

- `Exception` - If the model cannot be retrieved or doesn&#x27;t exist.
- `ValueError` - If neither model_id nor name is provided, or if both are provided.

