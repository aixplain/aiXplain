import requests
import logging
from typing import (
    List,
    TypedDict,
    TypeVar,
    Generic,
    Type,
    Any,
    Union,
    Optional,
    Dict,
    TYPE_CHECKING,
    Tuple,
)
from typing_extensions import Unpack, NotRequired

from .enums import OwnershipType, SortBy, SortOrder, ResponseStatus

if TYPE_CHECKING:
    from .core import Aixplain  # noqa: F401
    from .resource import BaseResource  # noqa: F401


# Base parameter classes for mixins
class BaseApiKeyParams(TypedDict):
    """Base class for parameters that include API key.

    Attributes:
        api_key: str: The API key for authentication.
    """

    api_key: NotRequired[str]


class BaseListParams(BaseApiKeyParams):
    """Base class for all list parameters.

    Attributes:
        query: str: The query string.
        ownership: Tuple[OwnershipType, List[OwnershipType]]: The ownership
            type.
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


class BaseGetParams(BaseApiKeyParams):
    """Base class for all get parameters.

    Attributes:
        id: str: The resource ID.
    """

    pass


class BaseCreateParams(BaseApiKeyParams):
    """Base class for all create parameters.

    Attributes:
        name: str: The name of the resource.
    """

    name: str


class BaseDeleteParams(BaseApiKeyParams):
    """Base class for all delete parameters."""

    pass


class BaseRunParams(BaseApiKeyParams):
    """Base class for all run parameters.

    Attributes:
        data: Input data for the resource
        name: Name/ID for the process
        timeout: Maximum time to wait for completion (default: 300)
        wait_time: Time between polling attempts (default: 0.5)
    """

    data: Union[str, Dict[str, Any]]
    name: NotRequired[str]
    timeout: NotRequired[float]
    wait_time: NotRequired[float]


# Default implementations
class BareListParams(BaseListParams):
    """Default implementation of list parameters."""

    pass


class BareGetParams(BaseGetParams):
    """Default implementation of get parameters."""

    pass


class BareCreateParams(BaseCreateParams):
    """Default implementation of create parameters."""

    pass


class BareDeleteParams(BaseDeleteParams):
    """Default implementation of delete parameters."""

    pass


class BareRunParams(BaseRunParams):
    """Default implementation of run parameters."""

    pass


# Type variables for generics
L = TypeVar("L", bound=BaseListParams)
C = TypeVar("C", bound=BaseCreateParams)
G = TypeVar("G", bound=BaseGetParams)
D = TypeVar("D", bound=BaseDeleteParams)
RU = TypeVar("RU", bound=BaseRunParams)
R = TypeVar("R", bound="BaseRunnableResponse")  # Response type variable
T = TypeVar("T", bound="BaseResource")  # Resources must extend BaseResource


class Page(Generic[T]):
    """Page of resources.

    Attributes:
        results: List[T]: The list of resources.
        total: int: The total number of resources.
    """

    results: List[T]
    page_number: int
    page_total: int
    total: int

    def __init__(self, results: List[T], page_number: int, page_total: int, total: int):
        self.results = results
        self.page_number = page_number
        self.page_total = page_total
        self.total = total

    def __repr__(self) -> str:
        import pprint

        return pprint.pformat(self.__dict__, depth=2, indent=2)

    def __getitem__(self, key: str):
        return getattr(self, key)


class ListResourceMixin(Generic[L, T]):
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
    def list(cls: Type[T], **kwargs: Unpack[L]) -> Page[T]:
        """
        List resources across the first n pages with optional filtering.

        Args:
            kwargs: Unpack[L]: The keyword arguments.

        Returns:
            Page[T]: Page of BaseResource instances
        """

        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        # TypedDict does not support default values, so we need to manually
        # set them. Dataclasses might be a better fit, but we're using the
        # TypedDict to ensure the correct types are used and to get IDE
        # support

        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        params = BareListParams(**kwargs)
        filters = cls._populate_filters(params)
        paginate_path = cls._populate_path(cls.RESOURCE_PATH)
        print(paginate_path, filters)
        response = cls.context.client.request(
            cls.PAGINATE_METHOD, paginate_path, json=filters
        )
        return cls._build_page(response, **kwargs)

    @classmethod
    def _build_page(cls, response: requests.Response, **kwargs: Unpack[L]) -> Page[T]:
        """
        Build a page of resources from the response.

        Args:
            response: requests.Response: The response to build the page from.

        Returns:
            Page[T]: The page of resources.
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


