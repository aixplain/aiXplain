"""Unit tests for structured diagnostic error codes in agent run responses (PR #718)."""

import pytest
from aixplain.v2.agent import AgentResponseData, AgentRunResult
from aixplain.v2.enums import DiagnosticErrorCode, GovernanceStatus


class TestDiagnosticErrorCodeEnum:
    def test_enum_values_are_strings(self):
        assert DiagnosticErrorCode.MAX_TOKENS_REACHED == "MAX_TOKENS_REACHED"
        assert DiagnosticErrorCode.TOOL_FAILED == "TOOL_FAILED"
        assert DiagnosticErrorCode.INVALID_JSON == "INVALID_JSON"
        assert DiagnosticErrorCode.INSPECTOR_ABORT == "INSPECTOR_ABORT"
        assert DiagnosticErrorCode.OUTPUT_TRUNCATED == "OUTPUT_TRUNCATED"

    def test_all_taxonomy_codes_present(self):
        expected = {
            "MAX_TOKENS_REACHED",
            "MAX_ITERATIONS_REACHED",
            "MODEL_TIMEOUT",
            "RATE_LIMITED",
            "TOOL_FAILED",
            "TOOL_TIMEOUT",
            "TOOL_AUTH_FAILED",
            "TOOL_BAD_RESPONSE",
            "INVALID_JSON",
            "WRONG_LANGUAGE",
            "EMPTY_OUTPUT",
            "OUTPUT_TRUNCATED",
            "INSPECTOR_ABORT",
            "POLICY_BLOCKED",
            "INVALID_AGENT_CONFIGURATION",
            "MISSING_TOOL_CONFIGURATION",
        }
        actual = {code.value for code in DiagnosticErrorCode}
        assert expected == actual


class TestGovernanceStatusEnum:
    def test_enum_values(self):
        assert GovernanceStatus.ALLOWED == "ALLOWED"
        assert GovernanceStatus.BLOCKED_BY_INSPECTOR == "BLOCKED_BY_INSPECTOR"
        assert GovernanceStatus.BLOCKED_BY_POLICY == "BLOCKED_BY_POLICY"

    def test_is_string_enum(self):
        assert isinstance(GovernanceStatus.ALLOWED, str)


class TestAgentResponseDataErrorCodes:
    def test_error_codes_defaults_to_empty_list(self):
        data = AgentResponseData()
        assert data.error_codes == []

    def test_error_codes_populated_from_response(self):
        data = AgentResponseData(error_codes=["TOOL_FAILED", "MAX_TOKENS_REACHED"])
        assert "TOOL_FAILED" in data.error_codes
        assert "MAX_TOKENS_REACHED" in data.error_codes

    def test_governance_status_defaults_to_none(self):
        data = AgentResponseData()
        assert data.governance_status is None

    def test_governance_fields_populated(self):
        data = AgentResponseData(
            governance_status="BLOCKED_BY_INSPECTOR",
            governance_source="INSPECTOR",
            governance_reason="Policy violation detected",
        )
        assert data.governance_status == "BLOCKED_BY_INSPECTOR"
        assert data.governance_source == "INSPECTOR"
        assert data.governance_reason == "Policy violation detected"

    def test_deserialization_from_dict(self):
        raw = {
            "input": "test query",
            "output": "test output",
            "error_codes": ["TOOL_FAILED"],
            "governance_status": "ALLOWED",
        }
        data = AgentResponseData.from_dict(raw)
        assert data.error_codes == ["TOOL_FAILED"]
        assert data.governance_status == "ALLOWED"
        assert data.input == "test query"

    def test_deserialization_missing_error_codes_defaults_to_empty(self):
        raw = {"input": "q", "output": "a"}
        data = AgentResponseData.from_dict(raw)
        assert data.error_codes == []

    def test_governance_status_accepts_enum_value(self):
        data = AgentResponseData(governance_status=GovernanceStatus.BLOCKED_BY_POLICY)
        assert data.governance_status == "BLOCKED_BY_POLICY"


class TestAgentRunResultErrorCodeAccess:
    def test_error_codes_accessible_through_data(self):
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data=AgentResponseData(
                input="q",
                output="a",
                error_codes=["MAX_TOKENS_REACHED"],
            ),
        )
        assert result.data.error_codes == ["MAX_TOKENS_REACHED"]

    def test_no_error_codes_on_clean_run(self):
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data=AgentResponseData(input="q", output="a"),
        )
        assert result.data.error_codes == []

    def test_governance_blocked_run(self):
        result = AgentRunResult(
            status="SUCCESS",
            completed=True,
            data=AgentResponseData(
                input="q",
                output="blocked",
                error_codes=["INSPECTOR_ABORT"],
                governance_status="BLOCKED_BY_INSPECTOR",
            ),
        )
        assert result.data.governance_status == "BLOCKED_BY_INSPECTOR"
        assert DiagnosticErrorCode.INSPECTOR_ABORT.value in result.data.error_codes
