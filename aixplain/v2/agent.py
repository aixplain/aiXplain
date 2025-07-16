from typing_extensions import List, Union

from .resource import (
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
)

from .enums import Supplier
from .tool import Tool


class Agent(
    BaseResource,
    PagedListResourceMixin[BareListParams, "Agent"],
    GetResourceMixin[BareGetParams, "Agent"],
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

    llm_id: str
    tools: List[Tool]
    api_key: str
    supplier: Union[dict, str, Supplier, int]
    version: str

    def __init__(
        self,
        llm_id: str,
        tools: List[Tool],
        api_key: str,
        supplier: Union[dict, str, Supplier, int],
        version: str,
    ):
        self.llm_id = llm_id
        self.tools = tools
        self.api_key = api_key
        self.supplier = supplier
        self.version = version
