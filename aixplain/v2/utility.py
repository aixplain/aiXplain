from typing import List, Tuple
from typing_extensions import NotRequired
from dataclasses import dataclass, field

from .resource import (
    BaseListParams,
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    BaseRunParams,
    Result,
    RunnableResourceMixin,
)
from .enums import Function, OwnershipType, SortBy, SortOrder


class UtilityListParams(BaseListParams):
    """Parameters for listing utilities.

    Attributes:
        function: Function: The function of the utility (should be UTILITIES).
        status: str: The status of the utility.
        query: str: Search query for utilities.
        ownership: Tuple[OwnershipType, List[OwnershipType]]: Ownership filter.
        sort_by: SortBy: Sort by attribute.
        sort_order: SortOrder: Sort order.
        page_number: int: Page number for pagination.
        page_size: int: Page size for pagination.
    """

    function: NotRequired[Function]
    status: NotRequired[str]
    query: NotRequired[str]
    ownership: NotRequired[Tuple[OwnershipType, List[OwnershipType]]]
    sort_by: NotRequired[SortBy]
    sort_order: NotRequired[SortOrder]
    page_number: NotRequired[int]
    page_size: NotRequired[int]


class UtilityRunParams(BaseRunParams):
    """Parameters for running utilities.

    Attributes:
        data: str: The data to run the utility on.
    """

    data: str


@dataclass
class Utility(
    BaseResource,
    PagedListResourceMixin[UtilityListParams, "Utility"],
    GetResourceMixin[BareGetParams, "Utility"],
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

    def __post_init__(self):
        from aixplain.modules.model.utils import parse_code_decorated

        code, inputs, description, name = parse_code_decorated(
            self.code, self.context.api_key
        )
        self.code = code
        self.inputs = inputs
        self.description = description
        self.name = name

        # Validate description length
        if not self.description or len(self.description.strip()) <= 10:
            current_length = len(self.description.strip()) if self.description else 0
            raise ValueError(
                f"Utility description must be more than 10 characters. "
                f"Current description length: {current_length}"
            )

        self.save()
