"""Argument-validation tests for `AgentFactory.create`.

Moved out of `tests/functional/` by BUG-947, where it used to occupy a CI leg
running against the production tenant. `AgentFactory.create` resolves the LLM
before it validates the agent name, so the lookup is stubbed out here; the
assertion below is on the name validation that follows it, and no HTTP call is
made.
"""

from unittest.mock import patch

import pytest
from aixplain.factories import AgentFactory


def test_invalid_agent_name():
    with patch("aixplain.utils.llm_utils.get_llm_instance") as mock_get_llm, pytest.raises(Exception) as exc_info:
        mock_get_llm.return_value = None
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
