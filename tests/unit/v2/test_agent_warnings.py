"""Structured agent warnings (ENG-3851): ``warnings`` on results, and ``error_details``/``warnings`` on a failed run."""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from dataclasses_json import dataclass_json

import aixplain
from aixplain.v2.agent import Agent, AgentError, AgentResponseData, AgentRunResult, AgentWarning
from aixplain.v2.exceptions import AgentRunFailedError, APIError

POLL_URL = "https://platform-api.aixplain.com/sdk/agents/x/result"
WARNING = {"code": "MAX_TOKENS_REACHED", "message": "The model reached its output token limit."}


def _create_agent(poll_body=None):
    """Agent whose poll returns ``poll_body``."""

    @dataclass_json
    @dataclass
    class BoundAgent(Agent):
        pass

    agent = BoundAgent(id="agent-123", name="test-agent")
    agent.context = Mock()
    agent.context.backend_url = "https://platform-api.aixplain.com"
    agent.context.client.get = Mock(return_value=poll_body)
    return agent


class TestWarningsOnResults:
    """``warnings`` decodes on both the result and its data."""

    def test_defaults_to_empty_list(self):
        """Warnings default to an empty list."""
        result = AgentRunResult.from_dict({"status": "SUCCESS", "completed": True, "data": {"output": "o"}})

        assert result.warnings == []
        assert result.data.warnings == []

    def test_explicit_null_is_empty_list(self):
        """An explicit null decodes to an empty list."""
        data = AgentResponseData.from_dict({"output": "o", "warnings": None})

        assert data.warnings == []

    def test_top_level_warnings_decode(self):
        """Top-level warnings (where the backend lifts them) decode."""
        result = AgentRunResult.from_dict(
            {"status": "SUCCESS", "completed": True, "warnings": [WARNING], "data": {"output": "o"}}
        )

        assert result.warnings == [AgentWarning(code="MAX_TOKENS_REACHED", message=WARNING["message"])]

    def test_warnings_under_data_are_promoted(self):
        """Warnings nested under ``data`` are promoted to the result."""
        result = AgentRunResult.from_dict(
            {"status": "SUCCESS", "completed": True, "data": {"output": "o", "warnings": [WARNING]}}
        )

        assert result.data.warnings == [AgentWarning(**WARNING)]
        assert result.warnings == [AgentWarning(**WARNING)]
        assert result.error is None

    def test_warnings_under_bare_dict_data_are_promoted(self):
        """A hand-built result with dict ``data`` still promotes warnings."""
        result = AgentRunResult(status="SUCCESS", completed=True, data={"warnings": [{"code": "TOOL_FAILED"}]})

        assert result.warnings == [AgentWarning(code="TOOL_FAILED")]

    def test_malformed_entries_are_skipped(self):
        """Entries with neither code nor message are skipped."""
        data = AgentResponseData.from_dict({"warnings": [WARNING, {}, "x", None]})

        assert data.warnings == [AgentWarning(**WARNING)]

    def test_round_trips_to_wire_shape(self):
        """Warnings serialize back to ``{code, message}``."""
        result = AgentRunResult.from_dict({"status": "SUCCESS", "completed": True, "warnings": [WARNING]})

        assert result.to_dict()["warnings"] == [WARNING]

    def test_poll_forwards_top_level_warnings(self):
        """A poll keeps the warnings the backend lifts to the top level."""
        agent = _create_agent({"status": "SUCCESS", "completed": True, "warnings": [WARNING], "data": {"output": "o"}})

        result = agent.poll(POLL_URL)

        assert result.status == "SUCCESS"
        assert result.warnings == [AgentWarning(**WARNING)]


class TestFailedRunCarriesStructuredDetails:
    """A FAILED agent run raises ``AgentRunFailedError`` with its error details and warnings."""

    FAILED_BODY = {
        "status": "FAILED",
        "completed": True,
        "data": {
            "output": "",
            "diagnosticErrorCodes": ["MAX_TOKENS_REACHED", "INTERNAL_ERROR"],
            "warnings": [WARNING],
            "errorDetails": {"code": "INTERNAL_ERROR", "message": "Something went wrong."},
        },
    }

    def test_poll_raises_agent_run_failed_error(self):
        """Poll raises with the fatal error and warnings attached."""
        agent = _create_agent(self.FAILED_BODY)

        with pytest.raises(AgentRunFailedError) as exc_info:
            agent.poll(POLL_URL)

        error = exc_info.value
        assert isinstance(error, APIError)
        assert error.error == "Something went wrong."
        assert error.retryable is False
        assert error.error_details == AgentError(code="INTERNAL_ERROR", message="Something went wrong.")
        assert error.warnings == [AgentWarning(**WARNING)]

    def test_sync_response_raises_agent_run_failed_error(self):
        """The direct-response path raises the same error."""
        agent = _create_agent()

        with pytest.raises(AgentRunFailedError) as exc_info:
            agent.handle_run_response(self.FAILED_BODY)

        assert exc_info.value.error_details.code == "INTERNAL_ERROR"

    def test_top_level_details_win(self):
        """Top-level error details and warnings win over ``data``."""
        agent = _create_agent()
        body = {
            "status": "FAILED",
            "errorDetails": {"code": "RUN_TIMEOUT"},
            "warnings": [{"code": "TOOL_FAILED"}],
            "data": {"errorDetails": {"code": "OTHER"}, "warnings": [WARNING]},
        }

        with pytest.raises(AgentRunFailedError) as exc_info:
            agent.handle_run_response(body)

        assert exc_info.value.error_details == AgentError(code="RUN_TIMEOUT")
        assert exc_info.value.warnings == [AgentWarning(code="TOOL_FAILED")]

    def test_description_fills_message(self):
        """A ``{code, description}`` error keeps the description as its message."""
        agent = _create_agent()
        body = {"status": "FAILED", "data": {"error": {"code": "AX-RES-1000", "description": "Tool missing."}}}

        with pytest.raises(AgentRunFailedError) as exc_info:
            agent.handle_run_response(body)

        assert exc_info.value.error_details == AgentError(code="AX-RES-1000", message="Tool missing.")

    def test_legacy_string_error_has_no_details(self):
        """A legacy string-only failure still raises, with no structured details."""
        agent = _create_agent()

        with pytest.raises(AgentRunFailedError) as exc_info:
            agent.handle_run_response({"status": "FAILED", "data": {"error": "old engine error"}})

        assert exc_info.value.error == "old engine error"
        assert exc_info.value.error_details is None
        assert exc_info.value.warnings == []


def test_new_names_are_exported():
    """The new names are importable from the package root and the exceptions path."""
    from aixplain.exceptions import AgentRunFailedError as from_exceptions

    assert aixplain.AgentWarning is AgentWarning
    assert aixplain.AgentRunFailedError is AgentRunFailedError
    assert from_exceptions is AgentRunFailedError
