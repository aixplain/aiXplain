from typing import List, Tuple
from typing_extensions import NotRequired

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

    def __post_init__(self):
        self.save()
