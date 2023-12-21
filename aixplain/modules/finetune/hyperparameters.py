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


EPOCHS = [1]
BATCH_SIZE = [1]


@dataclass_json
@dataclass
class Hyperparameters(object):
    epochs: int = 1
    train_batch_size: int = 1
    # work with only default values
    eval_batch_size: int = 1
    learning_rate: float = 2e-5
    generation_max_length: int = 225
    gradient_checkpointing: bool = False
    gradient_accumulation_steps: int = 1
    max_seq_length: int = 4096
    warmup_ratio: float = 0.0
    warmup_steps: int = 0
    lr_scheduler_type: SchedulerType = SchedulerType.LINEAR

    @property
    def epochs(self) -> int:
        return self._epochs

    @epochs.setter
    def epochs(self, value: int) -> None:
        if value not in EPOCHS:
            raise ValueError(f"epochs must be one of the following values: {EPOCHS}")
        self._epochs = value

    @property
    def train_batch_size(self) -> int:
        return self._train_batch_size

    @train_batch_size.setter
    def train_batch_size(self, value: int) -> None:
        if value not in BATCH_SIZE:
            raise ValueError(f"train_batch_size must be one of the following values: {BATCH_SIZE}")
        self._train_batch_size = value

    @property
    def eval_batch_size(self) -> int:
        return self._eval_batch_size

    @eval_batch_size.setter
    def eval_batch_size(self, value: int) -> None:
        if value not in BATCH_SIZE:
            raise ValueError(f"eval_batch_size must be one of the following values: {BATCH_SIZE}")
        self._eval_batch_size = value
