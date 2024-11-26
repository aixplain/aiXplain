import requests_mock
import pytest
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.factories import MetricFactory, BenchmarkFactory
from aixplain.modules.model import Model
from aixplain.modules.dataset import Dataset


def test_create_benchmark_error_response():
    metric_list = [MetricFactory.get("66df3e2d6eb56336b6628171")]
    with requests_mock.Mocker() as mock:
        name = "test-benchmark"
        dataset_list = [
            Dataset(
                id="dataset1",
                name="Dataset 1",
                description="Test dataset",
                function="test_func",
                source_data="src",
                target_data="tgt",
                onboard_status="onboarded",
            )
        ]
        model_list = [
            Model(id="model1", name="Model 1", description="Test model", supplier="Test supplier", cost=10, version="v1")
        ]

        url = urljoin(config.BACKEND_URL, "sdk/benchmarks")
        headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}

        error_response = {"statusCode": 400, "message": "Invalid request"}
        mock.post(url, headers=headers, json=error_response, status_code=400)

        with pytest.raises(Exception) as excinfo:
            BenchmarkFactory.create(name=name, dataset_list=dataset_list, model_list=model_list, metric_list=metric_list)

        assert "Benchmark Creation Error: Status 400 - {'statusCode': 400, 'message': 'Invalid request'}" in str(excinfo.value)


def test_get_benchmark_error():
    with requests_mock.Mocker() as mock:
        benchmark_id = "test-benchmark-id"
        url = urljoin(config.BACKEND_URL, f"sdk/benchmarks/{benchmark_id}")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"statusCode": 404, "message": "Benchmark not found"}
        mock.get(url, headers=headers, json=error_response, status_code=404)

        with pytest.raises(Exception) as excinfo:
            BenchmarkFactory.get(benchmark_id)

        assert "Benchmark GET Error: Status 404 - {'statusCode': 404, 'message': 'Benchmark not found'}" in str(excinfo.value)


def test_list_normalization_options_error():
    metric = MetricFactory.get("66df3e2d6eb56336b6628171")
    with requests_mock.Mocker() as mock:
        model = Model(id="model1", name="Test Model", description="Test model", supplier="Test supplier", cost=10, version="v1")

        url = urljoin(config.BACKEND_URL, "sdk/benchmarks/normalization-options")
        headers = {"Authorization": f"Token {config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}

        error_response = {"message": "Internal Server Error"}
        mock.post(url, headers=headers, json=error_response, status_code=500)

        with pytest.raises(Exception) as excinfo:
            BenchmarkFactory.list_normalization_options(metric, model)

        assert "Error listing normalization options: Status 500 - {'message': 'Internal Server Error'}" in str(excinfo.value)
