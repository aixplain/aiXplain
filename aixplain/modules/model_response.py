from dataclasses import dataclass


@dataclass
class ModelResponse:
    """Class for keeping track of an item in inventory."""

    status: str
    data: str
    completed: bool
    error_message: str

    def __init__(
        self, status: str, data: str = "", completed: bool = False, error_message: str = "", elapsed_time: float = 0.0
    ):
        self.status = status
        self.data = data
        self.completed = completed
        self.error_message = error_message
        self.elapsed_time = elapsed_time

    def __getitem__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        raise KeyError(f"Key '{key}' not found in ModelResponse.")
