---
sidebar_label: dataset
title: aixplain.v2.dataset
---

### DatasetListParams Objects

```python
class DatasetListParams(BaseListParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/dataset.py#L48)

Parameters for listing corpora.

**Attributes**:

- `query` - Optional[Text]: A search query.
- `function` - Optional[Function]: The function of the model.
- `suppliers` - Union[Supplier, List[Supplier]: The suppliers of the model.
- `source_languages` - Union[Language, List[Language]: The source languages of the model.
- `target_languages` - Union[Language, List[Language]: The target languages of the model.
- `is_finetunable` - bool: Whether the model is finetunable.

