"""Unit tests for v2 Inspector payload serialization."""

import pytest

from aixplain.v2.inspector import (
    Inspector,
    InspectorAction,
    InspectorActionConfig,
    InspectorOnExhaust,
    InspectorSeverity,
    InspectorTarget,
    EvaluatorType,
    EvaluatorConfig,
    EditorConfig,
    PrebuiltInspector,
    is_prebuilt_inspector,
)


# ---------------------------------------------------------------------------
# InspectorActionConfig
# ---------------------------------------------------------------------------


class TestInspectorActionConfig:
    def test_abort_to_dict(self):
        cfg = InspectorActionConfig(type=InspectorAction.ABORT)
        assert cfg.to_dict() == {"type": "abort"}

    def test_rerun_to_dict(self):
        cfg = InspectorActionConfig(
            type=InspectorAction.RERUN,
            max_retries=3,
            on_exhaust=InspectorOnExhaust.ABORT,
        )
        assert cfg.to_dict() == {"type": "rerun", "maxRetries": 3, "onExhaust": "abort"}

    def test_rerun_without_optional_fields(self):
        cfg = InspectorActionConfig(type=InspectorAction.RERUN)
        assert cfg.to_dict() == {"type": "rerun"}

    def test_max_retries_invalid_for_non_rerun(self):
        with pytest.raises(ValueError, match="max_retries is only valid"):
            InspectorActionConfig(type=InspectorAction.ABORT, max_retries=2)

    def test_on_exhaust_invalid_for_non_rerun(self):
        with pytest.raises(ValueError, match="on_exhaust is only valid"):
            InspectorActionConfig(type=InspectorAction.EDIT, on_exhaust=InspectorOnExhaust.ABORT)

    def test_negative_max_retries(self):
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            InspectorActionConfig(type=InspectorAction.RERUN, max_retries=-1)

    def test_from_dict_roundtrip(self):
        original = InspectorActionConfig(
            type=InspectorAction.RERUN,
            max_retries=2,
            on_exhaust=InspectorOnExhaust.CONTINUE,
        )
        restored = InspectorActionConfig.from_dict(original.to_dict())
        assert restored.type == original.type
        assert restored.max_retries == original.max_retries
        assert restored.on_exhaust == original.on_exhaust


# ---------------------------------------------------------------------------
# EvaluatorConfig
# ---------------------------------------------------------------------------


class TestEvaluatorConfig:
    def test_asset_to_dict(self):
        cfg = EvaluatorConfig(
            type=EvaluatorType.ASSET,
            asset_id="abc123",
            prompt="Check the output",
        )
        assert cfg.to_dict() == {
            "type": "asset",
            "assetId": "abc123",
            "prompt": "Check the output",
        }

    def test_function_to_dict(self):
        cfg = EvaluatorConfig(
            type=EvaluatorType.FUNCTION,
            function="def eval_fn(text: str) -> bool:\n    return True",
        )
        assert cfg.to_dict() == {
            "type": "function",
            "function": "def eval_fn(text: str) -> bool:\n    return True",
        }

    def test_callable_auto_converted(self):
        def my_evaluator(text: str) -> bool:
            return "ok" in text

        cfg = EvaluatorConfig(type=EvaluatorType.FUNCTION, function=my_evaluator)
        assert isinstance(cfg.function, str)
        assert "my_evaluator" in cfg.function

    def test_asset_requires_asset_id(self):
        with pytest.raises(ValueError, match="asset_id is required"):
            EvaluatorConfig(type=EvaluatorType.ASSET)

    def test_function_requires_function(self):
        with pytest.raises(ValueError, match="function is required"):
            EvaluatorConfig(type=EvaluatorType.FUNCTION)

    def test_from_dict_roundtrip(self):
        original = EvaluatorConfig(type=EvaluatorType.ASSET, asset_id="id1", prompt="p")
        restored = EvaluatorConfig.from_dict(original.to_dict())
        assert restored.type == original.type
        assert restored.asset_id == original.asset_id
        assert restored.prompt == original.prompt


# ---------------------------------------------------------------------------
# EditorConfig
# ---------------------------------------------------------------------------


class TestEditorConfig:
    def test_function_to_dict(self):
        cfg = EditorConfig(
            type=EvaluatorType.FUNCTION,
            function="def edit(text: str) -> str:\n    return text",
        )
        assert cfg.to_dict() == {
            "type": "function",
            "function": "def edit(text: str) -> str:\n    return text",
        }

    def test_callable_auto_converted(self):
        def my_editor(text: str) -> str:
            return text.upper()

        cfg = EditorConfig(type=EvaluatorType.FUNCTION, function=my_editor)
        assert isinstance(cfg.function, str)
        assert "my_editor" in cfg.function

    def test_from_dict_roundtrip(self):
        original = EditorConfig(type=EvaluatorType.FUNCTION, function="def f(): pass")
        restored = EditorConfig.from_dict(original.to_dict())
        assert restored.type == original.type
        assert restored.function == original.function


# ---------------------------------------------------------------------------
# Inspector (full payload)
# ---------------------------------------------------------------------------


