from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union, Text
from typing_extensions import Unpack, NotRequired
from dataclasses_json import dataclass_json, config

from aixplain.enums import AssetStatus, ResponseStatus


from .resource import (
    BaseResource,
    SearchResourceMixin,
    GetResourceMixin,
    DeleteResourceMixin,
    BaseSearchParams,
    BaseGetParams,
    BaseDeleteParams,
    BaseRunParams,
    Result,
    RunnableResourceMixin,
    Page,
)


class AgentRunParams(BaseRunParams):
    """Parameters for running an agent."""

    sessionId: NotRequired[Optional[Text]]
    query: NotRequired[Optional[Union[Dict, Text]]]
    allowHistoryAndSessionId: NotRequired[Optional[bool]]
    tasks: NotRequired[Optional[List[Any]]]
    prompt: NotRequired[Optional[Text]]
    history: NotRequired[Optional[List[Dict]]]
    executionParams: NotRequired[Optional[Dict[str, Any]]]
    criteria: NotRequired[Optional[Text]]
    evolve: NotRequired[Optional[Text]]
    inspectors: NotRequired[Optional[List[Dict]]]


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
class AgentRunResult(Result):
    """Result from running an agent."""

    data: Optional[Union[AgentResponseData, Text]] = None
    session_id: Optional[Text] = field(
        default=None, metadata=config(field_name="sessionId")
    )
    request_id: Optional[Text] = field(
        default=None, metadata=config(field_name="requestId")
    )
    used_credits: float = 0.0
    run_time: float = 0.0


