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


# We return a dictionary
# Run the models get the parameters
# Create a class with the 4 attributes + the error
# Every time they run a model returns a model response class
# getitem method for if someone is using the old code they want to access it as a dictionary.
# write unit

# Create a task for running the additional tests
# For our datasets run again with llaam3.1 topb=0 run with orchestrator, and one with orchestrator mentalist and inspector, and also single agent
# For each instance running three times
