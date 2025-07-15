from typing_extensions import Unpack, List, Union, NotRequired

from .resource import (
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
    BaseCreateParams,
    CreateResourceMixin,
)

from .enums import Supplier
from .tool import Tool


class AgentCreateParams(BaseCreateParams):
    name: str
    description: str
    llm_id: NotRequired[str]
    tools: NotRequired[List["Tool"]]
    api_key: NotRequired[str]
    supplier: NotRequired[Union[dict, str, "Supplier", int]]
    version: NotRequired[str]


class Agent(
    BaseResource,
    PagedListResourceMixin[BareListParams, "Agent"],
    GetResourceMixin[BareGetParams, "Agent"],
    CreateResourceMixin[AgentCreateParams, "Agent"],
):
    """Resource for agents.

    Attributes:
        RESOURCE_PATH: str: The resource path.
        PAGINATE_PATH: None: The path for pagination.
        PAGINATE_METHOD: str: The method for pagination.
        PAGINATE_ITEMS_KEY: None: The key for the response.
    """

    RESOURCE_PATH = "sdk/agents"
    PAGINATE_PATH = None
    PAGINATE_METHOD = "get"
    PAGINATE_ITEMS_KEY = None

    LLM_ID = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    @classmethod
    def create(cls, *args, **kwargs: Unpack[AgentCreateParams]) -> "Agent":
        kwargs.setdefault("llm_id", cls.LLM_ID)
        kwargs.setdefault("supplier", cls.SUPPLIER)
        kwargs.setdefault("tools", [])

        return super().create(*args, **kwargs)
