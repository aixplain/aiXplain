"""Regression tests: Pydantic ``expected_output`` must persist through ``save()``.

A ``BaseModel``-class ``expected_output`` used to be popped from the save
payload ("runtime-only"), so the backend stored ``null``. The create-response
re-hydration in ``BaseResource._create`` then overwrote the local value with
that ``null``, and every subsequent ``run()`` sent ``expectedOutput: null`` —
the engine never received the JSON contract, and fetched agents could never
recover it.
"""

import json
from unittest.mock import MagicMock
from typing import Optional

from pydantic import BaseModel

from aixplain.v2.agent import Agent


class ChatReply(BaseModel):
    content: str
    artifact: Optional[dict] = None


def _json_agent(**overrides):
    """Unsaved JSON-format agent with a mocked client context."""
    kwargs = {
        "name": "Strict JSON Agent",
        "instructions": "Reply as a JSON array.",
        "output_format": "json",
        "expected_output": ChatReply,
    }
    kwargs.update(overrides)
    agent = Agent(**kwargs)
    agent.context = MagicMock()
    return agent


def _echoing_client(agent):
    """Make the mocked client echo the create payload back, like the backend.

    The backend persists exactly what it receives and returns the stored
    document; a field missing from the request comes back as ``None``.
    """

    def fake_request(method, path, json=None, **kwargs):
        response = dict(json or {})
        response.setdefault("id", "agent-123")
        response.setdefault("expectedOutput", None)
        return response

    agent.context.client.request.side_effect = fake_request


class TestSavePayloadPersistsExpectedOutput:
    def test_basemodel_class_is_serialized_to_json_schema_string(self):
        payload = _json_agent().build_save_payload()

        sent = payload.get("expectedOutput")
        assert isinstance(sent, str), "BaseModel-class expected_output must be persisted as a JSON string"
        assert json.loads(sent) == ChatReply.model_json_schema()

    def test_basemodel_instance_is_still_dumped_to_dict(self):
        instance = ChatReply(content="hi", artifact=None)
        payload = _json_agent(expected_output=instance).build_save_payload()

        assert payload.get("expectedOutput") == instance.model_dump()


class TestSaveDoesNotLoseExpectedOutput:
    def test_expected_output_survives_save_rehydration(self):
        agent = _json_agent()
        _echoing_client(agent)

        agent.save()

        assert agent.expected_output is not None, "save() must not wipe expected_output from the local agent"

    def test_run_payload_carries_schema_after_save(self):
        agent = _json_agent()
        _echoing_client(agent)
        agent.save()

        run_payload = agent.build_run_payload(query="hi")

        sent = run_payload["executionParams"]["expectedOutput"]
        assert sent is not None, "run() after save() must send the JSON contract to the backend"
        assert json.loads(sent) == ChatReply.model_json_schema()
