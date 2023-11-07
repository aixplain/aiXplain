from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Hyperparameters(object):
    epochs: int = 4
    train_batch_size: int = 4
    eval_batch_size: int = 4
    learning_rate: float = 2e-5
    warmup_steps: int = 500
    generation_max_length: int = 225
    tokenizer_batch_size: int = 256
    gradient_checkpointing: bool = False
    gradient_accumulation_steps: int = 1
    max_seq_length: int = 4096
