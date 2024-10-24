from enum import Enum
from typing import Text


class Status(Text, Enum):
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
