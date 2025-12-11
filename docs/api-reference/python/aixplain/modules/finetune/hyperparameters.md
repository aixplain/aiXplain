---
sidebar_label: hyperparameters
title: aixplain.modules.finetune.hyperparameters
---

### SchedulerType Objects

```python
class SchedulerType(Text, Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/hyperparameters.py#L7)

Enum representing different learning rate schedulers.

This enum defines the possible learning rate schedulers that can be used
in the fine-tuning process. Each scheduler is represented by a string constant.

**Attributes**:

- `LINEAR` _Text_ - Linear learning rate scheduler.
- `COSINE` _Text_ - Cosine learning rate scheduler.
- `COSINE_WITH_RESTARTS` _Text_ - Cosine with restarts learning rate scheduler.
- `POLYNOMIAL` _Text_ - Polynomial learning rate scheduler.
- `CONSTANT` _Text_ - Constant learning rate scheduler.
- `CONSTANT_WITH_WARMUP` _Text_ - Constant with warmup learning rate scheduler.
- `INVERSE_SQRT` _Text_ - Inverse square root learning rate scheduler.
- `REDUCE_ON_PLATEAU` _Text_ - Reduce learning rate on plateau learning rate scheduler.

### Hyperparameters Objects

```python
@dataclass_json

@dataclass
class Hyperparameters(object)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/hyperparameters.py#L40)

Configuration for the fine-tuning process.

This class encapsulates the hyperparameters for training a model using a
fine-tuning approach. It includes settings for epochs, batch sizes, learning
rates, sequence lengths, and learning rate schedulers.

**Attributes**:

- `epochs` _int_ - Number of training epochs.
- `train_batch_size` _int_ - Batch size for training.
- `eval_batch_size` _int_ - Batch size for evaluation.
- `learning_rate` _float_ - Learning rate for training.
- `max_seq_length` _int_ - Maximum sequence length for model inputs.
- `warmup_ratio` _float_ - Warmup ratio for learning rate scheduler.
- `warmup_steps` _int_ - Number of warmup steps for learning rate scheduler.
- `lr_scheduler_type` _SchedulerType_ - Type of learning rate scheduler.

#### \_\_post\_init\_\_

```python
def __post_init__()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/finetune/hyperparameters.py#L66)

Post-initialization validation for the hyperparameters.

This method performs validation checks on the hyperparameters after
initialization. It ensures that the provided values are of the correct
types and within the allowed ranges.

**Raises**:

- `TypeError` - If the provided values are not of the correct types.
- `ValueError` - If the provided values are outside the allowed ranges.

