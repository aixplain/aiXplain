from typing_extensions import (
    Dict,
    Unpack,
    List,
    Union,
    TYPE_CHECKING,
    NotRequired,
    Text,
)

from .resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
    BaseCreateParams,
    Page,
)

if TYPE_CHECKING:
    from aixplain.modules.agent import Agent
    from aixplain.enums import Supplier


class TeamAgentCreateParams(BaseCreateParams):
    name: Text
    agents: List[Union[Text, "Agent"]]
    llm_id: Text
    description: Text
    api_key: Text
    supplier: Union[Dict, Text, "Supplier", int]
    version: NotRequired[Text]
    use_mentalist_and_inspector: bool


class TeamAgentGetParams(BareGetParams):
    api_key: NotRequired[str]


class TeamAgent(
    BaseResource,
    ListResourceMixin[BareListParams, "TeamAgent"],
    GetResourceMixin[BareGetParams, "TeamAgent"],
):
    """Resource for agents.

    Attributes:
        RESOURCE_PATH: str: The resource path.
        PAGINATE_PATH: None: The path for pagination.
        PAGINATE_METHOD: str: The method for pagination.
        PAGINATE_ITEMS_KEY: None: The key for the response.
    """

    RESOURCE_PATH = "sdk/agent-communities"
    PAGINATE_PATH = None
    PAGINATE_METHOD = "get"
    PAGINATE_ITEMS_KEY = None

    LLM_ID = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    @classmethod
    def list(cls, **kwargs: Unpack[BareListParams]) -> Page["TeamAgent"]:
        from aixplain.factories import TeamAgentFactory

        return TeamAgentFactory.list(**kwargs)

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[TeamAgentGetParams]) -> "TeamAgent":
        from aixplain.factories import TeamAgentFactory

        return TeamAgentFactory.get(id, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs: Unpack[TeamAgentCreateParams]) -> "TeamAgent":
        from aixplain.factories import TeamAgentFactory
        from aixplain.utils import config

        kwargs.setdefault("llm_id", cls.LLM_ID)
        kwargs.setdefault("api_key", config.TEAM_API_KEY)
        kwargs.setdefault("supplier", cls.SUPPLIER)
        kwargs.setdefault("description", "")
        kwargs.setdefault("use_mentalist_and_inspector", True)

        return TeamAgentFactory.create(*args, **kwargs)
