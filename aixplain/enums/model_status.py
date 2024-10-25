from enum import Enum
from typing import Text


class ModelStatus(Text, Enum):
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"

    def __str__(self):
        return self._value_
