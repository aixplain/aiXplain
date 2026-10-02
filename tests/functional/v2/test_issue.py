"""Functional tests for ``aix.issue`` against the live issue endpoint.

The issue endpoint may be gated per environment, so a controlled 4xx is an
acceptable acknowledgement; a 5xx or a missing ``issue_id`` is not.
"""

import time
import uuid

import pytest

from aixplain.v2.exceptions import AixplainIssueError


@pytest.fixture(scope="module")
def issue_agent(client, module_resource_tracker):
    agent = client.Agent(
        name=f"Issue Test Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        instructions="Answer in one short sentence.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


def _report_or_accept_gating(client, description, **kwargs):
    """Report an issue; return the id, or None when the endpoint is gated 4xx."""
    try:
        return client.issue.report(description, **kwargs)
    except AixplainIssueError as error:
        assert 400 <= (error.status_code or 0) < 500, error
        return None


def test_report_minimal_issue(client):
    issue_id = _report_or_accept_gating(client, "Functional test: minimal issue report.")

    if issue_id is not None:
        assert isinstance(issue_id, str) and issue_id


def test_report_issue_against_a_run_id(client, issue_agent):
    run = issue_agent.run(query="Say hello.")
    run_id = run.request_id or run.url

    issue_id = _report_or_accept_gating(
        client,
        "Functional test: issue tied to an agent run.",
        title="Agent run issue",
        severity="SEV3",
        runtime_context={"run_id": run_id},
    )

    if issue_id is not None:
        assert isinstance(issue_id, str) and issue_id


def test_report_validates_severity_without_a_backend_call(client):
    with pytest.raises(AixplainIssueError) as exc_info:
        client.issue.report("Functional test: bad severity.", severity="CRITICAL")

    assert exc_info.value.status_code == 400


def test_report_requires_a_description(client):
    with pytest.raises(AixplainIssueError):
        client.issue.report(None)
