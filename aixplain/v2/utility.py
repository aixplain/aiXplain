"""Utility resource module for managing custom Python code utilities."""

from typing import List, Any, Optional
from typing_extensions import NotRequired, Unpack
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json

from .resource import (
    BaseSearchParams,
    BaseResource,
    SearchResourceMixin,
    GetResourceMixin,
    BaseGetParams,
    BaseRunParams,
    Result,
    RunnableResourceMixin,
    DeleteResourceMixin,
    BaseDeleteParams,
)
from .enums import Function


class UtilitySearchParams(BaseSearchParams):
    """Parameters for listing utilities.

    Attributes:
        function: Function: The function of the utility (should be UTILITIES).
        status: str: The status of the utility.
        query: str: Search query for utilities.
        ownership: Tuple[OwnershipType, List[OwnershipType]]: Ownership filter.
    """

    function: NotRequired[Function]
    status: NotRequired[str]


class UtilityRunParams(BaseRunParams):
    """Parameters for running utilities.

    Attributes:
        data: str: The data to run the utility on.
    """

    data: str


@dataclass_json
@dataclass(repr=False)
class Utility(
    BaseResource,
    SearchResourceMixin[UtilitySearchParams, "Utility"],
    GetResourceMixin[BaseGetParams, "Utility"],
    DeleteResourceMixin[BaseDeleteParams, "Utility"],
    RunnableResourceMixin[UtilityRunParams, Result],
):
    """Resource for utilities.

    Utilities are standalone assets that can be created and managed
    independently of models. They represent custom functions that can be
    executed on the platform.
    """

    RESOURCE_PATH = "sdk/utilities"

    code: str = ""
    inputs: List[str] = field(default_factory=list)
    utility_id: str = "custom_python_code"

    def __post_init__(self) -> None:
        """Parse code and validate description for new utility instances."""
        # Only run parsing logic for new instances (no id yet)
        if not self.id:
            from aixplain.modules.model.utils import parse_code_decorated

            code, inputs, description, name = parse_code_decorated(self.code, self.context.api_key)
            self.code = code
            self.inputs = inputs
            self.description = description
            self.name = name

            # Validate description length
            if not self.description or len(self.description.strip()) <= 10:
                current_length = len(self.description.strip()) if self.description else 0
                raise ValueError(
                    f"Utility description must be more than 10 characters. Current description length: {current_length}"
                )

            # Only save if this is a new instance (no id yet)
            self.save()

    def build_save_payload(self, **kwargs: Any) -> dict:
        """Build the payload for the save action."""
        payload = self.to_dict()
        payload["inputs"] = [input.to_dict() for input in self.inputs]
        return payload

    @classmethod
    def get(cls: type["Utility"], id: str, **kwargs: Unpack[BaseGetParams]) -> "Utility":
        """Get a utility by ID.

        Args:
            id: The utility ID.
            **kwargs: Additional parameters for the get request.

        Returns:
            The retrieved Utility instance.
        """
        return super().get(id, resource_path="sdk/models", **kwargs)

    @classmethod
    def run(cls: type["Utility"], **kwargs: Unpack[UtilityRunParams]) -> Result:
        """Run the utility with provided parameters.

        Args:
            **kwargs: Run parameters including data to process.

        Returns:
            Result of the utility execution.
        """
        return super().run(**kwargs)

    @classmethod
    def search(
        cls: type["Utility"],
        query: Optional[str] = None,
        **kwargs: Unpack[UtilitySearchParams],
    ) -> "Page[Utility]":
        """Search utilities with optional query and filtering.

        Args:
            query: Optional search query string
            **kwargs: Additional search parameters (function, status, etc.)

        Returns:
            Page of utilities matching the search criteria
        """
        # If query is provided, add it to kwargs
        if query is not None:
            kwargs["query"] = query

        return super().search(**kwargs)
