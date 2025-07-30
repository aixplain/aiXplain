from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union, Text
from typing_extensions import Unpack, NotRequired
from dataclasses_json import dataclass_json, config

from aixplain.enums import AssetStatus, ResponseStatus


from .resource import (
    BaseResource,
    PagedListResourceMixin,
    GetResourceMixin,
    DeleteResourceMixin,
    BaseListParams,
    BaseGetParams,
    BaseDeleteParams,
    BaseRunParams,
    BaseResult,
    RunnableResourceMixin,
    Page
)


class AgentRunParams(BaseRunParams):
    """Parameters for running an agent."""

    query: NotRequired[Optional[Union[Dict, Text]]]
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
    intermediate_steps: Optional[List[Any]] = field(default_factory=list)
    execution_stats: Optional[Dict[str, Any]] = None
    critiques: Optional[str] = ""


@dataclass_json
@dataclass
class AgentRunResult(BaseResult):
    """Result from running an agent."""

    data: Optional[Union[AgentResponseData, Text]] = None
    session_id: Optional[Text] = field(
        default=None, metadata=config(field_name="sessionId")
    )
    request_id: Optional[Text] = field(
        default=None, metadata=config(field_name="requestId")
    )
    status: Optional[ResponseStatus] = ResponseStatus.IN_PROGRESS
    completed: Optional[bool] = False
    error_message: Optional[Text] = None
    used_credits: float = 0.0
    run_time: float = 0.0


@dataclass_json
@dataclass
class Agent(
    BaseResource,
    PagedListResourceMixin[BaseListParams, "Agent"],
    GetResourceMixin[BaseGetParams, "Agent"],
    DeleteResourceMixin[BaseDeleteParams, "Agent"],
    RunnableResourceMixin[AgentRunParams, AgentRunResult],
):
    RESOURCE_PATH = "sdk/agents"
    PAGINATE_PATH = None
    PAGINATE_METHOD = "get"
    PAGINATE_ITEMS_KEY = None

    LLM_ID = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    RESPONSE_CLASS = AgentRunResult

    id: str = ""
    name: str = ""
    status: str = ""
    team_id: Optional[int] = field(
        default=None, metadata=config(field_name="teamId")
    )
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
        """
        Override dataclass __repr__ to show only id, name, and description.
        """
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id}, name={self.name}, "
            f"description={self.description})"
        )

    def __post_init__(self) -> None:
        self.status = self.status or AssetStatus.DRAFT

    def before_run(self, **kwargs: Unpack[AgentRunParams]) -> None:
        pass

    def after_run(self, result: Union[AgentRunResult, Exception], **kwargs: Unpack[AgentRunParams]) -> None:
        pass

    @classmethod
    def get(
        cls: type["Agent"], id: str, **kwargs: Unpack[BaseGetParams]
    ) -> "Agent":
        return super().get(id, **kwargs)

    @classmethod
    def list(
        cls: type["Agent"], **kwargs: Unpack[BaseListParams]
    ) -> "Page[Agent]":
        return super().list(**kwargs)

    def build_save_payload(self, **kwargs: Any) -> dict:
        """
        Build the payload for the save action.
        """
        payload = self.to_dict()
        payload["assets"] = payload.pop("tools")
        payload["tools"] = [
            {
                "type": "llm", 
                "description": "main", 
                "parameters": []
            }
        ]
        payload["role"] = payload.pop("instructions")
        return payload

    def build_run_payload(self, **kwargs: Unpack[AgentRunParams]) -> dict:
        """
        Build the payload for the run action.
        """
        max_tokens = kwargs.pop("max_tokens", 2048)
        max_iterations = kwargs.pop("max_iterations", 10)
        output_format = kwargs.pop("output_format", "text")
        expected_output = kwargs.pop("expected_output", None)

        return {
            "id": self.id,
            "executionParams": {
                "maxTokens": max_tokens,
                "maxIterations": max_iterations,
                "outputFormat": output_format,
                "expectedOutput": expected_output,
            },
            **kwargs,
        }
