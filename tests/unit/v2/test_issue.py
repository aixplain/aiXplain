"""Unit tests for the v2 issue reporting client."""

from unittest.mock import Mock

import pytest

from aixplain.v2.core import Aixplain
from aixplain.v2.exceptions import APIError, AixplainIssueError
from aixplain.v2.issue import IssueSeverity


class TestIssueReporter:

    def test_report_minimal_submission(self):
        aix = Aixplain(api_key="test-key")
        aix.client.post = Mock(return_value={"issue_id": "issue-123", "bug_board_url": "https://bugs.example.com/issue-123"})

        issue_id = aix.issue.report("Pipeline times out on step 3 when using GPT-4o tool")

        assert issue_id == "issue-123"
        aix.client.post.assert_called_once_with(
            "https://dev-platform-api.aixplain.com/v1/issue",
            json={"description": "Pipeline times out on step 3 when using GPT-4o tool"},
        )

    def test_report_full_submission_payload(self):
        aix = Aixplain(api_key="test-key")
        aix.client.post = Mock(return_value={"issue_id": "issue-456", "bug_board_url": "https://bugs.example.com/issue-456"})

        issue_id = aix.issue.report(
            "Pipeline times out on step 3 when using GPT-4o tool",
            title="GPT-4o pipeline timeout on step 3",
            severity=IssueSeverity.SEV2,
            tags=["sdk", "timeout"],
            sdk_version="1.4.2",
            runtime_context={"trace_id": "abc-123", "environment": "production"},
            reporter_email="developer@example.com",
        )

        assert issue_id == "issue-456"
        aix.client.post.assert_called_once_with(
            "https://dev-platform-api.aixplain.com/v1/issue",
            json={
                "description": "Pipeline times out on step 3 when using GPT-4o tool",
                "title": "GPT-4o pipeline timeout on step 3",
                "severity": "SEV2",
                "tags": ["sdk", "timeout"],
                "sdk_version": "1.4.2",
                "runtime_context": {
                    "trace_id": "abc-123",
                    "environment": "production",
                },
                "reporter_email": "developer@example.com",
            },
        )

    def test_report_omits_none_fields(self):
        aix = Aixplain(api_key="test-key")
        aix.client.post = Mock(return_value={"issue_id": "issue-789"})

        aix.issue.report(
            "Agent crashes on tool invocation",
            title=None,
            severity="SEV1",
            sdk_version="1.4.2",
        )

        aix.client.post.assert_called_once_with(
            "https://dev-platform-api.aixplain.com/v1/issue",
            json={
                "description": "Agent crashes on tool invocation",
                "severity": "SEV1",
                "sdk_version": "1.4.2",
            },
        )


    @pytest.mark.parametrize(
        ("description", "message"),
        [
            (None, "Field 'description' is required.")
        ],
    )
    def test_report_validates_description(self, description, message):
        aix = Aixplain(api_key="test-key")

        with pytest.raises(AixplainIssueError, match=message):
            aix.issue.report(description)

    def test_report_validates_severity(self):
        aix = Aixplain(api_key="test-key")

        with pytest.raises(AixplainIssueError, match="severity must be one of: SEV1, SEV2, SEV3, SEV4."):
            aix.issue.report("Agent crashes on tool invocation", severity="CRITICAL")

    def test_report_wraps_api_error(self):
        aix = Aixplain(api_key="test-key")
        aix.client.post = Mock(
            side_effect=APIError(
                "Field 'description' must not be empty.",
                status_code=400,
                response_data={"message": "Field 'description' must not be empty."},
                error="VALIDATION_ERROR",
            )
        )

        with pytest.raises(AixplainIssueError) as exc_info:
            aix.issue.report("   broken   ".strip())

        assert exc_info.value.message == "Field 'description' must not be empty."
        assert exc_info.value.status_code == 400
        assert exc_info.value.response_data == {"message": "Field 'description' must not be empty."}
        assert exc_info.value.error == "VALIDATION_ERROR"

    def test_report_rejects_unknown_fields(self):
        aix = Aixplain(api_key="test-key")

        with pytest.raises(AixplainIssueError, match="Unsupported issue fields: unknown_field."):
            aix.issue.report("Example issue", unknown_field="value")

    def test_report_requires_issue_id_in_response(self):
        aix = Aixplain(api_key="test-key")
        aix.client.post = Mock(return_value={"bug_board_url": "https://bugs.example.com/issue-123"})

        with pytest.raises(AixplainIssueError, match="no issue_id was returned"):
            aix.issue.report("Pipeline times out on step 3 when using GPT-4o tool")
