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
        max_generations (int): Maximum number of generations.
        max_retries (int): Maximum number of retries.
        recursion_limit (int): Maximum number of recursion.
        max_iterations_without_improvement (int): Maximum number of iterations without improvement.
        evolver_llm (Optional[Dict[str, Any]]): Evolver LLM configuration with all parameters.
        additional_params (Optional[Dict[str, Any]]): Additional parameters.
    """

    to_evolve: bool = False
    evolve_type: Optional[EvolveType] = EvolveType.TEAM_TUNING
    max_generations: int = 3
    max_retries: int = 3
    recursion_limit: int = 50
    max_iterations_without_improvement: Optional[int] = 2
    evolver_llm: Optional[Dict[str, Any]] = None
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

        if self.max_generations is not None:
            if not isinstance(self.max_generations, int):
                raise ValueError("max_generations must be an integer")
            if self.max_generations <= 0:
                raise ValueError("max_generations must be positive")

        if self.max_retries is not None:
            if not isinstance(self.max_retries, int):
                raise ValueError("max_retries must be an integer")
            if self.max_retries <= 0:
                raise ValueError("max_retries must be positive")

        if self.recursion_limit is not None:
            if not isinstance(self.recursion_limit, int):
                raise ValueError("recursion_limit must be an integer")
            if self.recursion_limit <= 0:
                raise ValueError("recursion_limit must be positive")

        if self.max_iterations_without_improvement is not None:
            if not isinstance(self.max_iterations_without_improvement, int):
                raise ValueError("max_iterations_without_improvement must be an integer or None")
            if self.max_iterations_without_improvement <= 0:
                raise ValueError("max_iterations_without_improvement must be positive or None")

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
            "max_generations": data.get("max_generations"),
            "max_retries": data.get("max_retries"),
            "recursion_limit": data.get("recursion_limit"),
            "max_iterations_without_improvement": data.get("max_iterations_without_improvement"),
            "evolver_llm": data.get("evolver_llm"),
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
                "max_generations",
                "max_retries",
                "recursion_limit",
                "max_iterations_without_improvement",
                "evolver_llm",
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
        if self.max_generations is not None:
            result["max_generations"] = self.max_generations
        if self.max_retries is not None:
            result["max_retries"] = self.max_retries
        if self.recursion_limit is not None:
            result["recursion_limit"] = self.recursion_limit
        # Always include max_iterations_without_improvement, even if None
        result["max_iterations_without_improvement"] = self.max_iterations_without_improvement
        if self.evolver_llm is not None:
            result["evolver_llm"] = self.evolver_llm
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
            max_generations=(other.max_generations if other.max_generations is not None else self.max_generations),
            max_retries=(other.max_retries if other.max_retries is not None else self.max_retries),
            recursion_limit=(other.recursion_limit if other.recursion_limit is not None else self.recursion_limit),
            max_iterations_without_improvement=(
                other.max_iterations_without_improvement
                if other.max_iterations_without_improvement is not None
                else self.max_iterations_without_improvement
            ),
            evolver_llm=(other.evolver_llm if other.evolver_llm is not None else self.evolver_llm),
            additional_params=merged_additional,
        )

    def __repr__(self) -> str:
        return (
            f"EvolveParam("
            f"to_evolve={self.to_evolve}, "
            f"evolve_type={self.evolve_type}, "
            f"max_generations={self.max_generations}, "
            f"max_retries={self.max_retries}, "
            f"recursion_limit={self.recursion_limit}, "
            f"max_iterations_without_improvement={self.max_iterations_without_improvement}, "
            f"evolver_llm={self.evolver_llm}, "
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
