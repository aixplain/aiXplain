"""Mixins for v2 API classes."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Literal
from typing_extensions import TypedDict


class ParameterInput(TypedDict):
    """TypedDict for individual parameter input configuration."""

    name: str
    value: Optional[Any]
    required: bool
    datatype: Literal["boolean", "string", "text", "number", "integer", "array", "object"]
    allowMulti: bool
    supportsVariables: bool
    fixed: bool
    description: str


class ParameterDefinition(TypedDict):
    """TypedDict for parameter definition structure."""

    code: str
    name: str
    description: str
    inputs: Dict[str, ParameterInput]


class ToolDict(TypedDict):
    """TypedDict defining the expected structure for tool serialization.

    This provides type safety and documentation for the as_tool() method return value.
    """

    id: str
    name: str
    description: str
    supplier: str
    parameters: Optional[List[ParameterDefinition]]
    function: Literal[
        "utilities",
        "text-generation",
        "translation",
        "image-generation",
        "speech-to-text",
        "text-to-speech",
        "classification",
        "data-extraction",
    ]
    type: Literal["model", "pipeline", "utility", "tool"]
    version: str
    assetId: str


class ToolableMixin(ABC):
    """Mixin that enforces the as_tool() interface for classes that can be used as tools.

    Any class that inherits from this mixin must implement the as_tool() method,
    which serializes the object into a format suitable for agent tool usage.
    """

    @abstractmethod
    def as_tool(self) -> ToolDict:
        """Serialize this object as a tool for agent creation.

        This method converts the object into a dictionary format that can be used
        as a tool when creating agents. The format is strictly typed using ToolDict.

        Returns:
            ToolDict: A typed dictionary representing this object as a tool with:
                - id: The tool's unique identifier
                - name: The tool's display name
                - description: The tool's description
                - supplier: The supplier code (e.g., "aixplain")
                - parameters: Optional list of parameter configurations
                - function: The tool's function type (e.g., "utilities")
                - type: The tool type (e.g., "model")
                - version: The tool's version as a string
                - assetId: The tool's asset ID (usually same as id)

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
        """
        pass
