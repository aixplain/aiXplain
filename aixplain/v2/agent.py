from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union, Text
from typing_extensions import Unpack, NotRequired
from dataclasses_json import dataclass_json, config

from .resource import (
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    DeleteResourceMixin,
    BareListParams,
    BareGetParams,
    BareDeleteParams,
    BaseRunParams,
    BaseResult,
    RunnableResourceMixin,
)


class AgentRunParams(BaseRunParams):
    """Parameters for running an agent."""

    data: NotRequired[Optional[Union[Dict, Text]]]
    query: NotRequired[Optional[Text]]
    session_id: NotRequired[Optional[Text]]
    history: NotRequired[Optional[List[Dict]]]
    name: NotRequired[Text]
    parameters: NotRequired[Dict]
    content: NotRequired[Optional[Union[Dict[Text, Text], List[Text]]]]
    max_tokens: NotRequired[int]
    max_iterations: NotRequired[int]
    output_format: NotRequired[Optional[str]]
    expected_output: NotRequired[Optional[Union[Any, Text, dict]]]


@dataclass_json
@dataclass
class AgentResponseData:
    """Data structure for agent response."""

    input: Optional[Any] = None
    output: Optional[Any] = None
    session_id: str = ""
    intermediate_steps: Optional[List[Any]] = field(default_factory=list)
    execution_stats: Optional[Dict[str, Any]] = None
    critiques: Optional[str] = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "session_id": self.session_id,
            "intermediate_steps": self.intermediate_steps,
            "executionStats": self.execution_stats,
            "critiques": self.critiques,
        }


@dataclass_json
@dataclass
class AgentRunResult(BaseResult):
    """Result from running an agent."""

    data: Optional[AgentResponseData] = None
    used_credits: float = 0.0
    run_time: float = 0.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Handle data field specially
        if "data" in kwargs and isinstance(kwargs["data"], dict):
            self.data = AgentResponseData(**kwargs["data"])
        elif "data" in kwargs and isinstance(kwargs["data"], AgentResponseData):
            self.data = kwargs["data"]
        else:
            self.data = AgentResponseData()

        self.used_credits = kwargs.get("usedCredits", kwargs.get("used_credits", 0.0))
        self.run_time = kwargs.get("runTime", kwargs.get("run_time", 0.0))

    def __getitem__(self, key: Text) -> Any:
        if key == "data":
            return self.data.to_dict() if self.data else {}
        return getattr(self, key, None)

    def __setitem__(self, key: Text, value: Any) -> None:
        if key == "data" and isinstance(value, Dict):
            self.data = AgentResponseData(**value)
        elif key == "data" and isinstance(value, AgentResponseData):
            self.data = value
        else:
            setattr(self, key, value)


@dataclass_json
@dataclass
class Agent(
    BaseResource,
    PagedListResourceMixin[BareListParams, "Agent"],
    GetResourceMixin[BareGetParams, "Agent"],
    DeleteResourceMixin[BareDeleteParams, "Agent"],
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
