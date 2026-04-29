import requests_mock
import pytest
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.factories import BenchmarkFactory
from aixplain.modules.model import Model


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
