import json
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union, Text, Literal
from typing_extensions import Unpack, NotRequired, TypedDict
from dataclasses_json import dataclass_json, config

from pydantic import BaseModel

from aixplain.enums import AssetStatus, ResponseStatus
from aixplain.v2.model import Model
from aixplain.v2.mixins import ToolableMixin

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


# Type definitions for conversation history
class ConversationMessage(TypedDict):
    """Type definition for a conversation message in agent history.

    Attributes:
        role: The role of the message sender, either 'user' or 'assistant'
        content: The text content of the message
    """

    role: Literal["user", "assistant"]
    content: str


def validate_history(history: List[Dict[str, Any]]) -> bool:
    """
    Validates conversation history for agent sessions.

    This function ensures that the history is properly formatted for agent conversations,
    with each message containing the required 'role' and 'content' fields and proper types.

    Args:
        history: List of message dictionaries to validate

    Returns:
        bool: True if validation passes

    Raises:
        ValueError: If validation fails with detailed error messages

    Example:
        >>> history = [
        ...     {"role": "user", "content": "Hello"},
        ...     {"role": "assistant", "content": "Hi there!"}
        ... ]
        >>> validate_history(history)  # Returns True
    """
    if not isinstance(history, list):
        raise ValueError(
            "History must be a list of message dictionaries. "
            "Example: [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hi there!'}]"
        )

    allowed_roles = {"user", "assistant"}

    for i, item in enumerate(history):
        if not isinstance(item, dict):
            raise ValueError(
                f"History item at index {i} is not a dict: {item}. "
                "Each item must be a dictionary like: {'role': 'user', 'content': 'Hello'}"
            )

        if "role" not in item or "content" not in item:
            raise ValueError(
                f"History item at index {i} is missing 'role' or 'content': {item}. "
                "Example of a valid message: {'role': 'assistant', 'content': 'Hi there!'}"
            )

        if item["role"] not in allowed_roles:
            raise ValueError(
                f"Invalid role '{item['role']}' at index {i}. Allowed roles: {allowed_roles}. "
                "Example: {'role': 'user', 'content': 'Tell me a joke'}"
            )

        if not isinstance(item["content"], str):
            raise ValueError(
                f"'content' at index {i} must be a string. Got: {type(item['content'])}. "
                "Example: {'role': 'assistant', 'content': 'Sure! Here's one...'}"
            )

    return True


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"


class AgentRunParams(BaseRunParams):
    """Parameters for running an agent."""

    sessionId: NotRequired[Optional[Text]]
    query: NotRequired[Optional[Union[Dict, Text]]]
    allowHistoryAndSessionId: NotRequired[Optional[bool]]
    tasks: NotRequired[Optional[List[Any]]]
    prompt: NotRequired[Optional[Text]]
    history: NotRequired[Optional[List[ConversationMessage]]]
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
    intermediate_steps: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    execution_stats: Optional[Dict[str, Any]] = None
    critiques: Optional[str] = ""


@dataclass_json
@dataclass
class AgentRunResult(Result):
    """Result from running an agent."""

    data: Optional[Union[AgentResponseData, Text]] = None
    session_id: Optional[Text] = None
    request_id: Optional[Text] = None
    used_credits: float = 0.0
    run_time: float = 0.0
    completed: Optional[bool] = None
    error_message: Optional[str] = None
    url: Optional[str] = None
    result: Optional[Any] = None
    supplier_error: Optional[str] = None


