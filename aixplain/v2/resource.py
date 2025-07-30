import requests
import logging
import pprint
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from urllib.parse import quote
from typing import (
    List,
    Tuple,
    TypedDict,
    TypeVar,
    Generic,
    Any,
    Optional,
    Dict,
    TYPE_CHECKING,
    NotRequired,
    Protocol,
    runtime_checkable,
    Union,
)
from typing_extensions import Unpack


from .enums import OwnershipType, SortBy, SortOrder, ResponseStatus, ToolType
from .exceptions import (
    ResourceError,
    ValidationError,
    APIError,
    TimeoutError,
    create_operation_failed_error,
)


if TYPE_CHECKING:
    from .core import Aixplain


logger = logging.getLogger(__name__)


def encode_resource_id(resource_id: str) -> str:
    """
    URL encode a resource ID for use in API paths.

    Args:
        resource_id: The resource ID to encode

    Returns:
        The URL-encoded resource ID
    """
    return quote(resource_id, safe="")


# Protocol classes for better type safety
@runtime_checkable
class HasContext(Protocol):
    """Protocol for classes that have a context attribute."""

    context: Any


@runtime_checkable
class HasResourcePath(Protocol):
    """Protocol for classes that have a RESOURCE_PATH attribute."""

    RESOURCE_PATH: str


@runtime_checkable
class HasFromDict(Protocol):
    """Protocol for classes that have a from_dict method."""

    @classmethod
    def from_dict(cls: type, data: dict) -> Any: ...


@runtime_checkable
class HasToDict(Protocol):
    """Protocol for classes that have a to_dict method."""

    def to_dict(self) -> dict: ...


class BaseMixin:
    """Base mixin with meta capabilities for resource operations."""

    def __init_subclass__(cls: type, **kwargs: Any) -> None:
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

    context: Any = field(
        repr=False, compare=False, metadata=config(exclude=lambda x: True), init=False
    )
    RESOURCE_PATH: str = field(
        default="",
        repr=False,
        compare=False,
        metadata=config(exclude=lambda x: True),
        init=False,
    )
    _saved_state: Optional[dict] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=config(exclude=lambda x: True),
        init=False,
    )

    id: str = ""
    name: str = ""
    description: str = ""

    def _get_serializable_state(self) -> dict:
        """
        Get the current state of the resource as a serializable dictionary.

        Returns:
            dict: The serializable state of the resource
        """
        # All BaseResource subclasses inherit to_dict() from @dataclass_json
        # Internal fields are already excluded via metadata=config(
        #     exclude=lambda x: True
        # )
        return self.to_dict()

    def _is_state_changed(self) -> bool:
        """
        Check if the current state differs from the saved state.

        Returns:
            bool: True if the state has changed, False otherwise
        """
        if self._saved_state is None:
            # No saved state means this is a new resource or hasn't been saved
            return True

        current_state = self._get_serializable_state()
        return current_state != self._saved_state

    @property
    def is_modified(self) -> bool:
        """
        Check if the resource has been modified since last save.

        Returns:
            bool: True if the resource has been modified, False otherwise
        """
        return self._is_state_changed()

    def _update_saved_state(self) -> None:
        """
        Update the saved state to match the current state.
        Called after successful save operations.
        """
        self._saved_state = self._get_serializable_state()

    def before_save(self, result: dict) -> None:
        """
        Callback to be called before the resource is saved.
        """
        pass

    def after_save(self, result: dict) -> None:
        """
        Callback to be called after the resource is saved.
        """
        pass

    def build_save_payload(self, **kwargs: Any) -> dict:
        """
        Build the payload for the save action.
        """
        if isinstance(self, HasToDict):
            return self.to_dict()
        return {}

    def save(self, **kwargs: Any) -> "BaseResource":
        """Save the resource.

        If the resource has an ID, it will be updated, otherwise it will be
        created.
        """
        resource_path = kwargs.pop("resource_path", self.RESOURCE_PATH)

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.before_save(kwargs)

        payload = self.build_save_payload(**kwargs)
        result = None
        if self.id:
            result = self.context.client.request(
                "put", f"{resource_path}/{self.encoded_id}", json=payload
            )
        else:
            result = self.context.client.request(
                "post", f"{resource_path}", json=payload
            )
        self.id = result["id"]
        self._update_saved_state()
        self.after_save(result)
        return self

    def _action(
        self,
        method: Optional[str] = None,
        action_paths: Optional[List[str]] = None,
        **kwargs: Any,
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
            raise ValidationError("Action call requires an 'id' attribute")

        method = method or "GET"
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        if action_paths:
            path += "/".join(["", *action_paths])

        return self.context.client.request(method, path, **kwargs)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id}, name={self.name}, description={self.description})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def encoded_id(self) -> str:
        """
        Get the URL-encoded version of the resource ID.

        Returns:
            The URL-encoded resource ID, or empty string if no ID exists
        """
        return encode_resource_id(self.id) if self.id else ""


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


