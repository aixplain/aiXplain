"""Unit tests for :class:`~aixplain.v2.agent_evaluator.Metric` factory helpers."""

from __future__ import annotations

import warnings
from unittest.mock import MagicMock, patch

import pytest

from aixplain.v2.agent_evaluator import Metric
from aixplain.v2.exceptions import ValidationError


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
