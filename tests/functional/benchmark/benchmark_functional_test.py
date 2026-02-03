import uuid
import pandas as pd
import json
from dotenv import load_dotenv
import time

load_dotenv()
from aixplain.factories import ModelFactory, DatasetFactory, MetricFactory, BenchmarkFactory
from aixplain.modules.benchmark import Benchmark
from aixplain.modules.benchmark_job import BenchmarkJob
from pathlib import Path

import pytest
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

TIMEOUT = 60 * 30
RUN_FILE = str(Path(r"tests/functional/benchmark/data/benchmark_test_run_data.json"))
MODULE_FILE = str(Path(r"tests/functional/benchmark/data/benchmark_module_test_data.json"))
RUN_WITH_PARAMETERS_FILE = str(Path(r"tests/functional/benchmark/data/benchmark_test_with_parameters.json"))


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


@pytest.fixture(scope="module", params=[(name, params) for name, params in read_data(RUN_WITH_PARAMETERS_FILE).items()])
def run_with_parameters_input_map(request):
    return request.param


@pytest.fixture(scope="module", params=read_data(MODULE_FILE))
def module_input_map(request):
    return request.param


def is_job_finshed(benchmark_job):
    time_taken = 0
    sleep_time = 15
    timeout = 15 * 60
    while True:
        if time_taken > timeout:
            break
        job_status = benchmark_job.check_status()
        if job_status == "in_progress":
            time.sleep(sleep_time)
            time_taken += sleep_time
        elif job_status == "completed":
            return True
        else:
            break
    return False


def assert_correct_results(benchmark_job):
    df = benchmark_job.download_results_as_csv(return_dataframe=True)
    assert type(df) is pd.DataFrame, "Couldn't download CSV"
    model_success_rate = (sum(df["Model_success"]) * 100) / len(df.index)
    assert model_success_rate > 80, f"Low model success rate ({model_success_rate})"
    metric_name = "BLEU by sacrebleu"
    mean_score = df[metric_name].mean()
    assert mean_score != 0, f"Zero Mean Score - Please check metric ({metric_name})"


@pytest.mark.parametrize("BenchmarkFactory", [BenchmarkFactory])
def test_create_and_run(run_input_map, BenchmarkFactory):
    model_list = [ModelFactory.get(model_id) for model_id in run_input_map["model_ids"]]
    dataset_list = [
        DatasetFactory.list(query=dataset_name)["results"][0] for dataset_name in run_input_map["dataset_names"]
    ]
    metric_list = [MetricFactory.get(metric_id) for metric_id in run_input_map["metric_ids"]]
    benchmark = BenchmarkFactory.create(f"SDK Benchmark Test {uuid.uuid4()}", dataset_list, model_list, metric_list)
    assert type(benchmark) is Benchmark, "Couldn't create benchmark"
    benchmark_job = benchmark.start()
    assert type(benchmark_job) is BenchmarkJob, "Couldn't start job"
    assert is_job_finshed(benchmark_job), "Job did not finish in time"
    assert_correct_results(benchmark_job)


@pytest.mark.parametrize("BenchmarkFactory", [BenchmarkFactory])
def test_create_and_run_with_parameters(run_with_parameters_input_map, BenchmarkFactory):
    name, params = run_with_parameters_input_map
    model_list = []
    for model_info in params["models_with_parameters"]:
        model = ModelFactory.get(model_info["model_id"])
        model.add_additional_info_for_benchmark(
            display_name=model_info["display_name"], configuration=model_info["configuration"]
        )
        model_list.append(model)
    dataset_list = [DatasetFactory.list(query=dataset_name)["results"][0] for dataset_name in params["dataset_names"]]
    metric_list = [MetricFactory.get(metric_id) for metric_id in params["metric_ids"]]
    benchmark = BenchmarkFactory.create(
        f"SDK Benchmark Test With Parameters({name}) {uuid.uuid4()}", dataset_list, model_list, metric_list
    )
    assert type(benchmark) is Benchmark, "Couldn't create benchmark"
    benchmark_job = benchmark.start()
    assert type(benchmark_job) is BenchmarkJob, "Couldn't start job"
    assert is_job_finshed(benchmark_job), "Job did not finish in time"
    assert_correct_results(benchmark_job)
