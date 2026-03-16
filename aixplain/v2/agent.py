"""Agent module for aiXplain v2 SDK."""

import json
import logging
import re
import warnings
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Any, Dict, Union, Text
from typing_extensions import Unpack, NotRequired, TypedDict, Literal
from dataclasses_json import dataclass_json, config

from pydantic import BaseModel

from .enums import AssetStatus, ResponseStatus
from .model import Model
from .mixins import ToolableMixin

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
    """Validates conversation history for agent sessions.

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
    """Output format options for agent responses."""

    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"


class AgentRunParams(BaseRunParams):
    """Parameters for running an agent.

    Attributes:
        session_id: Session ID for conversation continuity
        query: The query to run
        variables: Variables to replace {{variable}} placeholders in instructions and description.
            The backend performs the actual substitution.
        allow_history_and_session_id: Allow both history and session ID
        tasks: List of tasks for the agent
        prompt: Custom prompt override
        history: Conversation history
        execution_params: Execution parameters (maxTokens, etc.)
        criteria: Criteria for evaluation
        evolve: Evolution parameters
        inspectors: Inspector configurations
        run_response_generation: Whether to run response generation. Defaults to False.
        progress_format: Display format - "status" (single line) or "logs" (timeline).
                        If None (default), progress tracking is disabled.
        progress_verbosity: Detail level - 1 (minimal), 2 (thoughts), 3 (full I/O)
        progress_truncate: Whether to truncate long text in progress display
    """

    session_id: NotRequired[Optional[Text]]
    query: NotRequired[Optional[Union[Dict, Text]]]
    variables: NotRequired[Optional[Dict[str, Any]]]
    allow_history_and_session_id: NotRequired[Optional[bool]]
    tasks: NotRequired[Optional[List[Any]]]
    prompt: NotRequired[Optional[Text]]
    history: NotRequired[Optional[List[ConversationMessage]]]
    execution_params: NotRequired[Optional[Dict[str, Any]]]
    criteria: NotRequired[Optional[Text]]
    evolve: NotRequired[Optional[Text]]
    inspectors: NotRequired[Optional[List[Dict]]]
    run_response_generation: NotRequired[Optional[bool]]
    progress_format: NotRequired[Optional[Text]]
    progress_verbosity: NotRequired[Optional[int]]
    progress_truncate: NotRequired[Optional[bool]]


@dataclass_json
@dataclass
class AgentResponseData:
    """Data structure for agent response."""

    input: Optional[Any] = None
    output: Optional[Any] = None
    steps: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    session_id: Optional[str] = None
    execution_stats: Optional[Dict[str, Any]] = field(default=None, metadata=config(field_name="executionStats"))
    critiques: Optional[str] = ""


@dataclass_json
@dataclass
class AgentRunResult(Result):
    """Result from running an agent."""

    data: Optional[Union[AgentResponseData, Text]] = None  # Override type from base class
    session_id: Optional[Text] = field(default=None, metadata=config(field_name="sessionId"))
    request_id: Optional[Text] = field(default=None, metadata=config(field_name="requestId"))
    used_credits: float = field(default=0.0, metadata=config(field_name="usedCredits"))
    run_time: float = field(default=0.0, metadata=config(field_name="runTime"))

    # Internal reference to client context for debug() method
    _context: Optional[Any] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=config(exclude=lambda x: True),
        init=False,
    )

    @property
    def execution_id(self) -> Optional[str]:
        """Extract the execution ID from the poll URL or request_id.

        The execution ID can be used with ``Agent.poll()`` and
        ``Agent.sync_poll()`` to resume polling a previously started run
        without persisting the full URL.

        Returns:
            The execution ID if available, None otherwise.
        """
        if self.request_id:
            return self.request_id

        if self.url:
            match = re.search(r"/sdk/agents/([^/]+)/", self.url)
            if match:
                return match.group(1)

        return None

    def debug(
        self,
        prompt: Optional[str] = None,
        execution_id: Optional[str] = None,
        **kwargs: Any,
    ) -> "DebugResult":
        """Debug this agent response using the Debugger meta-agent.

        This is a convenience method for quickly analyzing agent responses
        to identify issues, errors, or areas for improvement.

        Note: This method requires the AgentRunResult to have been created
        through an Aixplain client context. If you have a standalone result,
        use the Debugger directly: aix.Debugger().debug_response(result)

        Args:
            prompt: Optional custom prompt to guide the debugging analysis.
                   Examples: "Why did it take so long?", "Focus on error handling"
            execution_id: Optional execution ID (poll ID) for the run. If not provided,
                         it will be extracted from the response's request_id or poll URL.
                         This allows the debugger to fetch additional logs and information.
            **kwargs: Additional parameters to pass to the debugger.

        Returns:
            DebugResult: The debugging analysis result.

        Raises:
            ValueError: If no client context is available for debugging.

        Example:
            agent = aix.Agent.get("my_agent_id")
            response = agent.run("Hello!")
            debug_result = response.debug()  # Uses default prompt
            debug_result = response.debug("Why did it take so long?")  # Custom prompt
            debug_result = response.debug(execution_id="abc-123")  # With explicit ID
            print(debug_result.analysis)
        """
        from .meta_agents import Debugger, DebugResult

        if self._context is None:
            raise ValueError(
                "Cannot debug this response: no client context available. "
                "Use the Debugger directly: aix.Debugger().debug_response(result)"
            )

        # Create a bound Debugger class with the context
        BoundDebugger = type("Debugger", (Debugger,), {"context": self._context})
        debugger = BoundDebugger()
        return debugger.debug_response(self, prompt=prompt, execution_id=execution_id, **kwargs)


@dataclass_json
@dataclass
class Task:
    """A task definition for agent workflows."""

    name: str
    instructions: Optional[str] = field(metadata=config(field_name="description"))
    expected_output: Optional[str] = field(metadata=config(field_name="expectedOutput"))
    dependencies: List[Union[str, "Task"]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize task dependencies after dataclass creation."""
        if self.dependencies:
            self.dependencies = [
                dependency if isinstance(dependency, str) else dependency.name for dependency in self.dependencies
            ]


