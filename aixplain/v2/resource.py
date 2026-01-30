"""Resource management module for v2 API."""

import requests
import logging
import reprlib
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
    TYPE_CHECKING,
    Protocol,
    runtime_checkable,
    Union,
    Callable,
)
from typing_extensions import Unpack, NotRequired
from functools import wraps
from copy import deepcopy


from .enums import OwnershipType, SortBy, SortOrder
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


# Hook decorator system
def with_hooks(func: Callable) -> Callable:
    """Generic decorator to add before/after hooks to resource operations.

    This decorator automatically infers the operation name from the function name
    and provides a consistent pattern for all operations:
    - Before hooks can return early to bypass the operation
    - After hooks can transform the result
    - Error handling is consistent across all operations
    - Supports both positional and keyword arguments

    Usage:
        @with_hooks
        def save(self, **kwargs):
            # operation implementation

        @with_hooks
        def run(self, *args, **kwargs):
            # operation implementation with positional args
    """
    operation_name = func.__name__

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Call before hook with all arguments
        before_method = getattr(self, f"before_{operation_name}", None)
        if before_method:
            early_result = before_method(*args, **kwargs)
            if early_result is not None:
                return early_result

        # Execute the operation
        try:
            result = func(self, *args, **kwargs)

            # Call after hook (success case)
            after_method = getattr(self, f"after_{operation_name}", None)
            if after_method:
                custom_result = after_method(result, *args, **kwargs)
                if custom_result is not None:
                    return custom_result

            return result

        except Exception as e:
            # Transform low-level exceptions to domain-specific errors
            if not isinstance(e, ResourceError):
                raise ResourceError(f"Failed to {operation_name} resource: {e}")

            # Call after hook (error case)
            after_method = getattr(self, f"after_{operation_name}", None)
            if after_method:
                after_method(e, *args, **kwargs)
            raise e

    return wrapper


