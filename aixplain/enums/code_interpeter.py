from enum import Enum


class CodeInterpreterModel(str, Enum):
    """Code Interpreter Model IDs"""

    PYTHON_AZURE = "67476fa16eb563d00060ad62"

    def __str__(self):
        return self._value_