class TestInspector:
    def test_abort_inspector_payload(self):
        inspector = Inspector(
            name="abort_inspector",
            description="Always abort",
            severity=InspectorSeverity.HIGH,
            targets=["output"],
            action=InspectorActionConfig(type=InspectorAction.ABORT),
            evaluator=EvaluatorConfig(
                type=EvaluatorType.ASSET,
                asset_id="llm-123",
                prompt="Critique the output.",
            ),
        )
        payload = inspector.to_dict()
        assert payload == {
            "name": "abort_inspector",
            "description": "Always abort",
            "severity": "high",
            "targets": ["output"],
            "action": {"type": "abort"},
            "evaluator": {
                "type": "asset",
                "assetId": "llm-123",
                "prompt": "Critique the output.",
            },
        }

    def test_rerun_inspector_payload(self):
        inspector = Inspector(
            name="rerun_inspector",
            targets=["output"],
            action=InspectorActionConfig(
                type=InspectorAction.RERUN,
                max_retries=2,
                on_exhaust=InspectorOnExhaust.ABORT,
            ),
            evaluator=EvaluatorConfig(
                type=EvaluatorType.ASSET,
                asset_id="llm-456",
                prompt="Check for name.",
            ),
        )
        payload = inspector.to_dict()
        assert payload == {
            "name": "rerun_inspector",
            "targets": ["output"],
            "action": {"type": "rerun", "maxRetries": 2, "onExhaust": "abort"},
            "evaluator": {
                "type": "asset",
                "assetId": "llm-456",
                "prompt": "Check for name.",
            },
        }

    def test_edit_inspector_payload(self):
        inspector = Inspector(
            name="edit_inspector",
            severity=InspectorSeverity.MEDIUM,
            targets=["steps", "AgentA"],
            action=InspectorActionConfig(type=InspectorAction.EDIT),
            evaluator=EvaluatorConfig(
                type=EvaluatorType.FUNCTION,
                function="def eval_fn(text): return True",
            ),
            editor=EditorConfig(
                type=EvaluatorType.FUNCTION,
                function='def edit_fn(text): return "edited"',
            ),
        )
        payload = inspector.to_dict()
        assert payload == {
            "name": "edit_inspector",
            "severity": "medium",
            "targets": ["steps", "AgentA"],
            "action": {"type": "edit"},
            "evaluator": {
                "type": "function",
                "function": "def eval_fn(text): return True",
            },
            "editor": {
                "type": "function",
                "function": 'def edit_fn(text): return "edited"',
            },
        }

    def test_edit_requires_editor(self):
        with pytest.raises(ValueError, match="editor is required"):
            Inspector(
                name="bad_edit",
                targets=["steps"],
                action=InspectorActionConfig(type=InspectorAction.EDIT),
                evaluator=EvaluatorConfig(type=EvaluatorType.FUNCTION, function="def f(): pass"),
            )

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Inspector(
                name="",
                action=InspectorActionConfig(type=InspectorAction.ABORT),
                evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id="x"),
            )

    def test_from_dict_roundtrip(self):
        original = Inspector(
            name="roundtrip_test",
            description="desc",
            severity=InspectorSeverity.LOW,
            targets=["steps", "AgentB"],
            action=InspectorActionConfig(
                type=InspectorAction.RERUN,
                max_retries=1,
                on_exhaust=InspectorOnExhaust.CONTINUE,
            ),
            evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id="id1", prompt="p"),
        )
        restored = Inspector.from_dict(original.to_dict())
        assert restored.to_dict() == original.to_dict()

    def test_from_dict_with_editor(self):
        data = {
            "name": "test",
            "targets": ["input"],
            "action": {"type": "edit"},
            "evaluator": {"type": "function", "function": "def f(): pass"},
            "editor": {"type": "function", "function": "def g(): pass"},
        }
        inspector = Inspector.from_dict(data)
        assert inspector.editor is not None
        assert inspector.editor.function == "def g(): pass"
        assert inspector.to_dict() == data

    def test_optional_fields_omitted(self):
        """Verify that None description, severity, and editor are not in the payload."""
        inspector = Inspector(
            name="minimal",
            targets=["output"],
            action=InspectorActionConfig(type=InspectorAction.CONTINUE),
            evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id="x", prompt="p"),
        )
        payload = inspector.to_dict()
        assert "description" not in payload
        assert "severity" not in payload
        assert "editor" not in payload


# ---------------------------------------------------------------------------
# PrebuiltInspector
# ---------------------------------------------------------------------------


