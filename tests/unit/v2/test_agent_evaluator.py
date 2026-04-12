"""Unit tests for AgentEvaluationExecutor and eval row aggregation."""

from unittest.mock import MagicMock

from aixplain.v2.agent import AgentResponseData
from aixplain.v2.agent_evaluator import AgentEvaluationExecutor, EvalCase, MetricTool
from aixplain.v2.exceptions import APIError


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

    df = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="hello")], metrics=[metric])

    assert len(df) == 1
    row = df.iloc[0]
    assert row["agent_run_failed"] == True  # noqa: E712
    assert row["status"] == "FAILED"
    assert row["completed"] == False  # noqa: E712
    assert "Operation failed" in row["error_message"]
    assert row["agent_error_type"] == "APIError"
    assert row["agent_error_details"] is not None
    assert row["output"] is None
    assert row["agent_response"] is None
    metric.measure.assert_not_called()
    assert row["quality__metric_skipped"] == True  # noqa: E712
    assert row["quality__metric_skip_reason"] == "agent_run_failed"


def test_metric_failure_records_metric_columns() -> None:
    """When measure raises, metric error columns are set without aborting the row."""
    agent = MagicMock()
    agent.name = "agent_a"
    ard = AgentResponseData(input="q", output="out", steps=[])
    agent.run.return_value = _successful_run_result(ard)

    metric = MagicMock(spec=MetricTool)
    metric.name = "m1"
    metric.measure.side_effect = ValueError("invalid json")

    df = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])

    assert len(df) == 1
    row = df.iloc[0]
    assert row["agent_run_failed"] == False  # noqa: E712
    assert row["m1__metric_status"] == "FAILED"
    assert row["m1__metric_completed"] == False  # noqa: E712
    assert "invalid json" in row["m1__metric_error"]
    assert row["m1__metric_error_type"] == "ValueError"


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

    df = AgentEvaluationExecutor().evaluate(agent, [EvalCase(query="q")], metrics=[metric])
    row = df.iloc[0]
    assert row["agent_run_failed"] == False  # noqa: E712
    assert row["output"] == "ans"
    assert row["m1__metric_status"] == "SUCCESS"
    assert row["m1__score"] == 0.9


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

    df = AgentEvaluationExecutor().evaluate(
        agent,
        [EvalCase(query="bad"), EvalCase(query="good")],
    )
    assert len(df) == 2
    assert df.iloc[0]["agent_run_failed"] == True  # noqa: E712
    assert df.iloc[1]["agent_run_failed"] == False  # noqa: E712
    assert df.iloc[1]["output"] == "ok"
