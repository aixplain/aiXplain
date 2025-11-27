"""Agent resource for v2 API.

This module provides the Agent class for creating, managing, and running
AI agents with tools, tasks, and execution tracking.
"""

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
    """Output format options for agent execution."""

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
    progress_verbosity: NotRequired[Optional[Literal["full", "compact"]]]


@dataclass_json
@dataclass
class StepAgent:
    """Agent information within a step.

    Attributes:
        id: The unique identifier of the agent.
        name: The name of the agent.
        is_system_agent: Whether this is a system agent (e.g., response_generator).
    """

    id: Optional[str] = None
    name: Optional[str] = None
    is_system_agent: Optional[bool] = field(default=False, metadata=config(field_name="is_system_agent"))


@dataclass_json
@dataclass
class StepUnit:
    """Unit (model/tool) information within a step.

    Attributes:
        id: The unique identifier of the unit.
        name: The name of the unit (e.g., "GPT-4o Mini", "SLACK_CHAT_POST_MESSAGE").
        type: The type of unit ("model" or "tool").
    """

    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None


@dataclass_json
@dataclass
class Step:
    """A single execution step in the agent's workflow.

    Represents detailed information about each step during agent execution,
    including LLM reasoning steps and tool invocations.

    Attributes:
        agent: Information about the agent that executed this step.
        start_time: ISO timestamp when the step started.
        end_time: ISO timestamp when the step ended (None if still running).
        thought: The agent's reasoning/thought for this step.
        input: The input provided to this step.
        output: The output produced by this step.
        task: The task being performed (if applicable).
        unit: Information about the model or tool used.
        used_credits: Credits consumed by this step.
        api_calls: Number of API calls made in this step.
        run_time: Execution time in seconds.
        action: The action taken (if applicable).
    """

    agent: Optional[StepAgent] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    thought: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    task: Optional[str] = None
    unit: Optional[StepUnit] = None
    used_credits: Optional[float] = None
    api_calls: Optional[int] = None
    run_time: Optional[float] = None
    action: Optional[str] = None

    def __post_init__(self):
        """Convert nested dicts to dataclass instances if needed."""
        if isinstance(self.agent, dict):
            self.agent = StepAgent.from_dict(self.agent)
        if isinstance(self.unit, dict):
            self.unit = StepUnit.from_dict(self.unit)


