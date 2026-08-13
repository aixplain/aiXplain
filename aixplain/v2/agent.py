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
        attachments: Optional attachments — hosted-URL/local-path strings or dicts
            with ``url`` or ``path`` (plus optional type/name/mimeType).
        files: Deprecated. Local file paths to upload — pass through ``attachments``.
    """

    role: Literal["user", "assistant"]
    content: str
    attachments: NotRequired[Optional[List[Union[str, Dict[str, Any]]]]]
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
        session: Conversation thread to run within. A
            :class:`~aixplain.v2.session.Session` instance or a session id
            string. Omit for a one-shot, stateless run. Replaces the removed
            ``via_session`` flag and id-only ``session_id``.
        query: The query to run
        variables: Variables to replace {{variable}} placeholders in instructions and description.
            The backend performs the actual substitution.
        tasks: List of tasks for the agent
        prompt: Custom prompt override
        history: Conversation history
        execution_params: Execution parameters (maxTokens, etc.). Passing
            ``max_iterations`` here is deprecated; set ``agent.budget.max_iterations``
            instead. A deprecated value is folded into ``budget.max_iterations``
            (the agent's budget wins on conflict) and the standalone key is not
            emitted.
        criteria: Criteria for evaluation
        evolve: Evolution parameters
        inspectors: Inspector configurations
        run_response_generation: Whether to run response generation. Defaults to False.
        attachments: Multimodal attachments for the turn.
            Each entry is a hosted-URL/local-path string or a dict with ``url`` or
            ``path`` (plus optional ``type``/``name``/``mimeType``). Local paths are
            uploaded to aiXplain storage automatically.
        files: Deprecated. Local file paths to upload — pass through ``attachments`` instead.
        progress_format: Display format - "status" (single line) or "logs" (timeline).
                        If None (default), progress tracking is disabled.
        progress_verbosity: Detail level - 1 (minimal), 2 (thoughts), 3 (full I/O)
        progress_truncate: Whether to truncate long text in progress display
    """

    session: NotRequired[Optional[Union["Session", Text]]]
    query: NotRequired[Optional[Union[Dict, Text]]]
    variables: NotRequired[Optional[Dict[str, Any]]]
    tasks: NotRequired[Optional[List[Any]]]
    prompt: NotRequired[Optional[Text]]
    history: NotRequired[Optional[List[ConversationMessage]]]
    execution_params: NotRequired[Optional[Dict[str, Any]]]
    criteria: NotRequired[Optional[Text]]
    evolve: NotRequired[Optional[Text]]
    identifier: NotRequired[Optional[Text]]
    inspectors: NotRequired[Optional[List[Dict]]]
    run_response_generation: NotRequired[Optional[bool]]
    attachments: NotRequired[Optional[List[Union[str, Dict[str, Any]]]]]
    files: NotRequired[Optional[List[Any]]]
    progress_format: NotRequired[Optional[Text]]
    progress_verbosity: NotRequired[Optional[int]]
    progress_truncate: NotRequired[Optional[bool]]


@dataclass_json
@dataclass
class Budget:
    """Budget caps governing an agent run (cost / duration / iterations).

    Every :class:`Agent` owns a ``budget`` (defaulting to an empty ``Budget()``),
    mutated in place via attribute access — mirroring ``model.inputs``::

        agent.budget.max_cost = 0.5
        agent.budget.max_iterations = 10

    The same object serves two roles: ``agent.save()`` persists it as the agent's
    default budget, and ``agent.run(...)`` sends its current state as the run-time
    budget (the backend merges the run-time budget field-by-field over the
    persisted default). The Python API is snake_case; serialization produces the
    agreed camelCase wire keys (``maxCost`` / ``maxDurationSeconds`` /
    ``maxIterations``). All fields are optional and ``None`` fields are dropped
    from ``to_dict()``.
    """

    max_cost: Optional[float] = field(
        default=None,
        metadata=config(field_name="maxCost", exclude=lambda v: v is None),
    )
    max_duration_seconds: Optional[float] = field(
        default=None,
        metadata=config(field_name="maxDurationSeconds", exclude=lambda v: v is None),
    )
    max_iterations: Optional[int] = field(
        default=None,
        metadata=config(field_name="maxIterations", exclude=lambda v: v is None),
    )


@dataclass_json
@dataclass
class Artifact:
    """A user-facing deliverable produced during an agent run.

    Artifacts are captured by the agent engine and come from two sources:

    - ``source="tool_output"`` — media a tool generated (image/audio/video/page).
      Carries a ``url``, usually a **presigned** URL.
    - ``source="workspace"`` — a file the agent wrote into its workspace.
      Carries inline UTF-8 text in ``content`` (binary workspace files are
      skipped by the engine; there is no uploader yet).

    Exactly one of ``url`` / ``content`` is populated.

    .. warning::
       ``url_expires_at`` is when the **presigned URL** dies, not the artifact.
       Observed in the wild: a 24h window on a generated image URL. If you
       persist artifact URLs (database, cache, sent email), re-host the bytes
       before ``url_expires_at`` or the links will rot.

    ``category`` and ``source`` are plain strings, not enums: the engine may add
    new media categories before this SDK knows about them, and an unknown value
    must pass through rather than raise.

    Both wire casings deserialize: the poll/``checkRequest`` path emits
    snake_case (``mime_type``) while the webhook body is camelCased
    (``mimeType``). If a payload somehow carries both spellings of a field, the
    one appearing last in the payload wins.
    """

    id: str = ""
    name: str = ""
    title: Optional[str] = None
    mime_type: Optional[str] = field(default=None, metadata=config(field_name="mimeType"))
    category: str = "other"
    source: str = ""
    tool_name: Optional[str] = field(default=None, metadata=config(field_name="toolName"))
    url: Optional[str] = None
    url_expires_at: Optional[str] = field(default=None, metadata=config(field_name="urlExpiresAt"))
    content: Optional[str] = None
    sha256: Optional[str] = None
    byte_size: Optional[int] = field(default=None, metadata=config(field_name="byteSize"))
    mentioned_in_answer: bool = field(default=False, metadata=config(field_name="mentionedInAnswer"))
    created_at: str = field(default="", metadata=config(field_name="createdAt"))

    @classmethod
    def _coerce_list(cls, value: Any) -> List["Artifact"]:
        """Decode an ``artifacts`` payload without ever raising.

        Used as the ``decoder=`` for :attr:`AgentResponseData.artifacts`.
        Non-list values yield ``[]``; individual entries that fail to decode are
        dropped rather than failing the whole response.
        """
        if not isinstance(value, list):
            return []
        artifacts: List["Artifact"] = []
        for item in value:
            if isinstance(item, cls):
                artifacts.append(item)
            elif isinstance(item, dict):
                try:
                    artifacts.append(cls.from_dict(item))
                except Exception:  # pragma: no cover - defensive; engine shape drift
                    logger.debug("Skipping undecodable artifact entry: %r", item)
        return artifacts


