from enum import Enum
from typing import Text


class ModelStatus(Text, Enum):
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
