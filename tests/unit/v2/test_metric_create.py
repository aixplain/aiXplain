"""Unit tests for :class:`~aixplain.v2.agent_evaluator.Metric` factory helpers."""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock, patch

import pytest

from aixplain.v2.agent_evaluator import Metric, _clean_generated_instruction
from aixplain.v2.exceptions import ValidationError


def _fake_model_result(text: str) -> MagicMock:
    result = MagicMock()
    result.data = text
    result.result = None
    result.details = None
    return result


def test_metric_generate_prompt_template_numeric() -> None:
    raw = Metric._generate_prompt_template(
        score_type="numeric",
        instruction="Score relevance.",
        start_number=0.0,
        end_number=4.0,
    )
    assert "Score relevance." in raw
    assert "0" in raw and "4" in raw


def test_metric_generate_prompt_template_invalid_score_type() -> None:
    with pytest.raises(ValueError, match="Invalid score type"):
        Metric._generate_prompt_template(score_type="other", instruction="x")


def test_metric_create_requires_prompt_or_spec() -> None:
    with pytest.raises(ValidationError, match="prompt_template or score_type"):
        Metric.create("m", "llm-path")


def test_metric_create_requires_instruction_when_generating() -> None:
    with pytest.raises(ValidationError, match="instruction"):
        Metric.create("m", "llm-path", score_type="boolean")


def test_metric_create_numeric_requires_bounds() -> None:
    with pytest.raises(ValidationError, match="start_number and end_number"):
        Metric.create("m", "llm-path", score_type="numeric", instruction="Rate it.")


def test_metric_create_categorical_requires_categories() -> None:
    with pytest.raises(ValidationError, match="categories"):
        Metric.create("m", "llm-path", score_type="categorical", instruction="Pick one.")


@patch.object(Metric, "save", MagicMock())
def test_metric_create_with_explicit_prompt_strips_whitespace() -> None:
    m = Metric.create("name", "llm-id", prompt_template="  hi  ")
    assert m.config["prompt"] == "hi"
    assert m.config["llmId"] == "llm-id"


@patch.object(Metric, "save", MagicMock())
def test_metric_create_generates_boolean_prompt() -> None:
    m = Metric.create("name", "llm-id", score_type="boolean", instruction="Is it correct?")
    assert "Is it correct?" in m.config["prompt"]
    assert "true" in m.config["prompt"]


@patch.object(Metric, "save", MagicMock())
def test_metric_initialize_deprecated_alias() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        Metric.initialize("n", "prompt body", "llm")
    assert any(issubclass(x.category, DeprecationWarning) for x in w)


def test_metric_constructor_resolves_config_without_saving() -> None:
    """Metric(...) alone (no .save()) should resolve config/integration locally, no network call."""
    with patch.object(Metric, "save") as mock_save:
        m = Metric(name="name", llm_path="llm-id", prompt_template="  hi  ")
    mock_save.assert_not_called()
    assert m.id is None
    assert m.config == {"prompt": "hi", "llmId": "llm-id"}
    assert m.integration == "aixplain/custom-llm-prompt/aixplain"


@patch.object(Metric, "save", MagicMock())
def test_metric_constructor_plus_save_matches_create() -> None:
    """Metric(...).save() should be equivalent to Metric.create(...)."""
    m1 = Metric(name="name", llm_path="llm-id", score_type="boolean", instruction="Is it correct?")
    m1.save()
    m2 = Metric.create("name", "llm-id", score_type="boolean", instruction="Is it correct?")
    assert m1.config == m2.config
    assert m1.integration == m2.integration


def test_metric_constructor_requires_prompt_or_spec() -> None:
    with pytest.raises(ValidationError, match="prompt_template or score_type"):
        Metric(name="m", llm_path="llm-path")


def test_metric_constructor_numeric_requires_bounds() -> None:
    with pytest.raises(ValidationError, match="start_number and end_number"):
        Metric(name="m", llm_path="llm-path", score_type="numeric", instruction="Rate it.")


def test_metric_bare_constructor_unaffected() -> None:
    """A fully bare Metric() (no rubric fields) keeps its pre-existing script-tool behavior."""
    with pytest.raises(AssertionError, match="Code is required"):
        Metric(name="bare")


def test_metric_explicit_integration_unaffected() -> None:
    """Explicit integration/config construction bypasses rubric resolution entirely."""
    m = Metric(name="explicit", integration="some/integration", config={"foo": "bar"})
    assert m.config == {"foo": "bar"}
    assert m.integration == "some/integration"


def test_metric_hydration_with_id_skips_rubric_resolution() -> None:
    """Reconstructing an already-saved Metric (id set) must not re-trigger rubric validation."""
    m = Metric(id="existing-id", name="loaded")
    assert m.config is None