@dataclass_json
@dataclass
class AgentResponseData:
    """Data structure for agent response.

    Attributes:
        input: The input provided to the agent.
        output: The final output from the agent.
        intermediate_steps: List of aggregated steps per agent with tool/llm breakdown.
        steps: Detailed list of individual execution steps.
        execution_stats: Statistics about the execution.
        critiques: Any critiques or feedback about the execution.
    """

    input: Optional[Any] = None
    output: Optional[Any] = None
    intermediate_steps: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    steps: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    execution_stats: Optional[Dict[str, Any]] = field(default=None, metadata=config(field_name="executionStats"))
    critiques: Optional[str] = ""

    def __post_init__(self):
        """Convert steps from dicts to Step objects if needed."""
        if self.steps:
            self.steps = [Step.from_dict(step) if isinstance(step, dict) else step for step in self.steps]


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
    """A task definition for agent execution.

    Tasks represent individual steps or goals that an agent should accomplish,
    with optional dependencies on other tasks.
    """

    name: str
    instructions: Optional[str] = field(metadata=config(field_name="description"))
    expected_output: Optional[str] = field(metadata=config(field_name="expectedOutput"))
    dependencies: List[Union[str, "Task"]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize dependencies to strings after initialization."""
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

    DEFAULT_LLM = "669a63646eb56306647e1091"
    SUPPLIER = "aiXplain"

    RESPONSE_CLASS = AgentRunResult
    Task = Task
    OutputFormat = OutputFormat

    # Step-related classes for typed access to execution steps
    Step = Step
    StepAgent = StepAgent
    StepUnit = StepUnit

    # Core fields from Swagger
    instructions: Optional[str] = None
    status: AssetStatus = AssetStatus.DRAFT
    team_id: Optional[int] = field(default=None, metadata=config(field_name="teamId"))
    llm: Union[str, "Model"] = field(default=DEFAULT_LLM, metadata=config(field_name="llmId"))

    # Asset and tool fields
    assets: Optional[List[Dict[str, Any]]] = field(default_factory=list, metadata=config(field_name="tools"))
    tools: Optional[List[Dict[str, Any]]] = field(default_factory=list, metadata=config(field_name="assets"))

    # Inspector and supervisor fields
    inspector_id: Optional[str] = field(default=None, metadata=config(field_name="inspectorId"))
    supervisor_id: Optional[str] = field(default=None, metadata=config(field_name="supervisorId"))
    planner_id: Optional[str] = field(default=None, metadata=config(field_name="plannerId"))

    # Task fields
    tasks: Optional[List[Task]] = field(default_factory=list)
    subagents: Optional[List[Union[str, "Agent"]]] = field(default_factory=list, metadata=config(field_name="agents"))

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

    def __post_init__(self) -> None:
        """Initialize agent after dataclass creation.

        Converts tasks from dicts to Task objects, normalizes subagents,
        and sets up default assets.
        """
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

    def before_run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> Optional[AgentRunResult]:
        """Callback called before running the agent.

        Validates dependencies, resets progress tracking, and handles
        auto-saving for draft agents.

        Args:
            *args: Positional arguments passed to run
            **kwargs: Keyword arguments passed to run

        Returns:
            Optional early return result, or None to continue
        """
        # Reset progress message tracking for new run
        self._last_progress_message = None

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
        return None

    def after_run(
        self,
        result: Union[AgentRunResult, Exception],
        *args: Any,
        **kwargs: Unpack[AgentRunParams],
    ) -> Optional[AgentRunResult]:
        """Callback called after running the agent.

        Can be used for caching, logging, or custom result transformation.

        Args:
            result: The result from the run operation
            *args: Positional arguments that were passed to run
            **kwargs: Keyword arguments that were passed to run

        Returns:
            Optional modified result, or None to return original result
        """
        # Could implement caching, logging, or custom result transformation
        # here
        return None  # Return original result

    def _normalize_progress_data(self, progress: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize progress data from camelCase to snake_case.

        Args:
            progress: Progress data from backend (may use camelCase)

        Returns:
            Normalized progress data with snake_case keys
        """
        if not progress:
            return progress

        # Map camelCase to snake_case for known fields
        normalized = {}
        key_mapping = {
            "toolInput": "tool_input",
            "toolOutput": "tool_output",
            "currentStep": "current_step",
            "totalSteps": "total_steps",
        }

        for key, value in progress.items():
            # Use mapped key if available, otherwise keep original
            normalized_key = key_mapping.get(key, key)
            normalized[normalized_key] = value

        return normalized

    def _format_agent_progress(
        self,
        progress: Dict[str, Any],
        verbosity: Optional[str] = "full",
    ) -> Optional[str]:
        """Format agent progress message based on verbosity level.

        Args:
            progress: Progress data from polling response
            verbosity: "full", "compact", or None (disables output)

        Returns:
            Formatted message or None
        """
        if verbosity is None:
            return None

        stage = progress.get("stage", "working")
        tool = progress.get("tool")
        success = progress.get("success")
        reason = progress.get("reason", "")
        tool_input = progress.get("tool_input", "")
        tool_output = progress.get("tool_output", "")

        # Determine status icon
        if success is True:
            status_icon = "✓"
        elif success is False:
            status_icon = "✗"
        else:
            status_icon = "⏳"

        # Use agent name from progress if available (for team agents),
        # otherwise use self.name
        agent_name = progress.get("agent") or self.name

        if verbosity == "compact":
            # Compact mode: minimal info
            if tool:
                msg = f"⚙️  {agent_name} | {tool} | {status_icon}"
                if success is True and tool_output:
                    output_str = str(tool_output)[:200]
                    msg += f" {output_str}"
                    msg += "..." if len(str(tool_output)) > 200 else ""
            else:
                stage_name = stage.replace("_", " ").title()
                msg = f"🤖  {agent_name} | {status_icon} {stage_name}"
        else:
            # Full verbosity: detailed info
            if tool:
                msg = f"⚙️  {agent_name} | {tool} | {status_icon}"

                if tool_input:
                    msg += f" | Input: {tool_input}"

                if tool_output:
                    msg += f" | Output: {tool_output}"

                if reason:
                    msg += f" | Reason: {reason}"
            else:
                stage_name = stage.replace("_", " ").title()
                msg = f"🤖  {agent_name} | {status_icon} {stage_name}"
                if reason:
                    msg += f" | {reason}"

        return msg

    def _format_completion_message(
        self,
        elapsed_time: float,
        response: AgentRunResult,
        timed_out: bool = False,
        timeout: float = 300,
        verbosity: Optional[str] = "full",
    ) -> str:
        """Format completion message with metrics.

        Args:
            elapsed_time: Total elapsed time in seconds
            response: Final response
            timed_out: Whether the operation timed out
            timeout: Timeout value if timed out
            verbosity: "full" or "compact"

        Returns:
            Formatted completion message
        """
        if timed_out:
            return f"✅ Done | ✗ Timeout - No response after {timeout}s"

        # Collect metrics from execution_stats if available
        total_api_calls = 0
        total_credits = 0.0
        runtime = elapsed_time

        # Extract data dict (handle tuple or direct object) - matching v1 logic
        data_dict = None
        if hasattr(response, "data") and response.data:
            if isinstance(response.data, tuple) and len(response.data) > 0:
                # Data is a tuple, get first element
                data_dict = response.data[0] if isinstance(response.data[0], dict) else None
            elif isinstance(response.data, dict):
                # Data is already a dict
                data_dict = response.data
            elif hasattr(response.data, "executionStats") or hasattr(response.data, "execution_stats"):
                # Data is an object with attributes
                exec_stats = getattr(response.data, "executionStats", None) or getattr(
                    response.data, "execution_stats", None
                )
                if exec_stats and isinstance(exec_stats, dict):
                    total_api_calls = exec_stats.get("api_calls", 0)
                    total_credits = exec_stats.get("credits", 0.0)
                    runtime = exec_stats.get("runtime", elapsed_time)

        # Try to get metrics from data dict (camelCase fields from backend)
        if data_dict and isinstance(data_dict, dict):
            # Check executionStats first
            exec_stats = data_dict.get("executionStats")
            if exec_stats and isinstance(exec_stats, dict):
                total_api_calls = exec_stats.get("api_calls", 0)
                total_credits = exec_stats.get("credits", 0.0)
                runtime = exec_stats.get("runtime", elapsed_time)

            # Fallback: check top-level fields (usedCredits, runTime)
            if total_credits == 0.0:
                total_credits = data_dict.get("usedCredits", 0.0)
            if runtime == elapsed_time:
                runtime = data_dict.get("runTime", elapsed_time)

        # Also check _raw_data for metrics (v2-specific)
        if hasattr(response, "_raw_data") and response._raw_data:
            raw_data = response._raw_data
            # Check for data dict in raw_data
            if "data" in raw_data and isinstance(raw_data["data"], dict):
                data_dict = raw_data["data"]
                exec_stats = data_dict.get("executionStats")
                if exec_stats and isinstance(exec_stats, dict):
                    total_api_calls = exec_stats.get("api_calls", 0)
                    total_credits = exec_stats.get("credits", 0.0)
                    runtime = exec_stats.get("runtime", elapsed_time)
                # Fallback
                if total_credits == 0.0:
                    total_credits = data_dict.get("usedCredits", 0.0)
                if runtime == elapsed_time:
                    runtime = data_dict.get("runTime", elapsed_time)

        # Build single-line completion message with metrics
        if verbosity == "compact":
            msg = f"✅ Done | ({runtime:.1f} s total"
        else:
            msg = f"✅ Done | Completed successfully ({runtime:.1f} s total"

        # Always show API calls and credits
        if total_api_calls > 0:
            msg += f" | {total_api_calls} API calls"
        msg += f" | ${total_credits}"
        msg += ")"

        return msg

    def _format_step_progress(
        self,
        step: Union[Step, Dict[str, Any]],
        verbosity: Optional[str] = "full",
    ) -> Optional[str]:
        """Format progress message from a step in data.steps.

        Args:
            step: Step object or dict from data.steps
            verbosity: "full", "compact", or None

        Returns:
            Formatted message or None
        """
        if verbosity is None:
            return None

        # Extract step data (handle both Step objects and dicts)
        if isinstance(step, dict):
            unit = step.get("unit", {})
            agent = step.get("agent", {})
            tool = unit.get("name") if isinstance(unit, dict) else None
            unit_type = unit.get("type") if isinstance(unit, dict) else None
            agent_name = agent.get("name") if isinstance(agent, dict) else None
            thought = step.get("thought", "")
            step_input = step.get("input", "")
            step_output = step.get("output", "")
        else:
            # Step object
            tool = step.unit.name if step.unit else None
            unit_type = step.unit.type if step.unit else None
            agent_name = step.agent.name if step.agent else None
            thought = step.thought or ""
            step_input = step.input or ""
            step_output = step.output or ""

        # Convert output to string for consistent formatting
        if step_output and not isinstance(step_output, str):
            step_output = str(step_output)

        if not tool and not unit_type:
            return None

        status_icon = "✓"
        display_agent_name = agent_name or self.name

        if verbosity == "compact":
            if tool:
                msg = f"⚙️  {display_agent_name} | {tool} | {status_icon}"
            else:
                msg = f"🤖  {display_agent_name} | {status_icon}"
        else:
            if tool:
                msg = f"⚙️  {display_agent_name} | {tool} | {status_icon}"

                if step_input:
                    msg += f" | Input: {step_input}"

                if step_output:
                    output_str = str(step_output)
                    if len(output_str) > 200:
                        msg += f" | Output: {output_str[:200]}..."
                    else:
                        msg += f" | Output: {output_str}"

                # Match v1 format: "Reason: Completed {tool}" for LLM completion steps
                if unit_type == "model" and tool and not thought:
                    msg += f" | Reason: Completed {tool}"
                elif thought:
                    msg += f" | Reason: {thought}"
            else:
                msg = f"🤖  {display_agent_name} | {status_icon}"
                if thought:
                    msg += f" | {thought}"

        return msg

    def on_poll(self, response: AgentRunResult, **kwargs: Unpack[AgentRunParams]) -> None:
        """Hook called after each poll to display agent execution progress.

        This method displays real-time progress updates during agent execution,
        including tool usage, execution stages, and runtime information.
        Matches v1 behavior: only shows progress when not completed.

        Args:
            response: The poll response containing progress information
            **kwargs: Run parameters including progress_verbosity
        """
        # Default to "compact" if not provided, but respect explicit None
        verbosity = kwargs.get("progress_verbosity")
        if verbosity is None and "progress_verbosity" not in kwargs:
            verbosity = "compact"

        if verbosity is None:
            return

        # Initialize tracking state if needed
        if not hasattr(self, "_last_progress_message"):
            self._last_progress_message = None
        if not hasattr(self, "_displayed_step_indices"):
            self._displayed_step_indices = set()
        if not hasattr(self, "_displayed_tools_from_progress"):
            self._displayed_tools_from_progress = set()

        last_message = self._last_progress_message
        displayed_step_indices = self._displayed_step_indices
        displayed_tools_from_progress = self._displayed_tools_from_progress

        # Show progress field updates when not completed (matching v1 behavior)
        # V1 checks `if progress_verbosity and not completed`
        if not response.completed:
            progress = None
            if hasattr(response, "_raw_data") and response._raw_data:
                progress = response._raw_data.get("progress")
            else:
                try:
                    progress = getattr(response, "progress", None)
                except AttributeError:
                    pass

            if progress:
                progress = self._normalize_progress_data(progress)

                # Match v1: show formatting_output for main agent, not response_generator
                stage = progress.get("stage")
                agent_name = progress.get("agent")
                success = progress.get("success")

                if stage == "formatting_output" and agent_name and "response_generator" in str(agent_name).lower():
                    progress = progress.copy()
                    progress["agent"] = self.name

                # Build and display the progress message (matching v1's deduplication)
                message = self._format_agent_progress(progress, verbosity)
                if message and message != last_message:
                    print(message, flush=True)
                    self._last_progress_message = message

                    # Track what we showed to avoid duplicates from data.steps
                    # Track by tool+input+success to allow both ⏳ and ✓ updates for all steps
                    tool = progress.get("tool")
                    tool_input = progress.get("tool_input", "")

                    if tool:
                        # Track by tool+input+success to allow both ⏳ and ✓ updates
                        progress_key = f"{tool}_{tool_input}_{success}"
                        displayed_tools_from_progress.add(progress_key)
                    elif stage:
                        # Track by stage+success to allow both ⏳ and ✓ updates
                        stage_key = f"stage_{stage}_{success}"
                        displayed_tools_from_progress.add(stage_key)

        # Use data.steps as safety net to catch steps V1 missed between polls
        steps = None
        if hasattr(response, "data") and response.data:
            if hasattr(response.data, "steps"):
                steps = response.data.steps
            elif isinstance(response.data, dict) and "steps" in response.data:
                steps = response.data["steps"]
            elif hasattr(response, "_raw_data") and response._raw_data and "data" in response._raw_data:
                data_dict = response._raw_data["data"]
                if isinstance(data_dict, dict) and "steps" in data_dict:
                    steps = data_dict["steps"]

        if steps:
            for idx, step in enumerate(steps):
                if idx in displayed_step_indices:
                    continue

                # Extract step information
                step_tool = None
                step_unit_type = None
                step_input = ""
                step_agent = None

                if isinstance(step, dict):
                    step_unit = step.get("unit", {})
                    if isinstance(step_unit, dict):
                        step_tool = step_unit.get("name")
                        step_unit_type = step_unit.get("type")
                    step_input = step.get("input", "")
                    step_agent_dict = step.get("agent", {})
                    if isinstance(step_agent_dict, dict):
                        step_agent = step_agent_dict.get("name")
                elif hasattr(step, "unit") and step.unit:
                    step_tool = step.unit.name
                    step_unit_type = step.unit.type if hasattr(step.unit, "type") else None
                    step_input = step.input if hasattr(step, "input") else ""
                    if hasattr(step, "agent") and step.agent and hasattr(step.agent, "name"):
                        step_agent = step.agent.name

                # Skip response_generator steps (V1 shows formatting_output for main agent)
                if step_agent:
                    agent_lower = str(step_agent).lower().replace("_", " ").replace("-", " ")
                    if "response generator" in agent_lower or "responsegenerator" in agent_lower:
                        displayed_step_indices.add(idx)
                        continue

                # Skip model steps without tool name (formatting_output stages)
                # V1 only shows these from progress field, not from data.steps
                if step_unit_type == "model" and not step_tool:
                    displayed_step_indices.add(idx)
                    continue

                # Check if this step was already shown via progress field
                # For completed steps from data.steps, check if we saw the completed state (✓)
                step_input_str = str(step_input) if step_input else ""
                if step_tool:
                    # Check if we saw the completed state (✓) from progress field
                    step_key_completed = f"{step_tool}_{step_input_str}_True"
                    # Show if we didn't see the completed state from progress field
                    if step_key_completed not in displayed_tools_from_progress:
                        message = self._format_step_progress(step, verbosity)
                        if message:
                            print(message, flush=True)
                        displayed_step_indices.add(idx)
                        displayed_tools_from_progress.add(step_key_completed)
                elif step_unit_type == "model":
                    # For model steps, check if we saw the completed state (✓)
                    step_key_completed = f"model_{step_input_str}_True" if step_input_str else "model_True"
                    # Show if we didn't see the completed state from progress field
                    if step_key_completed not in displayed_tools_from_progress:
                        message = self._format_step_progress(step, verbosity)
                        if message:
                            print(message, flush=True)
                        displayed_step_indices.add(idx)
                        displayed_tools_from_progress.add(step_key_completed)
                else:
                    displayed_step_indices.add(idx)

    def run(self, *args: Any, **kwargs: Unpack[AgentRunParams]) -> AgentRunResult:
        """Run the agent synchronously with automatic polling.

        Supports both positional query argument and keyword arguments.
        Handles parameter name compatibility between snake_case and camelCase.

        Args:
            *args: Optional positional query argument
            **kwargs: Run parameters including query, progress_verbosity, etc.

        Returns:
            AgentRunResult with execution results and steps
        """
        import time

        # Reset progress deduplication state at the start of each run
        # This ensures we show all progress updates for this run
        self._last_progress_message = None
        self._displayed_step_indices = set()
        self._displayed_tools_from_progress = set()

        if len(args) > 0:
            kwargs["query"] = args[0]
            args = args[1:]

        # Handle session_id parameter name compatibility (snake_case -> camelCase)
        if "session_id" in kwargs and "sessionId" not in kwargs:
            kwargs["sessionId"] = kwargs.pop("session_id")

        # Default to "compact" if not provided, but respect explicit None
        verbosity = kwargs.get("progress_verbosity")
        if verbosity is None and "progress_verbosity" not in kwargs:
            verbosity = "compact"
        timeout = kwargs.get("timeout", 300)
        start_time = time.time()

        # Run with polling
        result = super().run(*args, **kwargs)

        # Display completion message if verbosity is enabled (not None)
        if verbosity is not None:
            elapsed_time = time.time() - start_time
            timed_out = not result.completed
            completion_msg = self._format_completion_message(elapsed_time, result, timed_out, timeout, verbosity)
            print(completion_msg, flush=True)

        return result

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
            *args: Positional arguments (currently unused)
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
                if hasattr(original_subagent, "save") and hasattr(original_subagent, "id") and not original_subagent.id:
                    try:
                        # Recursively save subagent and its components
                        original_subagent.save(save_subcomponents=True)
                        # Update the subagents list with the new ID
                        self.subagents[i] = original_subagent.id
                    except Exception as e:
                        subagent_name = getattr(original_subagent, "name", f"subagent_{i}")
                        failed_components.append(("subagent", subagent_name, str(e)))

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
        """Callback to be called before the resource is saved.

        Handles status transitions based on save type.

        Args:
            *args: Positional arguments passed to save
            **kwargs: Keyword arguments including as_draft flag

        Returns:
            Optional dict to modify save payload, or None
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

        Args:
            result: The cloned agent or exception if cloning failed
            **kwargs: Additional keyword arguments

        Returns:
            Optional modified agent, or None to return original
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

        # Convert tools intelligently based on their type
        converted_assets = []
        if self.tools:
            for tool in self.tools:
                if isinstance(tool, ToolableMixin):
                    # Non-tool objects (like Models) that can act as tools
                    converted_assets.append(tool.as_tool())
                else:
                    raise ValueError("A tool in the agent must be a Tool, Model or ToolableMixin instance.")

        # Update the payload with converted assets
        payload["assets"] = converted_assets

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
        if execution_params.get("outputFormat") in ["text", "markdown"] and expected_output == "":
            execution_params["expectedOutput"] = None
        elif (
            expected_output is not None and isinstance(expected_output, type) and issubclass(expected_output, BaseModel)
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

    def generate_session_id(self, history: Optional[List[ConversationMessage]] = None) -> str:
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
                    logging.error(f"Session {session_id} initialization failed: {final_result}")
                    return session_id
            else:
                # Direct completion or no polling needed
                return session_id

        except Exception as e:
            logging.error(f"Failed to initialize session {session_id}: {e}")
            return session_id
