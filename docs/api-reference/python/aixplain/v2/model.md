---
sidebar_label: model
title: aixplain.v2.model
---

### ModelListParams Objects

```python
class ModelListParams(BaseListParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L18)

Parameters for listing models.

**Attributes**:

- `function` - Function: The function of the model.
- `suppliers` - Union[Supplier, List[Supplier]: The suppliers of the model.
- `source_languages` - Union[Language, List[Language]: The source languages of the model.
- `target_languages` - Union[Language, List[Language]: The target languages of the model.
- `is_finetunable` - bool: Whether the model is finetunable.

### Model Objects

```python
class Model(BaseResource, ListResourceMixin[ModelListParams, "Model"],
            GetResourceMixin[BareGetParams, "Model"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/model.py#L36)

Resource for models.

