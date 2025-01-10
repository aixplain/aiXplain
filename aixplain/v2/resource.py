import requests
from typing import (
    Optional,
    List,
    Tuple,
    TypedDict,
    TypeVar,
    Generic,
    Type,
    Any,
    TYPE_CHECKING,
)


from .enums import OwnershipType, SortBy, SortOrder

if TYPE_CHECKING:
    from .core import Aixplain


class BaseResource:
    """Base class for all resources.

    Attributes:
        context: Aixplain: The Aixplain instance.
        RESOURCE_PATH: str: The resource path.
        _obj: dict: The resource's attributes.
    """

    context: "Aixplain"
    RESOURCE_PATH: str

    def __init__(self, obj: dict):
        """
        Initialize a BaseResource instance.

        Args:
            obj: dict: Dictionary containing the resource's attributes.
        """
        self._obj = obj

    def __getattr__(self, key: str) -> Any:
        """
        Return the value corresponding to the key from the wrapped dictionary
        if found, otherwise raise an AttributeError.

        Args:
            key: str: Attribute name to retrieve from the resource.

        Returns:
            Any: Value corresponding to the specified key.

        Raises:
            AttributeError: If the key is not found in the wrapped
                                dictionary.
        """
        if key in self._obj:
            return self._obj[key]
        raise AttributeError(f"Object has no attribute '{key}'")

    def save(self):
        """Save the resource.

        If the resource has an ID, it will be updated, otherwise it will be created.
        """
        if hasattr(self, "id") and self.id:
            self._action("put", [self.id], **self._obj)
        else:
            self._action("post", **self._obj)

    def _action(
        self, method: Optional[str] = None, action_paths: List[str] = None, **kwargs
    ) -> requests.Response:
        """
        Internal method to perform actions on the resource.

        Args:
            method: str, optional: HTTP method to use (default is 'GET').
            action_paths: List[str], optional: Optional list of action paths to append to the
                             URL.
            kwargs: dict: Additional keyword arguments to pass to the request.

        Returns:
            requests.Response: Response from the client's request as requests.Response

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass or
                            'id' attribute is missing.
        """

        assert getattr(
            self, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        if not self.id:
            raise ValueError("Action call requires an 'id' attribute")

        method = method or "GET"
        path = f"sdk/{self.RESOURCE_PATH}/{self.id}"
        if action_paths:
            path += "/".join(["", *action_paths])

        return self.context.client.request(method, path, **kwargs)


class BaseListParams(TypedDict):
    """Base class for all list parameters.

    Attributes:
        query: Optional[str]: The query string.
        ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]]: The ownership type.
        sort_by: Optional[SortBy]: The attribute to sort by.
        sort_order: Optional[SortOrder]: The order to sort by.
        page_number: Optional[int]: The page number.
        page_size: Optional[int]: The page size.
    """

    query: Optional[str] = ""
    ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]] = (
        OwnershipType.SUBSCRIBED,
        OwnershipType.OWNED,
    )
    sort_by: Optional[SortBy] = SortBy.CREATION_DATE
    sort_order: Optional[SortOrder] = SortOrder.DESCENDING
    page_number: Optional[int] = 0
    page_size: Optional[int] = 20


class BaseGetParams(TypedDict):
    """Base class for all get parameters.

    Attributes:
        id: str: The resource ID.
    """

    id: str


class BaseCreateParams(TypedDict):
    """Base class for all create parameters.

    Attributes:
        name: Optional[str]: The name of the resource.
    """

    name: Optional[str] = None


class BareCreateParams(BaseCreateParams):
    """Parameters for creating resources.

    Attributes:
        name: Optional[str]: The name of the resource.
    """

    pass


class BareListParams(BaseListParams):
    """Parameters for listing resources.

    Attributes:
        query: Optional[str]: The query string.
        ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]]: The ownership type.
        sort_by: Optional[SortBy]: The attribute to sort by.
        sort_order: Optional[SortOrder]: The order to sort by.
        page_number: Optional[int]: The page number.
        page_size: Optional[int]: The page size.
    """

    pass


