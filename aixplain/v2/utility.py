from typing import Union, List, Callable
from typing_extensions import NotRequired, Unpack

from .resource import (
    BaseListParams,
    BaseCreateParams,
    BaseResource,
    PlainListResourceMixin,
    GetResourceMixin,
    CreateResourceMixin,
    BareGetParams,
    BaseRunParams,
    Page,
    Result,
    RunnableResourceMixin,
)
from .enums import Function


class UtilityListParams(BaseListParams):
    """Parameters for listing utilities.

    Attributes:
        function: Function: The function of the utility (should be UTILITIES).
        status: str: The status of the utility.
    """

    function: NotRequired[Function]
    status: NotRequired[str]


class UtilityCreateParams(BaseCreateParams):
    """Parameters for creating utilities.

    Attributes:
        name: str: The name of the utility.
        code: Union[str, Callable]: The code of the utility.
        description: str: The description of the utility.
        inputs: List[dict]: The inputs of the utility.
        output_examples: str: Output examples for the utility.
    """

    code: Union[str, Callable]
    description: NotRequired[str]
    inputs: NotRequired[List[dict]]
    output_examples: NotRequired[str]


class UtilityRunParams(BaseRunParams):
    """Parameters for running utilities.

    Attributes:
        data: str: The data to run the utility on.
    """

    data: str


class Utility(
    BaseResource,
    PlainListResourceMixin[UtilityListParams, "Utility"],
    GetResourceMixin[BareGetParams, "Utility"],
    CreateResourceMixin[UtilityCreateParams, "Utility"],
    RunnableResourceMixin[UtilityRunParams, Result],
):
    """Resource for utilities.

    Utilities are standalone assets that can be created and managed
    independently of models. They represent custom functions that can be
    executed on the platform.
    """

    RESOURCE_PATH = "sdk/utilities"

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Utility":
        """Get a utility by ID.

        Args:
            id: str: The utility ID.
            **kwargs: Additional parameters.

        Returns:
            Utility: The utility resource.
        """
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs: Unpack[UtilityListParams]) -> List["Utility"]:
        """List utilities.

        Args:
            **kwargs: List parameters.

        Returns:
            Page[Utility]: Page of utilities.
        """
        return super().list(**kwargs)

    @classmethod
    def create(cls, **kwargs: Unpack[UtilityCreateParams]) -> "Utility":
        """Create a new utility.

        Args:
            **kwargs: Create parameters.

        Returns:
            Utility: The created utility resource.
        """
        return super().create(**kwargs)

    def run(self, **kwargs) -> Result:
        """Run the utility.

        Args:
            **kwargs: Run parameters.

        Returns:
            Result: The execution result.
        """
        return super().run(**kwargs)

    def deploy(self) -> "Utility":
        """Deploy the utility to make it permanent.

        Returns:
            Utility: The deployed utility.
        """
        response = self._action("post", ["deploy"])
        return Utility(response.json())

    def validate(self) -> bool:
        """Validate the utility.

        Returns:
            bool: True if valid, False otherwise.
        """
        response = self._action("post", ["validate"])
        return response.status_code == 200
