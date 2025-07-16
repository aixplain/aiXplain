from dataclasses import dataclass, field
from typing import List, Optional, Any
from typing_extensions import Unpack
from dataclasses_json import dataclass_json, config

from .resource import (
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
    BaseRunParams,
    BaseResult,
    RunnableResourceMixin,
)


class AgentRunParams(BaseRunParams):
    pass


class AgentRunResult(BaseResult):
    pass


@dataclass_json
@dataclass
class Agent(
    BaseResource,
    PagedListResourceMixin[BareListParams, "Agent"],
    GetResourceMixin[BareGetParams, "Agent"],
    RunnableResourceMixin[AgentRunParams, AgentRunResult],
):
    RESOURCE_PATH = "sdk/agents"
    PAGINATE_PATH = None
    PAGINATE_METHOD = "get"
    PAGINATE_ITEMS_KEY = None

    LLM_ID = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    id: str = ""
    name: str = ""
    status: str = ""
    team_id: Optional[int] = field(default=None, metadata=config(field_name="teamId"))
    description: str = ""
    role: str = ""
    tasks: Optional[List[Any]] = field(default_factory=list)
    llm_id: str = field(default=LLM_ID, metadata=config(field_name="llmId"))
    assets: Optional[List[Any]] = field(default_factory=list)
    tools: Optional[List[Any]] = field(default_factory=list)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    inspectorTargets: Optional[List[Any]] = field(default_factory=list)
    maxInspectors: Optional[int] = None
    inspectors: Optional[List[Any]] = field(default_factory=list)
    instructions: Optional[str] = None

    def __repr__(self) -> str:
        """Override dataclass __repr__ to show only id, name, and description."""
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id}, name={self.name}, description={self.description})"
        )

    def __post_init__(self):
        if not self.id:
            self.save(status="draft")

    @classmethod
    def get(cls, id: str, **kwargs) -> "Agent":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> List["Agent"]:
        return super().list(**kwargs)

    def run(self, **kwargs: Unpack[AgentRunParams]) -> "AgentRunResult":
        return super().run(**kwargs)
