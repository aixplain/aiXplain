"""Unit tests for AgentEvaluationExecutor and eval row aggregation."""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from aixplain.v2.agent import AgentResponseData
from aixplain.v2.agent_evaluator import (
    AgentEvaluationExecutor,
    AgentEvaluationResultsChatbot,
    AgentEvaluationRun,
    EvalCase,
    MetricTool,
    _infer_prompt_input_field_name,
    _reply_text_from_model_result,
    compare_agents_side_by_side,
    normalize_eval_results_dataframe,
)
from aixplain.v2.eval_results_display import summarize_by_agent
from aixplain.v2.eval_experiment import (
    EXPERIMENT_COMPARISON_COL_RUN_INDEX,
    Experiment,
    ExperimentLocalCache,
)
from aixplain.v2.model import Detail, Message, ModelResult
from aixplain.v2.exceptions import APIError, ValidationError


def _successful_run_result(ard: AgentResponseData) -> MagicMock:
    result = MagicMock()
    result.data = ard
    result.status = "SUCCESS"
    result.completed = True
    result.error_message = None
    result.run_time = 0.5
    result.used_credits = 0.1
    return result


def test_agent_run_failure_records_row_and_skips_metrics() -> None:
    """When agent.run raises, the row records failure and metrics are skipped."""
    agent = MagicMock()
    agent.name = "test_agent"
    agent.run.side_effect = APIError(
        "Operation failed: tool bad",
        status_code=500,
        response_data={"hint": "fix params"},
    )

    metric = MagicMock(spec=MetricTool)
    metric.name = "quality"

    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="hello")], metrics=[metric])

    assert len(run) == 1
    row = run.rows[0]
    assert row.agent_run_failed is True
    assert row.status == "FAILED"
    assert row.completed is False
    assert row.error_message and "Operation failed" in row.error_message
    assert row.agent_error_type == "APIError"
    assert row.agent_error_details is not None
    assert row.output is None
    assert row.agent_response is None
    metric.measure.assert_not_called()
    assert row.metric_value("quality", "metric_skipped") is True
    assert row.metric_value("quality", "metric_skip_reason") == "agent_run_failed"
    assert row.metric_value("quality", "metric_completed") is False
    assert row.metric_value("quality", "metric_status") == "SKIPPED"


def test_metric_failure_records_metric_columns() -> None:
    """When measure raises, metric error columns are set without aborting the row."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="out", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    metric.measure.side_effect = ValueError("invalid json")

    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])

    assert len(run) == 1
    row = run.rows[0]
    assert row.agent_run_failed is False
    assert row.metric_value("m1", "metric_status") == "FAILED"
    assert row.metric_value("m1", "metric_completed") is False
    assert row.metric_value("m1", "metric_error") and "invalid json" in str(row.metric_value("m1", "metric_error"))
    assert row.metric_value("m1", "metric_error_type") == "ValueError"


def test_success_merges_metric_columns() -> None:
    """Successful agent and metric runs flatten validated_data into columns."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="ans", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    metric.measure.return_value = mr

    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    row = run.rows[0]
    assert row.agent_run_failed is False
    assert row.output == "ans"
    assert row.metric_value("m1", "metric_status") == "SUCCESS"
    assert row.metric_value("m1", "score") == 0.9


def test_metric_numeric_threshold_sets_metric_pass() -> None:
    """Float threshold: metric_pass is True when score > threshold."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="ans", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    metric.threshold = 0.5
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    metric.measure.return_value = mr

    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    row = run.rows[0]
    assert row.metric_value("m1", "metric_pass") is True

    mr.validated_data = {"score": 0.3}
    metric.measure.return_value = mr
    run2 = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    assert run2.rows[0].metric_value("m1", "metric_pass") is False


def test_metric_pass_rates_in_run_summary_llm_context_and_summarize() -> None:
    """run_summary, to_llm_context, and summarize_by_agent surface pass-rate stats."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="ans", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    metric.threshold = 0.5
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    metric.measure.return_value = mr

    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    mpr = run.metric_pass_rates()
    assert "m1" in mpr
    assert mpr["m1"]["evaluated"] == 1 and mpr["m1"]["passed"] == 1 and mpr["m1"]["pass_rate"] == 1.0

    summary = run.run_summary(include_executive_summary=False)
    assert summary["metric_pass_rates"]["m1"]["passed"] == 1
    assert summary["per_agent"]["agent_a"]["metric_pass__m1"]["pass_rate"] == 1.0

    ctx = run.to_llm_context(layout="text", max_output_chars=200)
    assert "metric threshold pass rates" in ctx.lower()
    assert "m1" in ctx

    template = run._executive_summary_template()
    assert "Threshold pass rates" in template or "metric_pass" in template.lower()

    by_agent = summarize_by_agent(run.to_dataframe())
    assert "pass_rate__m1__metric_pass" in by_agent.columns
    assert by_agent.iloc[0]["pass_rate__m1__metric_pass"] == 1.0


