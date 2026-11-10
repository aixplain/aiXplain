"""Functional tests for ``aix.issue`` against the live issue endpoint.

A report must come back with an ``issue_id``: neither the SDK nor the backend
documents a gating response for this endpoint, so any error -- a wrong path, a
bad key, a rejected payload -- fails the test rather than passing as gated.

The endpoint has no delete API, so every issue these tests file stays on the
backend. Each one is marked as test traffic (the ``sdk-functional-test`` tag, a
``[sdk-functional-test]`` title prefix and the lowest severity, SEV4) so triage
can filter it out. The
validations that never reach the backend are unit-tested in
``tests/unit/v2/test_issue.py``.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
import uuid

import pytest

TEST_TAG = "sdk-functional-test"
TEST_SEVERITY = "SEV4"


@pytest.fixture(scope="module")
def issue_agent(client, module_resource_tracker):
    agent = client.Agent(
        name=f"Issue Test Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        instructions="Answer in one short sentence.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


def _report_test_issue(client, title, description, **kwargs):
    """File an issue marked as functional-test traffic and return its id."""
    return client.issue.report(
        description,
        title=f"[{TEST_TAG}] {title}",
        severity=TEST_SEVERITY,
        tags=[TEST_TAG],
        **kwargs,
    )


def test_report_minimal_issue(client):
    issue_id = _report_test_issue(client, "Minimal issue report", "Functional test: minimal issue report.")

    assert isinstance(issue_id, str) and issue_id, issue_id


def test_report_issue_against_a_run_id(client, issue_agent):
    run = issue_agent.run(query="Say hello.")
    run_id = run.request_id or run.url
    assert run_id, run

    issue_id = _report_test_issue(
        client,
        "Agent run issue",
        "Functional test: issue tied to an agent run.",
        runtime_context={"run_id": run_id},
    )

    assert isinstance(issue_id, str) and issue_id, issue_id
