---
sidebar_label: model_getter
title: aixplain.factories.model_factory.mixins.model_getter
---

### ModelGetterMixin Objects

```python
class ModelGetterMixin()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/mixins/model_getter.py#L12)

Mixin class providing model retrieval functionality.

This mixin provides methods for retrieving model instances from the backend,
with support for caching to improve performance.

#### get

```python
@classmethod
def get(cls,
        model_id: Text,
        api_key: Optional[Text] = None,
        use_cache: bool = False) -> Model
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/model_factory/mixins/model_getter.py#L19)

Retrieve a model instance by its ID.

This method attempts to retrieve a model from the cache if enabled,
falling back to fetching from the backend if necessary.

**Arguments**:

- `model_id` _Text_ - ID of the model to retrieve.
- `api_key` _Optional[Text], optional_ - API key for authentication.
  Defaults to None, using the configured TEAM_API_KEY.
- `use_cache` _bool, optional_ - Whether to attempt retrieving from cache.
  Defaults to False.
  

**Returns**:

- `Model` - Retrieved model instance.
  

**Raises**:

- `Exception` - If the model cannot be retrieved or doesn&#x27;t exist.