def test_metric_enum_threshold_sets_metric_pass() -> None:
    """List threshold: metric_pass is True when score string is in the passing list."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="ans", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    metric.threshold = ["PASS", "OK"]
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": "PASS"}
    metric.measure.return_value = mr

    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    assert run.rows[0].metric_value("m1", "metric_pass") is True

    mr.validated_data = {"score": "FAIL"}
    metric.measure.return_value = mr
    run2 = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    assert run2.rows[0].metric_value("m1", "metric_pass") is False


def test_evaluate_continues_after_agent_failure() -> None:
    """A failed case does not prevent later cases from being evaluated."""
    agent = MagicMock()
    agent.name = "a"
    ard = AgentResponseData(input="x", output="ok", steps=[])

    def run_side_effect(query: object, **kwargs: object) -> MagicMock:
        if query == "bad":
            raise APIError("fail")
        return _successful_run_result(ard)

    agent.run.side_effect = run_side_effect

    run = AgentEvaluationExecutor().evaluate(
        agent,
        [EvalCase(query="bad"), EvalCase(query="good")],
    )
    assert len(run) == 2
    assert run.rows[0].agent_run_failed is True
    assert run.rows[1].agent_run_failed is False
    assert run.rows[1].output == "ok"


def test_normalize_eval_results_dataframe_csv_like_strings() -> None:
    """After CSV round-trip, booleans and numeric metrics are coerced back."""
    raw = pd.DataFrame(
        [
            {
                "case_index": "0",
                "agent_name": "a",
                "agent_run_failed": "False",
                "completed": "True",
                "run_time": "0.5",
                "used_credits": "0.1",
                "m__score": "0.9",
                "m__label": "ok",
            }
        ]
    )
    norm = normalize_eval_results_dataframe(raw)
    assert norm["case_index"].dtype.name == "Int64"
    assert not norm.iloc[0]["agent_run_failed"]
    assert norm.iloc[0]["completed"]
    assert norm.iloc[0]["run_time"] == 0.5
    assert norm.iloc[0]["used_credits"] == 0.1
    assert norm.iloc[0]["m__score"] == 0.9
    assert norm.iloc[0]["m__label"] == "ok"


def test_compare_agents_side_by_side_two_agents() -> None:
    """Wide view has one row per case and output/score columns per agent."""
    long_df = pd.DataFrame(
        [
            {
                "case_index": 0,
                "query": "q1",
                "reference": None,
                "agent_name": "Agent A",
                "output": "out a",
                "m__score": 0.8,
                "m__reasoning": "because",
            },
            {
                "case_index": 0,
                "query": "q1",
                "reference": None,
                "agent_name": "Agent B",
                "output": "out b",
                "m__score": 0.9,
                "m__reasoning": "other",
            },
        ]
    )
    wide = compare_agents_side_by_side(long_df, include_reference=False)
    assert len(wide) == 1
    assert wide.iloc[0]["case_index"] == 0
    assert wide.iloc[0]["query"] == "q1"
    assert wide.iloc[0]["output__Agent A"] == "out a"
    assert wide.iloc[0]["output__Agent B"] == "out b"
    assert wide.iloc[0]["m__score__Agent A"] == 0.8
    assert wide.iloc[0]["m__score__Agent B"] == 0.9
    assert "m__reasoning__Agent A" not in wide.columns


def test_compare_agents_side_by_side_requires_columns() -> None:
    with pytest.raises(ValidationError, match="case_index"):
        compare_agents_side_by_side(pd.DataFrame({"agent_name": ["x"]}))


def test_execution_insights_row_dataframe_and_csv_roundtrip(tmp_path: object) -> None:
    """Request id, assets_used, tool counts, and per-asset time/credits are captured and exportable."""
    agent = MagicMock()
    agent.name = "Web Agent"
    steps = [
        {"unit": {"type": "model", "name": "GPT-5 Mini"}, "run_time": 1.0, "used_credits": 0.01, "api_calls": 1},
        {"unit": {"type": "tool", "name": "Tavily Web Search"}, "run_time": 2.0, "used_credits": 0.0, "api_calls": 1},
        {"unit": {"type": "tool", "name": "Tavily Web Search"}, "run_time": 1.5, "used_credits": 0.0, "api_calls": 1},
    ]
    stats = {
        "request_id": "req-uuid-1",
        "assets_used": ["agent:Web Agent", "tool:Tavily Web Search"],
        "api_calls": 9,
    }
    ard = AgentResponseData(input="q", output="ans", steps=steps, execution_stats=stats)
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")])
    row = run.rows[0]
    assert row.request_id == "req-uuid-1"
    assert row.assets_used == ["agent:Web Agent", "tool:Tavily Web Search"]
    assert row.total_tool_calls == 2
    assert row.per_asset_stats["model:GPT-5 Mini"]["run_time"] == 1.0
    assert row.per_asset_stats["model:GPT-5 Mini"]["used_credits"] == 0.01
    assert row.per_asset_stats["tool:Tavily Web Search"]["run_time"] == 3.5
    assert row.per_asset_stats["tool:Tavily Web Search"]["n_steps"] == 2

    df = run.to_dataframe()
    assert json.loads(df.iloc[0]["assets_used"]) == row.assets_used
    pas = json.loads(df.iloc[0]["per_asset_stats"])
    assert pas["tool:Tavily Web Search"]["run_time"] == 3.5
    assert df.iloc[0]["total_tool_calls"] == 2
    assert df.iloc[0]["request_id"] == "req-uuid-1"

    txt = run.to_llm_context(layout="text", max_output_chars=None)
    assert "req-uuid-1" in txt and "total_tool_calls" in txt and "Tavily Web Search" in txt

    rec = run.to_json_records()[0]
    assert rec["total_tool_calls"] == 2
    assert rec["request_id"] == "req-uuid-1"
    assert rec["assets_used"] == row.assets_used

    csv_path = tmp_path / "eval_exec.csv"
    df.to_csv(csv_path, index=False)
    loaded = AgentEvaluationExecutor.load_from_csv(csv_path)
    lr = loaded.rows[0]
    assert lr.request_id == "req-uuid-1"
    assert lr.total_tool_calls == 2
    assert lr.assets_used == row.assets_used
    assert lr.per_asset_stats["tool:Tavily Web Search"]["run_time"] == 3.5


def test_execution_insights_runtime_credit_breakdown_without_steps() -> None:
    """When there are no steps, per-asset stats use execution_stats breakdown dicts."""
    agent = MagicMock()
    agent.name = "A"
    ard = AgentResponseData(
        input="q",
        output="o",
        steps=[],
        execution_stats={
            "request_id": "r2",
            "assets_used": ["agent:A"],
            "runtime_breakdown": {"Agent A": 10.5},
            "credit_breakdown": {"Agent A": 0.25},
        },
    )
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")])
    row = run.rows[0]
    assert row.per_asset_stats["Agent A"]["run_time"] == 10.5
    assert row.per_asset_stats["Agent A"]["used_credits"] == 0.25
    assert row.total_tool_calls == 0
    assert row.request_id == "r2"


def test_eval_run_to_dataframe_matches_flat_columns() -> None:
    """Structured metrics round-trip to legacy ``prefix__key`` column names."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="ans", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    metric.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    df = run.to_dataframe()
    assert df.iloc[0]["m1__score"] == 0.9
    assert isinstance(run, AgentEvaluationRun)


