"""Unit tests for v2 Inspector payload serialization.

The public surface is intentionally tiny: an :class:`Inspector` built with plain
strings for ``action`` / ``targets`` / ``severity`` and a Metric / asset-id /
callable for ``metric`` (the universal judge). No enums or config classes.
"""

import ast
import functools
from unittest.mock import patch

import pytest

from aixplain import Inspector
from aixplain.v2.inspector import (
    _ActionConfig,
    _Judge,
    _check_top_level_binding,
    _guard_slugs,
    _resolve_guard_defaults,
    _top_level_binds,
)

_RUNNABLE_HINT = "module-level function"


def _binds(source, name):
    return _top_level_binds(ast.parse(source), name)


def module_check(text):
    import re

    return bool(re.search(r"HIGH", text))


async def module_async_check(text):
    return "HIGH" in text


def evaluator_fn(text):
    return "HIGH" in text


def edit_fn(text):
    return text.replace("HIGH", "")


lone_lambda = lambda text: "HIGH" in text  # noqa: E731

two_lambdas = (lambda a: a, lambda b: b)  # noqa: E731

# fmt: off
multiline_lambda = dict(name="i", metric=lambda text: (
    "HIGH"
    in text
))
partial_source_lambdas = [
    lambda text: "HIGH" in text, None]
# fmt: on


def _decorator(fn):
    return fn


@_decorator
def decorated_check(text):
    return True


class _Holder:
    def method_check(self, text):
        return True


class _CallableInstance:
    def __call__(self, text):
        return True


class _FakeMetric:
    """Duck-typed stand-in for ``aix.Metric`` — an asset-backed judge with an id."""

    def __init__(self, id, prompt_template=None):
        self.id = id
        self.prompt_template = prompt_template


# ---------------------------------------------------------------------------
# Action policy (string / dict, no InspectorActionConfig import)
# ---------------------------------------------------------------------------


class TestActionConfig:
    def test_abort_from_string(self):
        cfg = _ActionConfig.coerce("abort")
        assert cfg.to_dict() == {"type": "abort"}

    def test_rerun_from_dict(self):
        cfg = _ActionConfig.coerce({"type": "rerun", "max_retries": 3, "on_exhaust": "abort"})
        assert cfg.to_dict() == {"type": "rerun", "maxRetries": 3, "onExhaust": "abort"}

    def test_rerun_accepts_camelcase(self):
        cfg = _ActionConfig.coerce({"type": "rerun", "maxRetries": 1, "onExhaust": "continue"})
        assert cfg.to_dict() == {"type": "rerun", "maxRetries": 1, "onExhaust": "continue"}

    def test_rerun_without_optional_fields(self):
        assert _ActionConfig.coerce("rerun").to_dict() == {"type": "rerun"}

    def test_max_retries_invalid_for_non_rerun(self):
        with pytest.raises(ValueError, match="max_retries is only valid"):
            _ActionConfig.coerce({"type": "abort", "max_retries": 2})

    def test_on_exhaust_invalid_for_non_rerun(self):
        with pytest.raises(ValueError, match="on_exhaust is only valid"):
            _ActionConfig.coerce({"type": "edit", "on_exhaust": "abort"})

    def test_negative_max_retries(self):
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            _ActionConfig.coerce({"type": "rerun", "max_retries": -1})

    def test_invalid_action_type(self):
        with pytest.raises(ValueError, match="invalid action"):
            _ActionConfig.coerce("bogus")

    def test_invalid_on_exhaust_value(self):
        with pytest.raises(ValueError, match="invalid on_exhaust"):
            _ActionConfig.coerce({"type": "rerun", "on_exhaust": "explode"})


# ---------------------------------------------------------------------------
# Judge (the universal metric: Metric | asset-id str | callable)
# ---------------------------------------------------------------------------


