"""V2 Agent backward-compat regression tests (V3 engine compatibility).

Covers three SDK-side regressions surfaced during V3 DEV testing:
- R5: dict ``expected_output`` accepted at save but rejected at run.
- R6: ``output_format='json'`` crashes at save when ``expected_output`` is unset.
- R3: inspectors deserialize as plain dicts instead of ``Inspector`` objects on ``get()``.
"""

import json
from unittest.mock import MagicMock

import pytest

from aixplain.v2.agent import Agent
from aixplain.v2.inspector import Inspector


def _agent_from_dict(**overrides):
    """Build a V2 Agent through ``from_dict`` with a mocked client context."""
    base = {
        "id": "agent-123",
        "name": "Test Agent",
        "instructions": "Do the thing.",
        "llmId": "69b7e5f1b2fe44704ab0e7d0",
        "tools": [],
        "tasks": [],
        "agents": [],
        "outputFormat": "json",
        "inspectorTargets": [],
        "inspectors": [],
        "maxIterations": 5,
        "maxTokens": 2048,
    }
    base.update(overrides)
    agent = Agent.from_dict(base)
    agent.context = MagicMock()
    return agent


class TestR5DictExpectedOutputRunPayload:
    """A dict ``expected_output`` must be serialized to a JSON string at run time."""

    def test_dict_expected_output_becomes_json_string_in_run_payload(self):
        schema = {"name": "string", "city": "string"}
        agent = _agent_from_dict(outputFormat="json", expectedOutput=schema)

        payload = agent.build_run_payload(query="hi", run_response_generation=True)

        sent = payload["executionParams"]["expectedOutput"]
        assert isinstance(sent, str), "dict expected_output must be JSON-stringified for the backend"
        assert json.loads(sent) == schema


class TestR6JsonRequiresExpectedOutput:
    """``output_format='json'`` should default cleanly and fail with an actionable message."""

    def test_expected_output_defaults_to_none(self):
        agent = Agent(name="t", instructions="x", output_format="json")
        assert agent.expected_output is None

    def test_json_without_expected_output_raises_actionable_error(self):
        agent = Agent(name="t", instructions="x", output_format="json")
        with pytest.raises(ValueError, match="expected_output"):
            agent._validate_expected_output()

    def test_text_without_expected_output_is_valid(self):
        agent = Agent(name="t", instructions="x", output_format="text")
        # Must not raise: text/markdown agents don't require expected_output.
        agent._validate_expected_output()

    def test_json_with_dict_expected_output_is_valid(self):
        agent = Agent(name="t", instructions="x", output_format="json", expected_output={"a": "b"})
        agent._validate_expected_output()


class TestR3InspectorDeserialization:
    """Inspectors must round-trip as ``Inspector`` objects, not raw dicts."""

    def test_inspectors_deserialize_to_inspector_objects(self):
        inspector_payload = {
            "name": "Input Gate",
            "targets": ["input"],
            "action": {"type": "abort"},
            "evaluator": {"type": "asset", "assetId": "model-abc", "prompt": "PASS or FAIL"},
        }
        agent = _agent_from_dict(inspectors=[inspector_payload])

        assert isinstance(agent.inspectors[0], Inspector)
        assert agent.inspectors[0].name == "Input Gate"
