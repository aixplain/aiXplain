"""Argument-validation tests for `AgentFactory.create`.

Moved out of `tests/functional/` by BUG-947: every create here is inside
`pytest.raises` and the SDK raises while validating its arguments, before any
HTTP call is made, so this needs neither a credential nor a network -- and used
to occupy a CI leg running against the production tenant.
"""

import pytest
from aixplain.factories import AgentFactory


def test_invalid_agent_name():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="[Test]",
            description="",
            instructions="",
            tools=[],
            llm_id="69b7e5f1b2fe44704ab0e7d0",
        )
    assert str(exc_info.value) == (
        "Agent Creation Error: Agent name contains invalid characters. "
        "Only alphanumeric characters, spaces, hyphens, and brackets are allowed."
    )
