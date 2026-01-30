from enum import Enum


class CodeInterpreterModel(str, Enum):
    """Enumeration of available Code Interpreter model identifiers.

    This enum defines the unique identifiers for different code interpreter models
    available in the system. Each value represents a specific model's ID that can
    be used for code interpretation tasks.

    Attributes:
        PYTHON_AZURE (str): Model ID for the Python code interpreter running on Azure.
    """

    PYTHON_AZURE = "67476fa16eb563d00060ad62"

    def __str__(self) -> str:
        """Return the string representation of the model ID.

        Returns:
            str: The model ID value as a string.
        """
        return self._value_
