"""Functional tests for Eval / Metric / Dataset / EvalCase and experiment diffing.

These were entirely untested end to end: the only usage was an ad-hoc
root-level script outside ``testpaths``, deleted in ENG-3686. The tests build a local
dataset, run an eval against a saved agent with a metric this module creates,
fetch the structured results and diff two runs of one experiment. The
empty-dataset edge is covered too.

``Eval.evaluate`` records agent and metric exceptions as ``FAILED`` rows instead
of raising, so every run is checked row by row: a row count alone would pass
with every agent run and every metric call broken.
"""

import time
import uuid

import pytest

from aixplain.v2 import Dataset, EvalCase


@pytest.fixture(scope="module")
def eval_agent(client, module_resource_tracker):
    agent = client.Agent(
        name=f"Eval Test Agent {int(time.time())}-{uuid.uuid4().hex[:6]}",
        instructions="Answer every question with a single number, no prose.",
    )
    agent.save()
    module_resource_tracker.append(agent)
    return agent


@pytest.fixture(scope="module")
def eval_metric(client, module_resource_tracker):
    """A numeric 0-1 metric owned by this module.

    Created rather than fetched, so the module does not depend on a seeded asset
    existing on every backend it runs against, and numeric, so ``Experiment.diff``
    can compare its scores without a ``categorical_order``.
    """
    metric = client.Metric.create(
        name=f"Eval Test Metric {int(time.time())}-{uuid.uuid4().hex[:6]}",
        llm_path=client.Agent.DEFAULT_LLM,
        score_type="numeric",
        instruction="Rate how correct the answer is to the question.",
        start_number=0,
        end_number=1,
    )
    module_resource_tracker.append(metric)
    metric.agent_response_data_fields = client.Metric.AgentResponseDataFields(query=True, output=True)
    return metric


@pytest.fixture
def two_case_dataset():
    return Dataset(
        name=f"eval-dataset-{uuid.uuid4().hex[:6]}",
        cases=[EvalCase(query="What is 2 + 2?"), EvalCase(query="What is 3 + 4?")],
    )


def _metric_prefix(metric):
    return metric.name or metric.id


def _assert_every_row_succeeded(run, metric):
    """Every agent run succeeded and the metric scored every row."""
    frame = run.to_dataframe()
    prefix = _metric_prefix(metric)

    failed = frame[(frame["status"] != "SUCCESS") | frame["agent_run_failed"]]
    assert failed.empty, failed[["query", "status", "error_message"]].to_dict("records")

    score, metric_status = f"{prefix}__score", f"{prefix}__metric_status"
    assert score in frame.columns, f"no {score!r} column in {list(frame.columns)}"
    assert frame[score].notna().all(), frame[score].tolist()
    metric_failed = frame[frame[metric_status] == "FAILED"]
    assert metric_failed.empty, metric_failed.filter(like=prefix).to_dict("records")


def test_evaluate_returns_one_successful_row_per_case(client, eval_agent, eval_metric, two_case_dataset):
    run = client.Eval(cache_experiments=False).evaluate(eval_agent, two_case_dataset, [eval_metric])

    assert len(run) == 2
    assert set(run.to_dataframe()["query"]) == {"What is 2 + 2?", "What is 3 + 4?"}
    _assert_every_row_succeeded(run, eval_metric)


def test_experiment_runs_and_diffs(client, eval_agent, eval_metric, two_case_dataset):
    experiment = client.Eval(cache_experiments=False).create_experiment(eval_agent, two_case_dataset, [eval_metric])

    baseline = experiment.run()
    candidate = experiment.run()

    assert len(experiment.runs) == 2
    _assert_every_row_succeeded(baseline.results, eval_metric)
    _assert_every_row_succeeded(candidate.results, eval_metric)
    diff = experiment.diff(
        baseline=baseline,
        candidate=candidate,
        metric_prefix=_metric_prefix(eval_metric),
    )
    assert isinstance(diff.summary(), str)
    assert len(diff.regressions) + len(diff.improvements) + len(diff.unchanged) == 2


def test_empty_dataset_yields_an_empty_run(client, eval_agent, eval_metric):
    run = client.Eval(cache_experiments=False).evaluate(eval_agent, Dataset(name="empty", cases=[]), [eval_metric])

    assert len(run) == 0


def test_metric_create_round_trip(client, resource_tracker):
    metric = client.Metric.create(
        name=f"Functional Metric {int(time.time())}-{uuid.uuid4().hex[:6]}",
        llm_path=client.Agent.DEFAULT_LLM,
        score_type="numeric",
        instruction="Rate how correct the answer is.",
        start_number=0,
        end_number=1,
    )
    resource_tracker.append(metric)

    fetched = client.Metric.get(metric.id)
    assert fetched.id == metric.id
    assert fetched.name == metric.name
