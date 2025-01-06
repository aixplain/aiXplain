import os
import requests
from typing import (
    Optional,
    Union,
    List,
    Tuple,
    TypedDict,
    TypeVar,
    Generic,
    Type,
    Any,
)

from .client import AixplainClient
from .enums import (
    Function,
    Supplier,
    OwnershipType,
    SortBy,
    SortOrder,
    Language,
    DataType,
)


class Aixplain:
    """Main class for the Aixplain API."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton pattern for the Aixplain class.
        Otherwise, the environment variables will be overwritten in multiple instances.

        TODO: This should be removed once the factory classes are removed.
        """
        if not cls._instance:
            cls._instance = super(Aixplain, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        api_key: str,
        backend_url: str = "https://dev-platform-api.aixplain.com",
        pipeline_url: str = "https://dev-platform-api.aixplain.com/assets/pipeline/execution/run",
        model_url: str = "https://dev-models.aixplain.com/api/v1/execute",
    ):
        """Initialize the Aixplain class.

        :param api_key: The API key for the Aixplain API.
        :param backend_url: The URL for the backend.
        :param pipeline_url: The URL for the pipeline.
        :param model_url: The URL for the model.
        """
        self.api_key = api_key
        self.base_url = backend_url
        self.pipeline_url = pipeline_url
        self.model_url = model_url

        # Initialize the environment variables, this is required for the
        # legacy use of the factory classes
        self.init_env()

        # Initialize the client, this is going to be used by the new foundation
        # classes
        self.client = AixplainClient(
            base_url=self.base_url,
            team_api_key=self.api_key,
        )

        # We're dynamically creating the classes here to avoid potential race
        # conditions when using class level attributes
        self.Model = type("BareModel", (Model,), {"context": self})
        self.Pipeline = type("BarePipeline", (Pipeline,), {"context": self})
        self.Agent = type("BareAgent", (Agent,), {"context": self})

    def init_env(self):
        """Initialize the environment variables."""
        os.environ["TEAM_API_KEY"] = self.api_key
        os.environ["BACKEND_URL"] = self.base_url
        os.environ["PIPELINE_URL"] = self.pipeline_url
        os.environ["MODEL_URL"] = self.model_url


class BaseResource:
    """Base class for all resources."""

    context: Aixplain
    RESOURCE_PATH: str

    def __init__(self, obj: dict):
        """
        Initialize a BaseResource instance.

        :param obj: Dictionary containing the resource's attributes.
        """
        self._obj = obj

    def __getattr__(self, key: str) -> Any:
        """
        Return the value corresponding to the key from the wrapped dictionary
        if found, otherwise raise an AttributeError.

        :param key: Attribute name to retrieve from the resource.
        :return: Value corresponding to the specified key.
        :raises AttributeError: If the key is not found in the wrapped
                                dictionary.
        """
        if key in self._obj:
            return self._obj[key]
        raise AttributeError(f"Object has no attribute '{key}'")

    def _action(
        self, method: Optional[str] = None, action_paths: List[str] = None, **kwargs
    ) -> requests.Response:
        """
        Internal method to perform actions on the resource.

        :param method: HTTP method to use (default is 'GET').
        :param action_paths: Optional list of action paths to append to the
                             URL.
        :param kwargs: Additional keyword arguments to pass to the request.
        :return: Response from the client's request as requests.Response
        :raises ValueError: If 'RESOURCE_PATH' is not defined by the subclass or
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
    """Base class for all list parameters."""

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
    """Base class for all get parameters."""

    id: str


class BareGetParams(BaseGetParams):
    """Parameters for getting resources."""

    pass


class BaseCreateParams(TypedDict):
    """Base class for all create parameters."""

    name: Optional[str] = None


class BareCreateParams(BaseCreateParams):
    """Parameters for creating resources."""

    pass


class BareListParams(BaseListParams):
    """Parameters for listing resources."""

    pass


L = TypeVar("L", bound=BaseListParams)
C = TypeVar("C", bound=BaseCreateParams)
G = TypeVar("G", bound=BaseGetParams)


class ListResourceMixin(Generic[L]):
    """Mixin for listing resources."""

    PAGINATE_PATH = "paginate"
    PAGINATE_METHOD = "post"
    PAGINATE_RESPONSE_KEY = "items"

    @classmethod
    def list(cls: Type["BaseResource"], **kwargs: L) -> List["BaseResource"]:
        """
        List resources across the first n pages with optional filtering.

        :param n: Optional number of pages to fetch (default is 1).
        :param filters: Optional dictionary containing filters to apply to the
                        results.
        :param page_fn: Optional custom function to replace the default page
                        method.
        :param kwargs: Additional filter parameters.
        :return: List of BaseResource instances across n pages
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
        filters = {
            "pageNumber": params.get("page_number", 0),
            "pageSize": params.get("page_size", 20),
        }
        if params.get("query"):
            filters["q"] = params["query"]

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

    def list_legacy(cls, **kwargs):
        """
        List resources across the first n pages with optional filtering.
        """
        raise NotImplementedError("This method is deprecated")