def test_clean_generated_instruction_strips_quotes_fences_and_preamble() -> None:
    assert _clean_generated_instruction('  "Rate the tone of the response."  ') == "Rate the tone of the response."
    assert (
        _clean_generated_instruction("```\nSure, here is the instruction: Rate correctness.\n```")
        == "Rate correctness."
    )
    assert _clean_generated_instruction("Instruction: Judge relevance to the query.") == "Judge relevance to the query."
    assert _clean_generated_instruction("") == ""
    assert _clean_generated_instruction(None) == ""


def test_metric_instruction_optional_defers_to_save_without_network() -> None:
    """Omitting instruction (with description set) defers resolution; construction stays local."""
    with patch.object(Metric, "context"):
        m = Metric(
            name="Relevance",
            llm_path="llm-id",
            score_type="boolean",
            description="Judge if the answer is relevant to the query.",
        )
    assert m.config is None
    assert m._pending_rubric_resolution is True
    assert m.integration == "aixplain/custom-llm-prompt/aixplain"


def test_metric_instruction_and_description_both_missing_raises_at_construction() -> None:
    with pytest.raises(ValidationError, match="instruction"):
        Metric(name="Relevance", llm_path="llm-id", score_type="boolean")


def test_metric_save_generates_instruction_via_llm() -> None:
    fake_model = MagicMock()
    fake_model.params = []
    fake_model.run.return_value = _fake_model_result(
        "Judge whether the response directly and accurately answers the user query."
    )

    with patch.object(Metric, "context") as mock_context:
        mock_context.Model.get.return_value = fake_model
        m = Metric(
            name="Relevance",
            llm_path="llm-id",
            score_type="boolean",
            description="Judge if the answer is relevant to the query.",
        )
        with patch("aixplain.v2.agent_evaluator.Tool.save", MagicMock()):
            m.save()

    mock_context.Model.get.assert_called_once_with("llm-id")
    assert m.instruction == "Judge whether the response directly and accurately answers the user query."
    assert m.instruction in m.config["prompt"]
    assert m.config["llmId"] == "llm-id"
    assert m._pending_rubric_resolution is False


def test_metric_save_falls_back_to_templated_instruction_on_llm_failure() -> None:
    with patch.object(Metric, "context") as mock_context:
        mock_context.Model.get.side_effect = RuntimeError("network down")
        m = Metric(
            name="Relevance",
            llm_path="llm-id",
            score_type="boolean",
            description="Judge if the answer is relevant to the query.",
        )
        with patch("aixplain.v2.agent_evaluator.Tool.save", MagicMock()):
            m.save()

    assert m.instruction == "Evaluate the output according to the following description: Judge if the answer is relevant to the query."
    assert m.instruction in m.config["prompt"]


def test_metric_save_falls_back_when_llm_returns_empty_response() -> None:
    fake_model = MagicMock()
    fake_model.params = []
    fake_model.run.return_value = _fake_model_result("   ")

    with patch.object(Metric, "context") as mock_context:
        mock_context.Model.get.return_value = fake_model
        m = Metric(
            name="Relevance",
            llm_path="llm-id",
            score_type="boolean",
            description="Judge if the answer is relevant to the query.",
        )
        with patch("aixplain.v2.agent_evaluator.Tool.save", MagicMock()):
            m.save()

    assert m.instruction.startswith("Evaluate the output according to the following description:")


def test_metric_save_only_generates_instruction_once() -> None:
    """Calling save() twice must not trigger a second LLM call."""
    fake_model = MagicMock()
    fake_model.params = []
    fake_model.run.return_value = _fake_model_result("Judge correctness of the response.")

    with patch.object(Metric, "context") as mock_context:
        mock_context.Model.get.return_value = fake_model
        m = Metric(
            name="Relevance",
            llm_path="llm-id",
            score_type="boolean",
            description="Judge if the answer is relevant to the query.",
        )
        with patch("aixplain.v2.agent_evaluator.Tool.save", MagicMock()):
            m.save()
            m.save()

    assert mock_context.Model.get.call_count == 1


def test_metric_create_with_description_no_instruction_defers_generation() -> None:
    """Metric.create without instruction (but with metric_description) should auto-generate on save."""
    fake_model = MagicMock()
    fake_model.params = []
    fake_model.run.return_value = _fake_model_result("Judge whether the response is factually correct.")

    with patch.object(Metric, "context") as mock_context:
        mock_context.Model.get.return_value = fake_model
        with patch("aixplain.v2.agent_evaluator.Tool.save", MagicMock()):
            m = Metric.create(
                "correctness",
                "llm-id",
                metric_description="Judge if the answer is factually correct.",
                score_type="boolean",
            )

    assert m.instruction == "Judge whether the response is factually correct."
