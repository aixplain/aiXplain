"""Issue reporting helpers for the V2 SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING

from .exceptions import APIError, AixplainIssueError

if TYPE_CHECKING:
    from .core import Aixplain


class IssueSeverity(str, Enum):
    """Supported issue severity levels."""

    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"
    SEV4 = "SEV4"


class IssueReporter:
    """submitting SDK issues to the backend."""

    ISSUE_PATH = "/v1/issue"

    def __init__(self, context: "Aixplain") -> None:
        """Initialize the issue reporter."""
        self.context = context

    def _issue_url(self) -> str:
        """Build the full issue endpoint URL for the configured backend."""
        return f"{self.context.backend_url.rstrip('/')}{self.ISSUE_PATH}"

    def report(self, description: Optional[str], **kwargs: Any) -> str:
        """Submit an issue report and return its ID."""
        self._validate_description(description)

        allowed_fields = {
            "title",
            "severity",
            "tags",
            "sdk_version",
            "runtime_context",
            "reporter_email",
        }
        unexpected_fields = sorted(set(kwargs) - allowed_fields)
        if unexpected_fields:
            raise AixplainIssueError(
                f"Unsupported issue fields: {', '.join(unexpected_fields)}.",
            )

        severity = kwargs.get("severity")
        if severity is not None:
            self._validate_severity(severity)

        payload: Dict[str, Any] = {"description": description}
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value.value if isinstance(value, IssueSeverity) else value

        try:
            response = self.context.client.post(self._issue_url(), json=payload)
        except APIError as error:
            raise AixplainIssueError(
                error.message,
                status_code=error.status_code,
                response_data=error.response_data,
                error=error.error,
            ) from error

        issue_id = response.get("issue_id")
        if not issue_id:
            raise AixplainIssueError(
                "Issue report accepted but no issue_id was returned.",
                status_code=202,
                response_data=response,
                error="missing_issue_id",
            )
        return issue_id

    @staticmethod
    def _validate_description(description: Optional[str]) -> None:
        if description is None:
            raise AixplainIssueError("Field 'description' is required.", status_code=400)
    @staticmethod
    def _validate_severity(severity: Any) -> None:
        valid_values = {level.value for level in IssueSeverity}
        resolved = severity.value if isinstance(severity, IssueSeverity) else severity
        if resolved not in valid_values:
            raise AixplainIssueError(
                "severity must be one of: SEV1, SEV2, SEV3, SEV4.",
                status_code=400,
            )