class GetResourceMixin(Generic[G]):
    """Mixin for getting a resource."""

    @classmethod
    def get(cls: Type["BaseResource"], **kwargs) -> "BaseResource":
        """
        Retrieve a single resource by its ID (or other get parameters).

        :param kwargs: Get parameters to pass to the request.
        :return: Instance of the BaseResource class.
        :raises ValueError: If 'RESOURCE_PATH' is not defined by the subclass.
        """
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        id = kwargs.pop("id")
        path = f"{cls.RESOURCE_PATH}/{id}"
        obj = cls.context.client.get_obj(path, **kwargs)
        return cls(obj)

    def get_legacy(cls, **kwargs):
        """
        Get a single resource by its ID (or other get parameters).
        """
        raise NotImplementedError("This method is deprecated")


class CreateResourceMixin(Generic[C]):
    """Mixin for creating a resource."""

    @classmethod
    def create(cls, **kwargs: C):
        assert getattr(
            cls, "RESOURCE_PATH"
        ), "Subclasses of 'BaseResource' must specify 'RESOURCE_PATH'"

        return cls.context.client.request("post", cls.RESOURCE_PATH, **kwargs)

    def create_legacy(cls, **kwargs):
        """
        Create a resource.
        """
        raise NotImplementedError("This method is deprecated")


class ModelListParams(BaseListParams):
    """Parameters for listing models."""

    function: Optional[Function] = None
    suppliers: Optional[Union[Supplier, List[Supplier]]] = None
    source_languages: Optional[Union[Language, List[Language]]] = None
    target_languages: Optional[Union[Language, List[Language]]] = None
    is_finetunable: Optional[bool] = None


class Model(
    BaseResource, ListResourceMixin[ModelListParams], GetResourceMixin[BareGetParams]
):
    """Resource for models."""

    RESOURCE_PATH = "sdk/models"

    @classmethod
    def list_legacy(cls, **kwargs):
        from aixplain.factories import ModelFactory

        return ModelFactory.list(**kwargs)

    @classmethod
    def get_legacy(cls, **kwargs):
        from aixplain.factories import ModelFactory

        return ModelFactory.get(model_id=kwargs["id"])


class PipelineListParams(BareListParams):
    """Parameters for listing pipelines."""

    functions: Optional[Union[Function, List[Function]]] = None
    suppliers: Optional[Union[Supplier, List[Supplier]]] = None
    models: Optional[Union[Model, List[Model]]] = None
    input_data_types: Optional[Union[DataType, List[DataType]]] = None
    output_data_types: Optional[Union[DataType, List[DataType]]] = None
    drafts_only: bool = False


class Pipeline(
    BaseResource,
    ListResourceMixin[PipelineListParams],
    GetResourceMixin[BareGetParams],
    CreateResourceMixin[BareCreateParams],
):
    """Resource for pipelines."""

    RESOURCE_PATH = "sdk/pipelines"

    @classmethod
    def list_legacy(cls, **kwargs):
        from aixplain.factories import PipelineFactory

        return PipelineFactory.list(**kwargs)

    @classmethod
    def get_legacy(cls, **kwargs):
        from aixplain.factories import PipelineFactory

        return PipelineFactory.get(pipeline_id=kwargs["id"])

    @classmethod
    def create_legacy(cls, **kwargs):
        from aixplain.factories import PipelineFactory

        return PipelineFactory.init(**kwargs)


class Agent(
    BaseResource, ListResourceMixin[BareListParams], GetResourceMixin[BareGetParams]
):
    """Resource for agents."""

    RESOURCE_PATH = "sdk/agents"
    PAGINATE_PATH = None
    PAGINATE_METHOD = "get"
    PAGINATE_RESPONSE_KEY = None

    @classmethod
    def list_legacy(cls, **kwargs):
        from aixplain.factories import AgentFactory

        return AgentFactory.list(**kwargs)

    @classmethod
    def get_legacy(cls, **kwargs):
        from aixplain.factories import AgentFactory

        return AgentFactory.get(agent_id=kwargs["id"])
