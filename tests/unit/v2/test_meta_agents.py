"""Unit tests for the v2 meta_agents module.

This module tests the Debugger meta-agent and DebugResult dataclass
for analyzing agent responses.
"""

import json
import pytest
from unittest.mock import Mock, patch

from aixplain.v2.meta_agents import Debugger, DebugResult, DEBUGGER_AGENT_ID
from aixplain.v2.agent import AgentRunResult


# =============================================================================
# DebugResult Tests
# =============================================================================


class TestDebugResult:
    """Tests for DebugResult dataclass."""

    def test_analysis_from_dict_output(self):
        """Should extract analysis from data['output']."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={"output": "Analysis text from output"},
        )

        assert result.analysis == "Analysis text from output"

    def test_analysis_from_dict_result(self):
        """Should extract analysis from data['result'] when output is absent."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={"result": "Analysis text from result"},
        )

        assert result.analysis == "Analysis text from result"

    def test_analysis_from_dict_text(self):
        """Should extract analysis from data['text'] when output/result absent."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={"text": "Analysis text from text"},
        )

        assert result.analysis == "Analysis text from text"

    def test_analysis_from_dict_output_priority(self):
        """Should prefer 'output' over 'result' and 'text'."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={
                "output": "From output",
                "result": "From result",
                "text": "From text",
            },
        )

        assert result.analysis == "From output"

    def test_analysis_from_string(self):
        """Should return data directly when it's a string."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data="Direct string analysis",
        )

        assert result.analysis == "Direct string analysis"

    def test_analysis_from_object_with_output(self):
        """Should extract analysis from data.output attribute."""
        mock_data = Mock()
        mock_data.output = "Analysis from object attribute"

        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data=mock_data,
        )

        assert result.analysis == "Analysis from object attribute"

    def test_analysis_from_none(self):
        """Should return None when data is None."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data=None,
        )

        assert result.analysis is None

    def test_analysis_from_empty_dict(self):
        """Should return None when data is an empty dict."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={},
        )

        assert result.analysis is None

    def test_analysis_from_dict_with_falsy_output(self):
        """Should return None when output key exists but is empty/falsy."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={"output": ""},
        )

        # Empty string is falsy, should fall through to result/text
        assert result.analysis is None

    def test_debug_result_inherits_from_result(self):
        """DebugResult should inherit from Result."""
        from aixplain.v2.resource import Result

        result = DebugResult(status="SUCCESS", completed=True)

        assert isinstance(result, Result)

    def test_debug_result_has_session_id(self):
        """DebugResult should have session_id field."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            session_id="session-123",
        )

        assert result.session_id == "session-123"

    def test_debug_result_has_request_id(self):
        """DebugResult should have request_id field."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            request_id="request-456",
        )

        assert result.request_id == "request-456"

    def test_debug_result_has_used_credits(self):
        """DebugResult should have used_credits field."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            used_credits=1.5,
        )

        assert result.used_credits == 1.5

    def test_debug_result_has_run_time(self):
        """DebugResult should have run_time field."""
        result = DebugResult(
            status="SUCCESS",
            completed=True,
            run_time=2.5,
        )

        assert result.run_time == 2.5


# =============================================================================
# Debugger Initialization Tests
# =============================================================================


class TestDebuggerInitialization:
    """Tests for Debugger initialization and context requirement."""

    def test_debugger_requires_context(self):
        """Should raise ValueError when context is None."""
        with pytest.raises(ValueError, match="Debugger must be accessed through an Aixplain client"):
            Debugger()

    def test_debugger_with_context(self):
        """Should succeed when context is set as class attribute."""
        mock_context = Mock()

        # Create a bound Debugger class with context
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        debugger = BoundDebugger()

        assert debugger.context is mock_context

    def test_debugger_context_class_attribute(self):
        """Debugger context should be a class attribute."""
        assert hasattr(Debugger, "context")
        assert Debugger.context is None


# =============================================================================
# Debugger._build_query Tests
# =============================================================================


class TestDebuggerBuildQuery:
    """Tests for Debugger._build_query method."""

    def _create_debugger(self):
        """Helper to create a Debugger with mock context."""
        mock_context = Mock()
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        return BoundDebugger()

    def test_build_query_with_content_only(self):
        """Should format content without prompt."""
        debugger = self._create_debugger()

        query = debugger._build_query(content="Test content to analyze")

        assert "Content to analyze:" in query
        assert "Test content to analyze" in query
        assert "Focus:" not in query

    def test_build_query_with_prompt_only(self):
        """Should format prompt without content."""
        debugger = self._create_debugger()

        query = debugger._build_query(prompt="Focus on error handling")

        assert "Focus: Focus on error handling" in query
        assert "Content to analyze:" not in query

    def test_build_query_with_both(self):
        """Should format both prompt and content."""
        debugger = self._create_debugger()

        query = debugger._build_query(
            content="Error: 500 Internal Server Error",
            prompt="Why did this error occur?",
        )

        assert "Focus: Why did this error occur?" in query
        assert "Content to analyze:" in query
        assert "Error: 500 Internal Server Error" in query

    def test_build_query_prompt_before_content(self):
        """Prompt (Focus) should appear before content."""
        debugger = self._create_debugger()

        query = debugger._build_query(
            content="Some content",
            prompt="Some prompt",
        )

        focus_index = query.find("Focus:")
        content_index = query.find("Content to analyze:")
        assert focus_index < content_index

    def test_build_query_empty(self):
        """Should return default message when neither content nor prompt provided."""
        debugger = self._create_debugger()

        query = debugger._build_query()

        assert query == "Please analyze the agent response and provide debugging insights."

    def test_build_query_none_values(self):
        """Should handle explicit None values."""
        debugger = self._create_debugger()

        query = debugger._build_query(content=None, prompt=None)

        assert query == "Please analyze the agent response and provide debugging insights."


# =============================================================================
# Debugger._extract_execution_id Tests
# =============================================================================


class TestDebuggerExtractExecutionId:
    """Tests for Debugger._extract_execution_id method."""

    def _create_debugger(self):
        """Helper to create a Debugger with mock context."""
        mock_context = Mock()
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        return BoundDebugger()

    def test_extract_from_request_id(self):
        """Should use request_id directly when available."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id="direct-request-id-123",
        )

        execution_id = debugger._extract_execution_id(response)

        assert execution_id == "direct-request-id-123"

    def test_extract_from_url_uuid_format(self):
        """Should extract UUID from /sdk/agents/{uuid}/ URL pattern."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id=None,
            url="https://api.example.com/sdk/agents/a1b2c3d4-e5f6-7890-abcd-ef1234567890/poll",
        )

        execution_id = debugger._extract_execution_id(response)

        assert execution_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    def test_extract_from_url_non_uuid_format(self):
        """Should extract non-UUID ID from /sdk/agents/{id}/ URL pattern."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id=None,
            url="https://api.example.com/sdk/agents/simple-id-123/poll",
        )

        execution_id = debugger._extract_execution_id(response)

        assert execution_id == "simple-id-123"

    def test_extract_returns_none_when_no_id_available(self):
        """Should return None when no ID is available."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id=None,
            url=None,
        )

        execution_id = debugger._extract_execution_id(response)

        assert execution_id is None

    def test_extract_returns_none_with_invalid_url(self):
        """Should return None when URL doesn't match expected pattern."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id=None,
            url="https://api.example.com/other/path/without/agents",
        )

        execution_id = debugger._extract_execution_id(response)

        assert execution_id is None

    def test_extract_prefers_request_id_over_url(self):
        """Should prefer request_id over extracting from URL."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id="request-id-wins",
            url="https://api.example.com/sdk/agents/url-id-loses/poll",
        )

        execution_id = debugger._extract_execution_id(response)

        assert execution_id == "request-id-wins"


# =============================================================================
# Debugger._serialize_response Tests
# =============================================================================


class TestDebuggerSerializeResponse:
    """Tests for Debugger._serialize_response method."""

    def _create_debugger(self):
        """Helper to create a Debugger with mock context."""
        mock_context = Mock()
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        return BoundDebugger()

    def test_serialize_basic_fields(self):
        """Should serialize status, completed, run_time, used_credits."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            run_time=1.5,
            used_credits=0.5,
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["status"] == "SUCCESS"
        assert parsed["completed"] is True
        assert parsed["run_time"] == 1.5
        assert parsed["used_credits"] == 0.5

    def test_serialize_with_execution_id(self):
        """Should include execution_id at top when available."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id="exec-id-123",
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["execution_id"] == "exec-id-123"
        # execution_id should be first key (for visibility)
        keys = list(parsed.keys())
        assert keys[0] == "execution_id"

    def test_serialize_with_error(self):
        """Should include error_message and supplier_error when present."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="FAILED",
            completed=True,
            error_message="Something went wrong",
            supplier_error="Upstream error",
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["error_message"] == "Something went wrong"
        assert parsed["supplier_error"] == "Upstream error"

    def test_serialize_with_data_having_to_dict(self):
        """Should use to_dict() method when data has it."""
        debugger = self._create_debugger()
        mock_data = Mock()
        mock_data.to_dict.return_value = {"key": "value"}

        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data=mock_data,
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["data"] == {"key": "value"}
        mock_data.to_dict.assert_called_once()

    def test_serialize_with_data_having_dict_attr(self):
        """Should use __dict__ when data doesn't have to_dict."""
        debugger = self._create_debugger()

        class SimpleData:
            def __init__(self):
                self.field1 = "value1"
                self.field2 = "value2"

        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data=SimpleData(),
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["data"]["field1"] == "value1"
        assert parsed["data"]["field2"] == "value2"

    def test_serialize_with_data_as_string(self):
        """Should use str() for data without to_dict or __dict__."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data="Simple string data",
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["data"] == "Simple string data"

    def test_serialize_with_override_execution_id(self):
        """Should use override execution_id instead of extracting."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id="original-id",
        )

        serialized = debugger._serialize_response(response, execution_id_override="override-id")
        parsed = json.loads(serialized)

        assert parsed["execution_id"] == "override-id"

    def test_serialize_includes_session_id(self):
        """Should include session_id when present."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            session_id="session-abc",
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["session_id"] == "session-abc"

    def test_serialize_includes_poll_url(self):
        """Should include poll_url when present."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            url="https://api.example.com/poll/123",
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["poll_url"] == "https://api.example.com/poll/123"

    def test_serialize_includes_result(self):
        """Should include result when present."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            result="The final result",
        )

        serialized = debugger._serialize_response(response)
        parsed = json.loads(serialized)

        assert parsed["result"] == "The final result"


# =============================================================================
# Debugger._convert_to_debug_result Tests
# =============================================================================


class TestDebuggerConvertToDebugResult:
    """Tests for Debugger._convert_to_debug_result method."""

    def _create_debugger(self):
        """Helper to create a Debugger with mock context."""
        mock_context = Mock()
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        return BoundDebugger()

    def test_convert_copies_all_fields(self):
        """Should copy all fields from AgentRunResult to DebugResult."""
        debugger = self._create_debugger()
        agent_result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data={"output": "Debug analysis"},
            session_id="session-123",
            request_id="request-456",
            used_credits=1.5,
            run_time=2.5,
            error_message="Some error",
            url="https://poll.url",
            result="Final result",
            supplier_error="Supplier error",
        )

        debug_result = debugger._convert_to_debug_result(agent_result)

        assert isinstance(debug_result, DebugResult)
        assert debug_result.status == "SUCCESS"
        assert debug_result.completed is True
        assert debug_result.data == {"output": "Debug analysis"}
        assert debug_result.session_id == "session-123"
        assert debug_result.request_id == "request-456"
        assert debug_result.used_credits == 1.5
        assert debug_result.run_time == 2.5
        assert debug_result.error_message == "Some error"
        assert debug_result.url == "https://poll.url"
        assert debug_result.result == "Final result"
        assert debug_result.supplier_error == "Supplier error"

    def test_convert_preserves_analysis_property(self):
        """Converted result should have working analysis property."""
        debugger = self._create_debugger()
        agent_result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data={"output": "The analysis text"},
        )

        debug_result = debugger._convert_to_debug_result(agent_result)

        assert debug_result.analysis == "The analysis text"


# =============================================================================
# Debugger.run Tests
# =============================================================================


class TestDebuggerRun:
    """Tests for Debugger.run method."""

    def _create_debugger(self):
        """Helper to create a Debugger with mock context."""
        mock_context = Mock()
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        return BoundDebugger()

    def test_run_calls_debugger_agent(self):
        """Should build query, get agent, run, and convert result."""
        debugger = self._create_debugger()

        # Mock the agent and its run method
        mock_agent = Mock()
        mock_agent.run.return_value = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data={"output": "Debug analysis result"},
        )

        with patch.object(debugger, "_get_debugger_agent", return_value=mock_agent):
            result = debugger.run(content="Test content")

        assert isinstance(result, DebugResult)
        assert result.status == "SUCCESS"
        mock_agent.run.assert_called_once()

    def test_run_with_custom_prompt(self):
        """Should pass prompt to _build_query."""
        debugger = self._create_debugger()

        mock_agent = Mock()
        mock_agent.run.return_value = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data={"output": "Analysis"},
        )

        with patch.object(debugger, "_get_debugger_agent", return_value=mock_agent):
            debugger.run(content="Content", prompt="Focus on performance")

        # Verify the query contains the prompt
        call_args = mock_agent.run.call_args
        query = call_args.kwargs.get("query") or call_args.args[0] if call_args.args else call_args.kwargs.get("query")
        assert "Focus: Focus on performance" in query

    def test_run_passes_kwargs_to_agent(self):
        """Should pass additional kwargs to the agent run method."""
        debugger = self._create_debugger()

        mock_agent = Mock()
        mock_agent.run.return_value = AgentRunResult(
            status="SUCCESS",
            completed=True,
        )

        with patch.object(debugger, "_get_debugger_agent", return_value=mock_agent):
            debugger.run(content="Content", timeout=60, custom_param="value")

        call_kwargs = mock_agent.run.call_args.kwargs
        assert call_kwargs.get("timeout") == 60
        assert call_kwargs.get("custom_param") == "value"


# =============================================================================
# Debugger.debug_response Tests
# =============================================================================


class TestDebuggerDebugResponse:
    """Tests for Debugger.debug_response method."""

    def _create_debugger(self):
        """Helper to create a Debugger with mock context."""
        mock_context = Mock()
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        return BoundDebugger()

    def test_debug_response_serializes_and_runs(self):
        """Should serialize response and call run."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data="Test data",
        )

        mock_debug_result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={"output": "Debug analysis"},
        )

        with patch.object(debugger, "run", return_value=mock_debug_result) as mock_run:
            result = debugger.debug_response(response)

        assert result is mock_debug_result
        mock_run.assert_called_once()
        # Verify content was passed (serialized response)
        call_kwargs = mock_run.call_args.kwargs
        assert "content" in call_kwargs
        assert call_kwargs["content"] is not None

    def test_debug_response_with_execution_id_override(self):
        """Should pass execution_id to serialize."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
            request_id="original-id",
        )

        mock_debug_result = DebugResult(status="SUCCESS", completed=True)

        with patch.object(debugger, "run", return_value=mock_debug_result) as mock_run:
            debugger.debug_response(response, execution_id="override-exec-id")

        # Verify the serialized content contains the override ID
        call_kwargs = mock_run.call_args.kwargs
        content = call_kwargs["content"]
        parsed = json.loads(content)
        assert parsed["execution_id"] == "override-exec-id"

    def test_debug_response_with_prompt(self):
        """Should pass prompt to run method."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
        )

        mock_debug_result = DebugResult(status="SUCCESS", completed=True)

        with patch.object(debugger, "run", return_value=mock_debug_result) as mock_run:
            debugger.debug_response(response, prompt="Why is this slow?")

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["prompt"] == "Why is this slow?"

    def test_debug_response_passes_kwargs(self):
        """Should pass additional kwargs to run method."""
        debugger = self._create_debugger()
        response = AgentRunResult(
            status="SUCCESS",
            completed=True,
        )

        mock_debug_result = DebugResult(status="SUCCESS", completed=True)

        with patch.object(debugger, "run", return_value=mock_debug_result) as mock_run:
            debugger.debug_response(response, timeout=120, custom="value")

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs.get("timeout") == 120
        assert call_kwargs.get("custom") == "value"


