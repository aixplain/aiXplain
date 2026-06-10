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
# Marketplace retrieval: aix.Inspector.get / .search
# ---------------------------------------------------------------------------


class _FakeClient:
    """Records calls and returns canned guard payloads."""

    def __init__(self, get_result=None, paginate_result=None):
        self._get_result = get_result
        self._paginate_result = paginate_result
        self.got_path = None
        self.request_call = None

    def get(self, path, **kwargs):
        self.got_path = path
        return self._get_result

    def request(self, method, path, **kwargs):
        self.request_call = (method, path, kwargs.get("json"))
        return self._paginate_result


class _FakeContext:
    def __init__(self, client):
        self.client = client


def _bind_inspector(client):
    """Mirror ``aix.Inspector`` — Inspector subclass bound to a context."""
    ctx = _FakeContext(client)
    return type("Inspector", (Inspector,), {"context": ctx})


class TestFromGuardModel:
    def test_prompt_injection_defaults(self):
        guard = Inspector.from_guard_model(
            {"id": "pi-id", "name": "Prompt Injection Guard"},
            requested_path="aixplain/prompt-injection-guard",
        )
        assert guard.to_dict() == {
            "name": "Prompt Injection Guard",
            "targets": ["input"],
            "action": {"type": "abort"},
            "evaluator": {"type": "asset", "assetId": "pi-id"},
        }
        assert guard.id == "pi-id"

    def test_pii_redaction_defaults_with_editor(self):
        guard = Inspector.from_guard_model(
            {"id": "pii-id", "name": "Sensitive Information Guardrail"},
            requested_path="aixplain/pii-redaction",
        )
        payload = guard.to_dict()
        assert payload["action"] == {"type": "edit"}
        assert payload["targets"] == ["input"]
        # EDIT requires an editor; the guard model edits itself.
        assert payload["editor"] == {"type": "asset", "assetId": "pii-id"}

    def test_hallucination_defaults(self):
        guard = Inspector.from_guard_model(
            {"id": "h-id", "name": "Hallucination Guard"},
            requested_path="aixplain/hallucination-guard",
        )
        payload = guard.to_dict()
        assert payload["targets"] == ["output"]
        assert payload["action"] == {"type": "rerun", "maxRetries": 2, "onExhaust": "abort"}

    def test_unknown_guard_safe_default(self):
        guard = Inspector.from_guard_model(
            {"id": "x-id", "name": "Future Guard"},
            requested_path="aixplain/some-future-guard",
        )
        payload = guard.to_dict()
        assert payload["targets"] == ["input"]
        assert payload["action"] == {"type": "abort"}
        assert payload["evaluator"] == {"type": "asset", "assetId": "x-id"}

    def test_slug_resolved_from_payload_path(self):
        guard = Inspector.from_guard_model(
            {"id": "h-id", "name": "Hallucination Guard", "path": "aixplain/hallucination-guard"},
        )
        assert guard.to_dict()["action"]["type"] == "rerun"

    def test_returned_type_is_inspector(self):
        guard = Inspector.from_guard_model({"id": "id", "name": "G"}, requested_path="aixplain/pii-redaction")
        assert isinstance(guard, Inspector)

    def test_path_extracted_from_asset_info(self):
        # Paginate/get payloads carry the path under assetInfo.instanceId, like
        # any other model. It must surface as .path (REPL-browsable) and drive
        # the tuned defaults even when no requested_path is given (search flow).
        guard = Inspector.from_guard_model(
            {
                "id": "pii-id",
                "name": "Sensitive Information Guardrail",
                "assetInfo": {"instanceId": "aixplain/pii-redaction"},
            }
        )
        assert guard.path == "aixplain/pii-redaction"
        assert guard.to_dict()["action"] == {"type": "edit"}

    def test_tuned_defaults_when_fetched_by_bare_id(self):
        # The issue states IDs are also accepted. When retrieved by raw id, the
        # id never matches the registry, but the payload's path still should
        # select the tuned config rather than the safe abort/input fallback.
        guard = Inspector.from_guard_model(
            {"id": "69cbf63cd74e334a6bacfeb1", "name": "PII", "path": "aixplain/pii-redaction"},
            requested_path="69cbf63cd74e334a6bacfeb1",
        )
        assert guard.to_dict()["action"] == {"type": "edit"}


class TestInspectorGet:
    def test_get_fetches_and_adapts(self):
        client = _FakeClient(get_result={"id": "pii-id", "name": "PII", "path": "aixplain/pii-redaction"})
        Bound = _bind_inspector(client)

        guard = Bound.get("aixplain/pii-redaction")

        # URL-encodes the path and hits the models endpoint.
        assert client.got_path == "v2/models/aixplain%2Fpii-redaction"
        assert isinstance(guard, Inspector)
        assert guard.evaluator.asset_id == "pii-id"
        assert guard.action.type == InspectorAction.EDIT

    def test_get_accepts_attribute_override(self):
        client = _FakeClient(get_result={"id": "pi-id", "name": "PI"})
        Bound = _bind_inspector(client)

        guard = Bound.get("aixplain/prompt-injection-guard")
        guard.targets = ["output"]
        assert guard.to_dict()["targets"] == ["output"]

    def test_get_without_context_raises(self):
        with pytest.raises(Exception):
            Inspector.get("aixplain/prompt-injection-guard")


class TestInspectorSearch:
    def test_search_returns_page_shape(self):
        client = _FakeClient(
            paginate_result={
                "results": [
                    {"id": "pi-id", "name": "Prompt Injection Guard", "path": "aixplain/prompt-injection-guard"},
                    {"id": "pii-id", "name": "PII", "path": "aixplain/pii-redaction"},
                ],
                "total": 6,
                "pageTotal": 1,
            }
        )
        Bound = _bind_inspector(client)

        page = Bound.search("guard")

        method, path, body = client.request_call
        assert method == "post"
        assert path == "v2/models/paginate"
        # Pinned to the guardrails function and includes the query.
        assert body["functions"] == [{"id": "guardrails"}]
        assert body["q"] == "guard"

        assert page.total == 6
        assert page.page_number == 0
        assert page.page_total == 1
        assert all(isinstance(r, Inspector) for r in page.results)
        assert [r.name for r in page.results] == ["Prompt Injection Guard", "PII"]
