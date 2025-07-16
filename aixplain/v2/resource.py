import requests
import logging
import pprint
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import (
    List,
    Tuple,
    TypedDict,
    Type,
    TypeVar,
    Generic,
    Any,
    Optional,
    TYPE_CHECKING,
)
from typing_extensions import Unpack, NotRequired


from .enums import OwnershipType, SortBy, SortOrder, ResponseStatus

if TYPE_CHECKING:
    from .core import Aixplain


logger = logging.getLogger(__name__)


class BaseMixin:
    """Base mixin with meta capabilities for resource operations."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__.endswith("Mixin"):
            return
        if BaseMixin in cls.__mro__ and not issubclass(cls, BaseResource):
            raise TypeError(
                f"{cls.__name__} must inherit from BaseResource to use "
                "resource mixins"
            )


@dataclass_json
@dataclass
class BaseResource:
    """Base class for all resources.

    Attributes:
        context: Aixplain: The Aixplain instance (hidden from serialization).
        RESOURCE_PATH: str: The resource path.
        id: str: The resource ID.
        name: str: The resource name.
    """

    context: "Aixplain" = field(
        repr=False, compare=False, metadata=config(exclude=lambda x: True)
    )
    RESOURCE_PATH: str = field(
        default="", repr=False, compare=False, metadata=config(exclude=lambda x: True)
    )
    id: str = field(default="", repr=True, compare=True)
    name: str = field(default="", repr=True, compare=True)
    description: str = field(default="", repr=True, compare=True)

    def save(self):
        """Save the resource.

        If the resource has an ID, it will be updated, otherwise it will be
        created.
        """
        # Use dataclasses_json to_dict() which automatically excludes fields
        # marked with config(exclude=lambda x: True)
        data = self.to_dict()
        if self.id:
            self._action("put", [self.id], **data)
        else:
            self._action("post", **data)

    def _action(
        self,
        method: Optional[str] = None,
        action_paths: Optional[List[str]] = None,
        **kwargs
    ) -> requests.Response:
        """
        Internal method to perform actions on the resource.

        Args:
            method: str, optional: HTTP method to use (default is 'GET').
            action_paths: List[str], optional: Optional list of action paths to
                         append to the URL.
            kwargs: dict: Additional keyword arguments to pass to the request.

        Returns:
            requests.Response: Response from the client's request as
                              requests.Response

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass or
                            'id' attribute is missing.
        """

        assert getattr(self, "RESOURCE_PATH"), (
            "Subclasses of 'BaseResource' must " "specify 'RESOURCE_PATH'"
        )

        if not self.id:
            raise ValueError("Action call requires an 'id' attribute")

        method = method or "GET"
        path = f"sdk/{self.RESOURCE_PATH}/{self.id}"
        if action_paths:
            path += "/".join(["", *action_paths])

        return self.context.client.request(method, path, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}" f"(id={self.id}, name={self.name})"


class BaseParams(TypedDict):
    """Base class for parameters that include API key and resource path.

    Attributes:
        api_key: str: The API key for authentication.
        resource_path: str: Custom resource path for actions (optional).
    """

    api_key: NotRequired[str]
    resource_path: NotRequired[str]


class BaseListParams(BaseParams):
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


class BaseGetParams(BaseParams):
    """Base class for all get parameters.

    Attributes:
        id: str: The resource ID.
    """

    pass


class BaseDeleteParams(BaseParams):
    """Base class for all delete parameters.

    Attributes:
        id: str: The resource ID.
    """

    pass


class BaseRunParams(BaseParams):
    """Base class for all run parameters.

    Attributes:
        text: str: The text to run.
    """

    timeout: NotRequired[int]
    wait_time: NotRequired[int]


class BareListParams(BaseListParams):
    """Default implementation of list parameters."""

    pass


class BareGetParams(BaseGetParams):
    """Default implementation of get parameters."""

    pass


class BareDeleteParams(BaseDeleteParams):
    """Default implementation of delete parameters."""

    pass


class BareRunParams(BaseRunParams):
    """Default implementation of run parameters."""

    pass


@dataclass
class BaseResult:
    """Base class for running results."""

    status: str
    completed: bool
    error_message: Optional[str] = None
    url: Optional[str] = None
    result: Optional[Any] = None
    supplier_error: Optional[str] = None
    data: Optional[Any] = None
    _raw_data: Optional[dict] = field(
        default=None, repr=False
    )  # Store all raw response data

    def __init__(self, **kwargs):
        """Initialize with any fields from API response."""
        # Extract known fields
        self.status = kwargs.get("status", ResponseStatus.IN_PROGRESS.value)
        self.completed = kwargs.get("completed", False)
        self.error_message = kwargs.get("error_message")
        self.url = kwargs.get("url")
        self.result = kwargs.get("result")
        self.supplier_error = kwargs.get("supplier_error")
        self.data = kwargs.get("data")

        # Store all raw data for flexible access
        self._raw_data = kwargs

    def __getattr__(self, name: str) -> Any:
        """Allow access to any field from the raw response data."""
        if self._raw_data and name in self._raw_data:
            return self._raw_data[name]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


class Result(BaseResult):
    """Default implementation of running results."""

    pass


R = TypeVar("R", bound=BaseResource)
LP = TypeVar("LP", bound=BaseListParams)
GP = TypeVar("GP", bound=BaseGetParams)
DP = TypeVar("DP", bound=BaseDeleteParams)
RP = TypeVar("RP", bound=BaseRunParams)
RR = TypeVar("RR", bound=BaseResult)


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


class PagedListResourceMixin(BaseMixin, Generic[LP, R]):
    """Mixin for listing resources with pagination.

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
    def list(cls, **kwargs: Unpack[LP]) -> Page[R]:
        """
        List resources across the first n pages with optional filtering.

        Args:
            kwargs: Unpack[LP]: The keyword arguments.

        Returns:
            Page[R]: Page of BaseResource instances
        """

        # TypedDict does not support default values, so we need to manually set them
        # Dataclasses might be a better fit, but we're using the TypedDict to ensure
        # the correct types are used and to get IDE support

        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        params = BareListParams(**kwargs)
        filters = cls._populate_filters(params)

        # Use custom resource path if provided, otherwise use default
        custom_path = params.get("resource_path")
        resource_path = getattr(cls, "RESOURCE_PATH", "")
        paginate_path = cls._populate_path(resource_path, custom_path)
        context = getattr(cls, "context", None)

        if context is None:
            raise ValueError("Context is required for resource listing")

        response = context.client.request(
            cls.PAGINATE_METHOD, paginate_path, json=filters
        )
        return cls._build_page(response, **kwargs)

    @classmethod
    def _build_page(cls, response: requests.Response, **kwargs: Unpack[LP]) -> Page[R]:
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

        context = getattr(cls, "context", None)
        if context is None:
            raise ValueError("Context is required for resource operations")

        return Page(
            results=[cls(context=context, **item) for item in items],
            total=total,
            page_number=kwargs["page_number"],
            page_total=page_total,
        )

    @classmethod
    def _populate_path(cls, path: str, custom_path: Optional[str] = None) -> str:
        """
        Populate the path for pagination.

        Args:
            path: str: The path to populate.
            custom_path: str, optional: Custom resource path to use instead.

        Returns:
            str: The populated path.
        """
        base_path = custom_path if custom_path is not None else path
        if cls.PAGINATE_PATH:
            return f"{base_path}/{cls.PAGINATE_PATH}"
        return base_path

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

        # Handle function filter (for utilities and other function-specific listings)
        if params.get("function") is not None:
            if "functions" not in filters:
                filters["functions"] = []
            filters["functions"].append(params["function"].value)

        return filters