@dataclass_json
@dataclass
class Task:
    name: str
    instructions: Optional[str] = field(metadata=config(field_name="description"))
    expected_output: Optional[str] = field(metadata=config(field_name="expectedOutput"))
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

    DEFAULT_LLM = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    RESPONSE_CLASS = AgentRunResult
    Task = Task
    OutputFormat = OutputFormat

    # Core fields from Swagger
    instructions: Optional[str] = None
    status: AssetStatus = AssetStatus.DRAFT
    team_id: Optional[int] = field(default=None, metadata=config(field_name="teamId"))
    llm: Union[str, "Model"] = field(
        default=DEFAULT_LLM, metadata=config(field_name="llmId")
    )

    # Asset and tool fields
    assets: Optional[List[Dict[str, Any]]] = field(
        default_factory=list, metadata=config(field_name="tools")
    )
    tools: Optional[List[Dict[str, Any]]] = field(
        default_factory=list, metadata=config(field_name="assets")
    )

    # Inspector and supervisor fields
    inspector_id: Optional[str] = field(
        default=None, metadata=config(field_name="inspectorId")
    )
    supervisor_id: Optional[str] = field(
        default=None, metadata=config(field_name="supervisorId")
    )
    planner_id: Optional[str] = field(
        default=None, metadata=config(field_name="plannerId")
    )

    # Task fields
    tasks: Optional[List[Task]] = field(default_factory=list)
    subagents: Optional[List[Union[str, "Agent"]]] = field(
        default_factory=list, metadata=config(field_name="agents")
    )

    # Output and execution fields
    output_format: Optional[Union[str, OutputFormat]] = field(
        default=OutputFormat.TEXT.value, metadata=config(field_name="outputFormat")
    )
    expected_output: Optional[Union[str, dict, BaseModel]] = field(
        default="", metadata=config(field_name="expectedOutput")
    )

    # Metadata fields
    created_at: Optional[str] = field(
        default=None, metadata=config(field_name="createdAt")
    )
    updated_at: Optional[str] = field(
        default=None, metadata=config(field_name="updatedAt")
    )
    inspector_targets: Optional[List[Any]] = field(
        default_factory=list, metadata=config(field_name="inspectorTargets")
    )
    max_inspectors: Optional[int] = field(
        default=None, metadata=config(field_name="maxInspectors")
    )
    inspectors: Optional[List[Any]] = field(default_factory=list)
    resource_info: Optional[Dict[str, Any]] = field(
        default_factory=dict, metadata=config(field_name="resourceInfo")
    )

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
        self.assets = [{"type": "llm", "description": "main", "parameters": []}]
        if isinstance(self.output_format, OutputFormat):
            self.output_format = self.output_format.value

        if isinstance(self.llm, Model):
            self.llm = self.llm.id
        if self.subagents and (self.tasks or self.tools):
            raise ValueError(
                "Team agents cannot have tasks or tools. Please remove the tasks or tools and try again."
            )

    def mark_as_deleted(self) -> None:
        """Mark the agent as deleted by setting status to DELETED and calling parent method."""
        from .enums import AssetStatus

        self.status = AssetStatus.DELETED
        super().mark_as_deleted()

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

        # Handle session_id parameter name compatibility (snake_case -> camelCase)
        if "session_id" in kwargs and "sessionId" not in kwargs:
            kwargs["sessionId"] = kwargs.pop("session_id")

        return super().run(*args, **kwargs)

    def _validate_expected_output(self) -> None:
        if self.output_format == OutputFormat.JSON.value:
            if not isinstance(self.expected_output, (str, dict, BaseModel)):
                raise ValueError("Expected output must be a valid JSON object")
            if isinstance(self.expected_output, str):
                try:
                    json.loads(self.expected_output)
                except json.JSONDecodeError:
                    raise ValueError(
                        "Expected output must be a valid JSON string or dict or pydantic model"
                    )
        elif self.output_format in [
            OutputFormat.MARKDOWN.value,
            OutputFormat.TEXT.value,
        ]:
            if not isinstance(self.expected_output, str):
                raise ValueError("Expected output must be a string")

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

        # validate expected output as per output format
        # json should be a valid json string or dict or pydantic model
        self._validate_expected_output()

        # Convert Pydantic BaseModel to dict for serialization
        if isinstance(self.expected_output, BaseModel):
            self.expected_output = self.expected_output.model_dump()

        # if not all(t.status == AssetStatus.ONBOARDED for t in self.tools):
        #     raise ValueError(
        #         "All tools must be onboarded before saving the agent."
        #     )
        # if not all(t.status == AssetStatus.ONBOARDED for t in self.subagents):
        #     raise ValueError(
        #         "All subagents must be onboarded before saving the agent."
        #     )

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

        # Convert tools intelligently based on their type
        converted_assets = []
        if self.tools:
            for tool in self.tools:
                if isinstance(tool, ToolableMixin):
                    # Non-tool objects (like Models) that can act as tools
                    converted_assets.append(tool.as_tool())
                else:
                    raise ValueError(
                        "A tool in the agent must be a Tool, Model or ToolableMixin instance."
                    )

        # Update the payload with converted assets
        payload["assets"] = converted_assets

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
                "outputFormat": self.output_format,
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

    def generate_session_id(
        self, history: Optional[List[ConversationMessage]] = None
    ) -> str:
        """Generate a unique session ID for agent conversations.

        This method creates a unique session identifier based on the agent ID and current timestamp.
        If conversation history is provided, it attempts to initialize the session on the server
        to enable context-aware conversations.

        Args:
            history (Optional[List[Dict]], optional): Previous conversation history.
                Each dict should contain 'role' (either 'user' or 'assistant') and 'content' keys.
                Defaults to None.

        Returns:
            str: A unique session identifier in the format "{agent_id}_{timestamp}".

        Raises:
            ValueError: If the history format is invalid.

        Example:
            >>> agent = Agent.get("my_agent_id")
            >>> session_id = agent.generate_session_id()
            >>> # Or with history
            >>> history = [
            ...     {"role": "user", "content": "Hello"},
            ...     {"role": "assistant", "content": "Hi there!"}
            ... ]
            >>> session_id = agent.generate_session_id(history=history)
        """
        if history:
            validate_history(history)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_id = f"{self.id}_{timestamp}"

        if not history:
            return session_id

        try:
            # Use the existing run infrastructure to initialize the session
            result = self.run_async(
                query="/",
                sessionId=session_id,
                history=history,
                executionParams={
                    "maxTokens": 2048,
                    "maxIterations": 10,
                    "outputFormat": OutputFormat.TEXT.value,
                    "expectedOutput": None,
                },
                allowHistoryAndSessionId=True,
            )

            # If we got a polling URL, poll for completion
            if result.url and not result.completed:
                final_result = self.sync_poll(result.url, timeout=300, wait_time=0.5)

                if final_result.status == ResponseStatus.SUCCESS:
                    return session_id
                else:
                    logging.error(
                        f"Session {session_id} initialization failed: {final_result}"
                    )
                    return session_id
            else:
                # Direct completion or no polling needed
                return session_id

        except Exception as e:
            logging.error(f"Failed to initialize session {session_id}: {e}")
            return session_id