@dataclass_json
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
    _raw_data: Optional[dict] = field(default=None, repr=False)
    # Store all raw response data

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

    @classmethod
    def from_dict(cls: type, data: dict) -> "BaseResult":
        """Create a BaseResult instance from a dictionary."""
        return cls(**data)


@dataclass_json
@dataclass
class Result(BaseResult):
    """Default implementation of running results."""

    pass


# Standardized type variables with proper bounds
ResourceT = TypeVar("ResourceT", bound=BaseResource)
ListParamsT = TypeVar("ListParamsT", bound=BaseListParams)
GetParamsT = TypeVar("GetParamsT", bound=BaseGetParams)
DeleteParamsT = TypeVar("DeleteParamsT", bound=BaseDeleteParams)
RunParamsT = TypeVar("RunParamsT", bound=BaseRunParams)
ResultT = TypeVar("ResultT", bound=BaseResult)


class Page(Generic[ResourceT]):
    """Page of resources.

    Attributes:
        items: List[ResourceT]: The list of resources.
        total: int: The total number of resources.
    """

    results: List[ResourceT]
    page_number: int
    page_total: int
    total: int

    def __init__(
        self, results: List[ResourceT], page_number: int, page_total: int, total: int
    ):
        self.results = results
        self.page_number = page_number
        self.page_total = page_total
        self.total = total

    def __repr__(self) -> str:
        return pprint.pformat(self.__dict__, depth=2, indent=2)

    def __getitem__(self, key: str):
        return getattr(self, key)


class BaseListResourceMixin(BaseMixin, Generic[ListParamsT, ResourceT]):
    """Base mixin for listing resources with shared functionality."""

    @classmethod
    def _get_context_and_path(
        cls: type, **kwargs: Any
    ) -> Tuple["Aixplain", str, Optional[str]]:
        """Get context and resource path for listing operations."""
        # Use dict constructor instead of TypedDict unpacking for better mypy
        # support
        params_dict = dict(kwargs)
        custom_path = params_dict.get("resource_path")
        resource_path = getattr(cls, "RESOURCE_PATH", "")
        context = getattr(cls, "context", None)

        if context is None:
            raise ResourceError("Context is required for resource listing")

        return context, resource_path, custom_path

    @classmethod
    def _build_resources(
        cls: type, items: List[dict], context: "Aixplain"
    ) -> List[ResourceT]:
        """Build resource instances from response items."""
        resources = []
        for item in items:
            # Use dataclasses_json's from_dict to handle field aliasing
            # This will automatically map API field names to dataclass field
            # names
            if isinstance(cls, HasFromDict):
                obj = cls.from_dict(item)
            else:
                # Fallback for classes without from_dict
                obj = cls(**item)  # type: ignore[call-arg]
            setattr(obj, "context", context)
            # Set the saved state to match the loaded state
            obj._update_saved_state()
            resources.append(obj)
        return resources

    @classmethod
    def _populate_base_filters(cls: type, params: BaseListParams) -> dict:
        """Populate common filters for listing operations."""
        filters = {}

        if params.get("query") is not None:
            filters["q"] = params["query"]

        if params.get("ownership") is not None:
            filters["ownership"] = str(params["ownership"])

        if params.get("sort_by") is not None:
            filters["sortBy"] = str(params["sort_by"])

        if params.get("sort_order") is not None:
            filters["sortOrder"] = str(params["sort_order"])

        return filters


