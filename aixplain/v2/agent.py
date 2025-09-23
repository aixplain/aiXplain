import json
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict, Union, Text
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
    show_progress: NotRequired[Optional[bool]]


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
        if self.dependencies:
            self.dependencies = [
                dependency if isinstance(dependency, str) else dependency.name
                for dependency in self.dependencies
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

    def __post_init__(self) -> None:
        self.tasks = [Task.from_dict(task) for task in self.tasks]

        # Store original subagent objects for saving, convert to IDs for storage
        self._original_subagents = []
        converted_subagents = []
        for agent in self.subagents:
            if isinstance(agent, str):
                self._original_subagents.append(None)  # Already an ID
                converted_subagents.append(agent)
            else:
                self._original_subagents.append(agent)  # Store original object
                converted_subagents.append(agent.id)
        self.subagents = converted_subagents
        self.assets = [{"type": "llm", "description": "main", "parameters": []}]
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
        # if self.subagents and (self.tasks or self.tools):
        #     raise ValueError(
        #         "Team agents cannot have tasks or tools. Please remove the tasks or tools and try again."
        #     )

    def mark_as_deleted(self) -> None:
        """Mark the agent as deleted by setting status to DELETED and calling parent method."""
        from .enums import AssetStatus

        self.status = AssetStatus.DELETED
        super().mark_as_deleted()

    def before_run(
        self, *args: Any, **kwargs: Unpack[AgentRunParams]
    ) -> Optional[AgentRunResult]:
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
                raise ValueError(
                    "Agent is onboarded and cannot be modified unless you "
                    "explicitly save it."
                )
        return None

    def after_run(
        self,
        result: Union[AgentRunResult, Exception],
        *args: Any,
        **kwargs: Unpack[AgentRunParams],
    ) -> Optional[AgentRunResult]:
        # Could implement caching, logging, or custom result transformation
        # here
        return None  # Return original result

    def _build_progress_message(self, progress: Dict[str, Any]) -> str:
        """
        Build a formatted progress message from progress data.

        Args:
            progress: Dictionary containing progress information

        Returns:
            str: Formatted progress message
        """
        stage = progress.get("stage", "working")
        tool = progress.get("tool")
        runtime = progress.get("runtime", 0)
        success = progress.get("success")
        reason = progress.get("reason", "")
        tool_input = progress.get("tool_input", "")
        tool_output = progress.get("tool_output", "")

        # Build status message
        if tool:
            status_icon = "✓" if success else "✗" if success is False else "⏳"
            msg = (
                f"🤖 Agent: {stage.replace('_', ' ').title()} | "
                f"Tool: {tool} {status_icon}"
            )
            if runtime > 0:
                msg += f" ({runtime:.2f}s)"
            if reason:
                msg += f" | Reason: {reason}"
            if tool_input:
                msg += f" | Input: {tool_input}"
            if tool_output:
                msg += f" | Output: {tool_output}"
        else:
            msg = f"🤖 Agent: {stage.replace('_', ' ').title()}..."
            if reason:
                msg += f" | Reason: {reason}"

        return msg

    def on_poll(
        self, response: AgentRunResult, **kwargs: Unpack[AgentRunParams]
    ) -> None:
        """
        Hook called after each poll to display agent execution progress.

        This method displays real-time progress updates during agent execution,
        including tool usage, execution stages, and runtime information.

        Args:
            response: The poll response containing progress information
            **kwargs: Run parameters including show_progress flag
        """
        show_progress = kwargs.get("show_progress", False)

        if not show_progress or response.completed:
            return

        # Access progress data from the response
        # The response might have progress info in _raw_data or as attributes
        progress = None
        if hasattr(response, "_raw_data") and response._raw_data:
            progress = response._raw_data.get("progress")
        elif hasattr(response, "progress"):
            progress = response.progress

        if not progress:
            return

        # Build and display the progress message
        message = self._build_progress_message(progress)
        print(message, flush=True)

    def run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        if len(args) > 0:
            kwargs["query"] = args[0]
            args = args[1:]

        # Handle session_id parameter name compatibility (snake_case -> camelCase)
        if "session_id" in kwargs and "sessionId" not in kwargs:
            kwargs["sessionId"] = kwargs.pop("session_id")

        return super().run(*args, **kwargs)

    def _validate_expected_output(self) -> None:
        # Skip validation if expected_output is None (it's optional)
        if self.expected_output is None:
            return

        if self.output_format == OutputFormat.JSON.value:
            # Check if expected_output is a valid JSON type
            is_valid = isinstance(self.expected_output, (str, dict, BaseModel)) or (
                isinstance(self.expected_output, type)
                and issubclass(self.expected_output, BaseModel)
            )
            if not is_valid:
                raise ValueError(
                    "Expected output must be a valid JSON object, dict, string, or Pydantic BaseModel class/instance"
                )

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
                raise ValueError(
                    "Expected output must be a string for TEXT/MARKDOWN formats"
                )

    def save(self, *args: Any, **kwargs: Any) -> "Agent":
        """Save the agent with dependency management.

        This method extends the base save functionality to handle saving of dependent
        child components before the agent itself is saved.

        Args:
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

        # Save subagents (recursively)
        if hasattr(self, "_original_subagents") and self._original_subagents:
            for i in range(len(self.subagents)):
                original_subagent = self._original_subagents[i]
                if original_subagent is None:  # Already an ID string
                    continue
                if (
                    hasattr(original_subagent, "save")
                    and hasattr(original_subagent, "id")
                    and not original_subagent.id
                ):
                    try:
                        # Recursively save subagent and its components
                        original_subagent.save(save_subcomponents=True)
                        # Update the subagents list with the new ID
                        self.subagents[i] = original_subagent.id
                    except Exception as e:
                        subagent_name = getattr(
                            original_subagent, "name", f"subagent_{i}"
                        )
                        failed_components.append(("subagent", subagent_name, str(e)))

        if failed_components:
            error_details = "; ".join(
                [
                    f"{comp_type} '{name}': {error}"
                    for comp_type, name, error in failed_components
                ]
            )
            raise ValueError(
                f"Failed to save {len(failed_components)} component(s): {error_details}"
            )

    def _validate_run_dependencies(self) -> None:
        """Validate that all child components are saved before running."""
        unsaved_components = []

        # Check tools
        if self.tools:
            for tool in self.tools:
                if hasattr(tool, "id") and not tool.id:
                    unsaved_components.append(f"tool '{tool.name}'")

        # Check subagents - handle both _original_subagents and direct subagents list
        if self.subagents:
            for i, subagent in enumerate(self.subagents):
                # If it's an Agent object (not a string ID), check if it's saved
                if hasattr(subagent, "id") and hasattr(subagent, "name"):
                    if not subagent.id:
                        subagent_name = getattr(subagent, "name", "unnamed")
                        unsaved_components.append(f"subagent '{subagent_name}'")
                # Also check _original_subagents if available (for backward compatibility)
                elif (
                    hasattr(self, "_original_subagents")
                    and i < len(self._original_subagents)
                    and self._original_subagents[i] is not None
                ):
                    original_subagent = self._original_subagents[i]
                    if hasattr(original_subagent, "id") and not original_subagent.id:
                        subagent_name = getattr(original_subagent, "name", "unnamed")
                        unsaved_components.append(f"subagent '{subagent_name}'")

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

        # Check subagents
        if hasattr(self, "_original_subagents") and self._original_subagents:
            for i, original_subagent in enumerate(self._original_subagents):
                if original_subagent is None:  # Already an ID string
                    continue
                if hasattr(original_subagent, "id") and not original_subagent.id:
                    subagent_name = getattr(original_subagent, "name", "unnamed")
                    unsaved_components.append(f"subagent '{subagent_name}'")

        if unsaved_components:
            components_list = ", ".join(unsaved_components)
            raise ValueError(
                f"Component(s) {components_list} must be saved before saving the agent. "
                "Use agent.save(save_subcomponents=True) to automatically save all child components."
            )

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

        self._validate_expected_output()

        return None

    def after_clone(
        self, result: Union["Agent", Exception], **kwargs: Any
    ) -> Optional["Agent"]:
        """
        Callback called after the agent is cloned.
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
                    raise ValueError(
                        f"Inspector must be Inspector instance or dict, got {type(inspector)}"
                    )
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

        # Handle BaseModel expected_output for save operation
        # We don't send expected_output in the save payload - it's runtime-only
        if "expectedOutput" in payload:
            expected_output = payload["expectedOutput"]
            if isinstance(expected_output, type) and issubclass(
                expected_output, BaseModel
            ):
                # Remove BaseModel classes from save payload - they're not stored server-side
                payload.pop("expectedOutput")
            elif isinstance(expected_output, BaseModel):
                # Convert BaseModel instance to dict for save
                payload["expectedOutput"] = expected_output.model_dump()

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

        # Handle BaseModel conversion for expectedOutput (following legacy pattern)
        # Use agent's expected_output if none provided in executionParams
        if "expectedOutput" not in execution_params:
            execution_params["expectedOutput"] = self.expected_output

        expected_output = execution_params["expectedOutput"]

        # For non-JSON formats, don't send empty string expected_output
        if (
            execution_params.get("outputFormat") in ["text", "markdown"]
            and expected_output == ""
        ):
            execution_params["expectedOutput"] = None
        elif (
            expected_output is not None
            and isinstance(expected_output, type)
            and issubclass(expected_output, BaseModel)
        ):
            execution_params["expectedOutput"] = expected_output.model_json_schema()
        elif isinstance(expected_output, BaseModel):
            execution_params["expectedOutput"] = expected_output.model_dump()

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
