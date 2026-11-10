"""Unit tests for agent context-overflow-strategy serialization.

``context_overflow_strategy`` is a first-class agent field that can be set once
on the agent (persisted with the save payload) or overridden for a single run
via ``execution_params={"context_overflow_strategy": ...}``. The run-time value
is what the backend uses to condense the working context, so the precedence and
the exact wire key (``executionParams.contextOverflowStrategy``) both matter.
These tests cover:
- An unset strategy leaves the run payload's ``contextOverflowStrategy`` at
  ``None`` (the backend default).
- A strategy set as a plain string or the enum serializes to its string value in
  both the save and run payloads.
- The agent-level value is used as the run default when no override is given.
- A per-run ``execution_params`` override wins over the agent-level value.
"""

from unittest.mock import MagicMock

from aixplain.v2.agent import Agent, ContextOverflowStrategy


def _create_agent():
    """Build a V2 Agent through ``from_dict`` with a mocked client context."""
    agent = Agent.from_dict({"id": "agent-123", "name": "context-overflow-agent"})
    agent.context = MagicMock()
    return agent


def test_run_payload_defaults_context_overflow_strategy_to_none():
    agent = _create_agent()

    payload = agent.build_run_payload(query="hi")

    assert payload["executionParams"]["contextOverflowStrategy"] is None


def test_save_payload_serializes_strategy_set_as_string():
    agent = _create_agent()
    agent.context_overflow_strategy = "summarize"

    payload = agent.build_save_payload()

    assert payload["contextOverflowStrategy"] == "summarize"


def test_save_payload_serializes_strategy_set_as_enum():
    agent = _create_agent()
    agent.context_overflow_strategy = ContextOverflowStrategy.SUMMARIZE

    payload = agent.build_save_payload()

    assert payload["contextOverflowStrategy"] == "summarize"


def test_run_payload_uses_agent_level_strategy():
    agent = _create_agent()
    agent.context_overflow_strategy = "summarize"

    payload = agent.build_run_payload(query="hi")

    assert payload["executionParams"]["contextOverflowStrategy"] == "summarize"


def test_run_payload_per_run_override_wins():
    agent = _create_agent()
    agent.context_overflow_strategy = "summarize"

    payload = agent.build_run_payload(
        query="hi",
        execution_params={"context_overflow_strategy": "truncate"},
    )

    assert payload["executionParams"]["contextOverflowStrategy"] == "truncate"
