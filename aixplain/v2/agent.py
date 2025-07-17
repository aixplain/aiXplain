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
    BareListParams,
    BareGetParams,
    BareDeleteParams,
    BaseRunParams,
    BaseResult,
    RunnableResourceMixin,
    Page,
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

    def __post_init__(self):
        if not self.id:
            self.save(status=AssetStatus.DRAFT)

    @classmethod
    def get(cls, id: str, **kwargs) -> "Agent":
        return super().get(id, **kwargs)

    @classmethod
    def list(cls, **kwargs) -> "Page[Agent]":
        return super().list(**kwargs)

    def build_run_payload(self, **kwargs: Unpack[AgentRunParams]) -> dict:
        """
        Build the payload for the run action.

        Expample request:
            {
                "id": "687925d9153e7e4d81e495c4",
                "query": {
                    "input": "Who is the president of Brazil right now? Translate to pt"
                },
                "sessionId": null,
                "history": null,
                "executionParams": {
                    "maxTokens": 2048,
                    "maxIterations": 10,
                    "outputFormat": "text",
                    "expectedOutput": null
                }
            }
        """
        max_tokens = kwargs.pop("max_tokens", 2048)
        max_iterations = kwargs.pop("max_iterations", 10)
        output_format = kwargs.pop("output_format", "text")
        expected_output = kwargs.pop("expected_output", None)
        session_id = kwargs.pop("session_id", None)
        history = kwargs.pop("history", None)

        serialized = self.to_dict()  # type: ignore
        payload = {k: serialized[k] for k in ['id', 'tools'] if k in serialized}

        return {
            "executionParams": {
                "maxTokens": max_tokens,
                "maxIterations": max_iterations,
                "outputFormat": output_format,
                "expectedOutput": expected_output,
            },
            "sessionId": session_id,
            "history": history,
            **payload,
            **kwargs,
        }
