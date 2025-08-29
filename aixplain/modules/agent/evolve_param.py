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
        evolve_type (Optional[EvolveType]): Type of evolve.
        max_successful_generations (int): Maximum number of successful generations.
        max_failed_generation_retries (int): Maximum number of failed generation retries.
        max_iterations (int): Maximum number of iterations.
        max_non_improving_generations (Optional[int]): Maximum number of non-improving generations.
        llm (Optional[Dict[str, Any]]): LLM configuration with all parameters.
        additional_params (Optional[Dict[str, Any]]): Additional parameters.
    """

    to_evolve: bool = False
    evolve_type: Optional[EvolveType] = EvolveType.TEAM_TUNING
    max_successful_generations: int = 3
    max_failed_generation_retries: int = 3
    max_iterations: int = 50
    max_non_improving_generations: Optional[int] = 2
    llm: Optional[Dict[str, Any]] = None
    additional_params: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        """Validate parameters after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate evolve parameters.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if self.evolve_type is not None:
            if isinstance(self.evolve_type, str):
                # Convert string to EvolveType
                try:
                    self.evolve_type = EvolveType(self.evolve_type)
                except ValueError:
                    raise ValueError(
                        f"evolve_type '{self.evolve_type}' is not a valid EvolveType. Valid values are: {list(EvolveType)}"
                    )
            elif not isinstance(self.evolve_type, EvolveType):
                raise ValueError("evolve_type must be a valid EvolveType or string")
        if self.additional_params is not None:
            if not isinstance(self.additional_params, dict):
                raise ValueError("additional_params must be a dictionary")

        if self.max_successful_generations is not None:
            if not isinstance(self.max_successful_generations, int):
                raise ValueError("max_successful_generations must be an integer")
            if self.max_successful_generations <= 0:
                raise ValueError("max_successful_generations must be positive")

        if self.max_failed_generation_retries is not None:
            if not isinstance(self.max_failed_generation_retries, int):
                raise ValueError("max_failed_generation_retries must be an integer")
            if self.max_failed_generation_retries <= 0:
                raise ValueError("max_failed_generation_retries must be positive")

        if self.max_iterations is not None:
            if not isinstance(self.max_iterations, int):
                raise ValueError("max_iterations must be an integer")
            if self.max_iterations <= 0:
                raise ValueError("max_iterations must be positive")

        if self.max_non_improving_generations is not None:
            if not isinstance(self.max_non_improving_generations, int):
                raise ValueError("max_non_improving_generations must be an integer or None")
            if self.max_non_improving_generations <= 0:
                raise ValueError("max_non_improving_generations must be positive or None")

        # Add validation for llm parameter
        if self.llm is not None:
            if not isinstance(self.llm, dict):
                raise ValueError("llm must be a dictionary or None")

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
            "evolve_type": data.get("evolve_type"),
            "max_successful_generations": data.get("max_successful_generations"),
            "max_failed_generation_retries": data.get("max_failed_generation_retries"),
            "max_iterations": data.get("max_iterations"),
            "max_non_improving_generations": data.get("max_non_improving_generations"),
            "llm": data.get("llm"),
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
                "evolve_type",
                "max_successful_generations",
                "max_failed_generation_retries",
                "max_iterations",
                "max_non_improving_generations",
                "llm",
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
        if self.evolve_type is not None:
            result["evolve_type"] = self.evolve_type
        if self.max_successful_generations is not None:
            result["max_successful_generations"] = self.max_successful_generations
        if self.max_failed_generation_retries is not None:
            result["max_failed_generation_retries"] = self.max_failed_generation_retries
        if self.max_iterations is not None:
            result["max_iterations"] = self.max_iterations
        # Always include max_non_improving_generations, even if None
        result["max_non_improving_generations"] = self.max_non_improving_generations
        if self.llm is not None:
            result["llm"] = self.llm
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
            evolve_type=(other.evolve_type if other.evolve_type is not None else self.evolve_type),
            max_successful_generations=(
                other.max_successful_generations
                if other.max_successful_generations is not None
                else self.max_successful_generations
            ),
            max_failed_generation_retries=(
                other.max_failed_generation_retries
                if other.max_failed_generation_retries is not None
                else self.max_failed_generation_retries
            ),
            max_iterations=(other.max_iterations if other.max_iterations is not None else self.max_iterations),
            max_non_improving_generations=(
                other.max_non_improving_generations
                if other.max_non_improving_generations is not None
                else self.max_non_improving_generations
            ),
            llm=(other.llm if other.llm is not None else self.llm),
            additional_params=merged_additional,
        )

    def __repr__(self) -> str:
        return (
            f"EvolveParam("
            f"to_evolve={self.to_evolve}, "
            f"evolve_type={self.evolve_type}, "
            f"max_successful_generations={self.max_successful_generations}, "
            f"max_failed_generation_retries={self.max_failed_generation_retries}, "
            f"max_iterations={self.max_iterations}, "
            f"max_non_improving_generations={self.max_non_improving_generations}, "
            f"llm={self.llm}, "
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