class GetResourceMixin(Generic[G, T]):
    """Mixin for getting a resource."""

    @classmethod
    def get(cls: Type[T], id: Any, **kwargs: Unpack[G]) -> T:
        """
        Retrieve a single resource by its ID (or other get parameters).

        Args:
            id: Any: The ID of the resource to get.
            kwargs: Unpack[G]: Get parameters to pass to the request.

        Returns:
            T: Instance of the BaseResource class.

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass.
        """
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        path = f"{cls.RESOURCE_PATH}/{id}"
        obj = cls.context.client.get_obj(path, **kwargs)
        return cls(obj)


class CreateResourceMixin(Generic[C, T]):
    """Mixin for creating a resource."""

    @classmethod
    def create(cls, *args, **kwargs: Unpack[C]) -> T:
        """
        Create a resource.

        Args:
            kwargs: Unpack[C]: The keyword arguments.

        Returns:
            T: The created resource.
        """
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        obj = cls.context.client.request("post", cls.RESOURCE_PATH, *args, **kwargs)
        return cls(obj)


class DeleteResourceMixin(Generic[D, T]):
    """Mixin for deleting a resource."""

    @classmethod
    def delete(cls: Type[T], id: Any, **kwargs: Unpack[D]) -> Any:
        """
        Delete a resource.
        """
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        path = f"{cls.RESOURCE_PATH}/{id}"
        cls.context.client.request("delete", path, **kwargs)


class BaseRunnableResponse:
    """Base response class for runnable resources.

    This class provides core functionality for handling API responses from
    runnable resources. Subclasses can extend this to provide resource-specific
    fields and behavior while maintaining backward compatibility.
    """

    def __init__(self, response_data: Dict[str, Any]):
        """Initialize the response with raw data from API.

        Args:
            response_data: Raw response data from the API
        """
        self._raw_data = response_data
        self._parse_response(response_data)

    def _parse_response(self, response_data: Dict[str, Any]) -> None:
        """Parse the response data into instance attributes.

        This method can be overridden by subclasses to handle resource-specific
        parsing logic.

        Args:
            response_data: Raw response data from the API
        """
        # Core response fields that all resources share
        self.status: Optional[ResponseStatus] = self._parse_status(
            response_data.get("status")
        )
        self.data: Any = response_data.get("data", "")
        self.details: Dict[str, Any] = response_data.get("details", {})
        self.completed: bool = response_data.get("completed", False)
        self.error_message: str = response_data.get("error_message", "")

        # Resource usage fields (common across most resources)
        self.used_credits: float = response_data.get("usedCredits", 0)
        self.run_time: float = response_data.get("runTime", 0)
        self.usage: Optional[Dict[str, Any]] = response_data.get("usage")

        # Async operation fields
        self.url: Optional[str] = response_data.get("url")
        self.error_code: Optional[str] = response_data.get("error_code")

        # Store additional fields for extensibility
        self._known_fields = self._get_known_fields()
        self._additional_fields = {
            k: v for k, v in response_data.items() if k not in self._known_fields
        }

    def _get_known_fields(self) -> set:
        """Get the set of known fields for this response type.

        Subclasses can override this to define their own known fields.

        Returns:
            Set of field names that are handled by this response class
        """
        return {
            "status",
            "data",
            "details",
            "completed",
            "error_message",
            "usedCredits",
            "runTime",
            "usage",
            "url",
            "error_code",
        }

    def _parse_status(self, status: Any) -> Optional[ResponseStatus]:
        """Parse status into ResponseStatus enum."""
        if status is None:
            return None
        if isinstance(status, ResponseStatus):
            return status
        if isinstance(status, str):
            try:
                return ResponseStatus(status)
            except ValueError:
                logging.warning(f"Unknown status value: {status}")
                return None
        return None

    def __getitem__(self, key: str) -> Any:
        """Enable dictionary-style access for backward compatibility."""
        # Handle legacy field name mappings
        if key == "usedCredits":
            return self.used_credits
        elif key == "runTime":
            return self.run_time
        elif key == "status":
            # Return string value for backward compatibility
            return self.status.value if self.status else None
        elif hasattr(self, key):
            return getattr(self, key)
        elif key in self._additional_fields:
            return self._additional_fields[key]
        else:
            raise KeyError(f"Key '{key}' not found in {self.__class__.__name__}.")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value with optional default."""
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: str) -> bool:
        """Check if key exists in response."""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for backward compatibility."""
        return self._raw_data.copy()

    def __repr__(self) -> str:
        """String representation showing key fields."""
        fields = []
        if self.status:
            fields.append(f"status={self.status.value}")
        if self.data:
            data_preview = str(self.data)[:50]
            if len(str(self.data)) > 50:
                data_preview += "..."
            fields.append(f"data='{data_preview}'")
        if self.completed:
            fields.append(f"completed={self.completed}")
        if self.error_message:
            fields.append(f"error_message='{self.error_message}'")
        if self.url:
            fields.append(f"url='{self.url}'")
        return f"{self.__class__.__name__}({', '.join(fields)})"


