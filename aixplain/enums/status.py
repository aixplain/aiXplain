from enum import Enum
from typing import Text


class Status(Text, Enum):
    """Enumeration of possible status values.

    This enum defines the different statuses that a task or operation can be in,
    including failed, in progress, and success.

    Attributes:
        FAILED (str): Task failed.
        IN_PROGRESS (str): Task is in progress.
        SUCCESS (str): Task was successful.
    """
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
