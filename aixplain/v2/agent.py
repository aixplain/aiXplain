from dataclasses import dataclass, field
from typing import List, Optional, Any

from .resource import (
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    BareListParams,
    BareGetParams,
)


@dataclass
class Agent(
    BaseResource,
    PagedListResourceMixin[BareListParams, "Agent"],
    GetResourceMixin[BareGetParams, "Agent"],
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
    team_id: Optional[int] = None
    description: str = ""
    role: str = ""
    tasks: Optional[List[Any]] = field(default_factory=list)
    llm_id: str = ""
    assets: Optional[List[Any]] = field(default_factory=list)
    tools: Optional[List[Any]] = field(default_factory=list)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    inspectorTargets: Optional[List[Any]] = field(default_factory=list)
    maxInspectors: Optional[int] = None
    inspectors: Optional[List[Any]] = field(default_factory=list)

    def __repr__(self) -> str:
        """Override dataclass __repr__ to show only id, name, and description."""
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id}, name={self.name}, description={self.description})"
        )
