"""V2 Agent backward-compat regression tests (V3 engine compatibility).

Covers three SDK-side regressions surfaced during V3 DEV testing:
- R5: dict ``expected_output`` accepted at save but rejected at run.
- R6: ``output_format='json'`` crashes at save when ``expected_output`` is unset.
- R3: inspectors deserialize as plain dicts instead of ``Inspector`` objects on ``get()``.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from aixplain.v2.agent import Agent
from aixplain.v2.inspector import Inspector, PrebuiltInspector


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

    def test_prebuilt_inspector_payload_deserializes_to_prebuilt_inspector(self):
        # PrebuiltInspector.to_dict() emits a lightweight reference with no
        # "name" key; the backend echoes it back on save. __post_init__ must
        # not route it through Inspector.from_dict (KeyError: 'name').
        prebuilt_payload = PrebuiltInspector.prompt_injection_guard().to_dict()
        assert "name" not in prebuilt_payload  # precondition for the regression

        agent = _agent_from_dict(inspectors=[prebuilt_payload])

        assert isinstance(agent.inspectors[0], PrebuiltInspector)
        assert agent.inspectors[0].preset_id == "prompt_injection_guard"

    def test_mixed_full_and_prebuilt_inspectors_deserialize(self):
        full_payload = {
            "name": "Input Gate",
            "targets": ["input"],
            "action": {"type": "abort"},
            "evaluator": {"type": "asset", "assetId": "model-abc", "prompt": "PASS or FAIL"},
        }
        prebuilt_payload = {"presetId": "pii_redaction", "targets": ["output"]}

        agent = _agent_from_dict(inspectors=[full_payload, prebuilt_payload])

        assert isinstance(agent.inspectors[0], Inspector)
        assert isinstance(agent.inspectors[1], PrebuiltInspector)
        assert agent.inspectors[1].preset_id == "pii_redaction"


class TestRunPayloadAttachments:
    """Non-session run path resolves attachments into a structured payload field."""

    def test_url_attachments_not_uploaded_and_type_auto_detected(self):
        agent = _agent_from_dict()
        with patch("aixplain.v2.upload_utils.FileUploader") as MockUploader:
            payload = agent.build_run_payload(
                query="describe",
                attachments=[{"url": "https://s3/a.wav", "type": "audio"}, "https://s3/b.png"],
            )
            MockUploader.assert_not_called()
        # Explicit type preserved (+ mime inferred); bare URL string auto-typed as image.
        assert payload["attachments"][0] == {"url": "https://s3/a.wav", "type": "audio", "mimeType": "audio/wav"}
        assert payload["attachments"][1]["url"] == "https://s3/b.png"
        assert payload["attachments"][1]["type"] == "image"
        assert payload["attachments"][1]["mimeType"] == "image/png"

    def test_local_path_is_uploaded_with_mimetype(self):
        agent = _agent_from_dict()
        with (
            patch("aixplain.v2.upload_utils.FileUploader") as MockUploader,
            patch("aixplain.v2.upload_utils.MimeTypeDetector") as MockDetector,
        ):
            MockUploader.return_value.upload.return_value = "https://cdn/clip.wav"
            MockDetector.detect_mime_type.return_value = "audio/wav"
            payload = agent.build_run_payload(query="transcribe", attachments=["/tmp/clip.wav"])

        assert payload["attachments"] == [
            {"url": "https://cdn/clip.wav", "name": "clip.wav", "type": "audio", "mimeType": "audio/wav"}
        ]

    def test_files_kwarg_still_works_but_warns(self):
        agent = _agent_from_dict()
        with (
            patch("aixplain.v2.upload_utils.FileUploader") as MockUploader,
            patch("aixplain.v2.upload_utils.MimeTypeDetector") as MockDetector,
            pytest.warns(DeprecationWarning, match="files.*deprecated"),
        ):
            MockUploader.return_value.upload.return_value = "https://cdn/doc.pdf"
            MockDetector.detect_mime_type.return_value = "application/pdf"
            payload = agent.build_run_payload(query="q", files=["/tmp/doc.pdf"])

        assert payload["attachments"][0]["url"] == "https://cdn/doc.pdf"

    def test_no_attachments_means_no_attachments_field(self):
        agent = _agent_from_dict()
        payload = agent.build_run_payload(query="hi")
        assert "attachments" not in payload