class PlainListResourceMixin(BaseMixin, Generic[LP, R]):
    """Mixin for listing resources without pagination.

    This mixin provides a simple list method that returns all resources
    without pagination. It's useful for resources that don't support
    pagination or when you need all items at once.

    Attributes:
        LIST_METHOD: str: The HTTP method for listing.
        LIST_ITEMS_KEY: str: The key for the response items.
    """

    LIST_METHOD = "get"
    LIST_ITEMS_KEY = "items"

    @classmethod
    def list(cls, **kwargs: Unpack[LP]) -> List[R]:
        """
        List all resources without pagination.

        Args:
            kwargs: Unpack[LP]: The keyword arguments.

        Returns:
            List[R]: List of BaseResource instances
        """
        params = BareListParams(**kwargs)
        filters = cls._populate_plain_filters(params)
        list_path = getattr(cls, "RESOURCE_PATH", "")
        context = getattr(cls, "context", None)

        if context is None:
            raise ValueError("Context is required for resource listing")

        response = context.client.request(cls.LIST_METHOD, list_path, params=filters)
        return cls._build_plain_list(response)

    @classmethod
    def _build_plain_list(cls, response: requests.Response) -> List[R]:
        """
        Build a list of resources from the response.

        Args:
            response: requests.Response: The response to build the list from.

        Returns:
            List[R]: The list of resources.
        """
        json = response.json()

        items = json
        if cls.LIST_ITEMS_KEY and cls.LIST_ITEMS_KEY in json:
            items = json[cls.LIST_ITEMS_KEY]

        context = getattr(cls, "context", None)
        if context is None:
            raise ValueError("Context is required for resource operations")

        return [cls(context=context, **item) for item in items]

    @classmethod
    def _populate_plain_filters(cls, params: BaseListParams) -> dict:
        """
        Populate the filters for plain listing.

        Args:
            params: BaseListParams: The parameters to populate.

        Returns:
            dict: The populated filters.
        """
        filters = {}

        if params.get("query") is not None:
            filters["q"] = params["query"]

        if params.get("ownership") is not None:
            filters["ownership"] = params["ownership"]

        if params.get("sort_by") is not None:
            filters["sortBy"] = params["sort_by"]

        if params.get("sort_order") is not None:
            filters["sortOrder"] = params["sort_order"]

        return filters