def test_load_agent_evaluation_run_from_csv_roundtrip(tmp_path: object) -> None:
    """CSV from ``to_dataframe`` reloads into equivalent structured rows."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="ans", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    metric.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    csv_path = tmp_path / "eval.csv"
    run.to_dataframe().to_csv(csv_path, index=False)
    loaded = AgentEvaluationExecutor.load_from_csv(csv_path)
    assert len(loaded) == 1
    assert loaded.rows[0].output == "ans"
    assert loaded.rows[0].metric_value("m1", "score") == 0.9
    assert loaded.rows[0].metric_value("m1", "metric_status") == "SUCCESS"


def test_load_agent_evaluation_run_from_csv_requires_columns(tmp_path: object) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("agent_name\nx\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="case_index"):
        AgentEvaluationExecutor.load_from_csv(bad)


def test_compare_agents_side_by_side_accepts_eval_run() -> None:
    """Module and :meth:`AgentEvaluationRun.compare_agents_side_by_side` accept structured runs."""
    a1 = MagicMock()
    a1.name = "A"
    a2 = MagicMock()
    a2.name = "B"
    ard_a = AgentResponseData(input="q", output="out_a", steps=[])
    ard_b = AgentResponseData(input="q", output="out_b", steps=[])
    a1.run.return_value = _successful_run_result(ard_a)
    a2.run.return_value = _successful_run_result(ard_b)
    run = AgentEvaluationExecutor().evaluate([a1, a2], [EvalCase(query="q")])
    wide = compare_agents_side_by_side(run, include_reference=False)
    assert wide.iloc[0]["output__A"] == "out_a"
    assert wide.iloc[0]["output__B"] == "out_b"
    wide2 = run.compare_agents_side_by_side(include_reference=False)
    pd.testing.assert_frame_equal(wide, wide2)


def test_run_filter_subset_and_filter_where() -> None:
    a1 = MagicMock()
    a1.name = "A"
    a2 = MagicMock()
    a2.name = "B"
    ard = AgentResponseData(input="q", output="ok", steps=[])
    a1.run.return_value = _successful_run_result(ard)
    a2.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(
        [a1, a2],
        [EvalCase(query="q0"), EvalCase(query="q1")],
    )
    assert len(run.filter(case_indices=[0])) == 2
    assert len(run.filter(agent_names=["A"])) == 2
    assert len(run.subset_for_case(1)) == 2
    only_a = run.filter_where(lambda r: r.agent_name == "A")
    assert len(only_a) == 2
    assert all(r.agent_name == "A" for r in only_a.rows)


def test_run_to_llm_context_and_json_records() -> None:
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="hello", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 1.0}
    metric.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="qq")], metrics=[metric])
    txt = run.to_llm_context(layout="text", max_output_chars=100)
    assert "qq" in txt and "hello" in txt and "m1" in txt
    assert "run_time" in txt and "used_credits" in txt and "0.5" in txt and "0.1" in txt
    rec = run.to_json_records()
    assert rec[0]["m1__score"] == 1.0


def test_run_summary_and_executive_summary() -> None:
    """Run summary aggregates cost/time/agents/samples and includes narrative insights."""
    a1 = MagicMock()
    a1.name = "A"
    a2 = MagicMock()
    a2.name = "B"

    ard_a = AgentResponseData(
        input="q",
        output="out_a",
        steps=[{"unit": {"type": "tool", "name": "t1"}, "run_time": 1.0, "used_credits": 0.01}],
        execution_stats={"assets_used": ["agent:A", "tool:t1"], "request_id": "r1"},
    )
    ard_b = AgentResponseData(
        input="q",
        output="out_b",
        steps=[{"unit": {"type": "tool", "name": "t2"}, "run_time": 2.0, "used_credits": 0.02}],
        execution_stats={"assets_used": ["agent:B", "tool:t2"], "request_id": "r2"},
    )
    res_a = _successful_run_result(ard_a)
    res_b = _successful_run_result(ard_b)
    res_a.used_credits = 0.3
    res_b.used_credits = 0.1
    res_a.run_time = 1.5
    res_b.run_time = 0.5
    a1.run.return_value = res_a
    a2.run.return_value = res_b

    m = MagicMock(spec=MetricTool)
    m.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    m.measure.return_value = mr

    run = AgentEvaluationExecutor().evaluate([a1, a2], [EvalCase(query="q0"), EvalCase(query="q1")], metrics=[m])
    summary = run.run_summary()
    assert summary["total_samples"] == 2
    assert summary["n_agents"] == 2
    assert summary["rows_evaluated"] == 4
    assert summary["total_cost"] == pytest.approx(0.8)
    assert summary["total_time_seconds"] == pytest.approx(4.0)
    assert summary["total_tool_calls"] == 4
    assert set(summary["agents_evaluated"]) == {"A", "B"}
    assert "executive_summary" in summary
    assert "Evaluation overview" in summary["executive_summary"]
    assert "Actionable insights" in summary["executive_summary"]

    exec_summary = run.executive_summary()
    assert "Total cost" in exec_summary
    assert "samples" in exec_summary


def test_reply_text_from_model_result_reads_details_and_choices() -> None:
    """Model text may live under ``details[].message.content`` or OpenAI-style ``choices``."""
    with_details = ModelResult(
        status="SUCCESS",
        completed=True,
        data=None,
        details=[Detail(message=Message(role="assistant", content="From details."))],
    )
    assert _reply_text_from_model_result(with_details) == "From details."

    choices_payload = ModelResult(
        status="SUCCESS",
        completed=True,
        data={"choices": [{"message": {"role": "assistant", "content": "From choices."}}]},
    )
    assert _reply_text_from_model_result(choices_payload) == "From choices."


def test_executive_summary_uses_llm_when_model_is_provided() -> None:
    """Executive summary uses model output when a summary model is passed."""
    agent = MagicMock()
    agent.name = "A"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")])

    model = MagicMock()
    model.params = [SimpleNamespace(name="data", required=True, data_type="text")]
    model.run.return_value = MagicMock(data="Dynamic LLM executive summary with deeper insights.")

    txt = run.executive_summary(model=model)
    assert txt.startswith("Dynamic LLM executive summary")
    model.run.assert_called_once()

    kwargs = model.run.call_args.kwargs
    assert "data" in kwargs
    assert "run_summary_stats_json" in kwargs["data"]


def test_executive_summary_uses_model_when_text_only_in_details() -> None:
    """When ``data`` is empty but ``details`` carries the assistant message, use it."""
    agent = MagicMock()
    agent.name = "A"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")])

    model = MagicMock()
    model.params = [SimpleNamespace(name="data", required=True, data_type="text")]
    model.run.return_value = ModelResult(
        status="SUCCESS",
        completed=True,
        data="",
        details=[Detail(message=Message(role="assistant", content="Summary from details field."))],
    )

    txt = run.executive_summary(model=model)
    assert txt == "Summary from details field."
    model.run.assert_called_once()


def test_run_summary_uses_llm_executive_summary_when_requested() -> None:
    """run_summary embeds the model-generated executive summary when configured."""
    agent = MagicMock()
    agent.name = "A"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")])

    model = MagicMock()
    model.params = [SimpleNamespace(name="data", required=True, data_type="text")]
    model.run.return_value = MagicMock(data="LLM summary text.")

    summary = run.run_summary(summary_model=model)
    assert summary["executive_summary"] == "LLM summary text."
    assert summary["total_samples"] == 1
    model.run.assert_called_once()


def test_executive_summary_uses_default_model_when_none_passed() -> None:
    """When no model is provided, executive_summary resolves and uses default model."""
    agent = MagicMock()
    agent.name = "A"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")])

    default_model = MagicMock()
    default_model.params = [SimpleNamespace(name="data", required=True, data_type="text")]
    default_model.run.return_value = MagicMock(data="Default model executive summary.")

    with patch("aixplain.v2.agent_evaluator._default_insight_model", return_value=default_model):
        txt = run.executive_summary()

    assert txt == "Default model executive summary."
    default_model.run.assert_called_once()


def test_resolve_default_insight_model_calls_get_with_path() -> None:
    """Default insight model is loaded via bound Model.get(path) first."""
    mock_aix = MagicMock()
    bound_model_cls = MagicMock()
    bound_model_cls.context = object()
    resolved = MagicMock()
    bound_model_cls.get = MagicMock(return_value=resolved)
    mock_aix.Model = bound_model_cls
    saved_ctx = AgentEvaluationRun.insight_context
    saved_dm = AgentEvaluationRun.DEFAULT_INSIGHT_MODEL
    try:
        AgentEvaluationRun.configure_insights(mock_aix)
        out = AgentEvaluationRun._resolve_default_insight_model()
        bound_model_cls.get.assert_called_once_with("openai/gpt-5.4-mini/openai")
        assert out is resolved
    finally:
        AgentEvaluationRun.insight_context = saved_ctx
        AgentEvaluationRun.DEFAULT_INSIGHT_MODEL = saved_dm


def test_ensure_insight_model_loaded_invokes_resolve() -> None:
    """ensure_insight_model_loaded delegates to _resolve_default_insight_model."""
    with patch.object(AgentEvaluationRun, "_resolve_default_insight_model", return_value=None) as mock_r:
        assert AgentEvaluationRun.ensure_insight_model_loaded() is None
    mock_r.assert_called_once()


def test_configure_insights_sets_context_and_clears_model_cache() -> None:
    """configure_insights stores the client and invalidates cached default model."""
    saved_ctx = AgentEvaluationRun.insight_context
    saved_model = AgentEvaluationRun.DEFAULT_INSIGHT_MODEL
    try:
        AgentEvaluationRun.DEFAULT_INSIGHT_MODEL = MagicMock()
        mock_aix = MagicMock()
        AgentEvaluationRun.configure_insights(mock_aix)
        assert AgentEvaluationRun.insight_context is mock_aix
        assert AgentEvaluationRun.DEFAULT_INSIGHT_MODEL is None
    finally:
        AgentEvaluationRun.insight_context = saved_ctx
        AgentEvaluationRun.DEFAULT_INSIGHT_MODEL = saved_model


def test_chatbot_uses_default_insight_model_when_none_passed() -> None:
    """chatbot() resolves default insight model when model arg is omitted."""
    run = AgentEvaluationRun(rows=[])
    default_model = MagicMock()
    default_model.params = [SimpleNamespace(name="data", required=True, data_type="text")]
    default_model.run.return_value = MagicMock(data="default chatbot ok")

    with patch("aixplain.v2.agent_evaluator._default_insight_model", return_value=default_model):
        bot = run.chatbot()

    assert isinstance(bot, AgentEvaluationResultsChatbot)
    assert bot.ask("hi") == "default chatbot ok"
    default_model.run.assert_called_once()


def test_run_summarize_by_agent_and_pivot_wrappers() -> None:
    a1 = MagicMock()
    a1.name = "A"
    a2 = MagicMock()
    a2.name = "B"
    ard = AgentResponseData(input="q", output="x", steps=[])
    a1.run.return_value = _successful_run_result(ard)
    a2.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate([a1, a2], [EvalCase(query="q")])
    summary = run.summarize_by_agent()
    assert "agent_name" in summary.columns and len(summary) == 2
    wide = run.pivot_agents_wide(include_reference=False)
    assert wide.shape[0] == 1


def test_run_to_llm_context_invalid_layout() -> None:
    agent = MagicMock()
    agent.name = "a"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")])
    with pytest.raises(ValidationError, match="layout"):
        run.to_llm_context(layout="xml")


def test_run_case_comparison_html() -> None:
    agent = MagicMock()
    agent.name = "a"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="qq")])
    html = run.case_comparison_html(0)
    assert "case_index=0" in html and "qq" in html


def test_run_metric_tool_prefixes() -> None:
    agent = MagicMock()
    agent.name = "x"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    m = MagicMock(spec=MetricTool)
    m.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.5}
    m.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[m])
    assert run.metric_tool_prefixes() == ["m1"]


def test_run_case_rows_dataframe() -> None:
    a1 = MagicMock()
    a1.name = "A"
    a2 = MagicMock()
    a2.name = "B"
    ard = AgentResponseData(input="q", output="x", steps=[])
    a1.run.return_value = _successful_run_result(ard)
    a2.run.return_value = _successful_run_result(ard)
    run = AgentEvaluationExecutor().evaluate([a1, a2], [EvalCase(query="q")])
    sub = run.case_rows(0)
    assert len(sub) == 2 and set(sub["agent_name"]) == {"A", "B"}


def test_run_plot_mean_metric_by_agent() -> None:
    pytest.importorskip("plotly")
    a1 = MagicMock()
    a1.name = "A"
    a2 = MagicMock()
    a2.name = "B"
    ard = AgentResponseData(input="q", output="o", steps=[])
    a1.run.return_value = _successful_run_result(ard)
    a2.run.return_value = _successful_run_result(ard)
    m = MagicMock(spec=MetricTool)
    m.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.2}
    m.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate([a1, a2], [EvalCase(query="q")], metrics=[m])
    fig = run.plot_mean_metric_by_agent("score", tool_prefix="m1")
    assert (fig.layout.title.text or "") != ""


def test_run_chatbot_ask_uses_model() -> None:
    """LLM chatbot composes context and forwards to Model.run."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="hello out", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    metric.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="qq")], metrics=[metric])

    model = MagicMock()
    model.params = [SimpleNamespace(name="data", required=True, data_type="text")]
    model.run.return_value = MagicMock()
    model.run.return_value.data = "Agent output mentions hello."

    bot = run.chatbot(model, max_context_chars=50_000)
    assert isinstance(bot, AgentEvaluationResultsChatbot)
    reply = bot.ask("What did the agent output?")
    assert "hello" in reply.lower()
    model.run.assert_called_once()
    kwargs = model.run.call_args.kwargs
    assert "data" in kwargs and "hello out" in kwargs["data"]  # inferred from model.params
    assert len(bot.conversation_history) == 2

    bot.reset_conversation()
    assert bot.conversation_history == []


