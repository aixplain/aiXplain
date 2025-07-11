import requests
import pprint
import logging
from typing import (
    List,
    Tuple,
    TypedDict,
    TypeVar,
    Generic,
    Type,
    Any,
    Union,
    Optional,
    Dict,
    TYPE_CHECKING,
)
from typing_extensions import Unpack, NotRequired


from .enums import OwnershipType, SortBy, SortOrder, ResponseStatus

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

    @classmethod
    def _get_api_key(cls, kwargs: dict) -> str:
        """
        Get API key from kwargs or context, with fallback to config for
        backwards compatibility.
        
        Args:
            kwargs: dict: Keyword arguments passed to the method.
            
        Returns:
            str: API key from kwargs, context, or config.TEAM_API_KEY as
                 fallback.
        """
        api_key = (kwargs.get("api_key") or
                   getattr(cls.context, "api_key", None))
        
        if api_key is None:
            import aixplain.utils.config as config
            api_key = config.TEAM_API_KEY
            
        return api_key

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

        If the resource has an ID, it will be updated, otherwise it will be
        created.
        """
        if hasattr(self, "id") and self.id:
            self._action("put", [self.id], **self._obj)
        else:
            self._action("post", **self._obj)

    def _action(self, method: str = None, action_paths: List[str] = None,
                **kwargs) -> requests.Response:
        """
        Internal method to perform actions on the resource.

        Args:
            method: str, optional: HTTP method to use (default is 'GET').
            action_paths: List[str], optional: Optional list of action paths
                to append to the URL.
            kwargs: dict: Additional keyword arguments to pass to the request.

        Returns:
            requests.Response: Response from the client's request as
                requests.Response

        Raises:
            ValueError: If 'RESOURCE_PATH' is not defined by the subclass or
                'id' attribute is missing.
        """

        assert getattr(self, "RESOURCE_PATH"), (
            "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"
        )

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


class BareCreateParams(BaseCreateParams):
    """Default implementation of create parameters."""

    pass


class BareListParams(BaseListParams):
    """Default implementation of list parameters."""

    pass


class BareGetParams(BaseGetParams):
    """Default implementation of get parameters."""

    pass


class BaseDeleteParams(BaseApiKeyParams):
    """Base class for all delete parameters."""

    pass


class BaseRunParams(BaseApiKeyParams):
    """Base class for all run parameters.

    Attributes:
        data: Input data for the resource
        name: Name/ID for the process
    """

    data: Union[str, Dict[str, Any]]
    name: NotRequired[str]


class BareRunParams(BaseRunParams):
    """Default implementation of run parameters."""

    pass


R = TypeVar("R", bound=BaseResource)
L = TypeVar("L", bound=BaseListParams)
C = TypeVar("C", bound=BaseCreateParams)
G = TypeVar("G", bound=BaseGetParams)
D = TypeVar("D", bound=BaseDeleteParams)
RU = TypeVar("RU", bound=BaseRunParams)


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

    def __init__(self, results: List[R], page_number: int, page_total: int,
                 total: int):
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

        assert getattr(cls, "RESOURCE_PATH"), (
            "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"
        )

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
    def _build_page(cls, response: requests.Response,
                    **kwargs: Unpack[L]) -> Page[R]:
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
        assert getattr(cls, "RESOURCE_PATH"), (
            "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"
        )

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
        assert getattr(cls, "RESOURCE_PATH"), (
            "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"
        )

        obj = cls.context.client.request("post", cls.RESOURCE_PATH, *args,
                                         **kwargs)
        return cls(obj)


class DeleteResourceMixin(Generic[D, R]):
    """Mixin for deleting a resource."""

    @classmethod
    def delete(cls: Type[R], id: Any, **kwargs: Unpack[D]) -> R:
        """
        Delete a resource.
        """
        assert getattr(cls, "RESOURCE_PATH"), (
            "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"
        )

        path = f"{cls.RESOURCE_PATH}/{id}"
        cls.context.client.request("delete", path, **kwargs)


class RunnableResponse:
    """Response class for runnable resources."""
    
    def __init__(self, response_data: Dict[str, Any]):
        # Core response fields
        self.status: Optional[ResponseStatus] = self._parse_status(
            response_data.get("status")
        )
        self.data: Any = response_data.get("data", "")
        self.details: Dict[str, Any] = response_data.get("details", {})
        self.completed: bool = response_data.get("completed", False)
        self.error_message: str = response_data.get("error_message", "")
        
        # Resource usage fields
        self.used_credits: float = response_data.get("usedCredits", 0)
        self.run_time: float = response_data.get("runTime", 0)
        self.usage: Optional[Dict[str, Any]] = response_data.get("usage")
        
        # Async operation fields
        self.url: Optional[str] = response_data.get("url")
        self.error_code: Optional[str] = response_data.get("error_code")
        
        # Store additional fields for extensibility
        self._known_fields = {
            "status", "data", "details", "completed", "error_message",
            "usedCredits", "runTime", "usage", "url", "error_code"
        }
        self._additional_fields = {
            k: v for k, v in response_data.items() 
            if k not in self._known_fields
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
            raise KeyError(f"Key '{key}' not found in RunnableResponse.")

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
        return f"RunnableResponse({', '.join(fields)})"


class RunnableMixin(Generic[RU]):
    """Mixin for runnable resources like models, pipelines, and agents.
    
    This mixin provides execution capabilities for resources that can be run
    asynchronously or synchronously. It follows the same patterns as the
    legacy Model module while using modern v2 architecture and allows
    subclasses to define their own parameter shapes.
    
    Type Parameters:
        RU: Type for run parameters (extends BaseRunParams)
    
    Attributes:
        RUN_ACTION_PATH: str: The action path for running the resource.
            Defaults to "run".
    """
    
    RUN_ACTION_PATH = "run"
    
    def run(self, timeout: float = 300, wait_time: float = 0.5, 
            **kwargs: Unpack[RU]) -> RunnableResponse:
        """
        Run the resource synchronously with automatic polling.
        
        Args:
            timeout: Maximum time to wait for completion
            wait_time: Time between polling attempts
            **kwargs: Run parameters specific to the resource type
            
        Returns:
            RunnableResponse: The response from the resource
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
                timeout=timeout, 
                wait_time=wait_time
            )
        
        return async_response

    def run_async(self, **kwargs: Unpack[RU]) -> RunnableResponse:
        """
        Run the resource asynchronously.
        
        Args:
            **kwargs: Run parameters specific to the resource type
            
        Returns:
            RunnableResponse: Response containing polling URL or immediate
                result
        """
        name = kwargs.get("name", "process")
        
        logging.debug(f"Running {self.__class__.__name__} async: {name}")
        
        # Build the payload using the resource-specific implementation
        payload = self._build_run_payload(**kwargs)
        
        try:
            # Use _action to make the API call
            response = self._action(
                "post", [self.RUN_ACTION_PATH], json=payload
            )
            
            # Parse response
            response_data = response.json()
            return RunnableResponse(response_data)
            
        except Exception as e:
            logging.error(f"Error in async run for {name}: {e}")
            return RunnableResponse({
                "status": ResponseStatus.FAILED.value,
                "completed": True,
                "error_message": str(e)
            })

    def poll(self, poll_url: str, name: str = "process") -> RunnableResponse:
        """
        Poll for the result of an asynchronous operation.
        
        Args:
            poll_url: URL to poll for results
            name: Name/ID of the process
            
        Returns:
            RunnableResponse: Current status and results
        """
        logging.debug(f"Polling {self.__class__.__name__} for {name}")
        
        # Use the existing client infrastructure instead of manual requests
        try:
            # Extract path from full URL if needed
            if poll_url.startswith("http"):
                # For external polling URLs, we need to use direct requests
                return self._poll_external_url(poll_url, name)
            else:
                # Internal polling through the client
                response = self.context.client.get(poll_url)
                response_data = response.json()
        except Exception as e:
            logging.error(f"Error polling for {name}: {e}")
            return RunnableResponse({
                "status": ResponseStatus.FAILED.value,
                "completed": False,
                "error_message": str(e)
            })
        
        # Determine status based on completion
        if response_data.get("completed", False):
            if ("error_message" in response_data or
                    "supplierError" in response_data):
                status = ResponseStatus.FAILED
            else:
                status = ResponseStatus.SUCCESS
        else:
            status = ResponseStatus.IN_PROGRESS
            
        response_data.setdefault("status", status.value)
        
        return RunnableResponse(response_data)

    def sync_poll(
        self,
        poll_url: str,
        name: str = "process",
        wait_time: float = 0.5,
        timeout: float = 300,
    ) -> RunnableResponse:
        """
        Keeps polling until an asynchronous operation is complete.
        
        Args:
            poll_url: URL to poll for results
            name: Name/ID of the process
            wait_time: Time between polling attempts (minimum 0.2s)
            timeout: Maximum time to wait for completion
            
        Returns:
            RunnableResponse: Final result when complete or timeout
        """
        import time
        
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
        return RunnableResponse({
            "status": ResponseStatus.FAILED.value,
            "completed": False,
            "error_message": f"Timeout after {timeout} seconds"
        })

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
            k: v for k, v in kwargs.items() 
            if k not in core_fields and v is not None
        }
        
        if additional_params:
            payload["parameters"] = additional_params
            
        return payload

    def _poll_external_url(self, poll_url: str, name: str) -> RunnableResponse:
        """
        Poll an external URL (for backward compatibility).
        
        Args:
            poll_url: External URL to poll
            name: Process name
            
        Returns:
            RunnableResponse: The polling result
        """
        import requests
        
        # Get API key using the existing method
        api_key = getattr(self.context, "api_key", None)
        if not api_key:
            import aixplain.utils.config as config
            api_key = config.TEAM_API_KEY
            
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(poll_url, headers=headers)
            response.raise_for_status()
            
            response_data = response.json()
            
            # Determine status based on completion
            if response_data.get("completed", False):
                if ("error_message" in response_data or
                        "supplierError" in response_data):
                    status = ResponseStatus.FAILED
                else:
                    status = ResponseStatus.SUCCESS
            else:
                status = ResponseStatus.IN_PROGRESS
                
            response_data.setdefault("status", status.value)
            
            return RunnableResponse(response_data)
            
        except Exception as e:
            return RunnableResponse({
                "status": ResponseStatus.FAILED.value,
                "completed": False,
                "error_message": str(e)
            })


