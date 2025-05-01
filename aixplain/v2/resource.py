import requests
import pprint
from typing import (
    List,
    Tuple,
    TypedDict,
    TypeVar,
    Generic,
    Type,
    Any,
    Union,
    TYPE_CHECKING,
)
from typing_extensions import Unpack, NotRequired


from .enums import OwnershipType, SortBy, SortOrder

if TYPE_CHECKING:
    from .core import Aixplain


class BaseResource:
    """Base class for all resources.

    Attributes:
        context: Aixplain: The Aixplain instance.
        RESOURCE_PATH: str: The resource path.
    """

    _obj: Union[dict, Any]
    context: "Aixplain"
    RESOURCE_PATH: str

    def __init__(self, obj: Union[dict, Any]):
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
        if isinstance(self._obj, dict):
            if key in self._obj:
                return self._obj[key]
            raise AttributeError(f"Object has no attribute '{key}'")
        return getattr(self._obj, key)

    def save(self):
        """Save the resource.

        If the resource has an ID, it will be updated, otherwise it will be created.
        """
        if hasattr(self, "id") and self.id:
            self._action("put", [self.id], **self._obj)
        else:
            self._action("post", **self._obj)

    def _action(self, method: str = None, action_paths: List[str] = None, **kwargs) -> requests.Response:
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

        assert getattr(self, "RESOURCE_PATH"), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        if not self.id:
            raise ValueError("Action call requires an 'id' attribute")

        method = method or "GET"
        path = f"sdk/{self.RESOURCE_PATH}/{self.id}"
        if action_paths:
            path += "/".join(["", *action_paths])

        return self.context.client.request(method, path, **kwargs)

    def __repr__(self) -> str:
        if hasattr(self, "name"):
            return f"{self.__class__.__name__}(id={self.id}, name={self.name})"
        return f"{self.__class__.__name__}(id={self.id})"


class BaseListParams(TypedDict):
    """Base class for all list parameters.

    Attributes:
        query: str: The query string.
        ownership: Tuple[OwnershipType, List[OwnershipType]]: The ownership type.
        sort_by: SortBy: The attribute to sort by.
        sort_order: SortOrder: The order to sort by.
        page_number: int: The page number.
        page_size: int: The page size.
    """

    query: NotRequired[str]
    ownership: NotRequired[Tuple[OwnershipType, List[OwnershipType]]]
    sort_by: NotRequired[SortBy]
    sort_order: NotRequired[SortOrder]
    page_number: NotRequired[int]
    page_size: NotRequired[int]


class BaseGetParams(TypedDict):
    """Base class for all get parameters.

    Attributes:
        id: str: The resource ID.
    """

    pass


class BaseCreateParams(TypedDict):
    """Base class for all create parameters.

    Attributes:
        name: str: The name of the resource.
    """

    name: str


class BareCreateParams(BaseCreateParams):
    """Default implementation of create parameters."""

    pass


class BareListParams(BaseListParams):
    """Default implementation of list parameters."""

    pass


class BareGetParams(BaseGetParams):
    """Default implementation of get parameters."""

    pass


R = TypeVar("R", bound=BaseResource)
L = TypeVar("L", bound=BaseListParams)
C = TypeVar("C", bound=BaseCreateParams)
G = TypeVar("G", bound=BaseGetParams)


class Page(Generic[R]):
    """Page of resources.

    Attributes:
        items: List[R]: The list of resources.
        total: int: The total number of resources.
    """

    results: List[R]
    page_number: int
    page_total: int
    total: int

    def __init__(self, results: List[R], page_number: int, page_total: int, total: int):
        self.results = results
        self.page_number = page_number
        self.page_total = page_total
        self.total = total

    def __repr__(self) -> str:
        return pprint.pformat(self.__dict__, depth=2, indent=2)

    def __getitem__(self, key: str):
        return getattr(self, key)