def test_infer_prompt_input_field_name() -> None:
    m = MagicMock()
    m.params = []
    assert _infer_prompt_input_field_name(m) == "text"
    m.params = [SimpleNamespace(name="text", required=True, data_type="text")]
    assert _infer_prompt_input_field_name(m) == "text"
    m.params = [SimpleNamespace(name="data", required=True, data_type="text")]
    assert _infer_prompt_input_field_name(m) == "data"
    m.params = [
        SimpleNamespace(name="temperature", required=False, data_type="number"),
        SimpleNamespace(name="text", required=True, data_type="text"),
    ]
    assert _infer_prompt_input_field_name(m) == "text"


def test_run_chatbot_prompt_input_kw_text() -> None:
    run = AgentEvaluationRun(rows=[])
    model = MagicMock()
    model.run.return_value = MagicMock(data="ok")
    bot = run.chatbot(model, prompt_input_kw="text")
    assert bot.ask("hi?") == "ok"
    kwargs = model.run.call_args.kwargs
    assert "text" in kwargs and kwargs["text"].startswith("You are an analyst")


def test_run_plot_mean_metric_requires_prefix_when_ambiguous() -> None:
    pytest.importorskip("plotly")
    agent = MagicMock()
    agent.name = "x"
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    m1 = MagicMock(spec=MetricTool)
    m1.name = "m1"
    m2 = MagicMock(spec=MetricTool)
    m2.name = "m2"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.5}
    m1.measure.return_value = mr
    m2.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[m1, m2])
    with pytest.raises(ValidationError, match="Multiple metric"):
        run.plot_mean_metric_by_agent("score")


