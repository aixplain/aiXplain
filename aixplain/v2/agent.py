"""Agent module for aiXplain v2 SDK."""

import json
import logging
import re
import warnings
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, List, Optional, Any, Dict, Tuple, Union, Text
from typing_extensions import Unpack, NotRequired, TypedDict, Literal
from dataclasses_json import dataclass_json, config

from pydantic import BaseModel

from .enums import AssetStatus, ResponseStatus
from .model import Model
from .skill import Skill
from .mixins import ToolableMixin
from ..utils.user_info_utils import build_run_metadata

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
    with_hooks,
)

if TYPE_CHECKING:
    from .session import ExecutionConfig, Session


logger = logging.getLogger(__name__)


# Type definitions for conversation history
class ConversationMessage(TypedDict):
    """Type definition for a conversation message in agent history.

    Attributes:
        role: The role of the message sender, either 'user' or 'assistant'
        content: The text content of the message
        attachments: Optional pre-built attachment dicts (url, name, type)
        files: Optional local file paths to upload and attach
    """

    role: Literal["user", "assistant"]
    content: str
    attachments: NotRequired[Optional[List[Dict[str, Any]]]]
    files: NotRequired[Optional[List[Any]]]


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


class ContextOverflowStrategy(str, Enum):
    """Strategy applied when input messages exceed the model's context window.

    Attributes:
        TRUNCATE: Remove the oldest chat-history messages until the context fits.
        SUMMARIZE: Replace the full chat history with an LLM-generated summary.
    """

    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"


RoleModelRef = Union[str, Dict[str, Any], Model]


def _decode_role_ref(value: Any) -> Any:
    """Decode a backend role-ref response (``{id, name?, parameters?}``) for the SDK.

    Used as the ``decoder`` for ``llm`` / ``supervisor`` / ``planner`` /
    ``response_generator`` so ``from_dict`` (called by ``_create`` after a
    save POST and any subsequent fetch) can re-hydrate these fields from the
    V2 DTO response — which carries ``model`` / ``supervisor`` / ``planner``
    / ``responder`` as nested objects with ``parameters: [{name, value}]``.

    Returns:
        ``None`` if the response is null or has no ``id``.
        The original string if the response is a bare id.
        Otherwise ``{id, name?, parameters?: {name: value}}`` — parameters
        are flattened from the wire ``NameValue[]`` list into a dict for
        ergonomic in-Python access. The SDK's ``_extract_role_parameters``
        round-trips this back to ``[{name, value}]`` on the next run.
    """
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return value
    if value.get("id") is None:
        return None
    result: Dict[str, Any] = {"id": value["id"]}
    name = value.get("name")
    if name:
        result["name"] = name
    params = value.get("parameters")
    if params:
        if isinstance(params, list):
            flattened: Dict[str, Any] = {}
            for item in params:
                if isinstance(item, dict) and "name" in item:
                    flattened[item["name"]] = item.get("value")
            if flattened:
                result["parameters"] = flattened
        elif isinstance(params, dict):
            result["parameters"] = params
    return result


def _role_field(*, save_key: str, default: Any = None) -> Any:
    """Declare a role-ref field on :class:`Agent`.

    Pairs ``exclude=lambda x: True`` (manual serialization via
    ``_apply_llm_fields_to_save_payload`` / ``_apply_llm_fields_to_run_payload``)
    with ``decoder=_decode_role_ref`` (auto-deserialize from the V2 DTO save /
    fetch response). The ``field_name`` controls the response key the decoder
    reads from — emission paths look up their own keys via the ``_ROLES``
    config below, so changing one wire name only touches one place.
    """
    return field(
        default=default,
        metadata=config(
            field_name=save_key,
            exclude=lambda x: True,
            decoder=_decode_role_ref,
        ),
    )


@dataclass(frozen=True)
class _RoleSpec:
    """One row of role configuration shared by save / run / fetch.

    ``attr`` is the Python attribute on :class:`Agent`. ``save_key`` is the
    nested key emitted in :meth:`Agent.build_save_payload` and read by
    ``_decode_role_ref`` on a save / fetch response. ``run_key`` is the key
    under top-level ``modelParameters`` emitted in
    :meth:`Agent.build_run_payload`.
    """

    attr: str
    save_key: str
    run_key: str


