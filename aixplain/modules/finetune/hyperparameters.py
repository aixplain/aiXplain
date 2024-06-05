from dataclasses import dataclass
from dataclasses_json import dataclass_json
from enum import Enum
from typing import Text


class SchedulerType(Text, Enum):
    LINEAR = "linear"
    COSINE = "cosine"
    COSINE_WITH_RESTARTS = "cosine_with_restarts"
    POLYNOMIAL = "polynomial"
    CONSTANT = "constant"
    CONSTANT_WITH_WARMUP = "constant_with_warmup"
    INVERSE_SQRT = "inverse_sqrt"
    REDUCE_ON_PLATEAU = "reduce_lr_on_plateau"


EPOCHS_MAX_VALUE = 4
BATCH_SIZE_VALUES = [1, 2, 4, 8, 16, 32, 64]
MAX_SEQ_LENGTH_MAX_VALUE = 4096


@dataclass_json
@dataclass
class Hyperparameters(object):
    epochs: int = 1
    train_batch_size: int = 4
    eval_batch_size: int = 4
    learning_rate: float = 1e-5
    max_seq_length: int = 4096
    warmup_ratio: float = 0.0
    warmup_steps: int = 0
    lr_scheduler_type: SchedulerType = SchedulerType.LINEAR

    def __post_init__(self):
        if not isinstance(self.epochs, int):
            raise TypeError("epochs should be of type int")

        if not isinstance(self.train_batch_size, int):
            raise TypeError("train_batch_size should be of type int")

        if not isinstance(self.eval_batch_size, int):
            raise TypeError("eval_batch_size should be of type int")

        if not isinstance(self.learning_rate, float):
            raise TypeError("learning_rate should be of type float")

        if not isinstance(self.max_seq_length, int):
            raise TypeError("max_seq_length should be of type int")

        if not isinstance(self.warmup_ratio, float):
            raise TypeError("warmup_ratio should be of type float")

        if not isinstance(self.warmup_steps, int):
            raise TypeError("warmup_steps should be of type int")

        if not isinstance(self.lr_scheduler_type, SchedulerType):
            raise TypeError("lr_scheduler_type should be of type SchedulerType")

        if self.epochs > EPOCHS_MAX_VALUE:
            raise ValueError(f"epochs must be less or equal to {EPOCHS_MAX_VALUE}")

        if self.train_batch_size not in BATCH_SIZE_VALUES:
            raise ValueError(f"train_batch_size must be one of the following values: {BATCH_SIZE_VALUES}")

        if self.eval_batch_size not in BATCH_SIZE_VALUES:
            raise ValueError(f"eval_batch_size must be one of the following values: {BATCH_SIZE_VALUES}")

        if self.max_seq_length > MAX_SEQ_LENGTH_MAX_VALUE:
            raise ValueError(f"max_seq_length must be less or equal to {MAX_SEQ_LENGTH_MAX_VALUE}")
