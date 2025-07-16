"""
Generic parameter interfaces for v2 API.

This module provides reusable parameter classes that can be used across
different v2 interfaces like utilities, models, agents, etc.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .enums import DataType


@dataclass
class InputParameter:
    """Generic input parameter for any v2 resource.

    This class can be used for utility inputs, model parameters,
    agent inputs, or any other resource that requires typed inputs.

    Attributes:
        name: str: The name of the input parameter.
        description: str: The description of the input parameter.
        type: DataType: The data type of the input parameter.
        required: bool: Whether this parameter is required.
        default: Any: Default value for the parameter (optional).
        options: List[Any]: List of valid options for the parameter (optional).
    """

    name: str
    type: DataType = DataType.TEXT
    required: bool = True
    description: Optional[str] = None
    default: Optional[Any] = None
    options: Optional[List[Any]] = None

    def validate(self):
        """Validate the input parameter.

        Raises:
            ValueError: If the type is not supported or validation fails.
        """
        supported_types = [DataType.TEXT, DataType.BOOLEAN, DataType.NUMBER]
        if self.type not in supported_types:
            raise ValueError(
                f"Input parameter type must be one of {supported_types}, "
                f"got {self.type}"
            )

        if not self.name or not self.name.strip():
            raise ValueError("Input parameter name cannot be empty")

        if not self.description or not self.description.strip():
            raise ValueError("Input parameter description cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            dict: Dictionary representation of the input parameter.
        """
        result = {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "required": self.required,
        }

        if self.default is not None:
            result["default"] = self.default

        if self.options is not None:
            result["options"] = self.options

        return result

    def __repr__(self) -> str:
        return (
            f"InputParameter(name='{self.name}', "
            f"type={self.type.value}, required={self.required})"
        )