_ROLES: List[_RoleSpec] = [
    _RoleSpec("llm", "model", "llm"),
    _RoleSpec("supervisor", "supervisor", "supervisor"),
    _RoleSpec("planner", "planner", "planner"),
    _RoleSpec("response_generator", "responder", "responder"),
]


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
    identifier: NotRequired[Optional[Text]]
    inspectors: NotRequired[Optional[List[Dict]]]
    run_response_generation: NotRequired[Optional[bool]]
    via_session: NotRequired[Optional[bool]]
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
    governance: Optional[Dict[str, Any]] = None
    _governance_status: Optional[str] = field(
        default=None, repr=False, metadata=config(field_name="governanceStatus", exclude=lambda x: True)
    )
    _governance_source: Optional[str] = field(
        default=None, repr=False, metadata=config(field_name="governanceSource", exclude=lambda x: True)
    )
    _governance_reason: Optional[str] = field(
        default=None, repr=False, metadata=config(field_name="governanceReason", exclude=lambda x: True)
    )

    def __post_init__(self) -> None:
        """Assemble the nested ``governance`` dict from the flat wire fields."""
        if self.governance is None:
            self.governance = {
                "status": self._governance_status,
                "source": self._governance_source,
                "reason": self._governance_reason,
            }


@dataclass_json
@dataclass
class AgentRunResult(Result):
    """Result from running an agent."""

    data: Optional[Union[AgentResponseData, Text]] = None  # Override type from base class
    session_id: Optional[Text] = field(default=None, metadata=config(field_name="sessionId"))
    request_id: Optional[Text] = field(default=None, metadata=config(field_name="requestId"))
    used_credits: float = field(default=0.0, metadata=config(field_name="usedCredits"))
    run_time: float = field(default=0.0, metadata=config(field_name="runTime"))
    diagnostic_error_codes: List[str] = field(default_factory=list, metadata=config(field_name="diagnosticErrorCodes"))

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

    DEFAULT_LLM = "69b7e5f1b2fe44704ab0e7d0"
    SUPPLIER = "aiXplain"

    RESPONSE_CLASS = AgentRunResult
    Task = Task
    OutputFormat = OutputFormat
    ContextOverflowStrategy = ContextOverflowStrategy

    # Core fields from Swagger
    instructions: Optional[str] = None
    status: AssetStatus = AssetStatus.DRAFT
    team_id: Optional[int] = field(default=None, metadata=config(field_name="teamId"))
    # ``llm`` / ``supervisor`` / ``planner`` / ``response_generator`` are
    # serialized manually (see ``_apply_llm_fields_to_save_payload`` and
    # ``_apply_llm_fields_to_run_payload``) and auto-deserialized via the
    # ``_role_field`` factory. The wire-name mapping is centralized in the
    # module-level ``_ROLES`` table.
    llm: Union[str, Dict[str, Any], "Model"] = _role_field(save_key="model", default=DEFAULT_LLM)

    # Asset and tool fields
    tools: Optional[List[Dict[str, Any]]] = field(default_factory=list, metadata=config(field_name="tools"))

    # Inspector and team mentalist/planner/supervisor/response-generator.
    inspector_id: Optional[str] = field(default=None, metadata=config(field_name="inspectorId"))
    planner: Optional[RoleModelRef] = _role_field(save_key="planner")
    supervisor: Optional[RoleModelRef] = _role_field(save_key="supervisor")
    response_generator: Optional[RoleModelRef] = _role_field(save_key="responder")

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

    # Skills (knowledge bundles) attached to the agent — Skill objects or ids,
    # the same way `tools` and `agents` are passed.
    skills: Optional[List[Union[str, "Skill"]]] = field(default_factory=list, metadata=config(field_name="skills"))

    # Output and execution fields
    output_format: Optional[Union[str, OutputFormat]] = field(
        default=OutputFormat.TEXT.value, metadata=config(field_name="outputFormat")
    )
    expected_output: Optional[Union[str, dict, BaseModel]] = field(
        default=None, metadata=config(field_name="expectedOutput")
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
    context_overflow_strategy: Optional[str] = field(
        default=None,
        metadata=config(field_name="contextOverflowStrategy"),
    )

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

        # Deserialize inspectors to Inspector objects so mutate-and-save round-trips.
        # Prebuilt inspectors travel as a lightweight {presetId, ...} reference
        # (no "name"/"evaluator"), so dispatch on shape before deserializing.
        if self.inspectors:
            from .inspector import Inspector, PrebuiltInspector

            self.inspectors = [
                (PrebuiltInspector.from_dict(inspector) if "presetId" in inspector else Inspector.from_dict(inspector))
                if isinstance(inspector, dict)
                else inspector
                for inspector in self.inspectors
            ]

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

        # Skills behave exactly like agents: keep the originals to resolve ids
        # at save time, and serialize as a list of ids.
        self._original_skills = list(self.skills or [])
        self.skills = [
            s if isinstance(s, str) else s.get("id") if isinstance(s, dict) else s.id for s in (self.skills or [])
        ]

        if isinstance(self.output_format, OutputFormat):
            self.output_format = self.output_format.value

        if isinstance(self.context_overflow_strategy, ContextOverflowStrategy):
            self.context_overflow_strategy = self.context_overflow_strategy.value

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

    def _start_progress_tracker(self, kwargs: Dict[str, Any]) -> None:
        """Initialize ``self._progress_tracker`` from progress kwargs (no-op if disabled)."""
        progress_format = kwargs.get("progress_format")
        if progress_format is None:
            self._progress_tracker = None
            return

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

    def _finish_progress_tracker(self, result: Union[AgentRunResult, Exception]) -> None:
        """Finalize the progress tracker; safe to call even if it was never started."""
        if self._progress_tracker is not None:
            if not isinstance(result, Exception):
                self._progress_tracker.finish(result)
            self._progress_tracker = None

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

        self._start_progress_tracker(kwargs)
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
        self._finish_progress_tracker(result)

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
        "context_overflow_strategy": "contextOverflowStrategy",
    }

    def run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        """Run the agent with optional progress display.

        Args:
            *args: Positional arguments (first arg is treated as query)
            query: The query to run
            via_session: When True, opt into the new sessions+messages
                run path: a Session is created (or reused via
                ``session_id``) carrying the supplied execution params
                as its ``executionConfig``, the user message is posted,
                and the run is awaited via session message polling.
                Default False keeps the legacy
                ``/v2/agents/{id}/run`` path. Sessions auto-created by
                ``via_session=True`` persist; clean up via
                ``agent.list_sessions()`` and ``session.delete()``.
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

        if kwargs.pop("via_session", False):
            return self._run_via_session(**kwargs)

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

        if kwargs.get("via_session"):
            raise NotImplementedError(
                "via_session=True is sync-only for now; use agent.run(...) or "
                "session.add_message() + session.messages() directly."
            )

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
        if self.output_format == OutputFormat.JSON.value:
            # JSON output requires an explicit schema; the empty default is not enough.
            if self.expected_output is None or self.expected_output == "":
                raise ValueError(
                    "output_format='json' requires expected_output (a JSON string, dict, or Pydantic BaseModel)."
                )

            # Check if expected_output is a valid JSON type
            is_valid = isinstance(self.expected_output, (str, dict, BaseModel)) or (
                isinstance(self.expected_output, type) and issubclass(self.expected_output, BaseModel)
            )
            if not is_valid:
                raise ValueError(
                    "expected_output must be a valid JSON object, dict, string, or Pydantic BaseModel class/instance."
                )

            if isinstance(self.expected_output, str):
                try:
                    json.loads(self.expected_output)
                except json.JSONDecodeError:
                    raise ValueError("expected_output must be a valid JSON string, dict, or Pydantic BaseModel.")
        elif self.output_format in [
            OutputFormat.MARKDOWN.value,
            OutputFormat.TEXT.value,
        ]:
            # expected_output is optional for TEXT/MARKDOWN.
            if self.expected_output is None:
                return
            if not isinstance(self.expected_output, str):
                raise ValueError("expected_output must be a string for TEXT/MARKDOWN formats.")

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

        # Save skills
        if getattr(self, "_original_skills", None):
            for i, skill in enumerate(self._original_skills):
                if isinstance(skill, (str, dict)):  # Already an ID
                    continue
                if hasattr(skill, "save") and hasattr(skill, "id") and not skill.id:
                    try:
                        skill.save()
                    except Exception as e:
                        skill_name = getattr(skill, "name", f"skill_{i}")
                        failed_components.append(("skill", skill_name, str(e)))

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

        # Check skills
        if getattr(self, "_original_skills", None):
            for skill in self._original_skills:
                if isinstance(skill, (str, dict)):  # Already an ID
                    continue
                if hasattr(skill, "id") and not skill.id:
                    skill_name = getattr(skill, "name", "unnamed")
                    unsaved_components.append(f"skill '{skill_name}'")

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

        # Check skills
        if getattr(self, "_original_skills", None):
            for skill in self._original_skills:
                if isinstance(skill, (str, dict)):  # Already an ID
                    continue
                if hasattr(skill, "id") and not skill.id:
                    skill_name = getattr(skill, "name", "unnamed")
                    unsaved_components.append(f"skill '{skill_name}'")

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

    def after_duplicate(self, result: Union["Agent", Exception], **kwargs: Any) -> Optional["Agent"]:
        """Callback called after the agent is duplicated.

        Sets the duplicated agent's status to DRAFT.
        """
        if isinstance(result, Agent):
            result.status = AssetStatus.DRAFT
        return None

    @with_hooks
    def duplicate(self, duplicate_subagents: bool = False, name: Optional[str] = None) -> "Agent":
        """Duplicate this agent on the aiXplain platform (server-side).

        Creates a server-side copy of this agent with a clean usage baseline.
        The duplicate inherits the original's ownership, team, and permissions
        but resets all usage and cost metrics.

        Args:
            duplicate_subagents: If True, recursively duplicates referenced subagents
                so the duplicate has independent copies. If False, the duplicate
                keeps references to the original subagents. Defaults to False.
            name: Custom name for the duplicate. If None, a unique name is
                auto-generated by the platform. Defaults to None.

        Returns:
            Agent: The newly created duplicate agent.

        Raises:
            ResourceError: If the duplication request fails.
        """
        from .resource import _flatten_asset_info

        payload = {
            "cloneSubagents": duplicate_subagents,
        }
        if name is not None:
            payload["name"] = name

        response_data = self._action(method="post", action_paths=["duplicate"], json=payload)

        response_data = _flatten_asset_info(dict(response_data)) if isinstance(response_data, dict) else response_data

        duplicated = Agent.from_dict(response_data)
        duplicated.context = self.context
        duplicated._update_saved_state()

        return duplicated

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

    @staticmethod
    def _input_values_for_api(inputs: Any) -> Dict[str, Any]:
        """Extract changed/non-null model input values into a plain dict."""
        if inputs is None:
            return {}

        if hasattr(inputs, "items"):
            raw = dict(inputs.items())
        else:
            raw = {key: value for key, value in vars(inputs).items() if not key.startswith("_")}

        return {Agent._snake_to_camel(key): value for key, value in raw.items() if value is not None}

    @staticmethod
    def _snake_to_camel(name: str) -> str:
        """Convert reasoning_effort -> reasoningEffort."""
        if "_" not in name:
            return name

        parts = name.split("_")
        return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])

    @staticmethod
    def _params_dict_to_namevalue_list(params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert ``{key: value}`` to the platform's ``[{name, value}]`` list shape.

        The backend uses ``NameValue[]`` rather than a free-form dict so model
        parameters fit cleanly into the GraphQL schema without hard-coding
        per-parameter field names.
        """
        return [{"name": k, "value": v} for k, v in params.items()]

    @classmethod
    def _extract_role_parameters(cls, ref: Union[str, Dict[str, Any], "Model", None]) -> Optional[List[Dict[str, Any]]]:
        """Pull a role ref's parameters out as a ``[{name, value}]`` list.

        Accepts the user-facing shapes ``str`` / ``dict({id, parameters})`` /
        ``Model``. Returns ``None`` when no parameters are set.
        """
        if ref is None or isinstance(ref, str):
            return None
        if isinstance(ref, dict):
            params = ref.get("parameters")
            if not params:
                return None
            if isinstance(params, list):
                return params  # already in NameValue shape
            if isinstance(params, dict):
                return cls._params_dict_to_namevalue_list(params)
            return None
        if isinstance(ref, Model):
            params = cls._input_values_for_api(getattr(ref, "inputs", None))
            if not params:
                return None
            return cls._params_dict_to_namevalue_list(params)
        return None

    @classmethod
    def _role_ref_to_save_manifest(cls, ref: Union[str, Dict[str, Any], "Model"]) -> Dict[str, Any]:
        """Build the V2 ``AgentModelInput`` shape: ``{id, parameters?: [{name, value}]}``."""
        if isinstance(ref, str):
            return {"id": ref}
        if isinstance(ref, dict):
            manifest: Dict[str, Any] = {"id": ref.get("id")}
            params = cls._extract_role_parameters(ref)
            if params:
                manifest["parameters"] = params
            return manifest
        if isinstance(ref, Model):
            manifest = {"id": ref.id}
            params = cls._extract_role_parameters(ref)
            if params:
                manifest["parameters"] = params
            return manifest
        raise TypeError(f"LLM ref must be a string id, dict, or Model, got {type(ref)}")

    @classmethod
    def _llm_ref_to_manifest(cls, ref: Union[str, Dict[str, Any], "Model"]) -> Dict[str, Any]:
        """Back-compat alias for :meth:`_role_ref_to_save_manifest`."""
        return cls._role_ref_to_save_manifest(ref)

    @classmethod
    def _role_model_ref_to_manifest(cls, ref: RoleModelRef) -> Dict[str, Any]:
        """Back-compat alias for :meth:`_role_ref_to_save_manifest`."""
        return cls._role_ref_to_save_manifest(ref)

    # Legacy top-level role keys to strip from any payload we emit. Lived on
    # earlier SDK versions; kept here so a stale serializer can't leak them
    # into either build_save_payload or build_run_payload output.
    _LEGACY_ROLE_KEYS: ClassVar[Tuple[str, ...]] = (
        "llmId",
        "supervisorId",
        "plannerId",
        "responseGeneratorId",
    )

    def _apply_llm_fields_to_save_payload(self, payload: Dict[str, Any]) -> None:
        """Populate the V2 save shape: nested ``model``/``supervisor``/``planner``/``responder``.

        Each entry is ``{id, parameters?: [{name, value}]}`` (matches backend
        ``AgentModelInput``). Driven by the module-level ``_ROLES`` table.
        """
        for spec in _ROLES:
            ref = getattr(self, spec.attr, None)
            if ref is not None:
                payload[spec.save_key] = self._role_ref_to_save_manifest(ref)
            else:
                payload.pop(spec.save_key, None)
        for k in self._LEGACY_ROLE_KEYS:
            payload.pop(k, None)

    def _apply_llm_fields_to_run_payload(self, payload: Dict[str, Any]) -> None:
        """Populate the V2 run shape: top-level ``modelParameters: {llm, supervisor, planner, responder}``.

        Each role's parameters are emitted only when set. The backend uses
        these as run-time overrides on top of persisted ``modelParameters``;
        IDs are not overridable at run time (they come from the saved agent).
        Driven by the module-level ``_ROLES`` table.
        """
        model_parameters: Dict[str, Any] = {}
        for spec in _ROLES:
            params = self._extract_role_parameters(getattr(self, spec.attr, None))
            if params:
                model_parameters[spec.run_key] = params
        if model_parameters:
            payload["modelParameters"] = model_parameters
        else:
            payload.pop("modelParameters", None)
        for k in self._LEGACY_ROLE_KEYS:
            payload.pop(k, None)

    def _apply_llm_fields_to_payload(self, payload: Dict[str, Any]) -> None:
        """Back-compat shim — preserves the old ``build_save_payload`` call site."""
        self._apply_llm_fields_to_save_payload(payload)

    @property
    def llm_id(self) -> str:
        """Return main LLM id whether llm is a string or Model."""
        if isinstance(self.llm, str):
            return self.llm
        if isinstance(self.llm, Model):
            return self.llm.id
        raise TypeError(f"LLM must be a string id or Model, got {type(self.llm)}")

    def build_save_payload(self, **kwargs: Any) -> dict:
        """Build the payload for the save action."""
        # Import Inspector from v2 module
        from .inspector import Inspector, PrebuiltInspector

        # Pre-serialize inspectors before to_dict() to avoid dataclass_json issues
        original_inspectors = self.inspectors
        if self.inspectors:
            serialized_inspectors = []
            for inspector in self.inspectors:
                if isinstance(inspector, (Inspector, PrebuiltInspector)):
                    serialized_inspectors.append(inspector.to_dict())
                elif isinstance(inspector, dict):
                    serialized_inspectors.append(inspector)
                else:
                    raise ValueError(f"Inspector must be Inspector, PrebuiltInspector, or dict, got {type(inspector)}")
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

        self._apply_llm_fields_to_payload(payload)

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

        # Convert skills to API format. Skills follow the same wire design as
        # tools: each is sent as an object (via as_tool()), never a bare id.
        if getattr(self, "_original_skills", None):
            converted_skills = []
            for skill in self._original_skills:
                if isinstance(skill, ToolableMixin):
                    skill_dict = skill.as_tool()
                elif isinstance(skill, dict):
                    skill_dict = skill
                elif isinstance(skill, str):
                    skill_dict = {"id": skill, "type": "skill", "asset_id": skill}
                else:
                    raise ValueError("A skill must be a Skill instance, a dict, or a skill id string.")
                if not skill_dict.get("id"):
                    raise ValueError("All skills must be saved before saving the agent.")
                converted_skills.append(self._normalize_tool_dict_for_api(skill_dict))
            payload["skills"] = converted_skills
        else:
            payload.pop("skills", None)

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
            "contextOverflowStrategy": getattr(self, "context_overflow_strategy", None),
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
        elif isinstance(expected_output, dict):
            # Backend expects executionParams.expectedOutput as a string.
            execution_params["expectedOutput"] = json.dumps(expected_output)

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
            "metaData": build_run_metadata(),
        }

        # Add query back if present
        if query is not None:
            payload["query"] = query
        # Translate remaining snake_case kwargs to camelCase for the API
        for key, value in kwargs.items():
            if value is not None:
                api_key = self._SNAKE_TO_CAMEL.get(key, key)
                payload[api_key] = value

        self._apply_llm_fields_to_run_payload(payload)
        return payload

    def generate_session_id(self, history: Optional[List[ConversationMessage]] = None) -> str:
        """Generate a session ID for agent conversations.

        .. deprecated::
            Use :meth:`create_session` instead, which returns a full
            backend-managed :class:`~aixplain.v2.session.Session` object.
            This method is a thin backward-compatible shim that delegates
            to ``create_session`` and returns only the new session's ID.
            It will be removed in a future release.

        Args:
            history: Optional conversation history to seed the session with.
                Each message must have 'role' and 'content' keys.

        Returns:
            str: The ID of the newly created backend-managed session.

        Raises:
            ValueError: If the history format is invalid.
        """
        warnings.warn(
            "generate_session_id() is deprecated and will be removed in a "
            "future release. Use create_session() instead, which returns a "
            "backend-managed Session object.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Preserve the legacy auto-save behavior: callers relied on this
        # method persisting an unsaved agent for them. create_session()
        # itself requires a saved agent and would otherwise raise.
        if not self.id:
            self.save(as_draft=True)

        session = self.create_session(history=history)
        return session.id

    def create_session(
        self,
        name: Optional[str] = None,
        history: Optional[List[ConversationMessage]] = None,
        execution_config: Optional[Union["ExecutionConfig", Dict[str, Any]]] = None,
        execution_params: Optional[Dict[str, Any]] = None,
        criteria: Optional[str] = None,
        evolve: Optional[str] = None,
        identifier: Optional[str] = None,
        run_response_generation: Optional[bool] = None,
    ) -> "Session":
        """Create a new backend-managed session for this agent.

        Args:
            name: Optional human-readable name for the session.
            history: Optional conversation history to seed the session with.
                Each message must have 'role' and 'content' keys.
                Messages may also include optional 'attachments'
                (pre-built dicts with url/name/type) and/or 'files'
                (local file paths to upload).
            execution_config: Full ExecutionConfig (or equivalent dict) to
                attach to the session. Subsequent user messages will run
                the agent with these parameters. Mutually exclusive with
                the individual ``execution_params``/``criteria``/etc.
                shortcuts below.
            execution_params: Backend execution params (output format, max
                tokens, etc.). Mirrors the ``execution_params`` argument
                accepted by ``agent.run()``.
            criteria: Free-form evaluation criteria sent to the agent.
            evolve: Evolution config as a JSON string.
            identifier: Free-form identifier the backend can echo back on
                messages.
            run_response_generation: Whether the agent should run its
                final response-generation step.

        Returns:
            Session: The created Session instance, pre-populated with
            history messages when provided.

        Raises:
            ValueError: If the agent has not been saved yet, if history
                format is invalid, or if both ``execution_config`` and
                shortcut kwargs are provided.

        Example:
            >>> session = agent.create_session(
            ...     name="My Chat",
            ...     execution_params={"max_tokens": 1024, "max_iterations": 10},
            ...     criteria="Be concise",
            ...     run_response_generation=True,
            ...     history=[
            ...         {"role": "user", "content": "Analyze this",
            ...          "files": ["/tmp/data.csv"]},
            ...         {"role": "assistant", "content": "Here are the results..."},
            ...     ],
            ... )
        """
        if not self.id:
            raise ValueError("Agent must be saved before creating a session. Call agent.save() first.")

        if history:
            validate_history(history)

        config = self._resolve_execution_config(
            execution_config=execution_config,
            execution_params=execution_params,
            criteria=criteria,
            evolve=evolve,
            identifier=identifier,
            run_response_generation=run_response_generation,
        )

        session = self.context.Session(agent_id=self.id, name=name, execution_config=config)
        session.save()

        if history:
            for message in history:
                session.add_message(
                    role=message["role"],
                    content=message["content"],
                    attachments=message.get("attachments"),
                    files=message.get("files"),
                )

        return session

    @staticmethod
    def _resolve_execution_config(
        execution_config: Optional[Union["ExecutionConfig", Dict[str, Any]]] = None,
        execution_params: Optional[Dict[str, Any]] = None,
        criteria: Optional[str] = None,
        evolve: Optional[str] = None,
        identifier: Optional[str] = None,
        run_response_generation: Optional[bool] = None,
    ) -> Optional["ExecutionConfig"]:
        """Combine the explicit and shortcut forms into one ExecutionConfig.

        Returns ``None`` when neither form supplies any value so the
        Session save payload omits ``executionConfig`` entirely.
        """
        from .session import ExecutionConfig

        shortcut_values = {
            "execution_params": execution_params,
            "criteria": criteria,
            "evolve": evolve,
            "identifier": identifier,
            "run_response_generation": run_response_generation,
        }
        has_shortcut = any(v is not None for v in shortcut_values.values())

        if execution_config is not None and has_shortcut:
            raise ValueError(
                "Pass either 'execution_config' or the individual shortcut "
                "kwargs (execution_params, criteria, evolve, identifier, "
                "run_response_generation), not both."
            )

        if execution_config is not None:
            return ExecutionConfig.coerce(execution_config)

        if has_shortcut:
            return ExecutionConfig(**shortcut_values)

        return None

    @staticmethod
    def _apply_run_overrides_to_session(session: "Session", kwargs: Dict[str, Any]) -> None:
        """Apply per-run execution overrides onto a reused session.

        When a caller reuses an existing ``session_id`` but also passes
        per-run execution kwargs (``execution_params`` / ``criteria`` /
        ``evolve`` / ``identifier`` / ``run_response_generation``), those
        overrides would otherwise be silently dropped — the run would
        execute with whatever ``executionConfig`` the session was created
        with. Here we merge the supplied overrides onto the session's
        stored config (fields not overridden are preserved) and, when the
        result differs from what's stored, persist it so the overrides
        take effect.

        We warn because this mutates the session's ``executionConfig`` for
        every subsequent message in the session, not just this run.
        """
        from .session import ExecutionConfig

        overrides = {
            "execution_params": kwargs.get("execution_params"),
            "criteria": kwargs.get("criteria"),
            "evolve": kwargs.get("evolve"),
            "identifier": kwargs.get("identifier"),
            "run_response_generation": kwargs.get("run_response_generation"),
        }
        provided = {key: value for key, value in overrides.items() if value is not None}
        if not provided:
            return

        current = session.execution_config
        base = {
            "execution_params": getattr(current, "execution_params", None),
            "criteria": getattr(current, "criteria", None),
            "evolve": getattr(current, "evolve", None),
            "identifier": getattr(current, "identifier", None),
            "run_response_generation": getattr(current, "run_response_generation", None),
        }
        merged = ExecutionConfig(**{**base, **provided})

        if current is not None and merged.to_api_dict() == current.to_api_dict():
            return

        warnings.warn(
            f"Per-run execution overrides ({', '.join(sorted(provided))}) were "
            f"passed alongside an existing session_id '{session.id}'. Updating "
            f"the session's stored executionConfig so the overrides take effect; "
            f"this also applies to every subsequent message in this session.",
            UserWarning,
            stacklevel=3,
        )
        session.execution_config = merged
        session.save()

    _LEGACY_ONLY_RUN_KWARGS: ClassVar[tuple] = (
        "tasks",
        "prompt",
        "inspectors",
        "history",
        "variables",
        "allow_history_and_session_id",
    )

    def _run_via_session(self, **kwargs: Any) -> AgentRunResult:
        """Run the agent through a session, using the legacy result endpoint.

        Flow:
        1. Get-or-create a Session carrying the supplied ``executionConfig``.
        2. POST a ``role="user"`` message via ``session.add_message`` — this
           triggers the agent run on the backend with the session's
           ``executionConfig``. Any ``attachments`` / ``files`` passed to
           ``run`` are forwarded onto the user message so the agent receives
           them (uploaded and attached by ``add_message``).
        3. Pull the agent run's ``requestId`` off the user message and
           hand it to ``self.sync_poll`` (the legacy
           ``/sdk/agents/{request_id}/result`` endpoint), which returns a
           fully populated ``AgentRunResult`` including ``data.steps``,
           ``execution_stats``, ``used_credits``, and ``run_time``.

        We don't poll session messages for the assistant reply — the
        backend's session→assistant-message persistence is incomplete on
        dev today, but the legacy result endpoint is fully populated for
        the run that the user message triggered.
        """
        self._validate_run_dependencies()

        offending = [k for k in self._LEGACY_ONLY_RUN_KWARGS if kwargs.get(k) is not None]
        if offending:
            raise ValueError(
                f"via_session=True does not support legacy run kwargs: {offending}. "
                "Drop them or run without via_session=True."
            )

        query = kwargs.get("query")
        if query is None:
            raise ValueError("via_session=True requires a query.")
        if not isinstance(query, str):
            raise ValueError("via_session=True only supports string queries.")

        session_id = kwargs.get("session_id")
        if session_id:
            session = self.context.Session.get(session_id)
            self._apply_run_overrides_to_session(session, kwargs)
        else:
            session = self.create_session(
                execution_params=kwargs.get("execution_params"),
                criteria=kwargs.get("criteria"),
                evolve=kwargs.get("evolve"),
                identifier=kwargs.get("identifier"),
                run_response_generation=kwargs.get("run_response_generation"),
            )

        user_msg = session.add_message(
            role="user",
            content=query,
            attachments=kwargs.get("attachments"),
            files=kwargs.get("files"),
        )
        if not user_msg.request_id:
            raise ValueError(
                f"Backend did not return a requestId on the user message for "
                f"session '{session.id}'; cannot poll the agent run result."
            )

        # Same progress-tracker plumbing as the legacy path: sync_poll calls
        # self.on_poll(...) on every iteration, which forwards to the tracker.
        self._start_progress_tracker(kwargs)
        try:
            result = self.sync_poll(
                user_msg.request_id,
                timeout=kwargs.get("timeout", 300),
                wait_time=kwargs.get("wait_time", 0.5),
            )
        except Exception as e:
            self._finish_progress_tracker(e)
            raise
        self._finish_progress_tracker(result)

        # The legacy /sdk/agents/{id}/result response doesn't always echo
        # back identifiers at the top level — back-fill from what we know
        # locally so result.session_id / result.request_id are not None
        # for via_session callers.
        if not result.session_id:
            result.session_id = session.id
        if result.data is not None and getattr(result.data, "session_id", None) in (None, ""):
            result.data.session_id = session.id
        if not result.request_id:
            result.request_id = user_msg.request_id
        result._context = self.context
        return result

    def list_sessions(self, status: Optional[str] = None) -> list:
        """List sessions for this agent.

        Args:
            status: Optional status filter (e.g. "active", "completed").

        Returns:
            List of Session instances belonging to this agent.

        Raises:
            ValueError: If the agent has not been saved yet.
        """
        if not self.id:
            raise ValueError("Agent must be saved before listing sessions. Call agent.save() first.")

        return self.context.Session.list(agent_id=self.id, status=status)
