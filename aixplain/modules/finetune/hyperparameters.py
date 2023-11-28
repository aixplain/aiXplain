from dataclasses import dataclass
from dataclasses_json import dataclass_json


class SchedulerType:
    LINEAR = "linear"
    COSINE = "cosine"
    COSINE_WITH_RESTARTS = "cosine_with_restarts"
    POLYNOMIAL = "polynomial"
    CONSTANT = "constant"
    CONSTANT_WITH_WARMUP = "constant_with_warmup"
    INVERSE_SQRT = "inverse_sqrt"
    REDUCE_ON_PLATEAU = "reduce_lr_on_plateau"


@dataclass_json
@dataclass
class Hyperparameters(object):
    epochs: int = 4
    train_batch_size: int = 4
    eval_batch_size: int = 4
    learning_rate: float = 2e-5
    generation_max_length: int = 225
    tokenizer_batch_size: int = 256
    gradient_checkpointing: bool = False
    gradient_accumulation_steps: int = 1
    max_seq_length: int = 4096
    warmup_ratio: float = 0.0
    warmup_steps: int = 0
    early_stopping_patience: int = 1
    lr_scheduler_type: SchedulerType = SchedulerType.LINEAR