@dataclass_json
@dataclass
class Task:
    name: str
    description: Optional[str] = None
    expectedOutput: Optional[str] = ""
    dependencies: List[Union[str, "Task"]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.dependencies = [
            dependency if isinstance(dependency, str) else dependency.name
            for dependency in self.dependencies
        ]


@dataclass_json
@dataclass
class Agent(
    BaseResource,
    SearchResourceMixin[BaseSearchParams, "Agent"],
    GetResourceMixin[BaseGetParams, "Agent"],
    DeleteResourceMixin[BaseDeleteParams, "Agent"],
    RunnableResourceMixin[AgentRunParams, AgentRunResult],
):
    """
    Agent resource class.

    Note: There are some discrepancies between the Swagger documentation for creation
    and what the server returns when retrieving agents:

    - Server GET responses often omit: role, inspectorId, supervisorId, plannerId, tasks, tools
    - Server GET responses may omit 'name' field in assets
    - Some fields documented in Swagger may not be implemented server-side yet

    This structure accommodates both creation (with all documented fields) and
    retrieval (with potentially incomplete data from server).
    """

    RESOURCE_PATH = "v2/agents"

    LLM_ID = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    RESPONSE_CLASS = AgentRunResult
    Task = Task

    # Core fields from Swagger
    instructions: Optional[str] = None
    status: AssetStatus = AssetStatus.DRAFT
    team_id: Optional[int] = field(default=None, metadata=config(field_name="teamId"))
    llm_id: str = field(default=LLM_ID, metadata=config(field_name="llmId"))

    # Asset and tool fields
    assets: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    tools: Optional[List[Dict[str, Any]]] = field(default_factory=list)

    # Inspector and supervisor fields
    inspectorId: Optional[str] = field(
        default=None, metadata=config(field_name="inspectorId")
    )
    supervisorId: Optional[str] = field(
        default=None, metadata=config(field_name="supervisorId")
    )
    plannerId: Optional[str] = field(
        default=None, metadata=config(field_name="plannerId")
    )

    # Task fields
    tasks: Optional[List[Task]] = field(default_factory=list)
    subagents: Optional[List[Union[str, "Agent"]]] = field(default_factory=list)

    # Output and execution fields
    outputFormat: Optional[str] = field(
        default="text", metadata=config(field_name="outputFormat")
    )
    expectedOutput: Optional[Any] = None

    # Metadata fields
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    inspectorTargets: Optional[List[Any]] = field(default_factory=list)
    maxInspectors: Optional[int] = None
    inspectors: Optional[List[Any]] = field(default_factory=list)
    resourceInfo: Optional[Dict[str, Any]] = field(default_factory=dict)

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
        self.tasks = [Task.from_dict(task) for task in self.tasks]
        self.subagents = [
            agent if isinstance(agent, str) else agent.id for agent in self.subagents
        ]
        if self.subagents and (self.tasks or self.tools):
            raise ValueError(
                "Team agents cannot have tasks or tools. Please remove the tasks or tools and try again."
            )

    def before_run(
        self, *args: Any, **kwargs: Unpack[AgentRunParams]
    ) -> Optional[AgentRunResult]:
        # If the agent is draft or not set, and it is modified,
        # implicitly save it as draft
        if self.status in [AssetStatus.DRAFT, None]:
            if self.is_modified:
                self.save(as_draft=True)
        elif self.status == AssetStatus.ONBOARDED:
            if self.is_modified:
                raise ValueError(
                    "Agent is onboarded and cannot be modified unless you "
                    "explicitly save it."
                )
        return None  # Continue with normal operation

    def after_run(
        self,
        result: Union[AgentRunResult, Exception],
        *args: Any,
        **kwargs: Unpack[AgentRunParams],
    ) -> Optional[AgentRunResult]:
        # Could implement caching, logging, or custom result transformation
        # here
        return None  # Return original result

    def run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        if len(args) > 0:
            kwargs["query"] = args[0]
            args = args[1:]
        return super().run(*args, **kwargs)

    def before_save(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """
        Callback to be called before the resource is saved.
        Handles status transitions based on save type.
        """
        as_draft = kwargs.pop("as_draft", False)
        if as_draft:
            self.status = AssetStatus.DRAFT
        else:
            self.status = AssetStatus.ONBOARDED
        return None  # Continue with normal operation

    @classmethod
    def get(cls: type["Agent"], id: str, **kwargs: Unpack[BaseGetParams]) -> "Agent":
        return super().get(id, **kwargs)

    @classmethod
    def search(
        cls: type["Agent"],
        query: Optional[str] = None,
        **kwargs: Unpack[BaseSearchParams],
    ) -> "Page[Agent]":
        """
        Search agents with optional query and filtering.

        Args:
            query: Optional search query string
            **kwargs: Additional search parameters (ownership, status, etc.)

        Returns:
            Page of agents matching the search criteria
        """
        # If query is provided, add it to kwargs
        if query is not None:
            kwargs["query"] = query

        return super().search(**kwargs)

    def build_save_payload(self, **kwargs: Any) -> dict:
        """
        Build the payload for the save action.
        """
        payload = self.to_dict()
        payload["assets"] = payload.pop("tools")
        payload["agents"] = payload.pop("subagents")
        payload["tools"] = [{"type": "llm", "description": "main", "parameters": []}]

        for i, tool in enumerate(self.tools):
            payload["assets"][i]["parameters"] = tool.get_parameters()

        return payload

    def build_run_payload(self, **kwargs: Unpack[AgentRunParams]) -> dict:
        """
        Build the payload for the run action.
        """
        # Extract executionParams if provided, otherwise use defaults
        execution_params = kwargs.pop("executionParams", {})

        # Set default values for executionParams if not provided
        if not execution_params:
            execution_params = {
                "outputFormat": self.outputFormat or "text",
                "maxTokens": 2048,
                "maxIterations": 30,
                "maxTime": 300,
            }

        # Build the payload according to Swagger specification
        payload = {
            "id": self.id,
            "executionParams": execution_params,
        }

        # Add all other parameters from kwargs
        for key, value in kwargs.items():
            if value is not None:  # Only include non-None values
                payload[key] = value

        return payload