def encode_resource_id(resource_id: str) -> str:
    """URL encode a resource ID for use in API paths.

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
    def from_dict(cls: type, data: dict) -> Any:
        """Create an instance from a dictionary."""
        ...


@runtime_checkable
class HasToDict(Protocol):
    """Protocol for classes that have a to_dict method."""

    def to_dict(self) -> dict:
        """Convert instance to dictionary."""
        ...


def _flatten_asset_info(data: dict) -> dict:
    """Flatten assetInfo structure to top level for standard field mapping.

    Args:
        data: Dictionary that may contain nested assetInfo structure.

    Returns:
        Dictionary with path extracted from instanceId (or assetPath as fallback).
    """
    if isinstance(data, dict) and "assetInfo" in data:
        asset_info = data.get("assetInfo", {})
        if isinstance(asset_info, dict):
            # Priority: instanceId > assetPath for the path field
            if "instanceId" in asset_info:
                data["path"] = asset_info.get("instanceId")
            elif "assetPath" in asset_info:
                data["path"] = asset_info.get("assetPath")
    return data


class BaseMixin:
    """Base mixin with meta capabilities for resource operations."""

    def __init_subclass__(cls: type, **kwargs: Any) -> None:
        """Initialize subclass with validation."""
        super().__init_subclass__(**kwargs)
        if cls.__name__.endswith("Mixin"):
            return
        if BaseMixin in cls.__mro__ and not issubclass(cls, BaseResource):
            raise TypeError(f"{cls.__name__} must inherit from BaseResource to use resource mixins")


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

    context: Any = field(repr=False, compare=False, metadata=config(exclude=lambda x: True), init=False)
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

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None  # Full path e.g. "openai/whisper-large/groq"

    def _ensure_valid_state(self) -> None:
        """Ensure the resource is in a valid state for operations.

        Raises:
            ValidationError: If the resource is not in a valid state
        """
        # Check if resource has been deleted
        resource_name = self.__class__.__name__

        if self.is_deleted:
            raise ValidationError(f"{resource_name} has been deleted and cannot be used for operations.")

        if not self.id:
            if hasattr(self, "_saved_state") and self._saved_state is None:
                raise ValidationError(
                    f"{resource_name} has not been saved yet. Call .save() first to create the resource."
                )
            else:
                raise ValidationError(f"{resource_name} has been deleted or is invalid. {resource_name} ID is missing.")

    def _get_serializable_state(self) -> dict:
        """Get the current state of the resource as a serializable dictionary.

        Returns:
            dict: The serializable state of the resource
        """
        # All BaseResource subclasses inherit to_dict() from @dataclass_json
        # Internal fields are already excluded via metadata=config(
        #     exclude=lambda x: True
        # )
        return self.to_dict()

    def _is_state_changed(self) -> bool:
        """Check if the current state differs from the saved state.

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
        """Check if the resource has been modified since last save.

        Returns:
            bool: True if the resource has been modified, False otherwise
        """
        return self._is_state_changed()

    @property
    def is_deleted(self) -> bool:
        """Check if the resource has been deleted.

        Returns:
            bool: True if the resource has been deleted, False otherwise
        """
        return getattr(self, "_deleted", False)

    def _update_saved_state(self) -> None:
        """Update the saved state to match the current state.

        Called after successful save operations.
        """
        self._saved_state = self._get_serializable_state()

    # Optional hook methods - only implement what you need
    def before_save(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Optional callback called before the resource is saved.

        Override this method to add custom logic before saving.

        Args:
            *args: Positional arguments passed to the save operation
            **kwargs: Keyword arguments passed to the save operation

        Returns:
            Optional[dict]: If not None, this result will be returned early,
                          bypassing the actual save operation. If None, the
                          save operation will proceed normally.
        """
        return None

    def after_save(self, result: Union[dict, Exception], *args: Any, **kwargs: Any) -> Optional[dict]:
        """Optional callback called after the resource is saved.

        Override this method to add custom logic after saving.

        Args:
            result: The result from the save operation (dict on success,
                   Exception on failure)
            *args: Positional arguments that were passed to the save operation
            **kwargs: Keyword arguments that were passed to the save operation

        Returns:
            Optional[dict]: If not None, this result will be returned instead
                          of the original result. If None, the original result
                          will be returned.
        """
        return None

    def build_save_payload(self, **kwargs: Any) -> dict:
        """Build the payload for the save action."""
        if isinstance(self, HasToDict):
            return self.to_dict()
        return {}

    def _create(self, resource_path: str, payload: dict) -> None:
        """Create the resource."""
        result = self.context.client.request("post", f"{resource_path}", json=payload)
        # Flatten assetInfo structure before deserialization
        result = _flatten_asset_info(dict(result)) if isinstance(result, dict) else result
        # Update the object from the full response
        if isinstance(self, HasFromDict):
            updated = self.from_dict(result)
            # Update all fields from the response
            for field_name in self.__dataclass_fields__:
                if hasattr(updated, field_name):
                    setattr(self, field_name, getattr(updated, field_name))
        else:
            # Fallback: just set the ID
            self.id = result["id"]

    def _update(self, resource_path: str, payload: dict) -> None:
        """Update the resource."""
        self.context.client.request("put", f"{resource_path}/{self.encoded_id}", json=payload)

    @with_hooks
    def save(self, *args: Any, **kwargs: Any) -> "BaseResource":
        """Save the resource with attribute shortcuts.

        This generic implementation provides consistent save behavior across all resources:
        - Supports attribute shortcuts: resource.save(name="new_name", description="...")
        - Lets the backend handle validation (name uniqueness, ID existence, etc.)
        - If the resource has an ID, it will be updated, otherwise it will be created.

        Args:
            *args: Positional arguments (not used, but kept for compatibility)
            id: Optional[str] - Set resource ID before saving
            name: Optional[str] - Set resource name before saving
            description: Optional[str] - Set resource description before saving
            **kwargs: Other attributes to set before saving

        Returns:
            BaseResource: The saved resource instance

        Raises:
            Backend validation errors as appropriate
        """
        resource_path = kwargs.pop("resource_path", self.RESOURCE_PATH)

        # Set attributes from kwargs before saving
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        payload = self.build_save_payload(**kwargs)

        # Execute the save operation
        if self.id:
            self._update(resource_path, payload)
        else:
            self._create(resource_path, payload)

        self._update_saved_state()

        return self

    @with_hooks
    def clone(self, **kwargs: Any) -> "BaseResource":
        """Clone the resource and return a copy with id=None.

        This generic implementation provides consistent clone behavior across all resources:
        - Creates deep copy of the resource
        - Resets id=None and _saved_state=None
        - Supports attribute shortcuts: resource.clone(name="new_name", version="2.0")
        - Uses hook system for subclass-specific logic (status handling, etc.)

        Args:
            name: Optional[str] - Set name on cloned resource
            description: Optional[str] - Set description on cloned resource
            **kwargs: Other attributes to set on cloned resource

        Returns:
            BaseResource: New resource instance with id=None
        """
        # Create deep copy of the resource
        cloned = deepcopy(self)

        # Reset ID and saved state for new asset
        cloned.id = None
        cloned._saved_state = None

        # Set attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(cloned, key):
                setattr(cloned, key, value)

        return cloned

    def _action(
        self,
        method: Optional[str] = None,
        action_paths: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Internal method to perform actions on the resource.

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
        assert getattr(self, "RESOURCE_PATH"), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        self._ensure_valid_state()

        method = method or "GET"
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        if action_paths:
            path += "/".join(["", *action_paths])

        return self.context.client.request(method, path, **kwargs)

    def __repr__(self) -> str:
        """Return a string representation using path > id priority."""
        if self.path:
            return f"{self.__class__.__name__}(path={self.path})"
        else:
            return f"{self.__class__.__name__}(id={self.id}, name={self.name})"

    def __str__(self) -> str:
        """Return string representation of the resource."""
        return self.__repr__()

    @property
    def encoded_id(self) -> str:
        """Get the URL-encoded version of the resource ID.

        Returns:
            The URL-encoded resource ID, or empty string if no ID exists
        """
        self._ensure_valid_state()

        return encode_resource_id(self.id)


class BaseParams(TypedDict):
    """Base class for parameters that include API key and resource path.

    Attributes:
        api_key: str: The API key for authentication.
        resource_path: str: Custom resource path for actions (optional).
    """

    api_key: NotRequired[str]
    resource_path: NotRequired[str]


class BaseSearchParams(BaseParams):
    """Base class for all search parameters.

    Attributes:
        query: str: The query string.
        ownership: Tuple[OwnershipType, List[OwnershipType]]: The ownership
                  type.
        sort_by: SortBy: The attribute to sort by.
        sort_order: SortOrder: The order to sort by.
        page_number: int: The page number.
        page_size: int: The page size.
        resource_path: str: Optional custom resource path to override
                          RESOURCE_PATH.
        paginate_items_key: str: Optional key name for items in paginated
                                response (overrides PAGINATE_ITEMS_KEY).
    """

    query: NotRequired[str]
    ownership: NotRequired[Tuple[OwnershipType, List[OwnershipType]]]
    sort_by: NotRequired[SortBy]
    sort_order: NotRequired[SortOrder]
    page_number: NotRequired[int]
    page_size: NotRequired[int]
    resource_path: NotRequired[str]
    paginate_items_key: NotRequired[str]


class BaseGetParams(BaseParams):
    """Base class for all get parameters.

    Attributes:
        id: str: The resource ID.
        host: str: The host URL for the request (optional).
    """

    host: NotRequired[str]


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
    """Abstract base class for running results.

    This class provides a minimal interface that concrete result classes
    should implement. Subclasses are responsible for defining their own
    fields and handling their specific data structures.
    """

    # Abstract interface - subclasses must implement these
    status: str
    completed: bool


@dataclass_json
@dataclass(repr=False)
class Result(BaseResult):
    """Default implementation of running results with common fields."""

    status: str
    completed: bool
    error_message: Optional[str] = field(default=None, metadata=config(field_name="errorMessage"))
    url: Optional[str] = None
    result: Optional[Any] = None
    supplier_error: Optional[str] = field(default=None, metadata=config(field_name="supplierError"))
    data: Optional[Any] = None
    _raw_data: Optional[dict] = field(default=None, repr=False)

    def __getattr__(self, name: str) -> Any:
        """Allow access to any field from the raw response data."""
        if hasattr(self, "_raw_data") and self._raw_data and name in self._raw_data:
            return self._raw_data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __repr__(self) -> str:
        """Return a formatted string representation with truncated data."""
        # Configure reprlib to truncate long strings
        repr_obj = reprlib.Repr()
        repr_obj.maxstring = 200  # Truncate strings longer than 200 chars
        repr_obj.maxother = 200  # Truncate other objects longer than 200 chars

        def truncate_repr(value: Any) -> str:
            """Truncate representation of a value."""
            if value is None:
                return "None"
            repr_str = repr_obj.repr(value)
            # If it's still too long, truncate further
            if len(repr_str) > 200:
                return repr_str[:197] + "..."
            return repr_str

        # Build the representation
        field_parts = []

        # Always show status and completed
        field_parts.append(f"status={repr(self.status)}")
        field_parts.append(f"completed={repr(self.completed)}")

        # Show error_message if present
        if self.error_message is not None:
            field_parts.append(f"error_message={repr(self.error_message)}")

        # Show supplier_error if present
        if self.supplier_error is not None:
            field_parts.append(f"supplier_error={repr(self.supplier_error)}")

        # Show url if present
        if self.url is not None:
            field_parts.append(f"url={repr(self.url)}")

        # Show result only if it's informative (not None and not empty)
        if self.result is not None:
            # Check if result is "informative" - not empty string, empty dict, empty list, etc.
            is_informative = True
            if isinstance(self.result, str) and not self.result.strip():
                is_informative = False
            elif isinstance(self.result, (dict, list)) and len(self.result) == 0:
                is_informative = False

            if is_informative:
                field_parts.append(f"result={truncate_repr(self.result)}")

        # Always show data, but truncated
        if self.data is not None:
            data_repr = truncate_repr(self.data)
            field_parts.append(f"data={data_repr}")
        else:
            field_parts.append("data=None")

        # Format as multi-line with indentation
        fields_str = ",\n  ".join(field_parts)
        return f"{self.__class__.__name__}(\n  {fields_str}\n)"


@dataclass_json
@dataclass
class DeleteResult(Result):
    """Result for delete operations."""

    deleted_id: Optional[str] = field(default=None, metadata=config(field_name="deletedId"))


# Standardized type variables with proper bounds
ResourceT = TypeVar("ResourceT", bound=BaseResource)
SearchParamsT = TypeVar("SearchParamsT", bound=BaseSearchParams)
GetParamsT = TypeVar("GetParamsT", bound=BaseGetParams)
DeleteParamsT = TypeVar("DeleteParamsT", bound=BaseDeleteParams)
RunParamsT = TypeVar("RunParamsT", bound=BaseRunParams)
ResultT = TypeVar("ResultT", bound=BaseResult)
DeleteResultT = TypeVar("DeleteResultT", bound=DeleteResult)


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

    def __init__(self, results: List[ResourceT], page_number: int, page_total: int, total: int):
        """Initialize a Page instance.

        Args:
            results: List of resource instances in this page
            page_number: Current page number (0-indexed)
            page_total: Total number of pages
            total: Total number of resources across all pages
        """
        self.results = results
        self.page_number = page_number
        self.page_total = page_total
        self.total = total

    def __repr__(self) -> str:
        """Return JSON representation of the page."""
        import json

        return json.dumps(self.__dict__, indent=2, default=str)

    def __getitem__(self, key: str):
        """Allow dictionary-like access to page attributes."""
        return getattr(self, key)


class SearchResourceMixin(BaseMixin, Generic[SearchParamsT, ResourceT]):
    """Mixin for listing resources with pagination and search functionality.

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
    PAGINATE_ITEMS_KEY: str = "results"  # Default to match backend
    PAGINATE_TOTAL_KEY: str = "total"
    PAGINATE_PAGE_TOTAL_KEY: str = "pageTotal"
    PAGINATE_PAGE_NUMBER_KEY: str = "pageNumber"
    PAGINATE_DEFAULT_PAGE_NUMBER: int = 0
    PAGINATE_DEFAULT_PAGE_SIZE: int = 20

    @classmethod
    def _get_context_and_path(cls: type, **kwargs: Any) -> Tuple["Aixplain", str, Optional[str]]:
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
    def _build_resources(cls: type, items: List[dict], context: "Aixplain") -> List[ResourceT]:
        """Build resource instances from response items."""
        resources = []
        for item in items:
            # Flatten assetInfo structure before deserialization
            item = _flatten_asset_info(dict(item)) if isinstance(item, dict) else item
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
    def _populate_base_filters(cls: type, params: BaseSearchParams) -> dict:
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

    @classmethod
    def search(cls: type, **kwargs: Unpack[SearchParamsT]) -> Page[ResourceT]:
        """Search resources across the first n pages with optional filtering.

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
        paginate_path = cls._populate_path(resource_path, custom_path)
        params_dict = dict(kwargs)
        filters = cls._populate_filters(params_dict)

        # Make request
        paginate_method = getattr(cls, "PAGINATE_METHOD", "post")
        response = context.client.request(paginate_method, paginate_path, json=filters)

        return cls._build_page(response, context, **kwargs)

    @classmethod
    def _build_page(cls: type, response: "Any", context: "Aixplain", **kwargs: Any) -> Page[ResourceT]:
        """Build a page of resources from the response.

        Accepts either a requests.Response or already-decoded dict/list.
        """
        if hasattr(response, "json"):
            json_data = response.json()
        else:
            json_data = response

        items = json_data
        # Check for override in kwargs first, then fall back to class attribute
        paginate_items_key = kwargs.get("paginate_items_key") or getattr(cls, "PAGINATE_ITEMS_KEY", "items")
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
        results = cls._build_resources(items, context)

        return Page(
            results=results,
            total=total,
            page_number=kwargs["page_number"],
            page_total=page_total,
        )

    @classmethod
    def _populate_path(cls, path: str, custom_path: Optional[str] = None) -> str:
        """Populate the path for pagination.

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
        """Populate the filters for pagination.

        Args:
            params: dict: The parameters to populate.

        Returns:
            dict: The populated filters.
        """
        # Convert to BaseSearchParams for type safety
        list_params = BaseSearchParams(**params)
        filters = cls._populate_base_filters(list_params)

        # Add pagination-specific filters
        if params.get("page_number") is not None:
            filters["pageNumber"] = params["page_number"]

        if params.get("page_size") is not None:
            filters["pageSize"] = params["page_size"]

        return filters


class GetResourceMixin(BaseMixin, Generic[GetParamsT, ResourceT]):
    """Mixin for getting a resource."""

    @classmethod
    def get(cls: type, id: Any, host: Optional[str] = None, **kwargs: Unpack[GetParamsT]) -> ResourceT:
        """Retrieve a single resource by its ID (or other get parameters).

        Args:
            id: Any: The ID of the resource to get.
            host: str, optional: The host parameter to pass to the backend (default: None).
            kwargs: Get parameters to pass to the request.

        Returns:
            BaseResource: Instance of the BaseResource class.

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass.
        """
        resource_path = kwargs.pop("resource_path", None) or getattr(cls, "RESOURCE_PATH", "")
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for resource operations")

        encoded_id = encode_resource_id(id)
        path = f"{resource_path}/{encoded_id}"

        # Add host parameter as query parameter if provided
        if host is not None:
            kwargs["params"] = {"host": host}

        obj = context.client.get(path, **kwargs)

        # Flatten assetInfo structure before deserialization
        obj = _flatten_asset_info(dict(obj)) if isinstance(obj, dict) else obj

        if isinstance(cls, HasFromDict):
            instance = cls.from_dict(obj)
        else:
            instance = cls(**obj)  # type: ignore[call-arg]
        setattr(instance, "context", context)
        # Set the saved state to match the loaded state
        instance._update_saved_state()
        return instance


class DeleteResourceMixin(BaseMixin, Generic[DeleteParamsT, DeleteResultT]):
    """Mixin for deleting a resource."""

    DELETE_RESPONSE_CLASS: type = DeleteResult  # Default response class

    def build_delete_payload(self, **kwargs: Unpack[DeleteParamsT]) -> dict:
        """Build the payload for the delete action.

        This method can be overridden by subclasses to provide custom payload
        construction for delete operations.
        """
        # Default behavior - no payload for simple delete operations
        return kwargs

    def build_delete_url(self, **kwargs: Unpack[DeleteParamsT]) -> str:
        """Build the URL for the delete action.

        This method can be overridden by subclasses to provide custom URL
        construction. The default implementation uses the resource path with
        the resource ID.

        Returns:
            str: The URL to use for the delete action
        """
        assert getattr(self, "RESOURCE_PATH"), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        self._ensure_valid_state()

        resource_path = kwargs.pop("resource_path", None) or getattr(self, "RESOURCE_PATH", "")
        return f"{resource_path}/{self.encoded_id}"

    def handle_delete_response(self, response: Any, **kwargs: Unpack[DeleteParamsT]) -> DeleteResultT:
        """Handle the response from a delete request.

        This method can be overridden by subclasses to handle different
        response patterns. The default implementation creates a simple
        success response.

        Args:
            response: The raw response from the API (may be Response object or dict)
            **kwargs: Delete parameters

        Returns:
            DeleteResult instance from the configured response class
        """
        # Create a success response with basic information
        response_class = getattr(self, "DELETE_RESPONSE_CLASS", DeleteResult)

        # Store the resource info before marking as deleted
        deleted_id = self.id

        # Mark the resource as deleted
        self.mark_as_deleted()

        # Build response data manually since delete endpoints don't return JSON
        response_data = {
            "status": "SUCCESS",
            "completed": True,
            "deleted_id": deleted_id,
        }

        # Create the result object directly instead of using from_dict
        result = response_class(**response_data)
        result._raw_data = response  # Store raw response separately

        return result

    # Optional hook methods - only implement what you need
    def before_delete(self, *args: Any, **kwargs: Unpack[DeleteParamsT]) -> Optional[DeleteResultT]:
        """Optional callback called before the resource is deleted.

        Override this method to add custom logic before deleting.

        Args:
            *args: Positional arguments passed to the delete operation
            **kwargs: Keyword arguments passed to the delete operation

        Returns:
            Optional[DeleteResultT]: If not None, this result will be returned early,
                                   bypassing the actual delete operation. If None, the
                                   delete operation will proceed normally.
        """
        return None

    def after_delete(
        self,
        result: Union[DeleteResultT, Exception],
        *args: Any,
        **kwargs: Unpack[DeleteParamsT],
    ) -> Optional[DeleteResultT]:
        """Optional callback called after the resource is deleted.

        Override this method to add custom logic after deleting.

        Args:
            result: The result from the delete operation (DeleteResultT on success,
                   Exception on failure)
            *args: Positional arguments that were passed to the delete operation
            **kwargs: Keyword arguments that were passed to the delete operation

        Returns:
            Optional[DeleteResultT]: If not None, this result will be returned instead
                                   of the original result. If None, the original result
                                   will be returned.
        """
        return None

    @with_hooks
    def delete(self, *args: Any, **kwargs: Unpack[DeleteParamsT]) -> DeleteResultT:
        """Delete a resource.

        Returns:
            DeleteResultT: The result of the delete operation
        """
        self._ensure_valid_state()

        # Build the delete URL
        delete_url = self.build_delete_url(**kwargs)

        # Execute the delete operation (delete endpoints don't return JSON)
        response = self.context.client.request_raw("delete", delete_url, **kwargs)

        # Handle the response using the extensible response handler
        return self.handle_delete_response(response, **kwargs)

    def mark_as_deleted(self) -> None:
        """Mark the resource as deleted by clearing its ID and setting deletion flag."""
        self.id = None
        self._deleted = True


class RunnableResourceMixin(BaseMixin, Generic[RunParamsT, ResultT]):
    """Mixin for runnable resources."""

    RUN_ACTION_PATH: str = "run"
    RESPONSE_CLASS: type = Result  # Default response class

    def build_run_payload(self, **kwargs: Unpack[RunParamsT]) -> dict:
        """Build the payload for the run action.

        This method automatically handles dataclass serialization if the run
        parameters are dataclasses with @dataclass_json decorator.
        """
        # Default behavior for TypedDict or other parameter types
        return kwargs

    def build_run_url(self, **kwargs: Unpack[RunParamsT]) -> str:
        """Build the URL for the run action.

        This method can be overridden by subclasses to provide custom URL
        construction. The default implementation uses the resource path with
        the run action.

        Returns:
            str: The URL to use for the run action
        """
        assert getattr(self, "RESOURCE_PATH"), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        self._ensure_valid_state()

        run_action_path = getattr(self, "RUN_ACTION_PATH", None)
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}"
        if run_action_path:
            path += f"/{run_action_path}"

        return path

    def handle_run_response(self, response: dict, **kwargs: Unpack[RunParamsT]) -> ResultT:
        """Handle the response from a run request.

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
        if response.get("data") and isinstance(response["data"], str) and response["data"].startswith("http"):
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
            # Direct response case - pass the entire response to let dataclass_json handle field mapping
            # Check for failed status and raise appropriate error
            status = response.get("status", "IN_PROGRESS")
            if status == "FAILED":
                raise create_operation_failed_error(response)

            response_class = getattr(self, "RESPONSE_CLASS", Result)

            return response_class.from_dict(response)

    # Optional hook methods - only implement what you need
    def before_run(self, *args: Any, **kwargs: Unpack[RunParamsT]) -> Optional[ResultT]:
        """Optional callback called before the resource is run.

        Override this method to add custom logic before running.

        Args:
            *args: Positional arguments passed to the run operation
            **kwargs: Keyword arguments passed to the run operation

        Returns:
            Optional[ResultT]: If not None, this result will be returned early,
                             bypassing the actual run operation. If None, the
                             run operation will proceed normally.
        """
        return None

    def after_run(
        self,
        result: Union[ResultT, Exception],
        *args: Any,
        **kwargs: Unpack[RunParamsT],
    ) -> Optional[ResultT]:
        """Optional callback called after the resource is run.

        Override this method to add custom logic after running.

        Args:
            result: The result from the run operation (ResultT on success,
                   Exception on failure)
            *args: Positional arguments that were passed to the run operation
            **kwargs: Keyword arguments that were passed to the run operation

        Returns:
            Optional[ResultT]: If not None, this result will be returned instead
                             of the original result. If None, the original result
                             will be returned.
        """
        return None

    def run(self, *args: Any, **kwargs: Unpack[RunParamsT]) -> ResultT:
        """Run the resource synchronously with automatic polling.

        Args:
            *args: Positional arguments (converted to kwargs by subclasses)
            **kwargs: Run parameters including timeout and wait_time

        Returns:
            Response instance from the configured response class

        Note:
            The before_run hook is called via run_async(), not here, to avoid
            double invocation since run() delegates to run_async().
        """
        # Start async execution (before_run hook is called inside run_async)
        result = self.run_async(**kwargs)

        # Check if we need to poll
        if result.url and not result.completed:
            result = self.sync_poll(result.url, **kwargs)

        # Call after_run hook for synchronous completion
        after_method = getattr(self, "after_run", None)
        if after_method:
            custom_result = after_method(result, **kwargs)
            if custom_result is not None:
                return custom_result

        return result

    def run_async(self, **kwargs: Unpack[RunParamsT]) -> ResultT:
        """Run the resource asynchronously.

        Args:
            **kwargs: Run parameters specific to the resource type

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        # Call before_run hook to allow subclasses to prepare (e.g., auto-save drafts)
        before_method = getattr(self, "before_run", None)
        if before_method:
            early_result = before_method(**kwargs)
            if early_result is not None:
                return early_result

        self._ensure_valid_state()

        payload = self.build_run_payload(**kwargs)

        # Build the run URL using the extensible method
        run_url = self.build_run_url(**kwargs)

        response = self.context.client.request("post", run_url, json=payload)

        # Use the extensible response handler
        return self.handle_run_response(response, **kwargs)

    def poll(self, poll_url: str) -> ResultT:
        """Poll for the result of an asynchronous operation.

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

        # Handle polling response - use camelCase keys (what backend sends)
        # dataclass_json with config(field_name=...) handles mapping to snake_case
        filtered_response = {
            "status": response.get("status", "IN_PROGRESS"),
            "completed": response.get("completed", False),
            "errorMessage": response.get("errorMessage"),
            "url": response.get("url"),
            "result": response.get("result"),
            "supplierError": response.get("supplierError"),
            "data": response.get("data") or {},
            "sessionId": response.get("sessionId"),
            "usedCredits": response.get("usedCredits", 0.0),
            "runTime": response.get("runTime", 0.0),
            "requestId": response.get("requestId"),
        }
        status = response.get("status", "IN_PROGRESS")

        # Failure handling
        if status == "FAILED":
            raise create_operation_failed_error(response)

        response_class = getattr(self, "RESPONSE_CLASS", Result)

        try:
            result = response_class.from_dict(filtered_response)
        except Exception:
            raise

        # Attach raw response
        result._raw_data = response
        return result

    def on_poll(self, response: ResultT, **kwargs: Unpack[RunParamsT]) -> None:
        """Hook called after each successful poll with the poll response.

        Override this method in subclasses to handle poll responses,
        such as displaying progress updates or logging status changes.

        Args:
            response: The response from the poll operation
            **kwargs: Run parameters including show_progress, timeout, wait_time, etc.
        """
        pass  # Default implementation does nothing

    def sync_poll(self, poll_url: str, **kwargs: Unpack[RunParamsT]) -> ResultT:
        """Keeps polling until an asynchronous operation is complete.

        Args:
            poll_url: URL to poll for results
            name: Name/ID of the process
            **kwargs: Run parameters including timeout, wait_time, and show_progress

        Returns:
            Response instance from the configured RESPONSE_CLASS
        """
        import time

        timeout = kwargs.get("timeout", 300)
        wait_time = kwargs.get("wait_time", 0.5)
        show_progress = kwargs.get("show_progress", False)

        start_time = time.time()
        wait_time = max(wait_time, 0.2)  # Minimum wait time

        while (time.time() - start_time) < timeout:
            try:
                result = self.poll(poll_url)

                # Call the hook with the poll response
                self.on_poll(result, **kwargs)

                if result.completed:
                    if show_progress:
                        elapsed_time = time.time() - start_time
                        logger.info(f"Operation completed successfully ({elapsed_time:.1f}s total)")
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

        if show_progress:
            logger.error(f"Operation timeout - No response after {timeout}s")
        raise TimeoutError(f"Operation timed out after {timeout} seconds")