def test_run_metric_inner_key_is_numeric() -> None:
    a1 = MagicMock()
    a1.name = "A"
    ard = AgentResponseData(input="q", output="o", steps=[])
    a1.run.return_value = _successful_run_result(ard)
    m = MagicMock(spec=MetricTool)
    m.name = "m1"
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"label": "x"}
    m.measure.return_value = mr
    run = AgentEvaluationExecutor().evaluate(a1, [EvalCase(query="q")], metrics=[m])
    assert run.metric_inner_key_is_numeric("label", tool_prefix="m1") is False
    mr.validated_data = {"label": 0.5}
    run = AgentEvaluationExecutor().evaluate(a1, [EvalCase(query="q")], metrics=[m])
    assert run.metric_inner_key_is_numeric("label", tool_prefix="m1") is True


def test_run_plot_enum_and_plot_metric_by_agent_dispatch() -> None:
    pytest.importorskip("plotly")
    a1 = MagicMock()
    a1.name = "A"
    a2 = MagicMock()
    a2.name = "B"
    ard = AgentResponseData(input="q", output="o", steps=[])
    a1.run.return_value = _successful_run_result(ard)
    a2.run.return_value = _successful_run_result(ard)
    m = MagicMock(spec=MetricTool)
    m.name = "m1"
    results = [
        {"verdict": "pass"},
        {"verdict": "fail"},
    ]
    call = {"i": 0}

    def _measure(*args: object, **kwargs: object) -> MagicMock:
        mr = MagicMock()
        mr.status = "SUCCESS"
        mr.completed = True
        mr.validated_data = results[call["i"] % len(results)]
        call["i"] += 1
        return mr

    m.measure.side_effect = _measure
    run = AgentEvaluationExecutor().evaluate([a1, a2], [EvalCase(query="q")], metrics=[m])
    fig_enum = run.plot_enum_metric_by_agent("verdict", tool_prefix="m1")
    assert (fig_enum.layout.title.text or "") != ""
    fig_wrap = run.plot_metric_by_agent("verdict", tool_prefix="m1")
    assert (fig_wrap.layout.title.text or "") != ""

    mr_num = MagicMock()
    mr_num.status = "SUCCESS"
    mr_num.completed = True
    mr_num.validated_data = {"score": 0.8}
    m.measure.side_effect = None
    m.measure.return_value = mr_num
    run_num = AgentEvaluationExecutor().evaluate([a1, a2], [EvalCase(query="q")], metrics=[m])
    fig_num = run_num.plot_metric_by_agent("score", tool_prefix="m1")
    assert "Mean" in (fig_num.layout.title.text or "")


