"""Functional tests for Eval / Metric / Dataset / EvalCase and experiment diffing.

These were entirely untested end to end: the only usage was an untracked root
script against the dev backend. The tests build a local dataset, run an eval
against a saved agent with a real metric tool, fetch the structured results and
diff two runs of one experiment. The empty-dataset edge is covered too.
"""

import time
import uuid

import pytest

from aixplain.v2 import Dataset, EvalCase

# A seeded metric tool on the benchmarking workspace, used instead of creating
# one so the metric LLM path does not have to be guessed. Created metrics are
# covered by ``test_metric_create_round_trip`` below.
SEEDED_METRIC_ID = "aixplain-benchmarking/test-run-metric/aixplain"


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
def eval_metric(client):
    metric = client.Metric.get(SEEDED_METRIC_ID)
    metric.agent_response_data_fields = client.Metric.AgentResponseDataFields(output=True)
    return metric


@pytest.fixture
def two_case_dataset():
    return Dataset(
        name=f"eval-dataset-{uuid.uuid4().hex[:6]}",
        cases=[EvalCase(query="What is 2 + 2?"), EvalCase(query="What is 3 + 4?")],
    )


def _metric_prefix(metric):
    return metric.name or metric.id


def test_evaluate_returns_one_row_per_case(client, eval_agent, eval_metric, two_case_dataset):
    run = client.Eval(cache_experiments=False).evaluate(eval_agent, two_case_dataset, [eval_metric])

    assert len(run) == 2
    frame = run.to_dataframe()
    assert not frame.empty
    assert set(frame["query"]) == {"What is 2 + 2?", "What is 3 + 4?"}


def test_experiment_runs_and_diffs(client, eval_agent, eval_metric, two_case_dataset):
    experiment = client.Eval(cache_experiments=False).create_experiment(eval_agent, two_case_dataset, [eval_metric])

    baseline = experiment.run()
    candidate = experiment.run()

    assert len(experiment.runs) == 2
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


def test_metric_create_round_trip(client, eval_metric, resource_tracker):
    metric = client.Metric.create(
        name=f"Functional Metric {int(time.time())}-{uuid.uuid4().hex[:6]}",
        llm_path=eval_metric.llm_path,
        score_type="numeric",
        instruction="Rate how correct the answer is.",
        start_number=0,
        end_number=1,
    )
    resource_tracker.append(metric)

    fetched = client.Metric.get(metric.id)
    assert fetched.id == metric.id
    assert fetched.name == metric.name