class TestJudge:
    def test_metric_object_becomes_asset(self):
        judge = _Judge.coerce(_FakeMetric(id="metric-1", prompt_template="Judge it."))
        assert judge.to_dict() == {"type": "asset", "assetId": "metric-1", "prompt": "Judge it."}

    def test_metric_prompt_falls_back_to_config(self):
        class _MetricWithConfig:
            id = "metric-2"
            prompt_template = None
            config = {"prompt": "From config."}

        judge = _Judge.coerce(_MetricWithConfig())
        assert judge.to_dict() == {"type": "asset", "assetId": "metric-2", "prompt": "From config."}

    def test_asset_id_string(self):
        assert _Judge.coerce("abc123").to_dict() == {"type": "asset", "assetId": "abc123"}

    def test_dict_snake_and_prompt(self):
        judge = _Judge.coerce({"asset_id": "id1", "prompt": "p"})
        assert judge.to_dict() == {"type": "asset", "assetId": "id1", "prompt": "p"}

    def test_callable_becomes_function(self):
        def my_evaluator(text: str) -> bool:
            return "ok" in text

        judge = _Judge.coerce(my_evaluator)
        assert judge.type == "function"
        assert "def my_evaluator(text: str) -> bool:" in judge.function
        assert judge.function.rstrip().endswith("evaluator_fn = my_evaluator")
        assert _binds(judge.function, "evaluator_fn")

    def test_unonboarded_metric_raises(self):
        class _Unonboarded:
            id = None
            prompt_template = "x"

        with pytest.raises(ValueError, match="must be created"):
            _Judge.coerce(_Unonboarded())

    def test_empty_judge_raises(self):
        with pytest.raises(ValueError, match="needs an asset id"):
            _Judge()

    def test_from_dict_roundtrip(self):
        original = _Judge.from_dict({"type": "asset", "assetId": "id1", "prompt": "p"})
        restored = _Judge.from_dict(original.to_dict())
        assert restored.to_dict() == original.to_dict()


# ---------------------------------------------------------------------------
# Inspector (full payload)
# ---------------------------------------------------------------------------


