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
MAX_SEQ_LENGTH_MAX_VALUE = 4096
GENERATION_MAX_LENGTH_MAX_VALUE = 225


@dataclass_json
@dataclass
class Hyperparameters(object):
    epochs: int = 1
    learning_rate: float = 1e-5
    generation_max_length: int = 225
    max_seq_length: int = 4096
    warmup_ratio: float = 0.0
    warmup_steps: int = 0
    lr_scheduler_type: SchedulerType = SchedulerType.LINEAR

    def __post_init__(self):
        if not isinstance(self.epochs, int):
            raise TypeError("epochs should be of type int")

        if not isinstance(self.learning_rate, float):
            raise TypeError("learning_rate should be of type float")

        if not isinstance(self.generation_max_length, int):
            raise TypeError("generation_max_length should be of type int")

        if not isinstance(self.max_seq_length, int):
            raise TypeError("max_seq_length should be of type int")

        if not isinstance(self.warmup_ratio, float):
            raise TypeError("warmup_ratio should be of type float")

        if not isinstance(self.warmup_steps, int):
            raise TypeError("warmup_steps should be of type int")

        if not isinstance(self.lr_scheduler_type, SchedulerType):
            raise TypeError("lr_scheduler_type should be of type SchedulerType")

        if self.epochs > EPOCHS_MAX_VALUE:
            raise ValueError(f"epochs must be one less than {EPOCHS_MAX_VALUE}")

        if self.max_seq_length > MAX_SEQ_LENGTH_MAX_VALUE:
            raise ValueError(f"max_seq_length must be less than {MAX_SEQ_LENGTH_MAX_VALUE}")

        if self.generation_max_length > GENERATION_MAX_LENGTH_MAX_VALUE:
            raise ValueError(f"generation_max_length must be less than {GENERATION_MAX_LENGTH_MAX_VALUE}")
