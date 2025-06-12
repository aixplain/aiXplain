__author__ = "aiXplain"

"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain Team
Date: December 2024
Description:
    EvolveParam Base Model Class for Agent and TeamAgent evolve functionality
"""
from aixplain.enums import EvolveType
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union


@dataclass
class EvolveParam:
    """Base model for evolve parameters used in Agent and TeamAgent evolution.

    Attributes:
        to_evolve (bool): Whether to enable evolution. Defaults to False.
        criteria (Optional[str]): Custom criteria for evolution evaluation.
        max_iterations (Optional[int]): Maximum number of evolution iterations.
        temperature (Optional[float]): Temperature for evolution randomness (0.0-1.0).
        type (Optional[EvolveType]): Type of evolution.
    """

    to_evolve: bool = False
    criteria: Optional[str] = None
    max_iterations: Optional[int] = 100
    temperature: Optional[float] = 0.0
    type: Optional[EvolveType] = EvolveType.TEAM_TUNING
    additional_params: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Validate parameters after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate evolve parameters.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if self.temperature is not None:
            if not isinstance(self.temperature, (int, float)):
                raise ValueError("temperature must be a number")
            if not 0.0 <= self.temperature <= 1.0:
                raise ValueError("temperature must be between 0.0 and 1.0")

        if self.max_iterations is not None:
            if not isinstance(self.max_iterations, int):
                raise ValueError("max_iterations must be an integer")
            if self.max_iterations <= 0:
                raise ValueError("max_iterations must be positive")

        if self.type is not None:
            if not isinstance(self.type, EvolveType):
                raise ValueError("type must be a valid EvolveType")
        if self.additional_params is not None:
            if not isinstance(self.additional_params, dict):
                raise ValueError("additional_params must be a dictionary")

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], None]) -> "EvolveParam":
        """Create EvolveParam instance from dictionary.

        Args:
            data (Union[Dict[str, Any], None]): Dictionary containing evolve parameters.

        Returns:
            EvolveParam: Instance with parameters set from dictionary.

        Raises:
            ValueError: If data format is invalid.
        """
        if data is None:
            return cls()

        if not isinstance(data, dict):
            raise ValueError("evolve parameter must be a dictionary or None")

        # Extract known parameters
        known_params = {
            "to_evolve": data.get("toEvolve", data.get("to_evolve", False)),
            "criteria": data.get("criteria"),
            "max_iterations": data.get("maxIterations", data.get("max_iterations")),
            "temperature": data.get("temperature"),
            "type": data.get("type"),
            "additional_params": data.get("additional_params"),
        }

        # Remove None values
        known_params = {k: v for k, v in known_params.items() if v is not None}

        # Collect additional parameters
        additional_params = {
            k: v
            for k, v in data.items()
            if k
            not in [
                "toEvolve",
                "to_evolve",
                "criteria",
                "maxIterations",
                "max_iterations",
                "temperature",
                "type",
                "additional_params",
            ]
        }

        return cls(additional_params=additional_params, **known_params)

    def to_dict(self) -> Dict[str, Any]:
        """Convert EvolveParam instance to dictionary for API calls.

        Returns:
            Dict[str, Any]: Dictionary representation with API-compatible keys.
        """
        result = {
            "toEvolve": self.to_evolve,
        }

        # Add optional parameters if they are set
        if self.criteria is not None:
            result["criteria"] = self.criteria
        if self.max_iterations is not None:
            result["maxIterations"] = self.max_iterations
        if self.temperature is not None:
            result["temperature"] = self.temperature
        if self.type is not None:
            result["type"] = self.type
        if self.additional_params is not None:
            result.update(self.additional_params)

        return result

    def merge(self, other: Union[Dict[str, Any], "EvolveParam"]) -> "EvolveParam":
        """Merge this EvolveParam with another set of parameters.

        Args:
            other (Union[Dict[str, Any], EvolveParam]): Other parameters to merge.

        Returns:
            EvolveParam: New instance with merged parameters.
        """
        if isinstance(other, dict):
            other = EvolveParam.from_dict(other)
        elif not isinstance(other, EvolveParam):
            raise ValueError("other must be a dictionary or EvolveParam instance")

        # Create merged parameters
        merged_additional = {**self.additional_params, **other.additional_params}

        return EvolveParam(
            to_evolve=other.to_evolve if other.to_evolve else self.to_evolve,
            criteria=other.criteria if other.criteria is not None else self.criteria,
            max_iterations=(other.max_iterations if other.max_iterations is not None else self.max_iterations),
            temperature=(other.temperature if other.temperature is not None else self.temperature),
            type=(other.type if other.type is not None else self.type),
            additional_params=merged_additional,
        )

    def __repr__(self) -> str:
        return (
            f"EvolveParam("
            f"to_evolve={self.to_evolve}, "
            f"criteria={self.criteria}, "
            f"max_iterations={self.max_iterations}, "
            f"temperature={self.temperature}, "
            f"type={self.type}, "
            f"additional_params={self.additional_params})"
        )


def validate_evolve_param(
    evolve_param: Union[Dict[str, Any], EvolveParam, None],
) -> EvolveParam:
    """Utility function to validate and convert evolve parameters.

    Args:
        evolve_param (Union[Dict[str, Any], EvolveParam, None]): Input evolve parameters.

    Returns:
        EvolveParam: Validated EvolveParam instance.

    Raises:
        ValueError: If parameters are invalid.
    """
    if evolve_param is None:
        return EvolveParam()

    if isinstance(evolve_param, EvolveParam):
        evolve_param.validate()
        return evolve_param

    if isinstance(evolve_param, dict):
        # Check for required toEvolve key for backward compatibility
        if "toEvolve" not in evolve_param and "to_evolve" not in evolve_param:
            raise ValueError("evolve parameter must contain 'toEvolve' key")
        return EvolveParam.from_dict(evolve_param)

    raise ValueError("evolve parameter must be a dictionary, EvolveParam instance, or None")
