---
sidebar_label: finetune
title: aixplain.v2.finetune
---

### FinetuneCreateParams Objects

```python
class FinetuneCreateParams(BareCreateParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/finetune.py#L16)

Parameters for creating a finetune.

**Attributes**:

- `name` - str: The name of the finetune.
- `dataset_list` - List[Dataset]: The list of datasets.
- `model` - Union[Model, str]: The model.
- `prompt_template` - str: The prompt template.
- `hyperparameters` - Hyperparameters: The hyperparameters.
- `train_percentage` - float: The train percentage.
- `dev_percentage` - float: The dev percentage.

### Finetune Objects

```python
class Finetune(BaseResource, CreateResourceMixin[FinetuneCreateParams,
                                                 "Finetune"])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/finetune.py#L38)

Resource for finetunes.

