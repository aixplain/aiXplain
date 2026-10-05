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

from aixplain import Agent, ExecutionConfig


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


class TestRunPayloadSendsExpectedOutputAsString:
    """``executionParams.expectedOutput`` is always a string on the wire.

    The backend answers a non-string with ``400 executionParams.expectedOutput must
    be a string``; the first live CI run of the agent-lifecycle leg hit exactly that
    when a run passed ``execution_params={"expected_output": People}``.
    """

    def test_basemodel_class_in_execution_params_is_sent_as_schema_string(self):
        payload = _json_agent().build_run_payload(
            query="hi", execution_params={"output_format": "json", "expected_output": ChatReply}
        )

        sent = payload["executionParams"]["expectedOutput"]
        assert isinstance(sent, str)
        assert json.loads(sent) == ChatReply.model_json_schema()

    def test_unsaved_agent_basemodel_class_is_sent_as_the_string_save_persists(self):
        agent = _json_agent()

        sent = agent.build_run_payload(query="hi")["executionParams"]["expectedOutput"]

        assert sent == agent.build_save_payload()["expectedOutput"]

    def test_basemodel_instance_is_sent_as_json_string(self):
        instance = ChatReply(content="hi", artifact=None)
        payload = _json_agent(expected_output=instance).build_run_payload(query="hi")

        sent = payload["executionParams"]["expectedOutput"]
        assert isinstance(sent, str)
        assert json.loads(sent) == instance.model_dump()


class TestSessionExecutionConfigSendsExpectedOutputAsString:
    """Session runs go through ``ExecutionConfig.to_api_dict``, not ``build_run_payload``.

    The same ``400 executionParams.expectedOutput must be a string`` applies there, so
    the session path encodes ``expected_output`` the way the direct run path does.
    """

    def test_basemodel_class_is_sent_as_schema_string(self):
        sent = ExecutionConfig(execution_params={"expected_output": ChatReply}).to_api_dict()

        assert json.loads(sent["executionParams"]["expectedOutput"]) == ChatReply.model_json_schema()

    def test_basemodel_instance_is_sent_as_json_string(self):
        instance = ChatReply(content="hi")
        sent = ExecutionConfig(execution_params={"expectedOutput": instance}).to_api_dict()

        assert json.loads(sent["executionParams"]["expectedOutput"]) == instance.model_dump()

    def test_dict_is_sent_as_json_string_and_strings_pass_through(self):
        as_dict = ExecutionConfig(execution_params={"expected_output": {"type": "object"}}).to_api_dict()
        as_str = ExecutionConfig(execution_params={"expected_output": "a list of names"}).to_api_dict()

        assert as_dict["executionParams"]["expectedOutput"] == '{"type": "object"}'
        assert as_str["executionParams"]["expectedOutput"] == "a list of names"