class RunnableResponse(BaseRunnableResponse):
    """Default implementation of runnable response.

    This is the standard response class used by most resources. It provides
    all the common functionality without resource-specific customizations.
    """

    pass


class RunnableMixin(Generic[RU, R]):
    """Mixin for runnable resources like models, pipelines, and agents.

    This mixin provides execution capabilities for resources that can be run
    asynchronously or synchronously. It follows the same patterns as the
    legacy Model module while using modern v2 architecture.

    Type Parameters:
        RU: Type for run parameters (extends BaseRunParams)
        R: Type for the response (extends BaseRunnableResponse)

    Attributes:
        RUN_ACTION_PATH: str: The action path for running the resource.
            Defaults to "run".
        RESPONSE_CLASS: Type[R]: The response class to use.
            Must be set by subclasses.
    """

    RUN_ACTION_PATH = "run"
    RESPONSE_CLASS: Type[R] = RunnableResponse

    def run(
        self,
        **kwargs: Unpack[RU]
    ) -> R:
        """
        Run the resource synchronously with automatic polling.

        Args:
            **kwargs: Run parameters including timeout and wait_time

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        name = kwargs.get("name", "process")

        logging.debug(f"Running {self.__class__.__name__} sync: {name}")

        # Start async execution
        async_response = self.run_async(**kwargs)

        # If already completed, return immediately
        if async_response.completed:
            return async_response

        # If we have a polling URL, use sync_poll for continuous polling
        if async_response.url:
            return self.sync_poll(
                async_response.url,
                name=name,
                **kwargs
            )

        return async_response

    def run_async(self, **kwargs: Unpack[RU]) -> R:
        """
        Run the resource asynchronously.
        
        Args:
            **kwargs: Run parameters specific to the resource type
            
        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        name = kwargs.get("name", "process")
        
        logging.debug(f"Running {self.__class__.__name__} async: {name}")
        
        # Build the payload using the resource-specific implementation
        payload = self._build_run_payload(**kwargs)
        
        try:
            # Determine URL based on RUN_ACTION_PATH
            if self.RUN_ACTION_PATH is None:
                # Use direct execution service (for models/tools)
                url = f"{self.context.model_url}/{self.id}"
            else:
                # Use platform API with action path (for other resources)
                path = f"{self.RESOURCE_PATH}/{self.id}/{self.RUN_ACTION_PATH}"
                url = f"{self.context.base_url}/{path}"
            
            logging.debug(f"Run Async: {url} - {payload}")
            
            # Use context.client.request() instead of direct requests
            # Pass the full URL as path - urljoin will handle it correctly
            response = self.context.client.request(
                "post", url, json=payload
            )

            # Parse response using the resource-specific response class
            response_data = response.json()
            return self._create_response(response_data)
            
        except Exception as e:
            logging.error(f"Error in async run for {name}: {e}")
            return self._create_response(
                {
                    "status": ResponseStatus.FAILED.value,
                    "completed": True,
                    "error_message": str(e),
                }
            )

    def poll(self, poll_url: str, name: str = "process") -> R:
        """
        Poll for the result of an asynchronous operation.

        Args:
            poll_url: URL to poll for results
            name: Name/ID of the process

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        logging.debug(f"Polling {self.__class__.__name__} for {name}")

        try:
            # Use context.client for all polling operations
            # If poll_url is a full URL, urljoin will use it directly
            # If it's a relative path, it will be joined with base_url
            response = self.context.client.get(poll_url)
            response_data = response.json()
        except Exception as e:
            logging.error(f"Error polling for {name}: {e}")
            return self._create_response(
                {
                    "status": ResponseStatus.FAILED.value,
                    "completed": False,
                    "error_message": str(e),
                }
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

        return self._create_response(response_data)

    def sync_poll(
        self,
        poll_url: str,
        name: str = "process",
        **kwargs: Unpack[RU]
    ) -> R:
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

        logging.info(f"Sync polling {self.__class__.__name__} for {name}")

        start_time = time.time()
        wait_time = max(wait_time, 0.2)  # Minimum wait time

        while (time.time() - start_time) < timeout:
            result = self.poll(poll_url, name=name)

            if result.completed:
                logging.debug(f"Sync poll completed for {name}: {result}")
                return result

            time.sleep(wait_time)
            if wait_time < 60:
                wait_time *= 1.1  # Exponential backoff

        # Timeout reached
        logging.error(f"Sync poll timeout for {name} after {timeout}s")
        return self._create_response(
            {
                "status": ResponseStatus.FAILED.value,
                "completed": False,
                "error_message": f"Timeout after {timeout} seconds",
            }
        )

    def _create_response(self, response_data: Dict[str, Any]) -> R:
        """Create a response instance using the configured response class.

        Args:
            response_data: Raw response data from the API

        Returns:
            Instance of the response class specified in RESPONSE_CLASS
        """
        return self.RESPONSE_CLASS(response_data)

    def _build_run_payload(self, **kwargs) -> Dict[str, Any]:
        """
        Build the payload for running the resource.

        This method should be overridden by subclasses to handle their
        specific parameter structures.

        Args:
            **kwargs: All run parameters for the resource

        Returns:
            Dict: The payload to send to the API
        """
        # Default implementation for basic resources
        data = kwargs.get("data")
        name = kwargs.get("name", "process")

        payload = {
            "data": data,
            "name": name,
        }

        # Add any additional parameters that are not core fields
        core_fields = {"data", "name", "api_key"}
        additional_params = {
            k: v
            for k, v in kwargs.items()
            if k not in core_fields and v is not None
        }

        if additional_params:
            payload["parameters"] = additional_params
            
        return payload

    def _poll_external_url(
        self, poll_url: str, name: str
    ) -> R:
        """
        Poll an external URL (for backward compatibility).

        Args:
            poll_url: External URL to poll
            name: Process name

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        # Use context.client instead of manual requests
        # This method is now redundant since poll() handles both cases
        # but keeping for backward compatibility
        return self.poll(poll_url, name)