class TestInspector:
    def test_abort_inspector_payload(self):
        inspector = Inspector(
            name="abort_inspector",
            description="Always abort",
            severity="high",
            targets=["output"],
            action="abort",
            metric=_FakeMetric(id="llm-123", prompt_template="Critique the output."),
        )
        assert inspector.to_dict() == {
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
            action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"},
            metric={"asset_id": "llm-456", "prompt": "Check for name."},
        )
        assert inspector.to_dict() == {
            "name": "rerun_inspector",
            "targets": ["output"],
            "action": {"type": "rerun", "maxRetries": 2, "onExhaust": "abort"},
            "evaluator": {
                "type": "asset",
                "assetId": "llm-456",
                "prompt": "Check for name.",
            },
        }

    def test_edit_inspector_payload_with_callables(self):
        def eval_fn(text):
            return True

        def edit_fn(text):
            return "edited"

        inspector = Inspector(
            name="edit_inspector",
            severity="medium",
            targets=["steps", "AgentA"],
            action="edit",
            metric=eval_fn,
            editor=edit_fn,
        )
        payload = inspector.to_dict()
        assert payload["name"] == "edit_inspector"
        assert payload["severity"] == "medium"
        assert payload["targets"] == ["steps", "AgentA"]
        assert payload["action"] == {"type": "edit"}
        assert set(payload["evaluator"]) == {"type", "function"}
        assert payload["evaluator"]["type"] == "function"
        assert payload["evaluator"]["function"] == ("def eval_fn(text):\n    return True\n\nevaluator_fn = eval_fn\n")
        assert set(payload["editor"]) == {"type", "function"}
        assert payload["editor"]["type"] == "function"
        assert payload["editor"]["function"] == 'def edit_fn(text):\n    return "edited"\n'

    def test_edit_requires_editor(self):
        with pytest.raises(ValueError, match="editor is required"):
            Inspector(name="bad_edit", targets=["steps"], action="edit", metric="x")

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Inspector(name="", action="abort", metric="x")

    def test_action_required(self):
        with pytest.raises(ValueError, match="action is required"):
            Inspector(name="x", metric="y")

    def test_metric_required(self):
        with pytest.raises(ValueError, match="metric is required"):
            Inspector(name="x", action="abort")

    def test_invalid_severity_rejected(self):
        with pytest.raises(ValueError, match="invalid severity"):
            Inspector(name="x", action="abort", metric="y", severity="urgent")

    def test_from_dict_roundtrip(self):
        original = Inspector(
            name="roundtrip_test",
            description="desc",
            severity="low",
            targets=["steps", "AgentB"],
            action={"type": "rerun", "max_retries": 1, "on_exhaust": "continue"},
            metric={"asset_id": "id1", "prompt": "p"},
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
        """None description, severity, and editor are not in the payload."""
        inspector = Inspector(
            name="minimal",
            targets=["output"],
            action="continue",
            metric={"asset_id": "x", "prompt": "p"},
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


# Canonical marketplace paths for the onboarded AWS guards (host/asset-name/instance),
# verified against production. The asset-name (middle) segment drives the tuned config.
_PROMPT_ATTACKS_PATH = "aws/detect-prompt-attacks-guardrail/aws"
_PII_PATH = "aws/sensitive-information-guardrail/aws"
_HALLUCINATION_PATH = "aws/contextual-grounding-check-guardrail/aws"


class TestGuardSlugResolution:
    """Unit coverage for the asset-name-based tuned-config resolution."""

    def test_guard_slugs_returns_all_segments_lowercased(self):
        assert _guard_slugs("aws/Sensitive-Information-Guardrail/aws") == [
            "aws",
            "sensitive-information-guardrail",
            "aws",
        ]

    def test_guard_slugs_handles_bare_id_and_empty(self):
        assert _guard_slugs("69cbf63cd74e334a6bacfeb1") == ["69cbf63cd74e334a6bacfeb1"]
        assert _guard_slugs(None) == []
        assert _guard_slugs("") == []

    def test_asset_name_middle_segment_selects_config(self):
        # The guard identity is the middle segment, not the trailing host.
        cfg = _resolve_guard_defaults("aws/sensitive-information-guardrail/aws")
        assert cfg["action"]["type"] == "edit"
        assert cfg["targets"] == ["input"]

    def test_trailing_host_segment_does_not_match(self):
        # An unknown asset name (host segments ignored) falls back to abort/input.
        cfg = _resolve_guard_defaults("aws/some-future-guard/aws")
        assert cfg["action"]["type"] == "abort"
        assert cfg["targets"] == ["input"]

    def test_bare_id_falls_back_to_safe_default(self):
        cfg = _resolve_guard_defaults("69cbf63cd74e334a6bacfeb1")
        assert cfg["action"]["type"] == "abort"

    def test_first_matching_candidate_wins(self):
        # asset_name candidate (checked first) takes precedence over the path.
        cfg = _resolve_guard_defaults("contextual-grounding-check-guardrail", "aws/ignored/aws")
        assert cfg["action"]["type"] == "rerun"
        assert cfg["targets"] == ["output"]


class TestFromGuardModel:
    def test_prompt_injection_defaults(self):
        guard = Inspector.from_guard_model(
            {"id": "pi-id", "name": "Detect Prompt Attacks Guardrail"},
            requested_path=_PROMPT_ATTACKS_PATH,
        )
        assert guard.to_dict() == {
            "name": "Detect Prompt Attacks Guardrail",
            "targets": ["input"],
            "action": {"type": "abort"},
            "evaluator": {"type": "asset", "assetId": "pi-id"},
            "presetId": "prompt_injection_guard",
        }
        assert guard.id == "pi-id"
        assert guard.preset_id == "prompt_injection_guard"

    def test_pii_redaction_defaults_with_editor(self):
        guard = Inspector.from_guard_model(
            {"id": "pii-id", "name": "Sensitive Information Guardrail"},
            requested_path=_PII_PATH,
        )
        payload = guard.to_dict()
        assert payload["action"] == {"type": "edit"}
        assert payload["targets"] == ["input"]
        # EDIT requires an editor; the guard model edits itself.
        assert payload["editor"] == {"type": "asset", "assetId": "pii-id"}

    def test_hallucination_defaults(self):
        guard = Inspector.from_guard_model(
            {"id": "h-id", "name": "Contextual Grounding Check Guardrail"},
            requested_path=_HALLUCINATION_PATH,
        )
        payload = guard.to_dict()
        assert payload["targets"] == ["output"]
        assert payload["action"] == {"type": "rerun", "maxRetries": 2, "onExhaust": "abort"}

    def test_asset_name_segment_drives_config_not_host(self):
        # Real paths are host/asset-name/instance, so the trailing segment is the
        # host ("aws"), not the guard identity. The tuned config must resolve from
        # the asset-name (middle) segment — a regression guard for the slug bug
        # where the trailing segment was used and every guard fell back to abort.
        guard = Inspector.from_guard_model(
            {"id": "pii-id", "name": "Sensitive Information Guardrail"},
            requested_path=_PII_PATH,
        )
        assert guard.to_dict()["action"] == {"type": "edit"}

    def test_unknown_guard_safe_default(self):
        guard = Inspector.from_guard_model(
            {"id": "x-id", "name": "Future Guard"},
            requested_path="aws/some-future-guard/aws",
        )
        payload = guard.to_dict()
        assert payload["targets"] == ["input"]
        assert payload["action"] == {"type": "abort"}
        assert payload["evaluator"] == {"type": "asset", "assetId": "x-id"}
        # An unknown guard carries no presetId; the backend resolves it itself.
        assert guard.preset_id is None
        assert "presetId" not in payload

    def test_pii_guard_emits_preset_id(self):
        guard = Inspector.from_guard_model(
            {"id": "pii-id", "name": "Sensitive Information Guardrail"},
            requested_path=_PII_PATH,
        )
        assert guard.preset_id == "pii_redaction"
        assert guard.to_dict()["presetId"] == "pii_redaction"

    def test_hallucination_guard_emits_preset_id(self):
        guard = Inspector.from_guard_model(
            {"id": "h-id", "name": "Contextual Grounding Check Guardrail"},
            requested_path=_HALLUCINATION_PATH,
        )
        assert guard.preset_id == "hallucination_guard"
        assert guard.to_dict()["presetId"] == "hallucination_guard"

    def test_preset_id_resolved_from_asset_name_field(self):
        guard = Inspector.from_guard_model(
            {
                "id": "pi-id",
                "name": "Detect Prompt Attacks Guardrail",
                "assetInfo": {"assetName": "detect-prompt-attacks-guardrail"},
            }
        )
        assert guard.preset_id == "prompt_injection_guard"

    def test_preset_id_roundtrips_through_from_dict(self):
        guard = Inspector.from_guard_model(
            {"id": "pi-id", "name": "Detect Prompt Attacks Guardrail"},
            requested_path=_PROMPT_ATTACKS_PATH,
        )
        restored = Inspector.from_dict(guard.to_dict())
        assert restored.preset_id == "prompt_injection_guard"
        assert restored.to_dict() == guard.to_dict()

    def test_slug_resolved_from_payload_path(self):
        guard = Inspector.from_guard_model(
            {"id": "h-id", "name": "Contextual Grounding Check Guardrail", "path": _HALLUCINATION_PATH},
        )
        assert guard.to_dict()["action"]["type"] == "rerun"

    def test_slug_resolved_from_asset_name_field(self):
        # When the payload carries assetInfo.assetName directly, it selects the
        # tuned config regardless of the path shape.
        guard = Inspector.from_guard_model(
            {
                "id": "pii-id",
                "name": "Sensitive Information Guardrail",
                "assetInfo": {"assetName": "sensitive-information-guardrail"},
            }
        )
        assert guard.to_dict()["action"] == {"type": "edit"}

    def test_returned_type_is_inspector(self):
        guard = Inspector.from_guard_model({"id": "id", "name": "G"}, requested_path=_PII_PATH)
        assert isinstance(guard, Inspector)

    def test_path_extracted_from_asset_info(self):
        # Paginate/get payloads carry the path under assetInfo.instanceId, like
        # any other model. It must surface as .path (REPL-browsable) and drive
        # the tuned defaults even when no requested_path is given (search flow).
        guard = Inspector.from_guard_model(
            {
                "id": "pii-id",
                "name": "Sensitive Information Guardrail",
                "assetInfo": {"instanceId": _PII_PATH, "assetName": "sensitive-information-guardrail"},
            }
        )
        assert guard.path == _PII_PATH
        assert guard.to_dict()["action"] == {"type": "edit"}

    def test_tuned_defaults_when_fetched_by_bare_id(self):
        # The issue states IDs are also accepted. When retrieved by raw id, the
        # id never matches the registry, but the payload's path still should
        # select the tuned config rather than the safe abort/input fallback.
        guard = Inspector.from_guard_model(
            {"id": "69cbf63cd74e334a6bacfeb1", "name": "PII", "path": _PII_PATH},
            requested_path="69cbf63cd74e334a6bacfeb1",
        )
        assert guard.to_dict()["action"] == {"type": "edit"}


class TestInspectorGet:
    def test_get_fetches_and_adapts(self):
        client = _FakeClient(get_result={"id": "pii-id", "name": "PII", "path": _PII_PATH})
        Bound = _bind_inspector(client)

        guard = Bound.get(_PII_PATH)

        # URL-encodes the (multi-slash) path and hits the models endpoint.
        assert client.got_path == "v2/models/aws%2Fsensitive-information-guardrail%2Faws"
        assert isinstance(guard, Inspector)
        assert guard.metric.asset_id == "pii-id"
        assert guard.action.type == "edit"

    def test_get_accepts_attribute_override(self):
        client = _FakeClient(get_result={"id": "pi-id", "name": "PI"})
        Bound = _bind_inspector(client)

        guard = Bound.get(_PROMPT_ATTACKS_PATH)
        guard.targets = ["output"]
        assert guard.to_dict()["targets"] == ["output"]

    def test_get_without_context_raises(self):
        with pytest.raises(Exception):
            Inspector.get(_PROMPT_ATTACKS_PATH)


class TestInspectorSearch:
    def test_search_returns_page_shape(self):
        client = _FakeClient(
            paginate_result={
                "results": [
                    {"id": "pi-id", "name": "Detect Prompt Attacks Guardrail", "path": _PROMPT_ATTACKS_PATH},
                    {"id": "pii-id", "name": "Sensitive Information Guardrail", "path": _PII_PATH},
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
        # Pinned to the guardrails function (a list of function-id strings, the
        # shape v2/models/paginate requires) and includes the query.
        assert body["functions"] == ["guardrails"]
        assert body["q"] == "guard"

        assert page.total == 6
        assert page.page_number == 0
        assert page.page_total == 1
        assert all(isinstance(r, Inspector) for r in page.results)
        assert [r.name for r in page.results] == [
            "Detect Prompt Attacks Guardrail",
            "Sensitive Information Guardrail",
        ]


# ---------------------------------------------------------------------------
# Function judges: source the engine can run (BUG-1383)
# ---------------------------------------------------------------------------


class TestFunctionJudgeSource:
    def test_named_function_gets_the_binding(self):
        source = _Judge.coerce(module_check).function
        assert source.startswith("def module_check(text):")
        assert source.endswith("\n\nevaluator_fn = module_check\n")
        assert _binds(source, "evaluator_fn")

    def test_named_function_as_editor_binds_edit_fn(self):
        inspector = Inspector(name="i", action="edit", metric=module_check, editor=module_async_check)
        editor_source = inspector.to_dict()["editor"]["function"]
        assert editor_source.endswith("edit_fn = module_async_check\n")
        assert _binds(editor_source, "edit_fn")
        assert not _binds(editor_source, "evaluator_fn")

    def test_async_function_gets_the_binding(self):
        source = _Judge.coerce(module_async_check).function
        assert source.startswith("async def module_async_check(text):")
        assert _binds(source, "evaluator_fn")

    def test_correctly_named_functions_are_unchanged(self):
        assert _Judge.coerce(evaluator_fn).function == 'def evaluator_fn(text):\n    return "HIGH" in text\n'
        assert (
            _Judge.coerce(edit_fn, role="editor").function
            == 'def edit_fn(text):\n    return text.replace("HIGH", "")\n'
        )

    def test_lone_lambda_is_isolated(self):
        source = _Judge.coerce(lone_lambda).function
        assert source == 'evaluator_fn = lambda text: "HIGH" in text\n'
        namespace = {}
        exec(source, namespace)
        assert namespace["evaluator_fn"]("HIGH risk") is True

    def test_lambda_in_the_incident_shape_is_isolated(self):
        inspector = Inspector(name="i", action="abort", metric=lambda text: "HIGH" in text)
        assert inspector.to_dict()["evaluator"] == {
            "type": "function",
            "function": 'evaluator_fn = lambda text: "HIGH" in text\n',
        }

    def test_lambda_sharing_its_statement_is_rejected(self):
        with pytest.raises(ValueError, match=_RUNNABLE_HINT):
            _Judge.coerce(two_lambdas[0])

    def test_multiline_lambda_is_isolated_whole(self):
        source = _Judge.coerce(multiline_lambda["metric"]).function
        assert source == 'evaluator_fn = lambda text: (\n    "HIGH"\n    in text\n)\n'
        assert _binds(source, "evaluator_fn")

    def test_lambda_with_partial_source_is_rejected(self):
        """``getsource`` returns only ``lambda text: ..., None]`` here, which does not parse."""
        with pytest.raises(ValueError, match="cannot be isolated"):
            _Judge.coerce(partial_source_lambdas[0])

    def test_closure_is_rejected(self):
        threshold = 3

        def check(text):
            return len(text) > threshold

        with pytest.raises(ValueError, match="closes over threshold"):
            Inspector(name="i", action="abort", metric=check)

    def test_bound_method_is_rejected(self):
        with pytest.raises(ValueError, match="bound methods"):
            Inspector(name="i", action="abort", metric=_Holder().method_check)

    @pytest.mark.parametrize(
        "fn",
        [len, functools.partial(module_check, text="x"), _CallableInstance()],
        ids=["builtin", "partial", "callable-instance"],
    )
    def test_callables_without_source_are_rejected(self, fn):
        with pytest.raises(ValueError, match=_RUNNABLE_HINT):
            Inspector(name="i", action="abort", metric=fn)

    def test_decorated_function_is_rejected(self):
        with pytest.raises(ValueError, match="decorated"):
            Inspector(name="i", action="abort", metric=decorated_check)

    def test_function_without_retrievable_source_is_rejected(self):
        """A REPL function used to become ``module.qualname``, which can never run."""
        with patch("aixplain.v2.inspector.inspect.getsource", side_effect=OSError("could not get source")):
            with pytest.raises(ValueError, match="REPL or notebook"):
                Inspector(name="i", action="abort", metric=module_check)

    def test_error_names_what_is_required(self):
        with pytest.raises(ValueError) as excinfo:
            Inspector(name="i", action="abort", metric=len)
        message = str(excinfo.value)
        assert "module-level function" in message
        assert "own arguments and its own imports" in message
        assert "'function'" in message

    def test_source_string_passes_through_unchanged(self):
        source = "def evaluator_fn(t):\n    return True\n"
        inspector = Inspector(name="i", action="abort", metric={"function": source})
        assert inspector.to_dict()["evaluator"] == {"type": "function", "function": source}

    def test_dict_with_a_callable_is_serialised(self):
        inspector = Inspector(name="i", action="edit", metric={"function": module_check}, editor={"function": edit_fn})
        assert _binds(inspector.to_dict()["evaluator"]["function"], "evaluator_fn")
        assert _binds(inspector.to_dict()["editor"]["function"], "edit_fn")

    def test_backend_source_is_not_validated(self):
        data = {
            "name": "stored",
            "targets": ["output"],
            "action": {"type": "abort"},
            "evaluator": {"type": "function", "function": "def anything(t): return True"},
        }
        assert Inspector.from_dict(data).to_dict() == data

    @pytest.mark.parametrize(
        "source,ok",
        [
            ("def evaluator_fn(t):\n    return t\n", True),
            ("async def evaluator_fn(t):\n    return t\n", True),
            ("def f(t):\n    return t\nevaluator_fn = f\n", True),
            ("evaluator_fn: object = len\n", True),
            ("def f(t):\n    return t\n", False),
            ("if True:\n    evaluator_fn = len\n", False),
            ("class C:\n    pass\nevaluator_fn = C()\n", False),
        ],
    )
    def test_top_level_binding_mirrors_the_engine(self, source, ok):
        if ok:
            _check_top_level_binding(source, "evaluator_fn")
        else:
            with pytest.raises(ValueError, match="not defined at top level"):
                _check_top_level_binding(source, "evaluator_fn")

    def test_unparseable_source_is_rejected(self):
        with pytest.raises(ValueError, match="does not parse"):
            _check_top_level_binding("def evaluator_fn(:\n", "evaluator_fn")


def test_agent_save_payload_keeps_the_function_judge_shape():
    from unittest.mock import MagicMock

    from aixplain import Agent

    agent = Agent.from_dict({"id": "a1", "name": "t"})
    agent.context = MagicMock()
    agent.inspectors = [Inspector(name="i", targets=["output"], action="abort", metric=module_check)]

    payload = agent.build_save_payload()

    assert payload["inspectors"] == [
        {
            "name": "i",
            "targets": ["output"],
            "action": {"type": "abort"},
            "evaluator": {"type": "function", "function": _Judge.coerce(module_check).function},
        }
    ]
    assert _binds(payload["inspectors"][0]["evaluator"]["function"], "evaluator_fn")