@dataclass_json
@dataclass(repr=False)
class Agent(
    BaseResource,
    SearchResourceMixin[BaseSearchParams, "Agent"],
    GetResourceMixin[BaseGetParams, "Agent"],
    DeleteResourceMixin[BaseDeleteParams, "Agent"],
    RunnableResourceMixin[AgentRunParams, AgentRunResult],
):
    """Agent resource class."""

    RESOURCE_PATH = "v2/agents"
    POLL_URL_TEMPLATE = "sdk/agents/{execution_id}/result"

    DEFAULT_LLM = "6895d6d1d50c89537c1cf237"
    SUPPLIER = "aiXplain"

    RESPONSE_CLASS = AgentRunResult
    Task = Task
    OutputFormat = OutputFormat

    # Core fields from Swagger
    instructions: Optional[str] = None
    status: AssetStatus = AssetStatus.DRAFT
    team_id: Optional[int] = field(default=None, metadata=config(field_name="teamId"))
    llm: Union[str, "Model"] = field(default=DEFAULT_LLM, metadata=config(exclude=lambda x: True))

    # Asset and tool fields
    tools: Optional[List[Dict[str, Any]]] = field(default_factory=list, metadata=config(field_name="tools"))

    # Inspector and supervisor fields
    inspector_id: Optional[str] = field(default=None, metadata=config(field_name="inspectorId"))
    supervisor_id: Optional[str] = field(default=None, metadata=config(field_name="supervisorId"))
    planner_id: Optional[str] = field(default=None, metadata=config(field_name="plannerId"))

    # Task fields
    tasks: Optional[List[Task]] = field(default_factory=list)
    agents: Optional[List[Union[str, "Agent"]]] = field(default_factory=list, metadata=config(field_name="agents"))

    # Deprecated alias for `agents` — will be removed in a future release
    subagents: Optional[List[Union[str, "Agent"]]] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=config(exclude=lambda x: True),
    )

    # Output and execution fields
    output_format: Optional[Union[str, OutputFormat]] = field(
        default=OutputFormat.TEXT.value, metadata=config(field_name="outputFormat")
    )
    expected_output: Optional[Union[str, dict, BaseModel]] = field(
        default="", metadata=config(field_name="expectedOutput")
    )

    # Metadata fields
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))
    updated_at: Optional[str] = field(default=None, metadata=config(field_name="updatedAt"))
    inspector_targets: Optional[List[Any]] = field(default_factory=list, metadata=config(field_name="inspectorTargets"))
    max_inspectors: Optional[int] = field(default=None, metadata=config(field_name="maxInspectors"))
    inspectors: Optional[List[Any]] = field(default_factory=list)
    resource_info: Optional[Dict[str, Any]] = field(default_factory=dict, metadata=config(field_name="resourceInfo"))
    max_iterations: Optional[int] = field(default=5, metadata=config(field_name="maxIterations"))
    max_tokens: Optional[int] = field(default=2048, metadata=config(field_name="maxTokens"))

    # Internal state for progress tracking (excluded from serialization)
    _progress_tracker: Optional[Any] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=config(exclude=lambda x: True),
        init=False,
    )

    def __post_init__(self) -> None:
        """Initialize agent after dataclass creation."""
        self.tasks = [Task.from_dict(task) for task in self.tasks]

        if self.subagents is not None:
            warnings.warn(
                "The 'subagents' parameter is deprecated. Use 'agents' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.agents:
                raise ValueError("Cannot specify both 'agents' and 'subagents'.")
            self.agents = self.subagents
            self.subagents = None

        # Store original agent objects to resolve IDs at save time
        self._original_agents = list(self.agents)
        # Convert to IDs for serialization (to_dict), using None as placeholder for unsaved agents
        self.agents = [a if isinstance(a, str) else a.get("id") if isinstance(a, dict) else a.id for a in self.agents]

        if isinstance(self.output_format, OutputFormat):
            self.output_format = self.output_format.value

        if isinstance(self.llm, Model):
            self.llm = self.llm.id

        # Normalize inspector_targets to support both strings and InspectorTarget enums
        if self.inspector_targets:
            from .inspector import InspectorTarget

            normalized_targets = []
            for target in self.inspector_targets:
                if isinstance(target, str):
                    # Convert string to InspectorTarget enum
                    try:
                        normalized_targets.append(InspectorTarget(target.lower()))
                    except ValueError:
                        # If it's not a valid InspectorTarget value, keep as is
                        normalized_targets.append(target)
                else:
                    # Already an InspectorTarget or other type
                    normalized_targets.append(target)
            self.inspector_targets = normalized_targets

        # TODO: Re-enable this validation after backend data consistency is fixed
        # if self.agents and (self.tasks or self.tools):
        #     raise ValueError(
        #         "Team agents cannot have tasks or tools. Please remove the tasks or tools and try again."
        #     )

    def mark_as_deleted(self) -> None:
        """Mark the agent as deleted by setting status to DELETED and calling parent method."""
        from .enums import AssetStatus

        self.status = AssetStatus.DELETED
        super().mark_as_deleted()

    def before_run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]:
        """Hook called before running the agent to validate and prepare state."""
        # First, validate that all dependencies are saved before allowing run
        # This prevents auto-saving from masking the validation issue
        self._validate_run_dependencies()

        # If the agent is draft or not set, and it is modified,
        # implicitly save it as draft
        if self.status in [AssetStatus.DRAFT, None]:
            if self.is_modified:
                self.save(as_draft=True)
        elif self.status == AssetStatus.ONBOARDED:
            if self.is_modified:
                raise ValueError("Agent is onboarded and cannot be modified unless you explicitly save it.")

        # Initialize progress tracker if progress_format is provided
        # progress_format being None (default) means no progress tracking
        progress_format = kwargs.get("progress_format")
        if progress_format is not None:
            from .agent_progress import AgentProgressTracker, ProgressFormat

            progress_verbosity = kwargs.get("progress_verbosity", 1)
            progress_truncate = kwargs.get("progress_truncate", True)

            fmt = ProgressFormat(progress_format)

            self._progress_tracker = AgentProgressTracker(
                poll_func=lambda url: self.poll(url),
                poll_interval=0.05,
                max_polls=None,
            )
            self._progress_tracker.start(
                format=fmt,
                verbosity=progress_verbosity,
                truncate=progress_truncate,
            )
        else:
            self._progress_tracker = None

        return None

    def on_poll(self, response: AgentRunResult, **kwargs: Unpack[AgentRunParams]) -> None:
        """Hook called after each poll to update progress display.

        Args:
            response: The poll response containing progress information
            **kwargs: Run parameters
        """
        # Always update progress tracker, including on final completed response
        # This ensures the last step's completion state is displayed before finish() is called
        if self._progress_tracker is not None:
            self._progress_tracker.update(response)

    def after_run(
        self,
        result: Union[AgentRunResult, Exception],
        *args: Any,
        **kwargs: Unpack[AgentRunParams],
    ) -> Optional[AgentRunResult]:
        """Hook called after running the agent for result transformation."""
        # Finish progress tracking if enabled
        if self._progress_tracker is not None:
            if not isinstance(result, Exception):
                self._progress_tracker.finish(result)
            self._progress_tracker = None

        # Set the context on the result for debug() method support
        if not isinstance(result, Exception):
            result._context = self.context

        return None  # Return original result

    _SNAKE_TO_CAMEL: ClassVar[Dict[str, str]] = {
        "session_id": "sessionId",
        "allow_history_and_session_id": "allowHistoryAndSessionId",
        "execution_params": "executionParams",
        "run_response_generation": "runResponseGeneration",
    }

    _EXEC_PARAMS_MAP: ClassVar[Dict[str, str]] = {
        "output_format": "outputFormat",
        "max_tokens": "maxTokens",
        "max_iterations": "maxIterations",
        "max_time": "maxTime",
        "expected_output": "expectedOutput",
    }

    def run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        """Run the agent with optional progress display.

        Args:
            *args: Positional arguments (first arg is treated as query)
            query: The query to run
            progress_format: Display format - "status" or "logs". If None (default),
                           progress tracking is disabled.
            progress_verbosity: Detail level 1-3 (default: 1)
            progress_truncate: Truncate long text (default: True)
            **kwargs: Additional run parameters

        Returns:
            AgentRunResult: The result of the agent execution
        """
        if len(args) > 0:
            kwargs["query"] = args[0]
            args = args[1:]

        return super().run(*args, **kwargs)

    def run_async(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        """Run the agent asynchronously.

        Args:
            *args: Positional arguments (first arg is treated as query)
            query: The query to run
            **kwargs: Additional run parameters

        Returns:
            AgentRunResult: The result of the agent execution. Use ``result.url``
                to poll for completion via ``sync_poll(result.url)`` or
                ``client.get(result.url)``. Do not construct
                ``/sdk/runs/{execution_id}`` — that endpoint is not supported
                for agent runs.
        """
        if len(args) > 0:
            kwargs["query"] = args[0]
            args = args[1:]

        return super().run_async(**kwargs)

    def _resolve_poll_url(self, poll_url: str) -> str:
        """Resolve a poll URL or bare execution ID to a full poll URL.

        If *poll_url* is already a full URL (starts with ``http``), it is
        returned unchanged.  Otherwise it is treated as an execution ID and
        the correct agent-specific poll URL is constructed from
        ``POLL_URL_TEMPLATE``.

        This removes the need for callers to know the backend URL pattern,
        which is *not* the generic ``/sdk/runs/{id}`` path but rather
        ``/sdk/agents/{id}/result``.
        """
        if not poll_url:
            raise ValueError("poll_url must be a full URL or non-empty execution ID")
        if poll_url.startswith(("http://", "https://")):
            return poll_url
        backend_url = self.context.backend_url.rstrip("/")
        path = self.POLL_URL_TEMPLATE.format(execution_id=poll_url)
        return f"{backend_url}/{path}"

    def poll(self, poll_url: str) -> AgentRunResult:
        """Poll for the result of an asynchronous agent execution.

        Unlike the base implementation, *poll_url* may be either a full URL
        (as returned in ``AgentRunResult.url``) **or** a bare execution ID.
        When an execution ID is provided the correct
        ``/sdk/agents/{id}/result`` endpoint is used automatically, avoiding
        the common mistake of calling the unsupported
        ``/sdk/runs/{id}`` endpoint.

        Args:
            poll_url: Full poll URL or execution ID.

        Returns:
            AgentRunResult with current execution status.
        """
        return super().poll(self._resolve_poll_url(poll_url))

    def sync_poll(self, poll_url: str, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        """Poll until an asynchronous agent execution completes.

        Accepts either a full URL or a bare execution ID (see
        :meth:`poll` for details).

        Args:
            poll_url: Full poll URL or execution ID.
            **kwargs: Run parameters including ``timeout`` and ``wait_time``.

        Returns:
            AgentRunResult with final execution status.
        """
        return super().sync_poll(self._resolve_poll_url(poll_url), **kwargs)

    def _validate_expected_output(self) -> None:
        # Skip validation if expected_output is None (it's optional)
        if self.expected_output is None:
            return

        if self.output_format == OutputFormat.JSON.value:
            # Check if expected_output is a valid JSON type
            is_valid = isinstance(self.expected_output, (str, dict, BaseModel)) or (
                isinstance(self.expected_output, type) and issubclass(self.expected_output, BaseModel)
            )
            if not is_valid:
                raise ValueError(
                    "Expected output must be a valid JSON object, dict, string, or Pydantic BaseModel class/instance"
                )

            if isinstance(self.expected_output, str):
                try:
                    json.loads(self.expected_output)
                except json.JSONDecodeError:
                    raise ValueError("Expected output must be a valid JSON string or dict or pydantic model")
        elif self.output_format in [
            OutputFormat.MARKDOWN.value,
            OutputFormat.TEXT.value,
        ]:
            if not isinstance(self.expected_output, str):
                raise ValueError("Expected output must be a string for TEXT/MARKDOWN formats")

    def save(self, *args: Any, **kwargs: Any) -> "Agent":
        """Save the agent with dependency management.

        This method extends the base save functionality to handle saving of dependent
        child components before the agent itself is saved.

        Args:
            *args: Positional arguments passed to parent save method.
            save_subcomponents: bool - If True, recursively save all unsaved child components (default: False)
            as_draft: bool - If True, save agent as draft status (default: False)
            **kwargs: Other attributes to set before saving

        Returns:
            Agent: The saved agent instance

        Raises:
            ValueError: If child components are not saved and save_subcomponents is False
        """
        save_subcomponents = kwargs.pop("save_subcomponents", False)

        # Save all child components recursively if requested
        if save_subcomponents:
            self._save_subcomponents()

        # Validate that all dependencies are saved before proceeding
        self._validate_dependencies()

        # Call the parent save method
        return super().save(*args, **kwargs)

    def _save_subcomponents(self) -> None:
        """Recursively save all unsaved child components."""
        failed_components = []

        # Save tools
        if self.tools:
            for i, tool in enumerate(self.tools):
                if hasattr(tool, "save") and hasattr(tool, "id") and not tool.id:
                    try:
                        tool.save()
                    except Exception as e:
                        tool_name = getattr(tool, "name", f"tool_{i}")
                        failed_components.append(("tool", tool_name, str(e)))

        # Save agents (recursively)
        if hasattr(self, "_original_agents") and self._original_agents:
            for i, agent in enumerate(self._original_agents):
                if isinstance(agent, (str, dict)):  # Already an ID
                    continue
                if hasattr(agent, "save") and hasattr(agent, "id") and not agent.id:
                    try:
                        agent.save(save_subcomponents=True)
                    except Exception as e:
                        agent_name = getattr(agent, "name", f"agent_{i}")
                        failed_components.append(("agent", agent_name, str(e)))

        if failed_components:
            error_details = "; ".join(
                [f"{comp_type} '{name}': {error}" for comp_type, name, error in failed_components]
            )
            raise ValueError(f"Failed to save {len(failed_components)} component(s): {error_details}")

    def _validate_run_dependencies(self) -> None:
        """Validate that all child components are saved before running."""
        unsaved_components = []

        # Check tools
        if self.tools:
            for tool in self.tools:
                if hasattr(tool, "id") and not tool.id:
                    unsaved_components.append(f"tool '{tool.name}'")

        # Check agents
        if hasattr(self, "_original_agents") and self._original_agents:
            for agent in self._original_agents:
                if isinstance(agent, (str, dict)):  # Already an ID
                    continue
                if hasattr(agent, "id") and not agent.id:
                    agent_name = getattr(agent, "name", "unnamed")
                    unsaved_components.append(f"agent '{agent_name}'")

        if unsaved_components:
            components_list = ", ".join(unsaved_components)
            raise ValueError(
                f"Component(s) {components_list} must be saved before running the agent. "
                "Use agent.save(save_subcomponents=True) to automatically save all child components, "
                "or save each component individually before running."
            )

    def _validate_dependencies(self) -> None:
        """Validate that all child components are saved."""
        unsaved_components = []

        # Check tools
        if self.tools:
            for tool in self.tools:
                if hasattr(tool, "id") and not tool.id:
                    tool_name = getattr(tool, "name", "unnamed")
                    unsaved_components.append(f"tool '{tool_name}'")

        # Check agents
        if hasattr(self, "_original_agents") and self._original_agents:
            for agent in self._original_agents:
                if isinstance(agent, (str, dict)):  # Already an ID
                    continue
                if hasattr(agent, "id") and not agent.id:
                    agent_name = getattr(agent, "name", "unnamed")
                    unsaved_components.append(f"agent '{agent_name}'")

        if unsaved_components:
            components_list = ", ".join(unsaved_components)
            raise ValueError(
                f"Component(s) {components_list} must be saved before saving the agent. "
                "Use agent.save(save_subcomponents=True) to automatically save all child components."
            )

    def before_save(self, *args: Any, **kwargs: Any) -> Optional[dict]:
        """Callback to be called before the resource is saved.

        Handles status transitions based on save type.
        """
        as_draft = kwargs.pop("as_draft", False)
        if as_draft:
            self.status = AssetStatus.DRAFT
        else:
            self.status = AssetStatus.ONBOARDED

        self._validate_expected_output()

        return None

    def after_clone(self, result: Union["Agent", Exception], **kwargs: Any) -> Optional["Agent"]:
        """Callback called after the agent is cloned.

        Sets the cloned agent's status to DRAFT.
        """
        if isinstance(result, Agent):
            result.status = AssetStatus.DRAFT
        return None

    @classmethod
    def search(
        cls: type["Agent"],
        query: Optional[str] = None,
        **kwargs: Unpack[BaseSearchParams],
    ) -> "Page[Agent]":
        """Search agents with optional query and filtering.

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

    @staticmethod
    def _normalize_tool_dict_for_api(tool_dict: dict) -> dict:
        """Convert snake_case keys in a tool dict to the camelCase the API expects."""
        _KEY_MAP = {
            "asset_id": "assetId",
            "allow_multi": "allowMulti",
            "supports_variables": "supportsVariables",
        }
        result = {}
        for k, v in tool_dict.items():
            api_key = _KEY_MAP.get(k, k)
            if api_key == "parameters" and isinstance(v, list):
                result[api_key] = [Agent._normalize_parameter_for_api(p) for p in v]
            else:
                result[api_key] = v
        return result

    @staticmethod
    def _normalize_parameter_for_api(param: dict) -> dict:
        """Convert snake_case keys in a parameter definition to camelCase for the API.

        Handles both flat Model parameters (top-level keys) and nested Tool
        parameters (keys inside the 'inputs' dict).
        """
        _KEY_MAP = {
            "allow_multi": "allowMulti",
            "supports_variables": "supportsVariables",
        }
        result = {}
        for k, v in param.items():
            api_key = _KEY_MAP.get(k, k)
            if k == "inputs" and isinstance(v, dict):
                result[api_key] = {
                    input_name: {_KEY_MAP.get(ik, ik): iv for ik, iv in input_val.items()}
                    for input_name, input_val in v.items()
                }
            else:
                result[api_key] = v
        return result

    def build_save_payload(self, **kwargs: Any) -> dict:
        """Build the payload for the save action."""
        # Import Inspector from v2 module
        from .inspector import Inspector

        # Pre-serialize inspectors before to_dict() to avoid dataclass_json issues
        original_inspectors = self.inspectors
        if self.inspectors:
            serialized_inspectors = []
            for inspector in self.inspectors:
                if isinstance(inspector, Inspector):
                    # Use Inspector's to_dict method which handles callable policy serialization
                    serialized_inspectors.append(inspector.to_dict())
                elif isinstance(inspector, dict):
                    # Already serialized
                    serialized_inspectors.append(inspector)
                else:
                    raise ValueError(f"Inspector must be Inspector instance or dict, got {type(inspector)}")
            self.inspectors = serialized_inspectors

        # Pre-serialize inspector_targets to strings (enum values)
        from .inspector import InspectorTarget

        original_inspector_targets = self.inspector_targets
        if self.inspector_targets:
            serialized_targets = []
            for target in self.inspector_targets:
                if isinstance(target, InspectorTarget):
                    serialized_targets.append(target.value)
                elif isinstance(target, str):
                    serialized_targets.append(target)
                else:
                    serialized_targets.append(str(target))
            self.inspector_targets = serialized_targets

        # Now call to_dict() with inspectors and inspector_targets already serialized
        payload = self.to_dict()

        # Restore original values
        self.inspectors = original_inspectors
        self.inspector_targets = original_inspector_targets

        # Convert {{var}} to {var} in instructions and description for backend compatibility (v1 format)
        # User writes: {{language}} → Backend receives: {language}
        if payload.get("instructions"):
            payload["instructions"] = re.sub(r"\{\{(\w+)\}\}", r"{\1}", payload["instructions"])
        if payload.get("description"):
            payload["description"] = re.sub(r"\{\{(\w+)\}\}", r"{\1}", payload["description"])

        # Convert tools intelligently based on their type
        converted_assets = []
        if self.tools:
            for tool in self.tools:
                if isinstance(tool, ToolableMixin):
                    converted_assets.append(self._normalize_tool_dict_for_api(tool.as_tool()))
                elif isinstance(tool, dict):
                    converted_assets.append(self._normalize_tool_dict_for_api(tool))
                else:
                    raise ValueError(
                        "A tool in the agent must be a Tool, Model, ToolableMixin instance, or a dictionary."
                    )

        # Update the payload with converted assets
        payload["tools"] = converted_assets

        payload["model"] = {"id": self.llm}

        # Convert agents to API format, resolving IDs from original objects
        if hasattr(self, "_original_agents") and self._original_agents:
            converted_agents = []
            for agent in self._original_agents:
                if isinstance(agent, str):
                    agent_id = agent
                elif isinstance(agent, dict):
                    agent_id = agent.get("id")
                else:
                    agent_id = agent.id  # Get current ID from Agent object
                if not agent_id:
                    raise ValueError("All agents must be saved before saving the team agent.")
                converted_agents.append({"id": agent_id, "inspectors": []})
            payload["agents"] = converted_agents

        # Handle BaseModel expected_output for save operation
        # We don't send expected_output in the save payload - it's runtime-only
        if "expectedOutput" in payload:
            expected_output = payload["expectedOutput"]
            if isinstance(expected_output, type) and issubclass(expected_output, BaseModel):
                # Remove BaseModel classes from save payload - they're not stored server-side
                payload.pop("expectedOutput")
            elif isinstance(expected_output, BaseModel):
                # Convert BaseModel instance to dict for save
                payload["expectedOutput"] = expected_output.model_dump()

        return payload

    def build_run_payload(self, **kwargs: Unpack[AgentRunParams]) -> dict:
        """Build the payload for the run action."""
        # Extract execution_params if provided, otherwise use defaults
        execution_params = kwargs.pop("execution_params", {})

        # Normalize snake_case keys to camelCase for the API
        execution_params = {self._EXEC_PARAMS_MAP.get(k, k): v for k, v in execution_params.items()}

        # Set default values for execution_params if not provided
        defaults = {
            "outputFormat": self.output_format,
            "maxTokens": getattr(self, "max_tokens", 2048),
            "maxIterations": getattr(self, "max_iterations", 5),
            "maxTime": 300,
        }

        for k, v in defaults.items():
            execution_params.setdefault(k, v)

        # Handle BaseModel conversion for expectedOutput (following legacy pattern)
        # Use agent's expected_output if none provided in execution_params
        if "expectedOutput" not in execution_params:
            execution_params["expectedOutput"] = self.expected_output

        expected_output = execution_params["expectedOutput"]

        # For non-JSON formats, don't send empty string expected_output
        if execution_params.get("outputFormat") in ["text", "markdown"] and expected_output == "":
            execution_params["expectedOutput"] = None
        elif (
            expected_output is not None and isinstance(expected_output, type) and issubclass(expected_output, BaseModel)
        ):
            execution_params["expectedOutput"] = expected_output.model_json_schema()
        elif isinstance(expected_output, BaseModel):
            execution_params["expectedOutput"] = expected_output.model_dump()

        # Handle run_response_generation with default value of False
        run_response_generation = kwargs.pop("run_response_generation", False)

        # Process variables for instruction/description placeholders (sent to backend for substitution)
        variables = kwargs.pop("variables", None) or {}
        query = kwargs.pop("query", None)

        # Build input_data dict with query and variables
        if query is not None:
            if isinstance(query, dict):
                input_data = query.copy()
            else:
                input_data = {"input": query}

            # Add all provided variables to input_data for backend processing (same as v1)
            # User provides: {"persona": "good"} → Backend receives: {"persona": "good"}
            # Backend will substitute {{persona}} placeholders in instructions/description
            input_data.update(variables)

            # Use the processed input_data as query
            query = input_data

        # Build the payload according to Swagger specification
        payload = {
            "id": self.id,
            "executionParams": execution_params,
            "runResponseGeneration": run_response_generation,
        }

        # Add query back if present
        if query is not None:
            payload["query"] = query

        # Translate remaining snake_case kwargs to camelCase for the API
        for key, value in kwargs.items():
            if value is not None:
                api_key = self._SNAKE_TO_CAMEL.get(key, key)
                payload[api_key] = value

        return payload

    def generate_session_id(self, history: Optional[List[ConversationMessage]] = None) -> str:
        """Generate a unique session ID for agent conversations.

        Creates a unique session identifier based on the agent ID and current timestamp.
        If conversation history is provided, it attempts to initialize the session on the
        server to enable context-aware conversations.

        Args:
            history: Previous conversation history. Each message should contain
                'role' (either 'user' or 'assistant') and 'content' keys.
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
        if not self.id:
            self.save(as_draft=True)

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
                session_id=session_id,
                history=history,
                execution_params={
                    "max_tokens": 2048,
                    "max_iterations": 10,
                    "output_format": OutputFormat.TEXT.value,
                    "expected_output": None,
                },
                allow_history_and_session_id=True,
            )

            # If we got a polling URL, poll for completion
            if result.url and not result.completed:
                final_result = self.sync_poll(result.url, timeout=300, wait_time=0.5)

                if final_result.status == ResponseStatus.SUCCESS:
                    return session_id
                else:
                    logging.error(f"Session {session_id} initialization failed: {final_result}")
                    return session_id
            else:
                # Direct completion or no polling needed
                return session_id

        except Exception as e:
            logging.error(f"Failed to initialize session {session_id}: {e}")
            return session_id