@dataclass_json
@dataclass
class AgentResponseData:
    """Data structure for agent response."""

    input: Optional[Any] = None
    output: Optional[Any] = None
    steps: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    session_id: Optional[str] = None
    execution_stats: Optional[Dict[str, Any]] = field(default=None, metadata=config(field_name="executionStats"))
    diagnostic_error_codes: List[str] = field(default_factory=list, metadata=config(field_name="diagnosticErrorCodes"))
    critiques: Optional[str] = ""
    # Declared Optional only to keep dataclasses_json quiet: an explicit
    # ``"artifacts": null`` on a non-Optional field makes it emit a
    # "non-optional type ... detected when decoding" RuntimeWarning on every
    # decode. The attribute itself is never None — ``__post_init__`` normalizes.
    artifacts: Optional[List[Artifact]] = field(
        default_factory=list,
        metadata=config(decoder=Artifact._coerce_list),
    )
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
        """Normalize ``artifacts`` and assemble ``governance`` from flat wire fields."""
        # Also runs for direct construction, which never touches the field
        # decoder: ``AgentResponseData(artifacts=[{...}])`` must type its raw
        # dicts the way v1 does, and an explicit ``artifacts=None`` must land on
        # ``[]`` rather than ``None``. Re-coercing an already-decoded list is a
        # cheap no-op, since ``Artifact`` instances pass straight through.
        self.artifacts = Artifact._coerce_list(self.artifacts)
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

    def __post_init__(self) -> None:
        """Promote diagnostic codes the backend nests under ``data``.

        The poll body carries them at ``data.diagnosticErrorCodes`` (or only
        inside ``executionStats`` on older builds), never top-level.
        """
        if not self.diagnostic_error_codes:
            self.diagnostic_error_codes = self._codes_from_data()

    def _codes_from_data(self) -> List[str]:
        """Extract diagnostic codes from ``data`` or its execution stats."""
        data = self.data
        if isinstance(data, AgentResponseData):
            if data.diagnostic_error_codes:
                return list(data.diagnostic_error_codes)
            stats = data.execution_stats
        elif isinstance(data, dict):
            codes = data.get("diagnosticErrorCodes") or data.get("diagnostic_error_codes")
            if codes:
                return list(codes)
            stats = data.get("executionStats") or data.get("execution_stats")
        else:
            return []
        if isinstance(stats, dict):
            codes = stats.get("diagnostic_error_codes") or stats.get("diagnosticErrorCodes")
            if codes:
                return list(codes)
        return []

    # Internal reference to client context for debug() method
    _context: Optional[Any] = field(
        default=None,
        repr=False,
        compare=False,
        metadata=config(exclude=lambda x: True),
        init=False,
    )

    @property
    def artifacts(self) -> List[Artifact]:
        """Deliverables produced during the run (see :class:`Artifact`).

        Always a list — empty when the run produced nothing, when artifact
        capture is disabled, or when the backend predates artifact support.
        """
        data = self.data
        if isinstance(data, AgentResponseData):
            return data.artifacts or []
        if isinstance(data, dict):
            # ``data`` is a bare dict when the result was built by hand rather
            # than decoded through ``from_dict``.
            return Artifact._coerce_list(data.get("artifacts"))
        return []

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
    # Deprecated: persisted iteration cap. Use ``budget=Budget(max_iterations=...)``
    # instead. Defaults to ``None`` (was previously ``5``) so a plain ``Agent(...)``
    # does not warn; any non-None value (explicit or via ``from_dict``) is folded
    # into ``budget`` and is never serialized as a standalone ``maxIterations``
    # (see ``build_save_payload``).
    max_iterations: Optional[int] = field(default=None, metadata=config(field_name="maxIterations"))
    # Budget (cost / duration / iterations) for this agent. Always a ``Budget``
    # instance — defaults to an empty ``Budget()``, never ``None`` — so callers
    # can mutate ``agent.budget.max_cost`` etc. without a None check (mirrors
    # ``model.inputs``). Assigning a dict/Budget/None is coerced back to a
    # ``Budget`` by ``__setattr__``. Excluded from ``to_dict()`` (so it never
    # counts toward ``is_modified``); serialized manually in ``build_save_payload``
    # (persisted default) and ``build_run_payload`` (run-time budget) via
    # ``_normalize_budget``.
    budget: "Budget" = field(
        default_factory=lambda: Budget(),
        metadata=config(field_name="budget", exclude=lambda v: True),
    )
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
        # Prebuilt guards and custom inspectors are the same Inspector type, so a
        # single deserialization path covers both.
        if self.inspectors:
            from .inspector import Inspector

            self.inspectors = [
                Inspector.from_dict(inspector) if isinstance(inspector, dict) else inspector
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

        # ``self.budget`` is already a ``Budget`` instance here: the generated
        # ``__init__`` assignment routed through ``__setattr__``, which coerces
        # any dict/Budget/None into a (never-None) ``Budget``.

        # Deprecated persisted ``max_iterations``: fold into ``budget.max_iterations``.
        # ``None`` (the default) means "not provided" so a plain ``Agent(...)`` never
        # warns; any non-None value (explicit or via ``from_dict``) is folded.
        if self.max_iterations is not None:
            warnings.warn(
                "Agent 'max_iterations' is deprecated; set agent.budget.max_iterations instead. "
                "It will be removed in a future release.",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.budget.max_iterations is None:
                self.budget.max_iterations = self.max_iterations
            else:
                warnings.warn(self._BUDGET_ITER_CONFLICT_MSG, UserWarning, stacklevel=2)

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

        # Inspector targets are plain strings (e.g. "input" | "steps" | "output"
        # or a sub-agent name); normalize the known stage values to lowercase.
        if self.inspector_targets:
            self.inspector_targets = [
                target.lower() if isinstance(target, str) and target.lower() in {"input", "steps", "output"} else target
                for target in self.inspector_targets
            ]

        # Hydrate plain tool dicts (e.g. from a get()/create response) into
        # mutable Tool/Model objects so callers can override per-tool parameters
        # via ``agent.tools[i].actions[...].inputs[...] = value``. Best-effort and
        # offline — see :meth:`_hydrate_tools`.
        self._hydrate_tools()
        # Snapshot the (post-hydration) tool objects so save can restore them
        # after the create response would otherwise overwrite them with dicts.
        self._original_tools = list(self.tools) if self.tools else []

        # TODO: Re-enable this validation after backend data consistency is fixed
        # if self.agents and (self.tasks or self.tools):
        #     raise ValueError(
        #         "Team agents cannot have tasks or tools. Please remove the tasks or tools and try again."
        #     )

    def __setattr__(self, name: str, value: Any) -> None:
        """Keep ``self.budget`` a (never-None) ``Budget`` instance.

        Assigning ``agent.budget`` a dict / ``Budget`` / ``None`` is coerced into
        a ``Budget`` so attribute access (``agent.budget.max_cost = ...``) always
        works and the invariant "budget is never None" holds (mirrors how
        ``Model.__setattr__`` coerces bulk ``inputs`` assignment). This runs for
        the generated ``__init__`` assignment too, so the field is a ``Budget``
        by the time ``__post_init__`` executes.
        """
        if name == "budget":
            coerced = self._coerce_budget(value)
            value = coerced if coerced is not None else Budget()
        super().__setattr__(name, value)

    @classmethod
    def _fold_legacy_max_iterations(cls, kvs: Any) -> Any:
        """Fold a legacy top-level ``maxIterations`` into the ``budget`` slot.

        Backend agents may still carry a top-level legacy ``maxIterations``. The
        public constructor (``Agent(max_iterations=...)``) emits a
        ``DeprecationWarning`` in ``__post_init__``, but deserialization must NOT
        warn — loading an agent the caller never configured should be silent.
        So we fold the legacy ``maxIterations`` straight into the ``budget`` slot
        (Budget wins silently if it already carries one) and drop the standalone
        key, so ``__post_init__`` sees ``max_iterations=None`` and the deprecation
        path never fires on load. Returns a copy; the caller's dict is untouched.
        """
        if isinstance(kvs, dict) and kvs.get("maxIterations") is not None:
            kvs = dict(kvs)  # shallow copy; never mutate the caller's dict
            legacy_iterations = kvs.pop("maxIterations")
            budget = kvs.get("budget")
            # Normalize to the camelCase wire shape so the nested fold is uniform
            # regardless of whether ``budget`` arrived snake_case, camelCase, or absent.
            normalized = cls._normalize_budget(budget) if budget is not None else {}
            # Budget wins silently on conflict; otherwise fill the empty slot.
            if normalized.get("maxIterations") is None:
                normalized["maxIterations"] = legacy_iterations
            kvs["budget"] = normalized
        return kvs

    def mark_as_deleted(self) -> None:
        """Mark the agent as deleted by setting status to DELETED and calling parent method."""
        from .enums import AssetStatus

        self.status = AssetStatus.DELETED
        super().mark_as_deleted()

    def _get_serializable_state(self) -> dict:
        """Serializable state used for change detection (``is_modified``).

        Tools are reduced to identity-only signatures (id + type, excluding
        per-input values) so that (a) ``to_dict()`` does not recurse into
        ``Tool`` / ``Model`` objects and crash, and (b) mutating a tool's action
        inputs does not mark the agent as modified — run-time tool-parameter
        overrides are ephemeral and must not trigger an auto-save or block an
        onboarded agent's run. Adding or removing a whole tool is still
        detected; ``save()`` persists changed values unconditionally.
        """
        original_tools = self.tools
        try:
            self.tools = [self._tool_identity(tool) for tool in original_tools or []]
            return super()._get_serializable_state()
        finally:
            self.tools = original_tools

    @staticmethod
    def _tool_identity(tool: Any) -> dict:
        """Return a stable id/type signature for a tool entry (no param values)."""
        if isinstance(tool, str):
            return {"id": tool}
        if isinstance(tool, dict):
            return {"id": tool.get("id"), "type": tool.get("type")}
        return {"id": getattr(tool, "id", None), "type": getattr(tool, "type", None)}

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
        "execution_params": "executionParams",
        "run_response_generation": "runResponseGeneration",
    }

    # ``max_iterations`` is intentionally absent: it is deprecated and folded into
    # ``budget.maxIterations`` (see ``_fold_iter_into_budget`` and the run path),
    # never emitted as a standalone ``executionParams.maxIterations``. The session
    # path (``ExecutionConfig`` in session.py) keeps the same invariant.
    _EXEC_PARAMS_MAP: ClassVar[Dict[str, str]] = {
        "output_format": "outputFormat",
        "max_tokens": "maxTokens",
        "max_time": "maxTime",
        "expected_output": "expectedOutput",
        "context_overflow_strategy": "contextOverflowStrategy",
    }

    # snake_case → camelCase wire keys for the nested executionParams.budget object.
    _BUDGET_PARAMS_MAP: ClassVar[Dict[str, str]] = {
        "max_cost": "maxCost",
        "max_duration_seconds": "maxDurationSeconds",
        "max_iterations": "maxIterations",
    }

    # Emitted (as a UserWarning) when a deprecated ``max_iterations`` and an
    # explicit ``budget.max_iterations`` are both set; Budget wins. Shared by the
    # constructor, the run path, and the session path so the text never drifts.
    _BUDGET_ITER_CONFLICT_MSG: ClassVar[str] = (
        "Both 'max_iterations' and budget.max_iterations are set; budget.max_iterations takes precedence."
    )

    @classmethod
    def _normalize_budget(cls, budget: Union[Dict, "Budget"]) -> dict:
        """Normalize a Budget instance or dict to the camelCase wire shape.

        Accepts a ``Budget`` instance, a snake_case dict, or a camelCase dict and
        returns a camelCase dict with ``None`` fields dropped. Unknown keys are
        passed through unchanged (forward compatibility).
        """
        if isinstance(budget, Budget):
            raw = budget.to_dict()  # already camelCase, None dropped
        else:
            raw = dict(budget)
        # Map snake_case keys to camelCase; pass camelCase (and unknown) keys through.
        normalized = {cls._BUDGET_PARAMS_MAP.get(k, k): v for k, v in raw.items()}
        # Never emit null fields.
        return {k: v for k, v in normalized.items() if v is not None}

    @classmethod
    def _coerce_budget(cls, budget: Optional[Union[Dict, "Budget"]]) -> Optional["Budget"]:
        """Coerce ``None`` / dict / ``Budget`` into a ``Budget`` instance.

        A dict may use snake_case or camelCase keys; it is normalized to the
        camelCase wire shape first so a single decoder handles both styles.
        ``None`` passes through as ``None`` (session's ExecutionConfig relies on
        this); ``Agent.__setattr__`` is what upgrades a ``None`` agent budget to
        an empty ``Budget()`` to keep ``agent.budget`` never-None.
        """
        if budget is None or isinstance(budget, Budget):
            return budget
        if isinstance(budget, dict):
            normalized = cls._normalize_budget(budget)
            return Budget(
                max_cost=normalized.get("maxCost"),
                max_duration_seconds=normalized.get("maxDurationSeconds"),
                max_iterations=normalized.get("maxIterations"),
            )
        raise TypeError(f"budget must be a Budget, dict, or None, got {type(budget)}")

    @classmethod
    def _fold_iter_into_budget(
        cls, budget: Optional[Union[Dict, "Budget"]], max_iterations: int
    ) -> "tuple[dict, bool]":
        """Fold a deprecated ``max_iterations`` into a budget (Budget wins on conflict).

        Pure: emits no warnings. Returns ``(normalized, conflicted)`` where
        ``normalized`` is the camelCase wire dict and ``conflicted`` is ``True``
        when the budget already carried ``maxIterations`` (so the deprecated value
        was dropped). The caller owns the conflict warning — it knows the right
        ``stacklevel`` for its own call depth (see the run and session paths).
        """
        normalized = cls._normalize_budget(budget) if budget is not None else {}
        if normalized.get("maxIterations") is not None:
            return normalized, True
        normalized["maxIterations"] = max_iterations
        return normalized, False

    def run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        """Run the agent with optional progress display.

        Args:
            *args: Positional arguments (first arg is treated as query)
            query: The query to run
            session: Run within a conversation thread. Accepts a
                :class:`~aixplain.v2.session.Session` instance or a session id
                string. When supplied, the run routes through the session path:
                the user message is posted to
                ``POST /v1/sessions/{id}/messages`` (carrying the session's
                ``executionConfig`` plus any per-run execution overrides) and the
                triggered agent run is awaited. Omit ``session`` for a one-shot,
                stateless run over ``POST /v2/agents/{id}/run``. There is no
                ``via_session`` flag and no id-only ``session_id`` — manage
                threads through ``aix.Session`` and pass them here.
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

        session = kwargs.pop("session", None)
        if session is not None:
            return self._run_with_session(session, **kwargs)

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

        if kwargs.pop("session", None) is not None:
            raise NotImplementedError(
                "session=… runs are sync-only for now; use agent.run(...) or "
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

        # Capture names before save because the backend response can rebuild self.tools without Integration objects.
        unconnected_integration_names = self._get_unconnected_integration_names()

        # Preserve the in-memory tool objects (carrying any per-tool parameter
        # overrides the caller set): a create response would otherwise replace
        # ``self.tools`` with backend dicts and drop those mutations.
        pre_save_tools = list(self.tools) if self.tools else []

        # Call the parent save method
        saved_agent = super().save(*args, **kwargs)

        # Restore the caller's tool objects, then re-hydrate any dict entries so
        # ``agent.tools[i]`` stays a mutable Tool/Model object after save.
        self.tools = pre_save_tools
        self._hydrate_tools()
        self._original_tools = list(self.tools) if self.tools else []

        # Re-baseline the saved state against the restored tool objects. The
        # parent save() captured it mid-flow from the response dicts; without
        # this, the restored objects would read as "modified" and a subsequent
        # run() on an onboarded agent would wrongly raise.
        self._update_saved_state()

        self._warn_for_unconnected_integrations(unconnected_integration_names)
        return saved_agent

    def _warn_for_unconnected_integrations(self, integration_names: Optional[List[str]] = None) -> None:
        """Warn when an agent is saved with integration definitions that need connection."""
        if integration_names is None:
            integration_names = self._get_unconnected_integration_names()
        if not integration_names or not self.id:
            return

        schema_url = f"https://studio.aixplain.com/build/{self.id}/schema"
        for integration_name in integration_names:
            warnings.warn(
                f"Warning: Integration '{integration_name}' is not connected. "
                f"Connect your unconnected integrations here: {schema_url}",
                UserWarning,
                stacklevel=2,
            )

    def _get_unconnected_integration_names(self) -> List[str]:
        """Return unique names for Integration objects used directly as tools."""
        from .integration import Integration

        if not self.tools:
            return []

        names = []
        seen = set()
        for tool in self.tools:
            if isinstance(tool, Integration):
                integration_name = tool.name or tool.id
                if integration_name and integration_name not in seen:
                    names.append(integration_name)
                    seen.add(integration_name)
        return names

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

    @classmethod
    def _normalize_tool_for_api(cls, tool: Any) -> dict:
        """Normalize one ``tools`` entry into the API dict shape.

        Per-tool parameter overrides are expressed by mutating the tool object's
        typed action inputs (``tool.actions[...].inputs[...] = value``); the
        current values are read back through the object's ``as_tool()`` snapshot
        (see :meth:`Tool.get_parameters` / :meth:`Model.get_parameters`).

        Accepts:

        - a :class:`ToolableMixin` (``Tool`` / ``Model`` / ``Integration``)
          whose ``as_tool()`` snapshot carries the correct ``type`` and current
          parameter values;
        - a plain string id — resolved to its ``as_tool()`` snapshot so the
          create payload gets the required ``type``;
        - an ``as_tool()`` snapshot dict (already carries ``type``) — passed
          through; a bare ``{"id": ...}`` attach dict is resolved for its type.
        """
        if isinstance(tool, ToolableMixin):
            return cls._normalize_tool_dict_for_api(tool.as_tool())
        if isinstance(tool, str):
            return cls._normalize_tool_dict_for_api(cls._resolve_tool_entry(tool))
        if isinstance(tool, dict):
            if tool.get("type") or not tool.get("id"):
                return cls._normalize_tool_dict_for_api(tool)
            return cls._normalize_tool_dict_for_api(cls._resolve_tool_entry(tool["id"], tool))
        raise ValueError(
            f"A tool must be a Tool, Model, ToolableMixin instance, a string id, or a dictionary, got {type(tool)}."
        )

    @classmethod
    def _resolve_tool_entry(cls, tool_id: str, attach: Optional[dict] = None) -> dict:
        """Build a typed tool dict for ``tool_id`` from its ``as_tool()`` snapshot.

        Resolves the asset by id (Tool, then Model) so the entry carries the
        backend-required ``type`` and other snapshot fields, then overlays any
        extra keys from the caller-provided attach dict. Falls back to a bare
        ``{"id": tool_id}`` when the id can't be resolved — preserving the prior
        behavior offline.
        """
        snapshot = cls._resolve_tool_snapshot(tool_id)
        entry: dict = dict(snapshot) if snapshot else {}
        entry["id"] = tool_id
        if isinstance(attach, dict):
            for key, value in attach.items():
                if key != "id":
                    entry[key] = value
        return entry

    @classmethod
    def _resolve_tool_snapshot(cls, tool_id: str) -> Optional[dict]:
        """Return the ``as_tool()`` snapshot for ``tool_id``, or ``None``.

        Tries the ``Tool`` resource first, then ``Model`` (mirroring how the
        platform resolves an asset id). Any failure (no client context,
        unknown id, network error) yields ``None`` so normalization degrades
        gracefully instead of raising.
        """
        context = getattr(cls, "context", None)
        if context is None:
            return None
        for resource_name in ("Tool", "Model"):
            resource = getattr(context, resource_name, None)
            if resource is None:
                continue
            try:
                return dict(resource.get(tool_id).as_tool())
            except Exception:
                continue
        return None

    def _hydrate_tools(self) -> None:
        """Convert plain tool dicts in ``self.tools`` into mutable objects.

        Runs from :meth:`__post_init__` (so it fires on ``get()``/``create``
        responses). Entries that are already ``Tool`` / ``Model`` /
        ``Integration`` objects, plain string ids, or unresolvable dicts are
        left untouched. Hydration is **offline**: the object's action inputs are
        reconstructed from the ``parameters`` snapshot embedded in the dict so
        reads and ``inputs[...] = value`` mutations do not require a network
        call. When the snapshot carries no parameters, the object is left to
        load its input specs lazily on first ``.actions`` access (matching a
        normal ``Tool.get``). Requires a client context; without one (e.g. an
        unbound ``Agent`` in unit tests) the raw entries are kept as-is.
        """
        context = getattr(self, "context", None)
        if context is None or not self.tools:
            return
        self.tools = [self._hydrate_tool_entry(entry, context) for entry in self.tools]

    def _hydrate_tool_entry(self, entry: Any, context: Any) -> Any:
        """Hydrate one ``tools`` entry into a Tool/Model object (best-effort)."""
        if not isinstance(entry, dict):
            return entry  # already a Tool/Model/Integration object or a string id
        tool_id = entry.get("id")
        if not tool_id:
            return entry

        parameters = entry.get("parameters")
        is_model = entry.get("type") == "model"
        try:
            if is_model:
                return self._build_model_tool(entry, context, parameters)
            return self._build_tool_tool(entry, context, parameters)
        except Exception:
            # Never let hydration break construction — fall back to the raw dict.
            return entry

    @staticmethod
    def _build_model_tool(entry: dict, context: Any, parameters: Any) -> Any:
        """Build a bound ``Model`` from a tool dict, seeding inputs from ``parameters``.

        ``parameters`` is the flat ``[{name, value, datatype, required, ...}]``
        list produced by ``Model.as_tool()``. It is turned into ``params`` so the
        rebuilt ``Model`` exposes working ``inputs`` (and ``as_tool()`` round-trips
        the current values offline).
        """
        from .model import Parameter

        params = []
        for param in parameters or []:
            if not isinstance(param, dict) or not param.get("name"):
                continue
            value = param.get("value")
            params.append(
                Parameter(
                    name=param["name"],
                    required=bool(param.get("required", False)),
                    data_type=param.get("datatype") or param.get("dataType"),
                    default_values=[value] if value is not None else [],
                )
            )
        model = context.Model(
            id=entry.get("id"),
            name=entry.get("name"),
            description=entry.get("description"),
            params=params or None,
        )
        model.context = context
        return model

    @staticmethod
    def _build_tool_tool(entry: dict, context: Any, parameters: Any) -> Any:
        """Build a bound ``Tool`` from a tool dict, seeding action inputs offline.

        ``parameters`` is the nested ``[{code, name, inputs: {code: {value, ...}}}]``
        list produced by ``Tool.as_tool()`` / ``Tool.get_parameters()``. When
        present, the tool's ``actions`` cache is pre-populated so mutations are
        offline; otherwise the tool loads its input specs lazily on first access.
        """
        from .actions import Action, Actions, Input, Inputs

        tool = context.Tool(
            id=entry.get("id"),
            name=entry.get("name"),
            description=entry.get("description"),
        )
        tool.context = context

        actions_map: Dict[str, Action] = {}
        for action_def in parameters or []:
            if not isinstance(action_def, dict):
                continue
            action_name = action_def.get("name") or action_def.get("code")
            if not action_name:
                continue
            input_objs: Dict[str, Input] = {}
            for code, spec in (action_def.get("inputs") or {}).items():
                if not isinstance(spec, dict):
                    continue
                input_objs[code] = Input(
                    name=code,
                    required=bool(spec.get("required", False)),
                    type=spec.get("datatype") or spec.get("dataType"),
                    value=spec.get("value"),
                    description=spec.get("description", "") or "",
                )
            actions_map[action_name] = Action(
                name=action_name, description=action_def.get("description"), inputs=Inputs(input_objs)
            )

        if actions_map:
            # Pre-populate the ``actions`` cached_property so reads/mutations are
            # offline. Also scope allowed_actions so as_tool() serializes them.
            tool.__dict__["actions"] = Actions(actions_map)
            tool.allowed_actions = list(actions_map.keys())
        return tool

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
                # Snapshot from ``as_tool()`` -> list of full parameter
                # definitions (current input values included); normalize each
                # definition's keys to camelCase.
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
        from .inspector import Inspector

        # Pre-serialize inspectors before to_dict() to avoid dataclass_json issues
        original_inspectors = self.inspectors
        if self.inspectors:
            serialized_inspectors = []
            for inspector in self.inspectors:
                if isinstance(inspector, Inspector):
                    serialized_inspectors.append(inspector.to_dict())
                elif isinstance(inspector, dict):
                    serialized_inspectors.append(inspector)
                else:
                    raise ValueError(f"Inspector must be Inspector or dict, got {type(inspector)}")
            self.inspectors = serialized_inspectors

        # Pre-serialize inspector_targets to strings
        original_inspector_targets = self.inspector_targets
        if self.inspector_targets:
            self.inspector_targets = [
                target if isinstance(target, str) else str(target) for target in self.inspector_targets
            ]

        # Null out tools before to_dict(): dataclass_json would otherwise recurse
        # into Tool/Model objects (which raises on their ``context`` descriptor).
        # The real tools payload is rebuilt from ``self.tools`` below.
        original_tools = self.tools
        self.tools = []

        # Now call to_dict() with inspectors and inspector_targets already serialized
        payload = self.to_dict()

        # Restore original values
        self.inspectors = original_inspectors
        self.inspector_targets = original_inspector_targets
        self.tools = original_tools

        # Budget is the single source of truth for the persisted iteration cap.
        # Drop the deprecated standalone ``maxIterations`` and emit the persisted
        # ``budget`` (camelCase) only when it carries at least one cap. (The
        # ``budget`` field is ``exclude=lambda v: True`` so ``to_dict()`` never
        # emits it — we build the wire shape explicitly below.)
        payload.pop("maxIterations", None)
        budget = getattr(self, "budget", None)
        if budget is not None:
            normalized_budget = self._normalize_budget(budget)
            if normalized_budget:
                payload["budget"] = normalized_budget

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
                converted_assets.append(self._normalize_tool_for_api(tool))

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

        # Persist expected_output server-side so fetched agents and runs that
        # don't pass executionParams.expectedOutput (the backend falls back to
        # the stored value) keep the JSON contract.
        if "expectedOutput" in payload:
            expected_output = payload["expectedOutput"]
            if isinstance(expected_output, type) and issubclass(expected_output, BaseModel):
                payload["expectedOutput"] = json.dumps(expected_output.model_json_schema())
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

        # Set default values for execution_params if not provided.
        # No ``maxIterations`` default: the iteration cap now travels inside
        # ``executionParams.budget`` and the backend supplies its own default.
        defaults = {
            "outputFormat": self.output_format,
            "maxTokens": getattr(self, "max_tokens", 2048),
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

        # Run-time budget: the agent's current ``budget`` state travels inside
        # ``executionParams.budget`` (the backend merges it field-by-field over the
        # persisted default). Set the key only when the budget carries at least one
        # cap; an empty budget must leave the payload unchanged. ``budget`` is no
        # longer a run kwarg — drop any stray one so it can't leak to the payload.
        kwargs.pop("budget", None)
        # ``getattr`` (not ``self.budget``) mirrors the defensive reads above so a
        # test-constructed agent (``Agent.__new__`` bypassing ``__init__``) still
        # works; a missing/None budget is treated as an empty one.
        budget = getattr(self, "budget", None) or Budget()

        # Deprecated run-time ``max_iterations`` exec param: fold into the run-time
        # budget (the agent's budget wins on conflict) and stop emitting a standalone
        # ``executionParams.maxIterations``. ``max_iterations`` is not in
        # ``_EXEC_PARAMS_MAP``, so a snake_case key passes through unmapped — accept
        # both spellings here (mirrors ExecutionConfig.to_api_dict in session.py).
        deprecated_iterations = execution_params.pop("maxIterations", None)
        if deprecated_iterations is None:
            deprecated_iterations = execution_params.pop("max_iterations", None)
        if deprecated_iterations is not None:
            # Point past the SDK run plumbing (build_run_payload ->
            # _post_and_handle_run -> _submit_with_retries ->
            # RunnableResourceMixin.run -> Agent.run) to the user's agent.run(...)
            # call site. The conflict warning (below) is emitted from this same
            # frame, so it shares the stacklevel. ``_submit_with_retries`` is the
            # POST-only retry boundary added for BUG-1090; it sits on both the
            # run and run_async paths, so both stay at this depth.
            warnings.warn(
                "Execution param 'max_iterations' is deprecated; set agent.budget.max_iterations instead. "
                "It will be removed in a future release.",
                DeprecationWarning,
                stacklevel=6,
            )
            normalized_budget, conflicted = self._fold_iter_into_budget(budget, deprecated_iterations)
            if conflicted:
                warnings.warn(self._BUDGET_ITER_CONFLICT_MSG, UserWarning, stacklevel=6)
        else:
            normalized_budget = self._normalize_budget(budget)

        if normalized_budget:
            execution_params["budget"] = normalized_budget

        # Handle run_response_generation with default value of False
        run_response_generation = kwargs.pop("run_response_generation", False)

        # Process variables for instruction/description placeholders (sent to backend for substitution)
        variables = kwargs.pop("variables", None) or {}
        query = kwargs.pop("query", None)

        # Multimodal attachments on the non-session run path: resolve them to
        # ``{url, name, type, mimeType}`` descriptors (uploading any local paths)
        # and send them as a structured ``attachments`` field — the same shape
        # the agent worker consumes. Popped here so they aren't forwarded raw by
        # the generic kwargs loop below.
        attachments = kwargs.pop("attachments", None)
        files = kwargs.pop("files", None)

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
        if attachments or files:
            from .session import resolve_attachments

            payload["attachments"] = resolve_attachments(
                self.context, attachments, files, error_label=f"agent '{self.id}'"
            )
        # Translate remaining snake_case kwargs to camelCase for the API
        for key, value in kwargs.items():
            if value is not None:
                api_key = self._SNAKE_TO_CAMEL.get(key, key)
                payload[api_key] = value

        # Send the agent's current per-tool parameter state as an ephemeral
        # run-time override. Mutating ``agent.tools[i].actions[...].inputs[...]``
        # and calling ``run()`` forwards those values without persisting them
        # (the backend merges by tool id). Only tools that carry parameter
        # values are included, so the common no-override case stays lightweight.
        tool_overrides = self._build_tool_overrides()
        if tool_overrides:
            payload["tools"] = tool_overrides

        self._apply_llm_fields_to_run_payload(payload)
        return payload

    def _build_tool_overrides(self) -> List[dict]:
        """Serialize ``self.tools`` into run-time per-tool parameter overrides.

        Reads each tool object's *current* action-input values **offline** and
        emits the ``[{id, parameters: [{name, value}]}]`` shape the backend
        merges by tool id. Only tools that carry at least one set value are
        emitted, so runs without overrides stay lightweight; bare string ids and
        attach-only dicts are skipped.
        """
        overrides: List[dict] = []
        for tool in getattr(self, "tools", None) or []:
            if not isinstance(tool, ToolableMixin):
                continue
            tool_id = getattr(tool, "id", None)
            if not tool_id:
                continue
            values = self._current_tool_parameters(tool)
            if values:
                overrides.append(
                    {
                        "id": tool_id,
                        "parameters": self._params_dict_to_namevalue_list(values),
                    }
                )
        return overrides

    @staticmethod
    def _current_tool_parameters(tool: Any) -> Dict[str, Any]:
        """Read a tool object's current, non-null input values as ``{name: value}``.

        Fully offline — only inspects input collections that are already
        materialized (a Model's single ``inputs``, or the actions a caller has
        touched on a Tool), so it never triggers a lazy spec fetch.
        """
        values: Dict[str, Any] = {}

        # Model-style: a single ``inputs`` collection (Tools raise on ``.inputs``).
        try:
            inputs = tool.inputs
        except Exception:
            inputs = None
        if inputs is not None and hasattr(inputs, "items"):
            for name, value in inputs.items():
                if value is not None:
                    values[name] = value
            return values

        # Tool-style: gather values from already-materialized actions.
        actions = getattr(tool, "actions", None)
        materialized = getattr(actions, "_actions", None)
        if isinstance(materialized, dict):
            for action in materialized.values():
                action_inputs = getattr(action, "_inputs", None)
                if action_inputs is None or not hasattr(action_inputs, "items"):
                    continue
                for name, value in action_inputs.items():
                    if value is not None:
                        values[name] = value
        return values

    @staticmethod
    def _apply_run_overrides_to_session(session: "Session", kwargs: Dict[str, Any]) -> None:
        """Apply per-run execution overrides onto a session.

        When a caller runs within a ``session`` but also passes
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
            f"passed alongside session '{session.id}'. Updating the session's "
            f"stored executionConfig so the overrides take effect; this also "
            f"applies to every subsequent message in this session.",
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
    )

    def _resolve_session(self, session: Any) -> "Session":
        """Resolve the ``session=`` run argument to a bound :class:`Session`.

        Accepts a :class:`~aixplain.v2.session.Session` instance (bound to this
        agent's context if it isn't already) or a session id string (fetched via
        ``Session.get``). Any other type is a ``TypeError``.
        """
        from .session import Session

        if isinstance(session, Session):
            if getattr(session, "context", None) is None:
                session.context = self.context
            return session
        if isinstance(session, str):
            return self.context.Session.get(session)
        raise TypeError(f"session must be a Session instance or a session id string, got {type(session).__name__}")

    def _run_with_session(self, session: Any, **kwargs: Any) -> AgentRunResult:
        """Run the agent within a session, awaiting the triggered run.

        Flow:
        1. Resolve ``session`` (a Session object or id) to a bound Session and
           merge any per-run execution overrides onto its ``executionConfig``.
        2. POST a ``role="user"`` message via ``session.add_message`` — this
           triggers the agent run on the backend with the session's
           ``executionConfig``. Any ``attachments`` / ``files`` passed to
           ``run`` are forwarded onto the user message so the agent receives
           them (uploaded and attached by ``add_message``).
        3. Pull the agent run's ``requestId`` off the user message and hand it to
           ``self.sync_poll`` (the ``/sdk/agents/{request_id}/result`` endpoint),
           which returns a fully populated ``AgentRunResult`` including
           ``data.steps``, ``execution_stats``, ``used_credits``, and ``run_time``.

        We don't poll session messages for the assistant reply — the run result
        endpoint is fully populated for the run the user message triggered.
        """
        self._validate_run_dependencies()

        offending = [k for k in self._LEGACY_ONLY_RUN_KWARGS if kwargs.get(k) is not None]
        if offending:
            raise ValueError(
                f"session=… runs do not support legacy run kwargs: {offending}. Drop them or run without a session."
            )

        query = kwargs.get("query")
        attachments = kwargs.get("attachments")
        files = kwargs.get("files")
        # The query is optional when attachments carry the turn's input (e.g. an
        # audio clip that is itself the prompt); otherwise a text query is required.
        if query is None and not (attachments or files):
            raise ValueError("A session run requires a query or attachments.")
        if query is not None and not isinstance(query, str):
            raise ValueError("session=… only supports string queries.")
        query = query or ""

        session = self._resolve_session(session)
        self._apply_run_overrides_to_session(session, kwargs)

        # The agent's current per-tool parameter state (set by mutating
        # ``agent.tools[i].actions[...].inputs[...]``) becomes the per-message
        # override for this run, matching the single-shot run path.
        message_tools = self._build_tool_overrides() or None

        user_msg = session.add_message(
            role="user",
            content=query,
            attachments=attachments,
            files=files,
            tools=message_tools,
        )
        if not user_msg.request_id:
            raise ValueError(
                f"Backend did not return a requestId on the user message for "
                f"session '{session.id}'; cannot poll the agent run result."
            )

        # Same progress-tracker plumbing as the direct path: sync_poll calls
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

        # The /sdk/agents/{id}/result response doesn't always echo back
        # identifiers at the top level — back-fill from what we know locally so
        # result.session_id / result.request_id are not None for session callers.
        if not result.session_id:
            result.session_id = session.id
        if result.data is not None and getattr(result.data, "session_id", None) in (None, ""):
            result.data.session_id = session.id
        if not result.request_id:
            result.request_id = user_msg.request_id
        result._context = self.context
        return result


# ``@dataclass_json`` injects its own ``from_dict`` onto the class, which would
# clobber any ``from_dict`` defined in the class body. So we wrap the injected
# decoder here (after decoration) to silently fold a legacy top-level
# ``maxIterations`` into ``budget`` before decoding — keeping deserialization
# warning-free while the explicit ``Agent(max_iterations=...)`` constructor path
# still warns via ``__post_init__``.
_dataclass_json_agent_from_dict = Agent.from_dict.__func__


def _agent_from_dict(cls, kvs: Any, *, infer_missing: bool = False) -> "Agent":
    kvs = cls._fold_legacy_max_iterations(kvs)
    return _dataclass_json_agent_from_dict(cls, kvs, infer_missing=infer_missing)


Agent.from_dict = classmethod(_agent_from_dict)