class GetResourceMixin(BaseMixin, Generic[GP, R]):
    """Mixin for getting a resource."""

    @classmethod
    def get(cls: Type[R], id: Any, **kwargs: Unpack[GP]) -> R:
        """
        Retrieve a single resource by its ID (or other get parameters).

        Args:
            id: Any: The ID of the resource to get.
            kwargs: Unpack[GP]: Get parameters to pass to the request.

        Returns:
            BaseResource: Instance of the BaseResource class.

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass.
        """
        resource_path = kwargs.pop("resource_path", None) or getattr(
            cls, "RESOURCE_PATH", ""
        )
        context = getattr(cls, "context", None)
        if context is None:
            raise ValueError("Context is required for resource operations")

        path = f"{resource_path}/{id}"
        obj = context.client.get_obj(path, **kwargs)
        return cls(context=context, **obj)


class DeleteResourceMixin(BaseMixin, Generic[DP, R]):
    """Mixin for deleting a resource."""

    @classmethod
    def delete(cls, id: Any, **kwargs: Unpack[DP]) -> R:
        """
        Delete a resource.
        """
        resource_path = kwargs.pop("resource_path", None) or getattr(
            cls, "RESOURCE_PATH", ""
        )
        context = getattr(cls, "context", None)
        if context is None:
            raise ValueError("Context is required for resource operations")

        path = f"{resource_path}/{id}"
        context.client.request("delete", path, **kwargs)
        return cls(context=context, id=id)


