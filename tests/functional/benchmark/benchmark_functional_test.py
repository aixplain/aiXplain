import uuid
import pandas as pd
import json
from dotenv import load_dotenv

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


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


@pytest.fixture(scope="module", params=read_data(MODULE_FILE))
def module_input_map(request):
    return request.param


def test_run(run_input_map):
    model_list = [ModelFactory.get(model_id) for model_id in run_input_map["model_ids"]]
    dataset_list = [DatasetFactory.get(dataset_id) for dataset_id in run_input_map["dataset_ids"]]
    metric_list = [MetricFactory.get(metric_id) for metric_id in run_input_map["metric_ids"]]
    benchmark = BenchmarkFactory.create(f"SDK Benchmark Test {uuid.uuid4()}", dataset_list, model_list, metric_list)
    assert type(benchmark) is Benchmark
    benchmark_job = benchmark.start()
    assert type(benchmark_job) is BenchmarkJob


def test_module(module_input_map):
    benchmark = BenchmarkFactory.get(module_input_map["benchmark_id"])
    assert benchmark.id == module_input_map["benchmark_id"]
    benchmark_job = benchmark.job_list[0]
    assert benchmark_job.benchmark_id == module_input_map["benchmark_id"]
    job_status = benchmark_job.check_status()
    assert job_status in ["in_progress", "completed"]
    df = benchmark_job.download_results_as_csv(return_dataframe=True)
    assert type(df) is pd.DataFrame
