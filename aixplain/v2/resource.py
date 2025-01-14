import requests
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
from typing_extensions import Unpack


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

    def _action(
        self, method: str = None, action_paths: List[str] = None, **kwargs
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

    def __repr__(self) -> str:
        return repr(self._obj)


class BaseListParams(TypedDict, total=False):
    """Base class for all list parameters.

    Attributes:
        query: str: The query string.
        ownership: Tuple[OwnershipType, List[OwnershipType]]: The ownership type.
        sort_by: SortBy: The attribute to sort by.
        sort_order: SortOrder: The order to sort by.
        page_number: int: The page number.
        page_size: int: The page size.
    """

    query: str
    ownership: Tuple[OwnershipType, List[OwnershipType]]
    sort_by: SortBy
    sort_order: SortOrder
    page_number: int
    page_size: int


class BaseGetParams(TypedDict, total=False):
    """Base class for all get parameters.

    Attributes:
        id: str: The resource ID.
    """

    id: str


class BaseCreateParams(TypedDict, total=False):
    """Base class for all create parameters.

    Attributes:
        name: str: The name of the resource.
    """

    name: str


class BareCreateParams(BaseCreateParams):
    pass


class BareListParams(BaseListParams):

    pass


class BareGetParams(BaseGetParams):
    pass


R = TypeVar("R", bound=BaseResource)
L = TypeVar("L", bound=BaseListParams)
C = TypeVar("C", bound=BaseCreateParams)
G = TypeVar("G", bound=BaseGetParams)


class ListResourceMixin(Generic[L, R]):
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
    def list(cls: Type[R], **kwargs: Unpack[L]) -> List[R]:
        """
        List resources across the first n pages with optional filtering.

        Args:
            kwargs: Unpack[L]: The keyword arguments.

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
    def _populate_objects(cls, response: requests.Response) -> List[R]:
        """
        Populate the objects from the response.
        """
        items = response.json()
        if cls.PAGINATE_RESPONSE_KEY:
            items = response.json()[cls.PAGINATE_RESPONSE_KEY]
        return [cls(item) for item in items]


class GetResourceMixin(Generic[G, R]):
    """Mixin for getting a resource.

    Attributes:
        None
    """

    @classmethod
    def get(cls: Type[R], **kwargs: Unpack[G]) -> R:
        """
        Retrieve a single resource by its ID (or other get parameters).

        Args:
            kwargs: Unpack[G]: Get parameters to pass to the request.

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


class CreateResourceMixin(Generic[C, R]):
    """Mixin for creating a resource."""

    @classmethod
    def create(cls, **kwargs: Unpack[C]) -> R:
        """
        Create a resource.

        Args:
            kwargs: Unpack[C]: The keyword arguments.

        Returns:
            BaseResource: The created resource.
        """
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        obj = cls.context.client.request("post", cls.RESOURCE_PATH, **kwargs)
        return cls(obj)