class PagedListResourceMixin(BaseListResourceMixin, Generic[ListParamsT, ResourceT]):
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

    PAGINATE_PATH: str = "paginate"
    PAGINATE_METHOD: str = "post"
    PAGINATE_ITEMS_KEY: str = "items"
    PAGINATE_TOTAL_KEY: str = "total"
    PAGINATE_PAGE_TOTAL_KEY: str = "pageTotal"
    PAGINATE_PAGE_NUMBER_KEY: str = "pageNumber"
    PAGINATE_DEFAULT_PAGE_NUMBER: int = 0
    PAGINATE_DEFAULT_PAGE_SIZE: int = 20

    @classmethod
    def list(cls: type, **kwargs: Unpack[ListParamsT]) -> Page[ResourceT]:
        """
        List resources across the first n pages with optional filtering.

        Args:
            kwargs: The keyword arguments.

        Returns:
            Page[ResourceT]: Page of BaseResource instances
        """
        # Set default pagination values
        default_page_number = getattr(cls, "PAGINATE_DEFAULT_PAGE_NUMBER", 0)
        default_page_size = getattr(cls, "PAGINATE_DEFAULT_PAGE_SIZE", 20)

        kwargs.setdefault("page_number", default_page_number)
        kwargs.setdefault("page_size", default_page_size)

        # Get context and path
        context, resource_path, custom_path = cls._get_context_and_path(**kwargs)

        # Build path and filters
        paginate_path = cls._populate_path(  # type: ignore[attr-defined]
            resource_path, custom_path
        )
        params_dict = dict(kwargs)
        filters = cls._populate_filters(params_dict)  # type: ignore[attr-defined]

        # Make request
        paginate_method = getattr(cls, "PAGINATE_METHOD", "post")
        response = context.client.request(paginate_method, paginate_path, json=filters)
        return cls._build_page(  # type: ignore[attr-defined,misc]
            response, context, **kwargs
        )

    @classmethod
    def search(cls: type, query: str, **kwargs: Unpack[ListParamsT]) -> Page[ResourceT]:
        """
        Search resources across the first n pages with optional filtering.
        """
        return cls.list(query=query, **kwargs)

    @classmethod
    def _build_page(
        cls: type, response: "Any", context: "Aixplain", **kwargs: Any
    ) -> Page[ResourceT]:
        """
        Build a page of resources from the response.
        Accepts either a requests.Response or already-decoded dict/list.
        """
        if hasattr(response, "json"):
            json_data = response.json()
        else:
            json_data = response

        items = json_data
        paginate_items_key = getattr(cls, "PAGINATE_ITEMS_KEY", "items")
        if paginate_items_key and isinstance(json_data, dict):
            items = json_data[paginate_items_key]

        total = len(items)
        paginate_total_key = getattr(cls, "PAGINATE_TOTAL_KEY", "total")
        if paginate_total_key and isinstance(json_data, dict):
            total = json_data[paginate_total_key]

        page_total = len(items)
        paginate_page_total_key = getattr(cls, "PAGINATE_PAGE_TOTAL_KEY", "pageTotal")
        if paginate_page_total_key and isinstance(json_data, dict):
            page_total = json_data[paginate_page_total_key]

        # Build resources using shared method
        results = cls._build_resources(items, context)  # type: ignore[attr-defined]

        return Page(
            results=results,
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
        paginate_path = getattr(cls, "PAGINATE_PATH", "paginate")
        if paginate_path:
            return f"{base_path}/{paginate_path}"
        return base_path

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """
        Populate the filters for pagination.

        Args:
            params: dict: The parameters to populate.

        Returns:
            dict: The populated filters.
        """
        # Convert to BaseListParams for type safety
        list_params = BaseListParams(**params)
        filters = cls._populate_base_filters(list_params)

        # Add pagination-specific filters
        if params.get("page_number") is not None:
            filters["pageNumber"] = params["page_number"]

        if params.get("page_size") is not None:
            filters["pageSize"] = params["page_size"]

        return filters


class PlainListResourceMixin(BaseListResourceMixin, Generic[ListParamsT, ResourceT]):
    """Mixin for listing resources without pagination.

    This mixin provides a simple list method that returns all resources
    without pagination. It's useful for resources that don't support
    pagination or when you need all items at once.

    Attributes:
        LIST_METHOD: str: The HTTP method for listing.
        LIST_ITEMS_KEY: str: The key for the response items.
    """

    LIST_METHOD: str = "get"
    LIST_ITEMS_KEY: str = "items"

    @classmethod
    def list(cls: type, **kwargs: Unpack[ListParamsT]) -> List[ResourceT]:
        """
        List all resources without pagination.

        Args:
            kwargs: The keyword arguments.

        Returns:
            List[ResourceT]: List of BaseResource instances
        """
        # Get context and path
        context, resource_path, _ = cls._get_context_and_path(**kwargs)

        # Build filters
        params_dict = dict(kwargs)
        filters = cls._populate_plain_filters(params_dict)  # type: ignore[attr-defined]

        # Make request
        list_method = getattr(cls, "LIST_METHOD", "get")
        response = context.client.request(list_method, resource_path, params=filters)
        return cls._build_plain_list(response, context)  # type: ignore[attr-defined]

    @classmethod
    def _build_plain_list(
        cls: type, response: "Any", context: "Aixplain"
    ) -> List[ResourceT]:
        """
        Build a list of resources from the response.
        Accepts either a requests.Response or already-decoded list/dict.
        """
        if hasattr(response, "json"):
            json_data = response.json()
        else:
            json_data = response

        items = json_data
        list_items_key = getattr(cls, "LIST_ITEMS_KEY", "items")
        if (
            list_items_key
            and isinstance(json_data, dict)
            and list_items_key in json_data
        ):
            items = json_data[list_items_key]

        # Build resources using shared method
        return cls._build_resources(items, context)

    @classmethod
    def _populate_plain_filters(cls: type, params: dict) -> dict:
        """
        Populate the filters for plain listing.

        Args:
            params: dict: The parameters to populate.

        Returns:
            dict: The populated filters.
        """
        # Convert to BaseListParams for type safety
        list_params = BaseListParams(**params)
        return cls._populate_base_filters(list_params)


class GetResourceMixin(BaseMixin, Generic[GetParamsT, ResourceT]):
    """Mixin for getting a resource."""

    @classmethod
    def get(cls: type, id: Any, **kwargs: Unpack[GetParamsT]) -> ResourceT:
        """
        Retrieve a single resource by its ID (or other get parameters).

        Args:
            id: Any: The ID of the resource to get.
            kwargs: Get parameters to pass to the request.

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
            raise ResourceError("Context is required for resource operations")

        encoded_id = encode_resource_id(id)
        path = f"{resource_path}/{encoded_id}"
        obj = context.client.get(path, **kwargs)

        if isinstance(cls, HasFromDict):
            instance = cls.from_dict(obj)
        else:
            instance = cls(**obj)  # type: ignore[call-arg]
        setattr(instance, "context", context)
        # Set the saved state to match the loaded state
        instance._update_saved_state()
        return instance


class DeleteResourceMixin(BaseMixin, Generic[DeleteParamsT, ResourceT]):
    """Mixin for deleting a resource."""

    def delete(self, **kwargs: Unpack[DeleteParamsT]) -> "BaseResource":
        """
        Delete a resource.
        """
        resource_path = kwargs.pop("resource_path", None) or getattr(
            self, "RESOURCE_PATH", ""
        )

        path = f"{resource_path}/{self.encoded_id}"
        self.context.client.request_raw("delete", path, **kwargs)
        return self


class RunnableResourceMixin(BaseMixin, Generic[RunParamsT, ResultT]):
    """Mixin for runnable resources."""

    RUN_ACTION_PATH: str = "run"
    RESPONSE_CLASS: type = Result  # Default response class

    def build_run_payload(self, **kwargs: Unpack[RunParamsT]) -> dict:
        """
        Build the payload for the run action.

        This method automatically handles dataclass serialization if the run
        parameters are dataclasses with @dataclass_json decorator.
        """
        # Default behavior for TypedDict or other parameter types
        return kwargs

    def build_run_url(self, **kwargs: Unpack[RunParamsT]) -> str:
        """
        Build the URL for the run action.

        This method can be overridden by subclasses to provide custom URL
        construction. The default implementation uses the resource path with
        the run action.

        Returns:
            str: The URL to use for the run action
        """
        assert getattr(self, "RESOURCE_PATH"), (
            "Subclasses of 'BaseResource' must " "specify 'RESOURCE_PATH'"
        )

        if not self.id:
            raise ValidationError("Run call requires an 'id' attribute")

        run_action_path = getattr(self, "RUN_ACTION_PATH", None)
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        if run_action_path:
            path += f"/{run_action_path}"

        return path

    def handle_run_response(
        self, response: dict, **kwargs: Unpack[RunParamsT]
    ) -> ResultT:
        """
        Handle the response from a run request.

        This method can be overridden by subclasses to handle different
        response patterns. The default implementation assumes a polling URL
        in the 'data' field.

        Args:
            response: The raw response from the API
            **kwargs: Run parameters

        Returns:
            Response instance from the configured response class
        """
        # Check for polling URL in data field (legacy format)
        if (
            response.get("data")
            and isinstance(response["data"], str)
            and response["data"].startswith("http")
        ):
            # This is a polling URL case
            response_class = getattr(self, "RESPONSE_CLASS", Result)
            return response_class.from_dict(
                {
                    "status": response.get("status", "IN_PROGRESS"),
                    "url": response["data"],
                    "completed": False,
                }
            )
        elif response.get("status") == "IN_PROGRESS" and response.get("data"):
            # This is a polling URL case
            response_class = getattr(self, "RESPONSE_CLASS", Result)
            return response_class.from_dict(
                {
                    "status": response["status"],
                    "url": response["data"],
                    "completed": True,
                }
            )
        else:
            # Direct response case - include original response data
            filtered_response = {
                "status": response.get("status", "IN_PROGRESS"),
                "completed": response.get("completed", False),
                "error_message": response.get("error_message"),
                "url": response.get("url"),
                "result": response.get("result"),
                "supplier_error": response.get("supplier_error"),
                "supplierError": response.get(
                    "supplierError"
                ),  # Include camelCase version
                "data": response.get("data"),
                "_raw_data": response,  # Include original response data
            }

            # Check for failed status and raise appropriate error
            status = response.get("status", "IN_PROGRESS")
            if status == "FAILED":
                raise create_operation_failed_error(response)

            response_class = getattr(self, "RESPONSE_CLASS", Result)
            return response_class.from_dict(filtered_response)

    def before_run(self, **kwargs: Unpack[RunParamsT]) -> ResultT:
        pass

    def after_run(
        self, result: Union[ResultT, Exception], **kwargs: Unpack[RunParamsT]
    ) -> None:
        pass

    def run(self, **kwargs: Unpack[RunParamsT]) -> ResultT:
        """
        Run the resource synchronously with automatic polling.

        Args:
            **kwargs: Run parameters including timeout and wait_time

        Returns:
            Response instance from the configured response class
        """
        self.before_run(**kwargs)

        # Start async execution
        try:
            result = self.run_async(**kwargs)

            # Check if we need to poll
            if result.url and not result.completed:
                return self.sync_poll(result.url, **kwargs)
        except Exception as e:
            self.after_run(e, **kwargs)
            raise e
        finally:
            self.after_run(result, **kwargs)

        return result

    def run_async(self, **kwargs: Unpack[RunParamsT]) -> ResultT:
        """
        Run the resource asynchronously.

        Args:
            **kwargs: Run parameters specific to the resource type

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        payload = self.build_run_payload(**kwargs)

        # Build the run URL using the extensible method
        run_url = self.build_run_url(**kwargs)

        # Use context.client.request() with the custom URL
        response = self.context.client.request("post", run_url, json=payload)

        # Use the extensible response handler
        return self.handle_run_response(response, **kwargs)

    def poll(self, poll_url: str) -> ResultT:
        """
        Poll for the result of an asynchronous operation.

        Args:
            poll_url: URL to poll for results
            name: Name/ID of the process

        Returns:
            Response instance from the configured RESPONSE_CLASS

        Raises:
            APIError: If the polling request fails
            OperationFailedError: If the operation has failed
        """

        try:
            # Use context.client for all polling operations
            # If poll_url is a full URL, urljoin will use it directly
            # If it's a relative path, it will be joined with base_url
            response = self.context.client.get(poll_url)
        except Exception as e:
            # Re-raise as APIError instead of silently returning failed result
            from .exceptions import APIError

            raise APIError(f"Polling failed: {str(e)}", 0, {"poll_url": poll_url})

        # Handle polling response - it might not have all the expected fields
        filtered_response = {
            "status": response.get("status", "IN_PROGRESS"),
            "completed": response.get("completed", False),
            "error_message": response.get("error_message"),
            "url": response.get("url"),
            "result": response.get("result"),
            "supplier_error": response.get("supplier_error"),
            "data": response.get("data"),
        }

        # Check if the operation has failed and raise appropriate error
        status = response.get("status", "IN_PROGRESS")
        if status == "FAILED":
            raise create_operation_failed_error(response)

        response_class = getattr(self, "RESPONSE_CLASS", Result)
        return response_class.from_dict(filtered_response)

    def sync_poll(self, poll_url: str, **kwargs: Unpack[RunParamsT]) -> ResultT:
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

        start_time = time.time()
        wait_time = max(wait_time, 0.2)  # Minimum wait time

        while (time.time() - start_time) < timeout:
            try:
                result = self.poll(poll_url)

                if result.completed:
                    return result

            except (APIError, ResourceError) as e:
                # Re-raise API and resource errors immediately
                raise e
            except Exception as e:
                # Log other errors but continue polling
                logger.warning(f"Polling error: {e}, continuing...")

            time.sleep(wait_time)
            if wait_time < 60:
                wait_time *= 1.1  # Exponential backoff

        raise TimeoutError(f"Operation timed out after {timeout} seconds")


class ToolMixin(BaseMixin):
    """Mixin for resources that can be used as tools.

    This mixin provides a default implementation of as_tool() that uses
    the TOOL_TYPE class variable and the resource's id to create a simple
    tool representation.

    Subclasses must define a TOOL_TYPE class variable with a ToolType enum
    value.
    """

    TOOL_TYPE: Optional[ToolType] = None  # Must be set by subclasses

    def as_tool(self) -> Dict[str, Any]:
        """Convert the resource to a tool representation.

        Returns:
            Dict containing basic tool information (id, type).
            Subclasses can override this to provide additional information.
        """
        if not self.TOOL_TYPE:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define TOOL_TYPE class " "variable"
            )

        return {
            "assetId": self.id,
            "type": self.TOOL_TYPE.value,
        }
