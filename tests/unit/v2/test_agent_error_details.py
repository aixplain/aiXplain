"""Structured agent errors (PROD-2521): ``errorDetails`` is added without changing what agent results already expose."""

from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from dataclasses_json import dataclass_json

from aixplain.v2.agent import Agent, AgentError, AgentResponseData, AgentRunResult
from aixplain.v2.agent_progress import _step_error_text
from aixplain.v2.exceptions import APIError, create_operation_failed_error

POLL_URL = "https://platform-api.aixplain.com/sdk/agents/x/result"


def _create_agent(poll_body):
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


class TestLegacyFieldsUnchanged:
    """Fields agent results exposed before PROD-2521 keep their values."""

    def test_error_message_and_supplier_error_still_construct_and_serialize(self):
        """Error message and supplier error still construct and serialize."""
        result = AgentRunResult(status="FAILED", completed=True, error_message="boom", supplier_error="upstream")

        assert result.error_message == "boom"
        assert result.supplier_error == "upstream"
        payload = result.to_dict()
        assert payload["errorMessage"] == "boom"
        assert payload["supplierError"] == "upstream"

    def test_legacy_fields_default_to_none(self):
        """Legacy fields default to none."""
        result = AgentRunResult.from_dict({"status": "SUCCESS", "completed": True, "data": {"output": "o"}})

        assert result.error_message is None
        assert result.supplier_error is None
        assert result.error is None

    def test_poll_fills_error_message_from_error_details(self):
        """Poll fills error message from error details."""
        agent = _create_agent(
            {
                "status": "SUCCESS",
                "completed": True,
                "data": {"output": "o", "errorDetails": {"code": "TOOL_FAILED", "message": "Tool broke."}},
            }
        )

        result = agent.poll(POLL_URL)

        assert result.error_message == "Tool broke."
        assert result.error == AgentError(code="TOOL_FAILED", message="Tool broke.")
        assert result.supplier_error is None

    def test_poll_still_reads_the_legacy_error_string(self):
        """Poll still reads the legacy error string."""
        agent = _create_agent({"status": "SUCCESS", "completed": True, "data": {"output": "o", "error": "old text"}})

        result = agent.poll(POLL_URL)

        assert result.error_message == "old text"
        assert result.error == AgentError(message="old text")

    def test_poll_keeps_supplier_error(self):
        """Poll keeps supplier error."""
        agent = _create_agent(
            {"status": "SUCCESS", "completed": True, "supplierError": "upstream", "data": {"output": "o"}}
        )

        assert agent.poll(POLL_URL).supplier_error == "upstream"


class TestStructuredError:
    """The new ``error`` field decodes ``errorDetails``."""

    def test_top_level_error_details(self):
        """Top level error details."""
        result = AgentRunResult.from_dict(
            {"status": "SUCCESS", "completed": True, "errorDetails": {"code": "TOOL_FAILED", "message": "x"}}
        )

        assert result.error == AgentError(code="TOOL_FAILED", message="x")
        assert result.to_dict()["errorDetails"] == {"code": "TOOL_FAILED", "message": "x"}

    def test_error_details_promoted_from_data(self):
        """Error details promoted from data."""
        result = AgentRunResult.from_dict(
            {
                "status": "SUCCESS",
                "completed": True,
                "data": {"output": "o", "errorDetails": {"code": "RUN_TIMEOUT", "message": "late"}},
            }
        )

        assert isinstance(result.data, AgentResponseData)
        assert result.data.error == AgentError(code="RUN_TIMEOUT", message="late")
        assert result.error == AgentError(code="RUN_TIMEOUT", message="late")