class TestPrebuiltInspector:
    def test_prompt_injection_guard_defaults(self):
        inspector = PrebuiltInspector.prompt_injection_guard()
        payload = inspector.to_dict()
        assert payload == {"presetId": "prompt_injection_guard"}

    def test_pii_redaction_defaults(self):
        inspector = PrebuiltInspector.pii_redaction()
        payload = inspector.to_dict()
        assert payload == {"presetId": "pii_redaction"}

    def test_prompt_injection_guard_with_overrides(self):
        inspector = PrebuiltInspector.prompt_injection_guard(
            targets=[InspectorTarget.OUTPUT],
            severity=InspectorSeverity.CRITICAL,
            name="my_guard",
            description="Custom guard",
        )
        payload = inspector.to_dict()
        assert payload == {
            "presetId": "prompt_injection_guard",
            "name": "my_guard",
            "description": "Custom guard",
            "targets": ["output"],
            "severity": "critical",
        }

    def test_pii_redaction_with_action_override(self):
        inspector = PrebuiltInspector.pii_redaction(
            action={"type": "abort"},
            targets=[InspectorTarget.INPUT, InspectorTarget.OUTPUT],
        )
        payload = inspector.to_dict()
        assert payload == {
            "presetId": "pii_redaction",
            "targets": ["input", "output"],
            "action": {"type": "abort"},
        }

    def test_unknown_preset_rejected(self):
        with pytest.raises(ValueError, match="Unknown inspector preset"):
            PrebuiltInspector(preset_id="nonexistent")

    def test_unsupported_action_rejected(self):
        with pytest.raises(ValueError, match="not supported by preset"):
            PrebuiltInspector.prompt_injection_guard(action={"type": "edit"})

    def test_pii_redaction_rejects_rerun(self):
        with pytest.raises(ValueError, match="not supported by preset"):
            PrebuiltInspector.pii_redaction(action={"type": "rerun"})

    def test_hallucination_guard_defaults(self):
        inspector = PrebuiltInspector.hallucination_guard()
        payload = inspector.to_dict()
        assert payload == {"presetId": "hallucination_guard"}

    def test_hallucination_guard_with_overrides(self):
        inspector = PrebuiltInspector.hallucination_guard(
            targets=[InspectorTarget.OUTPUT],
            severity=InspectorSeverity.HIGH,
            name="my_hallucination_guard",
            description="Custom hallucination guard",
        )
        payload = inspector.to_dict()
        assert payload == {
            "presetId": "hallucination_guard",
            "name": "my_hallucination_guard",
            "description": "Custom hallucination guard",
            "targets": ["output"],
            "severity": "high",
        }

    def test_hallucination_guard_with_action_override(self):
        inspector = PrebuiltInspector.hallucination_guard(
            action={"type": "abort"},
        )
        payload = inspector.to_dict()
        assert payload == {
            "presetId": "hallucination_guard",
            "action": {"type": "abort"},
        }

    def test_hallucination_guard_rejects_edit(self):
        with pytest.raises(ValueError, match="not supported by preset"):
            PrebuiltInspector.hallucination_guard(action={"type": "edit"})

    def test_targets_normalized_from_enums(self):
        inspector = PrebuiltInspector.pii_redaction(
            targets=[InspectorTarget.STEPS, InspectorTarget.OUTPUT],
        )
        assert inspector.targets == ["steps", "output"]

    def test_targets_normalized_from_strings(self):
        inspector = PrebuiltInspector.prompt_injection_guard(
            targets=["INPUT", "Steps"],
        )
        assert inspector.targets == ["input", "steps"]

    def test_from_dict_roundtrip(self):
        original = PrebuiltInspector.prompt_injection_guard(
            targets=[InspectorTarget.INPUT],
            severity=InspectorSeverity.HIGH,
            name="custom_name",
        )
        restored = PrebuiltInspector.from_dict(original.to_dict())
        assert restored.to_dict() == original.to_dict()

    def test_from_dict_minimal(self):
        data = {"presetId": "pii_redaction"}
        inspector = PrebuiltInspector.from_dict(data)
        assert inspector.preset_id == "pii_redaction"
        assert inspector.targets is None
        assert inspector.action is None

    def test_list_presets_returns_all(self):
        presets = PrebuiltInspector.list_presets()
        assert "prompt_injection_guard" in presets
        assert "pii_redaction" in presets
        assert "hallucination_guard" in presets
        assert presets["prompt_injection_guard"]["category"] == "protection"
        assert presets["pii_redaction"]["category"] == "redaction"
        assert presets["hallucination_guard"]["category"] == "quality"

    def test_list_presets_contains_expected_fields(self):
        presets = PrebuiltInspector.list_presets()
        for preset_id, meta in presets.items():
            assert "name" in meta
            assert "description" in meta
            assert "default_targets" in meta
            assert "default_action" in meta
            assert "supported_actions" in meta


# ---------------------------------------------------------------------------
# is_prebuilt_inspector helper
# ---------------------------------------------------------------------------


class TestIsPrebuiltInspector:
    def test_prebuilt_instance(self):
        assert is_prebuilt_inspector(PrebuiltInspector.pii_redaction()) is True

    def test_preset_dict(self):
        assert is_prebuilt_inspector({"presetId": "prompt_injection_guard"}) is True

    def test_regular_inspector_instance(self):
        inspector = Inspector(
            name="custom",
            action=InspectorActionConfig(type=InspectorAction.ABORT),
            evaluator=EvaluatorConfig(type=EvaluatorType.ASSET, asset_id="x"),
        )
        assert is_prebuilt_inspector(inspector) is False

    def test_regular_dict(self):
        assert is_prebuilt_inspector({"name": "foo", "action": {"type": "abort"}}) is False

    def test_none(self):
        assert is_prebuilt_inspector(None) is False