def test_create_dataset_from_csv_basic(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,reference\nq1,r1\nq2,\n", encoding="utf-8")
    cases = AgentEvaluationExecutor.create_dataset_from_csv(p)
    assert len(cases) == 2
    assert cases[0].query == "q1" and cases[0].reference == "r1"
    assert cases[1].query == "q2" and cases[1].reference is None


def test_create_dataset_from_csv_no_reference_column(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query\nq1\n", encoding="utf-8")
    cases = AgentEvaluationExecutor.create_dataset_from_csv(p)
    assert len(cases) == 1 and cases[0].reference is None


def test_create_dataset_from_csv_metadata_columns(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,id,note\na,1,hello\n", encoding="utf-8")
    cases = AgentEvaluationExecutor.create_dataset_from_csv(p, metadata_columns=["id", "note"])
    assert cases[0].metadata == {"id": 1, "note": "hello"}


def test_create_dataset_from_csv_reference_column_none(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,reference\nq,r\n", encoding="utf-8")
    cases = AgentEvaluationExecutor.create_dataset_from_csv(p, reference_column=None)
    assert cases[0].reference is None


def test_create_dataset_from_csv_custom_query_column(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("prompt\nhello\n", encoding="utf-8")
    cases = AgentEvaluationExecutor.create_dataset_from_csv(p, query_column="prompt")
    assert cases[0].query == "hello"


def test_create_dataset_from_csv_missing_query_column_raises(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("foo\nbar\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="query"):
        AgentEvaluationExecutor.create_dataset_from_csv(p)


def test_create_dataset_from_csv_empty_header_only(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query\n", encoding="utf-8")
    assert AgentEvaluationExecutor.create_dataset_from_csv(p) == []


def test_create_dataset_from_csv_empty_query_raises(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,reference\n  ,\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="Empty"):
        AgentEvaluationExecutor.create_dataset_from_csv(p)


def test_experiment_run_appends_and_cache_roundtrip(tmp_path: Path) -> None:
    """Experiment.run appends runs; cache load preserves rows and supports another run."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="out", steps=[])
    agent.run.return_value = _successful_run_result(ard)
    agent.to_dict.return_value = {"id": "agent-1", "name": "agent_a"}

    cache_dir = tmp_path / "exp_cache"
    ex = AgentEvaluationExecutor(cache_experiments=True, experiment_cache_dir=cache_dir)
    exp = ex.create_experiment(agent, [EvalCase(query="hello")], metadata={"label": "e1"})
    assert exp.id
    assert exp.agents_snapshot == [{"id": "agent-1", "name": "agent_a"}]
    assert exp.metadata == {"label": "e1"}

    r1 = exp.run()
    r2 = exp.run()
    assert len(exp.runs) == 2
    assert r1.id != r2.id
    assert r1.parent is exp and r2.parent is exp
    assert len(r1.results) == 1

    summaries = ex.list_cached_experiments()
    assert any(s.get("id") == exp.id for s in summaries)

    ex2 = AgentEvaluationExecutor(cache_experiments=True, experiment_cache_dir=cache_dir)
    loaded = ex2.load_cached_experiment(exp.id)
    assert len(loaded.runs) == 2
    assert loaded.agents_snapshot == exp.agents_snapshot
    r3 = loaded.run(agents=agent)
    assert len(loaded.runs) == 3

    loaded_again = ex2.load_cached_experiment(exp.id)
    assert len(loaded_again.runs) == 3


def test_experiment_cache_disabled_skips_write(tmp_path: Path) -> None:
    agent = MagicMock()
    agent.name = "a"
    agent.to_dict.return_value = {"id": "x"}
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    ex = AgentEvaluationExecutor(cache_experiments=False, experiment_cache_dir=tmp_path)
    exp = ex.create_experiment(agent, [EvalCase(query="q")])
    assert not list(tmp_path.glob("*.json"))
    exp.run()
    assert not list(tmp_path.glob("*.json"))


def test_experiment_local_cache_list_and_load(tmp_path: Path) -> None:
    store = ExperimentLocalCache(tmp_path)
    agent = MagicMock()
    agent.name = "n"
    agent.to_dict.return_value = {"id": "1"}
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    ex = AgentEvaluationExecutor(cache_experiments=True, experiment_cache_dir=tmp_path)
    exp = ex.create_experiment(agent, [EvalCase(query="x")])
    exp.run()
    listed = store.list_experiments()
    assert len(listed) >= 1
    got = store.load_experiment(str(exp.id), executor=ex)
    assert got.id == exp.id
    assert len(got.runs) == 1


def test_experiment_runs_comparison_dataframe_and_regression_plot(tmp_path: Path) -> None:
    """runs_comparison_dataframe and plot_runs_regression compare successive ExperimentRuns."""
    agent = MagicMock()
    agent.name = "agent_a"
    agent.to_dict.return_value = {"id": "agent-1"}
    ard = AgentResponseData(input="q", output="o", steps=[])

    costs: List[float] = []

    def run_side_effect(*args: Any, **kwargs: Any) -> MagicMock:
        mr = _successful_run_result(ard)
        mr.used_credits = 0.1 + 0.05 * len(costs)
        costs.append(mr.used_credits)
        return mr

    agent.run.side_effect = run_side_effect

    ex = AgentEvaluationExecutor(cache_experiments=False, experiment_cache_dir=tmp_path)
    exp = ex.create_experiment(agent, [EvalCase(query="hello")])
    assert isinstance(exp, Experiment)
    exp.run()
    exp.run()
    exp.run()

    df = exp.runs_comparison_dataframe()
    assert len(df) == 3
    assert EXPERIMENT_COMPARISON_COL_RUN_INDEX in df.columns
    assert list(df[EXPERIMENT_COMPARISON_COL_RUN_INDEX]) == [0, 1, 2]
    assert df["Total credits (sum)"].is_monotonic_increasing
    assert "Avg credits per evaluation row" in df.columns

    df_machine = exp.runs_comparison_dataframe(human_column_names=False)
    assert "total_cost" in df_machine.columns and "run_index" in df_machine.columns

    pytest.importorskip("plotly")
    fig = exp.plot_runs_regression(y="Total credits (sum)", show_trendline=True)
    assert fig.layout.title is not None
    assert len(fig.data) >= 2


def test_experiment_runs_comparison_includes_metric_pass_rate(tmp_path: Path) -> None:
    agent = MagicMock()
    agent.name = "agent_a"
    agent.to_dict.return_value = {"id": "agent-1"}
    ard = AgentResponseData(input="q", output="o", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    metric.threshold = 0.5
    mr = MagicMock()
    mr.status = "SUCCESS"
    mr.completed = True
    mr.validated_data = {"score": 0.9}
    metric.measure.return_value = mr

    ex = AgentEvaluationExecutor(cache_experiments=False, experiment_cache_dir=tmp_path)
    exp = ex.create_experiment(agent, [EvalCase(query="q")], metrics=[metric])
    exp.run()
    df = exp.runs_comparison_dataframe()
    assert "Pass rate (m1)" in df.columns
    assert float(df.iloc[0]["Pass rate (m1)"]) == 1.0
