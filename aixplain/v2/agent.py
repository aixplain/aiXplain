from typing_extensions import Unpack, List

from .resource import (
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
)


class Agent(
    BaseResource,
    ListResourceMixin[BareListParams, "Agent"],
    GetResourceMixin[BareGetParams, "Agent"],
):
    """Resource for agents.

    Attributes:
        RESOURCE_PATH: str: The resource path.
        PAGINATE_PATH: None: The path for pagination.
        PAGINATE_METHOD: str: The method for pagination.
        PAGINATE_RESPONSE_KEY: None: The key for the response.
    """

    RESOURCE_PATH = "sdk/agents"
    PAGINATE_PATH = None
    PAGINATE_METHOD = "get"
    PAGINATE_RESPONSE_KEY = None

    @classmethod
    def list(cls, **kwargs: Unpack[BareListParams]) -> List["Agent"]:
        from aixplain.factories import AgentFactory

        return [Agent(obj) for obj in AgentFactory.list(**kwargs)["results"]]

    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "Agent":
        from aixplain.factories import AgentFactory

        return Agent(AgentFactory.get(agent_id=kwargs["id"]))