# =============================================================================
# Debugger._get_debugger_agent Tests
# =============================================================================


class TestDebuggerGetDebuggerAgent:
    """Tests for Debugger._get_debugger_agent method."""

    def test_get_debugger_agent_uses_correct_id(self):
        """Should call Agent.get with DEBUGGER_AGENT_ID."""
        mock_context = Mock()
        BoundDebugger = type("Debugger", (Debugger,), {"context": mock_context})
        debugger = BoundDebugger()

        mock_agent = Mock()

        # Patch the Agent.get class method at the class level
        # When the dynamic BoundAgent is created, it will inherit this patched method
        from aixplain.v2.agent import Agent

        with patch.object(Agent, "get", return_value=mock_agent) as mock_get:
            agent = debugger._get_debugger_agent()

            # Verify Agent.get was called with the correct ID
            mock_get.assert_called_once_with(DEBUGGER_AGENT_ID)
            assert agent is mock_agent

    def test_debugger_agent_id_constant(self):
        """DEBUGGER_AGENT_ID should have expected value."""
        assert DEBUGGER_AGENT_ID == "696fdccad63e898317c097a0"


# =============================================================================
# AgentRunResult.debug Tests
# =============================================================================


class TestAgentRunResultDebug:
    """Tests for AgentRunResult.debug method."""

    def test_debug_without_context_raises(self):
        """Should raise ValueError when _context is None."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
        )
        # _context is None by default

        with pytest.raises(ValueError, match="no client context available"):
            result.debug()

    def test_debug_with_context(self):
        """Should create bound debugger and call debug_response."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data="Test data",
        )
        result._context = Mock()

        mock_debug_result = DebugResult(
            status="SUCCESS",
            completed=True,
            data={"output": "Analysis"},
        )

        # Patch Debugger.debug_response at the class level
        # The dynamically created BoundDebugger will inherit this patched method
        with patch.object(Debugger, "debug_response", return_value=mock_debug_result) as mock_debug_response:
            # Also need to patch __init__ to avoid context validation since
            # the bound class has context set
            with patch.object(Debugger, "__init__", return_value=None):
                debug_result = result.debug()

        assert debug_result is mock_debug_result
        mock_debug_response.assert_called_once()

    def test_debug_passes_prompt(self):
        """Should forward prompt to debugger."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
        )
        result._context = Mock()

        mock_debug_result = DebugResult(status="SUCCESS", completed=True)

        with patch.object(Debugger, "debug_response", return_value=mock_debug_result) as mock_debug_response:
            with patch.object(Debugger, "__init__", return_value=None):
                result.debug(prompt="Why is it slow?")

        mock_debug_response.assert_called_once()
        call_kwargs = mock_debug_response.call_args.kwargs
        assert call_kwargs.get("prompt") == "Why is it slow?"

    def test_debug_passes_execution_id(self):
        """Should forward execution_id to debugger."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
        )
        result._context = Mock()

        mock_debug_result = DebugResult(status="SUCCESS", completed=True)

        with patch.object(Debugger, "debug_response", return_value=mock_debug_result) as mock_debug_response:
            with patch.object(Debugger, "__init__", return_value=None):
                result.debug(execution_id="exec-123")

        call_kwargs = mock_debug_response.call_args.kwargs
        assert call_kwargs.get("execution_id") == "exec-123"

    def test_debug_passes_kwargs(self):
        """Should forward additional kwargs to debugger."""
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
        )
        result._context = Mock()

        mock_debug_result = DebugResult(status="SUCCESS", completed=True)

        with patch.object(Debugger, "debug_response", return_value=mock_debug_result) as mock_debug_response:
            with patch.object(Debugger, "__init__", return_value=None):
                result.debug(timeout=60, custom_param="value")

        call_kwargs = mock_debug_response.call_args.kwargs
        assert call_kwargs.get("timeout") == 60
        assert call_kwargs.get("custom_param") == "value"