class RunnableResourceMixin(BaseMixin, Generic[RP, RR]):
    """Mixin for runnable resources."""

    ACTION_PATH = None
    RESPONSE_CLASS = Result  # Default response class

    def run(self, **kwargs: Unpack[RP]) -> RR:
        """
        Run the resource synchronously with automatic polling.

        Args:
            **kwargs: Run parameters including timeout and wait_time

        Returns:
            Response instance from the configured response class
        """
        name = kwargs.get("name", "process")

        logger.debug(f"Running {self.__class__.__name__} sync: {name}")

        # Start async execution
        result = self.run_async(**kwargs)

        # If already completed, return immediately
        if result.completed:
            return result

        # If we have a polling URL, use sync_poll for continuous polling
        # Check both 'url' and 'data' fields for the polling URL
        poll_url = result.url or result.data
        if poll_url:
            return self.sync_poll(poll_url, name=name, **kwargs)

        return result

    def run_async(self, **kwargs: Unpack[RP]) -> RR:
        """
        Run the resource asynchronously.

        Args:
            **kwargs: Run parameters specific to the resource type

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        name = kwargs.get("name", "process")

        logger.debug(f"Running {self.__class__.__name__} async: {name}")

        try:
            # Determine URL based on ACTION_PATH
            resource_path = kwargs.pop("resource_path", None) or getattr(
                self, "RESOURCE_PATH", ""
            )
            if getattr(self, "ACTION_PATH", None) is None:
                # Use direct execution service (for models/tools)
                url = f"{self.context.model_url}/{self.id}"
            else:
                # Use platform API with action path (for other resources)
                path = f"{resource_path}/{self.id}/" f"{self.ACTION_PATH}"
                url = f"{self.context.base_url}/{path}"

            logger.debug(f"Run Async: {url} - {kwargs}")

            # Use context.client.request() instead of direct requests
            # Pass the full URL as path - urljoin will handle it correctly
            response = self.context.client.request("post", url, json=kwargs)

            # Parse response using the resource-specific response class
            response_data = response.json()

            # Provide default values for required fields
            if "status" not in response_data:
                response_data["status"] = ResponseStatus.IN_PROGRESS.value
            if "completed" not in response_data:
                response_data["completed"] = False

            # Store raw data for flexible access
            response_data["_raw_data"] = response_data

            return self.RESPONSE_CLASS(**response_data)

        except Exception as e:
            logger.error(f"Error in async run for {name}: {e}")
            return self.RESPONSE_CLASS(
                status=ResponseStatus.FAILED.value,
                completed=True,
                error_message=str(e),
            )

    def poll(self, poll_url: str, name: str = "process") -> RR:
        """
        Poll for the result of an asynchronous operation.

        Args:
            poll_url: URL to poll for results
            name: Name/ID of the process

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        logger.debug(f"Polling {self.__class__.__name__} for {name}")

        try:
            # Use context.client for all polling operations
            # If poll_url is a full URL, urljoin will use it directly
            # If it's a relative path, it will be joined with base_url
            response = self.context.client.get(poll_url)
            response_data = response.json()
        except Exception as e:
            logger.error(f"Error polling for {name}: {e}")
            return self.RESPONSE_CLASS(
                status=ResponseStatus.FAILED.value,
                completed=False,
                error_message=str(e),
            )

        # Determine status based on completion
        if response_data.get("completed", False):
            if "error_message" in response_data or "supplierError" in response_data:
                status = ResponseStatus.FAILED
            else:
                status = ResponseStatus.SUCCESS
        else:
            status = ResponseStatus.IN_PROGRESS

        response_data.setdefault("status", status.value)

        # Provide default values for required fields
        if "completed" not in response_data:
            response_data["completed"] = False

        # Store raw data for flexible access
        response_data["_raw_data"] = response_data

        return self.RESPONSE_CLASS(**response_data)

    def sync_poll(
        self, poll_url: str, name: str = "process", **kwargs: Unpack[RP]
    ) -> RR:
        """
        Keeps polling until an asynchronous operation is complete.

        Args:
            poll_url: URL to poll for results
            name: Name/ID of the process
            **kwargs: Run parameters including timeout and wait_time

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        import time

        timeout = kwargs.get("timeout", 300)
        wait_time = kwargs.get("wait_time", 0.5)

        logger.info(f"Starting sync polling for {name} (timeout: {timeout}s)")

        start_time = time.time()
        wait_time = max(wait_time, 0.2)  # Minimum wait time
        poll_count = 0

        while (time.time() - start_time) < timeout:
            poll_count += 1
            result = self.poll(poll_url, name=name)

            if result.completed:
                logger.info(f"Sync poll completed for {name} after {poll_count} polls")
                return result

            # Log progress every 10 polls
            if poll_count % 10 == 0:
                elapsed = time.time() - start_time
                logger.info(
                    f"Still polling {name}... "
                    f"({poll_count} polls, {elapsed:.1f}s elapsed)"
                )

            time.sleep(wait_time)
            if wait_time < 60:
                wait_time *= 1.1  # Exponential backoff

        # Timeout reached
        logger.error(
            f"Sync poll timeout for {name} after {timeout}s " f"({poll_count} polls)"
        )
        return self.RESPONSE_CLASS(
            status=ResponseStatus.FAILED.value,
            completed=False,
            error_message=f"Timeout after {timeout} seconds",
        )

    def is_completed(self, result: RR) -> bool:
        """
        Check if a result is completed.

        Args:
            result: The result to check

        Returns:
            bool: True if completed, False otherwise
        """
        return result.completed

    def is_successful(self, result: RR) -> bool:
        """
        Check if a result is successful.

        Args:
            result: The result to check

        Returns:
            bool: True if successful, False otherwise
        """
        return result.completed and result.status == ResponseStatus.SUCCESS.value

    def is_failed(self, result: RR) -> bool:
        """
        Check if a result failed.

        Args:
            result: The result to check

        Returns:
            bool: True if failed, False otherwise
        """
        return result.completed and result.status == ResponseStatus.FAILED.value

    def get_result_data(self, result: RR) -> Any:
        """
        Extract the result data from a completed result.

        Args:
            result: The result to extract data from

        Returns:
            Any: The result data

        Raises:
            ValueError: If the result is not completed or failed
        """
        if not result.completed:
            raise ValueError("Cannot extract data from incomplete result")

        if result.status == ResponseStatus.FAILED.value:
            raise ValueError(f"Result failed: {result.error_message}")

        return result.result

    def get_error_message(self, result: RR) -> Optional[str]:
        """
        Get the error message from a failed result.

        Args:
            result: The result to get error from

        Returns:
            Optional[str]: The error message, or None if no error
        """
        return result.error_message or result.supplier_error
