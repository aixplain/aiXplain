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