class TestFailedStepsKeepTheirOutput:
    """A failed step's ``output`` reads as it did before steps had ``error``."""

    def test_failed_step_output_reads_as_before(self):
        """Failed step output reads as before."""
        data = AgentResponseData.from_dict(
            {"steps": [{"step_id": "c1", "output": None, "error": {"code": "TOOL_FAILED", "message": "timeout"}}]}
        )

        (step,) = data.steps
        assert step["output"] == "ERROR: timeout"
        assert step["error"] == {"code": "TOOL_FAILED", "message": "timeout"}

    def test_steps_without_error_or_with_output_are_untouched(self):
        """Steps without error or with output are untouched."""
        steps = [
            {"step_id": "ok", "output": "fine"},
            {"step_id": "kept", "output": "partial", "error": {"code": "X", "message": "m"}},
        ]

        data = AgentResponseData.from_dict({"steps": steps})

        assert [s["output"] for s in data.steps] == ["fine", "partial"]

    def test_nested_delegation_steps_are_restored(self):
        """Nested delegation steps are restored."""
        data = AgentResponseData.from_dict(
            {
                "steps": [
                    {
                        "step_id": "c1",
                        "output": "done",
                        "steps": [{"step_id": "child", "error": {"code": "TOOL_FAILED", "message": "m"}}],
                    }
                ]
            }
        )

        assert data.steps[0]["steps"][0]["output"] == "ERROR: m"

    def test_poll_restores_the_raw_steps_progress_display_reads(self):
        """Poll restores the raw steps progress display reads."""
        agent = _create_agent(
            {
                "status": "IN_PROGRESS",
                "completed": False,
                "data": {"steps": [{"step_id": "c1", "error": {"code": "TOOL_FAILED", "message": "m"}}]},
            }
        )

        result = agent.poll(POLL_URL)

        assert result._raw_data["data"]["steps"][0]["output"] == "ERROR: m"


class TestFailedRunRaises:
    """A FAILED run raises ``APIError`` with the run's message."""

    def test_poll_failed_raises_with_the_structured_message(self):
        """Poll failed raises with the structured message."""
        agent = _create_agent(
            {
                "status": "FAILED",
                "completed": True,
                "data": {"errorDetails": {"code": "MODEL_UNAVAILABLE", "message": "model down"}},
            }
        )

        with pytest.raises(APIError) as exc_info:
            agent.poll(POLL_URL)

        assert exc_info.value.error == "model down"

    def test_error_details_win_over_legacy_strings(self):
        """Error details win over legacy strings."""
        error = create_operation_failed_error(
            {
                "status": "FAILED",
                "errorMessage": "legacy top",
                "data": {"errorDetails": {"code": "TOOL_FAILED", "message": "structured"}},
            }
        )

        assert error.error == "structured"
        assert error.retryable is False

    def test_code_only(self):
        """Code only."""
        error = create_operation_failed_error({"status": "FAILED", "errorDetails": {"code": "RUN_TIMEOUT"}})

        assert error.error == "RUN_TIMEOUT"

    def test_legacy_string_still_used_without_error_details(self):
        """Legacy string still used without error details."""
        error = create_operation_failed_error({"status": "FAILED", "data": {"error": "old engine error"}})

        assert error.error == "old engine error"

    def test_structured_error_under_error_key_is_not_stringified(self):
        """Structured error under error key is not stringified."""
        error = create_operation_failed_error({"status": "FAILED", "error": {"code": "X", "message": "m"}})

        assert error.error == "m"


class TestStepErrorText:
    """Progress display renders a step's ``error``."""

    @pytest.mark.parametrize(
        "step, expected",
        [
            ({"error": {"code": "TOOL_FAILED", "message": "timeout"}}, "TOOL_FAILED: timeout"),
            ({"error": {"code": "TOOL_FAILED"}}, "TOOL_FAILED"),
            ({"error": {}}, None),
            ({"error": "legacy"}, "legacy"),
            ({"error_message": "older"}, "older"),
            ({"output": "fine"}, None),
        ],
    )
    def test_formats(self, step, expected):
        """Formats."""
        assert _step_error_text(step) == expected
