from dataclasses import dataclass
from typing import Text, Any, Optional
from aixplain.enums import ModelStatus


@dataclass
class ModelResponse:
    """Class for keeping track of an item in inventory."""

    status: ModelStatus
    data: Text
    completed: bool
    error_message: Text
    elapsed_time: Optional[float]
    used_credits: Optional[float]
    run_time: Optional[float]

    def __init__(
        self,
        status: ModelStatus,
        data: Text = "",
        completed: bool = False,
        error_message: Text = "",
        elapsed_time: Optional[float] = 0.0,
        used_credits: Optional[float] = 0.0,
        run_time: Optional[float] = 0.0,
    ):
        self.status = status
        self.data = data
        self.completed = completed
        self.error_message = error_message
        self.elapsed_time = elapsed_time
        self.used_credits = used_credits
        self.run_time = run_time

    def __getitem__(self, key: Text) -> Any:
        if key in self.__dict__:
            return self.__dict__[key]
        raise KeyError(f"Key '{key}' not found in ModelResponse.")