class ListResourceMixin(Generic[L, R]):
    """Mixin for listing resources.

    Attributes:
        PAGINATE_PATH: str: The path for pagination.
        PAGINATE_METHOD: str: The method for pagination.
        PAGINATE_ITEMS_KEY: str: The key for the response.
        PAGINATE_TOTAL_KEY: str: The key for the total number of resources.
        PAGINATE_PAGE_TOTAL_KEY: str: The key for the total number of pages.
        PAGINATE_DEFAULT_PAGE_NUMBER: int: The default page number.
        PAGINATE_DEFAULT_PAGE_SIZE: int: The default page size.
    """

    PAGINATE_PATH = "paginate"
    PAGINATE_METHOD = "post"
    PAGINATE_ITEMS_KEY = "items"
    PAGINATE_TOTAL_KEY = "total"
    PAGINATE_PAGE_TOTAL_KEY = "pageTotal"
    PAGINATE_PAGE_NUMBER_KEY = "pageNumber"
    PAGINATE_DEFAULT_PAGE_NUMBER = 0
    PAGINATE_DEFAULT_PAGE_SIZE = 20

    @classmethod
    def list(cls: Type[R], **kwargs: Unpack[L]) -> Page[R]:
        """
        List resources across the first n pages with optional filtering.

        Args:
            kwargs: Unpack[L]: The keyword arguments.

        Returns:
            Page[R]: Page of BaseResource instances
        """

        assert getattr(cls, "RESOURCE_PATH"), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        # TypedDict does not support default values, so we need to manually set them
        # Dataclasses might be a better fit, but we're using the TypedDict to ensure
        # the correct types are used and to get IDE support

        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        params = BareListParams(**kwargs)
        filters = cls._populate_filters(params)
        paginate_path = cls._populate_path(cls.RESOURCE_PATH)
        print(paginate_path, filters)
        response = cls.context.client.request(cls.PAGINATE_METHOD, paginate_path, json=filters)
        return cls._build_page(response, **kwargs)

    @classmethod
    def _build_page(cls, response: requests.Response, **kwargs: Unpack[L]) -> Page[R]:
        """
        Build a page of resources from the response.

        Args:
            response: requests.Response: The response to build the page from.

        Returns:
            Page[R]: The page of resources.
        """
        json = response.json()

        items = json
        if cls.PAGINATE_ITEMS_KEY:
            items = json[cls.PAGINATE_ITEMS_KEY]

        total = len(items)
        if cls.PAGINATE_TOTAL_KEY:
            total = json[cls.PAGINATE_TOTAL_KEY]

        page_total = len(items)
        if cls.PAGINATE_PAGE_TOTAL_KEY:
            page_total = json[cls.PAGINATE_PAGE_TOTAL_KEY]

        return Page(
            results=[cls(item) for item in items],
            total=total,
            page_number=kwargs["page_number"],
            page_total=page_total,
        )

    @classmethod
    def _populate_path(cls, path: str) -> str:
        """
        Populate the path for pagination.

        Args:
            path: str: The path to populate.

        Returns:
            str: The populated path.
        """
        if cls.PAGINATE_PATH:
            return f"{path}/{cls.PAGINATE_PATH}"
        return path

    @classmethod
    def _populate_filters(cls, params: BaseListParams) -> dict:
        """
        Populate the filters for pagination.

        Args:
            params: BaseListParams: The parameters to populate.

        Returns:
            dict: The populated filters.
        """
        filters = {}

        if params.get("page_number") is not None:
            filters["pageNumber"] = params["page_number"]

        if params.get("page_size") is not None:
            filters["pageSize"] = params["page_size"]

        if params.get("query") is not None:
            filters["q"] = params["query"]

        if params.get("ownership") is not None:
            filters["ownership"] = params["ownership"]

        if params.get("sort_by") is not None:
            filters["sortBy"] = params["sort_by"]

        if params.get("sort_order") is not None:
            filters["sortOrder"] = params["sort_order"]

        print("filters", filters)

        return filters


class GetResourceMixin(Generic[G, R]):
    """Mixin for getting a resource."""

    @classmethod
    def get(cls: Type[R], id: Any, **kwargs: Unpack[G]) -> R:
        """
        Retrieve a single resource by its ID (or other get parameters).

        Args:
            id: Any: The ID of the resource to get.
            kwargs: Unpack[G]: Get parameters to pass to the request.

        Returns:
            BaseResource: Instance of the BaseResource class.

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass.
        """
        assert getattr(cls, "RESOURCE_PATH"), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        path = f"{cls.RESOURCE_PATH}/{id}"
        obj = cls.context.client.get_obj(path, **kwargs)
        return cls(obj)


class CreateResourceMixin(Generic[C, R]):
    """Mixin for creating a resource."""

    @classmethod
    def create(cls, *args, **kwargs: Unpack[C]) -> R:
        """
        Create a resource.

        Args:
            kwargs: Unpack[C]: The keyword arguments.

        Returns:
            BaseResource: The created resource.
        """
        assert getattr(cls, "RESOURCE_PATH"), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        obj = cls.context.client.request("post", cls.RESOURCE_PATH, *args, **kwargs)
        return cls(obj)
