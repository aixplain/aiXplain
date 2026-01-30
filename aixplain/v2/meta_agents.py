"""Meta agents module - Debugger and other meta-agent utilities.

This module provides meta-agents that operate on top of other agents,
such as the Debugger for analyzing agent responses.

Example usage:
    from aixplain import Aixplain

    # Initialize the client
    aix = Aixplain("<api_key>")

    # Standalone usage
    debugger = aix.Debugger()
    result = debugger.run("Analyze this agent output: ...")

    # Or with custom prompt
    result = debugger.run(content="...", prompt="Focus on error handling")

    # From agent response (chained)
    agent = aix.Agent.get("my_agent_id")
    response = agent.run("Hello!")
    debug_result = response.debug()  # Uses default prompt
    debug_result = response.debug("Why did it take so long?")  # Custom prompt
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Union, TYPE_CHECKING
from dataclasses_json import dataclass_json, config

from .resource import Result

if TYPE_CHECKING:
    from .agent import AgentRunResult


# Debugger agent ID - pre-configured aiXplain agent for debugging
DEBUGGER_AGENT_ID = "696fdccad63e898317c097a0"


@dataclass_json
@dataclass
class DebugResult(Result):
    """Result from running the Debugger meta-agent.

    Attributes:
        data: The debugging analysis output.
        session_id: Session ID for conversation continuity.
        request_id: Request ID for tracking.
        used_credits: Credits consumed by the debugging operation.
        run_time: Time taken to run the debugging analysis.
        analysis: The main debugging analysis text (extracted from data output).
    """

    data: Optional[Any] = None
    session_id: Optional[str] = field(default=None, metadata=config(field_name="sessionId"))
    request_id: Optional[str] = field(default=None, metadata=config(field_name="requestId"))
    used_credits: float = field(default=0.0, metadata=config(field_name="usedCredits"))
    run_time: float = field(default=0.0, metadata=config(field_name="runTime"))

    @property
    def analysis(self) -> Optional[str]:
        """Extract the debugging analysis text from the result data.

        Returns:
            The analysis text if available, None otherwise.
        """
        if self.data is None:
            return None

        # Handle different data structures
        if isinstance(self.data, str):
            return self.data
        elif isinstance(self.data, dict):
            # Try common output keys
            return self.data.get("output") or self.data.get("result") or self.data.get("text")
        elif hasattr(self.data, "output"):
            return self.data.output

        return None


class Debugger:
    """Meta-agent for debugging and analyzing agent responses.

    The Debugger uses a pre-configured aiXplain agent to provide insights into
    agent runs, errors, and potential improvements.

    Attributes:
        context: The Aixplain client context for API access.

    Example:
        # Create a debugger through the client
        aix = Aixplain("<api_key>")
        debugger = aix.Debugger()

        # Analyze content directly
        result = debugger.run("Agent returned: 'Error 500'")

        # Debug an agent response
        agent_result = agent.run("Hello!")
        debug_result = debugger.debug_response(agent_result)
    """

    context: Any = None

    def __init__(self) -> None:
        """Initialize the Debugger.

        The context is set as a class attribute by the Aixplain client
        when creating the Debugger class dynamically.
        """
        if self.context is None:
            raise ValueError(
                "Debugger must be accessed through an Aixplain client instance. "
                "Use: aix = Aixplain('<api_key>'); debugger = aix.Debugger()"
            )

    def _get_debugger_agent(self) -> Any:
        """Get the pre-configured debugger agent.

        Returns:
            The debugger Agent instance.
        """
        from .agent import Agent

        # Create a dynamically bound Agent class with our context
        BoundAgent = type("Agent", (Agent,), {"context": self.context})
        return BoundAgent.get(DEBUGGER_AGENT_ID)

    def run(
        self,
        content: Optional[str] = None,
        prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> DebugResult:
        """Run the debugger on provided content.

        This is the standalone usage mode where you can analyze any content
        or agent output directly.

        Args:
            content: The content to analyze/debug. Can be agent output,
                    error messages, or any text requiring analysis.
            prompt: Optional custom prompt to guide the debugging analysis.
                   If not provided, uses a default debugging prompt.
            **kwargs: Additional parameters to pass to the underlying agent.

        Returns:
            DebugResult: The debugging analysis result.

        Example:
            debugger = aix.Debugger()
            result = debugger.run("Agent returned: 'Error 500'")
            print(result.analysis)
        """
        # Build the query for the debugger agent
        query = self._build_query(content=content, prompt=prompt)

        # Get the debugger agent and run
        agent = self._get_debugger_agent()
        agent_result = agent.run(query=query, **kwargs)

        # Convert AgentRunResult to DebugResult
        return self._convert_to_debug_result(agent_result)

    def debug_response(
        self,
        response: "AgentRunResult",
        prompt: Optional[str] = None,
        execution_id: Optional[str] = None,
        **kwargs: Any,
    ) -> DebugResult:
        """Debug an agent response.

        This method is designed to analyze AgentRunResult objects to provide
        insights into what happened during the agent execution.

        Args:
            response: The AgentRunResult to analyze.
            prompt: Optional custom prompt to guide the debugging analysis.
            execution_id: Optional execution ID override. If not provided, will be
                         extracted from the response's request_id or poll URL.
                         The execution_id allows the debugger to fetch additional
                         information like logs from the backend.
            **kwargs: Additional parameters to pass to the underlying agent.

        Returns:
            DebugResult: The debugging analysis result.

        Example:
            agent_result = agent.run("Hello!")
            debug_result = debugger.debug_response(agent_result, prompt="Why is it slow?")

            # Or with explicit execution ID
            debug_result = debugger.debug_response(agent_result, execution_id="abc-123")
        """
        # Serialize the response for analysis
        content = self._serialize_response(response, execution_id_override=execution_id)

        # Run debugging with the serialized content
        return self.run(content=content, prompt=prompt, **kwargs)

    def _build_query(
        self,
        content: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> str:
        """Build the query string for the debugger agent.

        Args:
            content: The content to analyze.
            prompt: Optional custom prompt.

        Returns:
            The formatted query string.
        """
        parts = []

        if prompt:
            parts.append(f"Focus: {prompt}")

        if content:
            parts.append(f"Content to analyze:\n{content}")

        if not parts:
            return "Please analyze the agent response and provide debugging insights."

        return "\n\n".join(parts)

    def _extract_execution_id(self, response: "AgentRunResult") -> Optional[str]:
        """Extract the execution ID from an AgentRunResult.

        The execution ID can be used to fetch additional information like logs.

        Args:
            response: The agent result to extract from.

        Returns:
            The execution ID if found, None otherwise.
        """
        import re

        # First try request_id directly
        if response.request_id:
            return response.request_id

        # Try to extract from poll URL (format: .../sdk/agents/{execution_id}/...)
        if response.url:
            # Pattern matches UUID-like IDs in the URL path
            match = re.search(r"/sdk/agents/([a-f0-9-]{36})/", response.url)
            if match:
                return match.group(1)

            # Also try matching non-UUID format IDs
            match = re.search(r"/sdk/agents/([^/]+)/", response.url)
            if match:
                return match.group(1)

        return None

    def _serialize_response(
        self,
        response: "AgentRunResult",
        execution_id_override: Optional[str] = None,
    ) -> str:
        """Serialize an AgentRunResult for debugging analysis.

        Args:
            response: The agent result to serialize.
            execution_id_override: Optional execution ID to use instead of extracting
                                  from the response.

        Returns:
            A string representation suitable for debugging analysis.
        """
        import json

        # Use override if provided, otherwise extract from response
        execution_id = execution_id_override or self._extract_execution_id(response)

        # Build a structured representation with execution_id first for visibility
        debug_info = {}

        # Add execution_id prominently at the top if available
        if execution_id:
            debug_info["execution_id"] = execution_id

        # Add core status info
        debug_info.update({
            "status": response.status,
            "completed": response.completed,
            "run_time": response.run_time,
            "used_credits": response.used_credits,
        })

        # Add error information if present
        if response.error_message:
            debug_info["error_message"] = response.error_message
        if response.supplier_error:
            debug_info["supplier_error"] = response.supplier_error

        # Add data/output
        if response.data:
            if hasattr(response.data, "to_dict"):
                debug_info["data"] = response.data.to_dict()
            elif hasattr(response.data, "__dict__"):
                debug_info["data"] = response.data.__dict__
            else:
                debug_info["data"] = str(response.data)

        # Add result if present
        if response.result:
            debug_info["result"] = response.result

        # Add session/request IDs if present
        if response.session_id:
            debug_info["session_id"] = response.session_id
        if response.request_id:
            debug_info["request_id"] = response.request_id

        # Add poll URL if present (useful for manual investigation)
        if response.url:
            debug_info["poll_url"] = response.url

        return json.dumps(debug_info, indent=2, default=str)

    def _convert_to_debug_result(self, agent_result: "AgentRunResult") -> DebugResult:
        """Convert an AgentRunResult to a DebugResult.

        Args:
            agent_result: The agent result to convert.

        Returns:
            A DebugResult with the same information.
        """
        return DebugResult(
            status=agent_result.status,
            completed=agent_result.completed,
            data=agent_result.data,
            session_id=agent_result.session_id,
            request_id=agent_result.request_id,
            used_credits=agent_result.used_credits,
            run_time=agent_result.run_time,
            error_message=agent_result.error_message,
            url=agent_result.url,
            result=agent_result.result,
            supplier_error=agent_result.supplier_error,
        )