class BareGetParams(BaseGetParams):
    """Parameters for getting resources.

    Attributes:
        id: str: The resource ID.
    """

    pass


L = TypeVar("L", bound=BaseListParams)
C = TypeVar("C", bound=BaseCreateParams)
G = TypeVar("G", bound=BaseGetParams)


class ListResourceMixin(Generic[L]):
    """Mixin for listing resources.

    Attributes:
        PAGINATE_PATH: str: The path for pagination.
        PAGINATE_METHOD: str: The method for pagination.
        PAGINATE_RESPONSE_KEY: str: The key for the response.
    """

    PAGINATE_PATH = "paginate"
    PAGINATE_METHOD = "post"
    PAGINATE_RESPONSE_KEY = "items"

    @classmethod
    def list(cls: Type["BaseResource"], **kwargs: L) -> List["BaseResource"]:
        """
        List resources across the first n pages with optional filtering.

        Args:
            n: int, optional: Optional number of pages to fetch (default is 1).
            filters: dict, optional: Optional dictionary containing filters to apply to the
                        results.
            page_fn: function, optional: Optional custom function to replace the default page
                        method.
            kwargs: dict: Additional filter parameters.

        Returns:
            List[BaseResource]: List of BaseResource instances across n pages
        """

        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        # TypedDict does not support default values, so we need to manually set them
        # Dataclasses might be a better fit, but we're using the TypedDict to ensure
        # the correct types are used and to get IDE support
        params = BareListParams(**kwargs)
        filters = cls._populate_filters(params)
        paginate_path = cls._populate_path(cls.RESOURCE_PATH)
        response = cls.context.client.request(
            cls.PAGINATE_METHOD, paginate_path, json=filters
        )
        return cls._populate_objects(response)

    @classmethod
    def _populate_path(cls, path: str) -> str:
        if cls.PAGINATE_PATH:
            return f"{path}/{cls.PAGINATE_PATH}"
        return path

    @classmethod
    def _populate_filters(cls, params: BaseListParams) -> dict:
        filters = {}
        if params.get("page_number"):
            filters["pageNumber"] = params["page_number"]

        if params.get("page_size"):
            filters["pageSize"] = params["page_size"]

        if params.get("query"):
            filters["q"] = params["query"]

        if params.get("ownership"):
            filters["ownership"] = params["ownership"]

        if params.get("sort_by"):
            filters["sortBy"] = params["sort_by"]

        if params.get("sort_order"):
            filters["sortOrder"] = params["sort_order"]

        return filters

    @classmethod
    def _populate_objects(cls, response: requests.Response) -> List[BaseResource]:
        """
        Populate the objects from the response.
        """
        items = response.json()
        if cls.PAGINATE_RESPONSE_KEY:
            items = response.json()[cls.PAGINATE_RESPONSE_KEY]
        return [cls(item) for item in items]


class GetResourceMixin(Generic[G]):
    """Mixin for getting a resource.

    Attributes:
        None
    """

    @classmethod
    def get(cls: Type["BaseResource"], **kwargs) -> "BaseResource":
        """
        Retrieve a single resource by its ID (or other get parameters).

        Args:
            kwargs: dict: Get parameters to pass to the request.

        Returns:
            BaseResource: Instance of the BaseResource class.

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass.
        """
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        id = kwargs.pop("id")
        path = f"{cls.RESOURCE_PATH}/{id}"
        obj = cls.context.client.get_obj(path, **kwargs)
        return cls(obj)


class CreateResourceMixin(Generic[C]):
    """Mixin for creating a resource.

    Attributes:
        None
    """

    @classmethod
    def create(cls, **kwargs: C):
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        return cls.context.client.request("post", cls.RESOURCE_PATH, **kwargs)
