__author__='shreyassharma'

import json
import pytest
import requests_mock
from pathlib import Path
import pandas as pd
from aixplain.utils import config

from aixplain.factories.benchmark_factory import BenchmarkFactory, ModelFactory, DatasetFactory, MetricFactory

FIXED_HEADER = {
    'Authorization': f"Token {config.TEAM_API_KEY}",
    'Content-Type': 'application/json'
}

def __get_asset_factory(asset_name):
    if asset_name == "model":
        AssetFactory = ModelFactory
    elif asset_name == "dataset":
        AssetFactory = DatasetFactory
    elif asset_name == "metric":
        AssetFactory = MetricFactory
    return AssetFactory

def __mock_benchmark_create_dependecies(mock, asset_id):
    asset_list = ["model", "metric", "dataset"]
    url_dict = {
        "model" : f"{config.BENCHMARKS_BACKEND_URL}/sdk/inventory/models/{asset_id}",
        "metric": f"{config.BENCHMARKS_BACKEND_URL}/sdk/scores/{asset_id}",
        "dataset": f"{config.BENCHMARKS_BACKEND_URL}/sdk/datasets/{asset_id}",
    }
    for asset_name in asset_list:
        url = url_dict[asset_name]
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json = json.load(f)[asset_name]
        mock.get( url, headers=FIXED_HEADER, json=mock_json)
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json = json.load(f)['benchmarkJob']
        url_benchmarkJobs = f"{config.BENCHMARKS_BACKEND_URL}/sdk/benchmarks/{asset_id}/jobs"
        mock.get( url_benchmarkJobs, headers=FIXED_HEADER, json=[mock_json])

        url_benchmark = f"{config.BENCHMARKS_BACKEND_URL}/sdk/benchmarks/{asset_id}"
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json = json.load(f)['benchmark']
        mock.get( url_benchmark, headers=FIXED_HEADER, json=mock_json)

        url_benchmarkJob = f"{config.BENCHMARKS_BACKEND_URL}/sdk/benchmarks/jobs/{asset_id}"
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json = json.load(f)['benchmarkJob']
        mock.get( url_benchmarkJob, headers=FIXED_HEADER, json=mock_json)



def test_benchmark_assets_creation_from_id_with_updation():
    asset_id = "test_asset_id"
    with requests_mock.Mocker() as mock:
        __mock_benchmark_create_dependecies(mock, asset_id)

        benchmark = BenchmarkFactory.create_asset_from_id(asset_id)
        benchmarkJob = BenchmarkFactory.create_asset_from_id(asset_id)

        newBenchmark = BenchmarkFactory.update_benchmark_info(benchmark)
        newbenchmarkJob = BenchmarkFactory.update_benchmark_job_info(benchmarkJob)
    assert benchmark.get_asset_info()['id'] == asset_id
    assert benchmarkJob.get_asset_info()['id'] == asset_id
    assert benchmark.id == newBenchmark.id
    assert benchmarkJob.id == newbenchmarkJob.id


def test_create_benchmark_with_assets():
    asset_id = "test_asset_id"
    asset_name = "test_asset_name"
    asset_list = ["dataset", "model", "metric"]
    benchmark_creation_params = [asset_name]
    with requests_mock.Mocker() as mock:
        __mock_benchmark_create_dependecies(mock, asset_id)
        for asset_name in asset_list:
            AssetFactory = __get_asset_factory(asset_name)
            asset = AssetFactory.create_asset_from_id(asset_id)
            benchmark_creation_params.append([asset])

        url = f"{config.BENCHMARKS_BACKEND_URL}/sdk/benchmarks"
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json = json.load(f)['benchmark']
        mock.post(url, headers=FIXED_HEADER, json=mock_json)
        benchmark = BenchmarkFactory.create_benchmark(*benchmark_creation_params)
    assert benchmark.id == asset_id


def test_start_benchmark_job():
    asset_id = "test_asset_id"
    with requests_mock.Mocker() as mock:
        __mock_benchmark_create_dependecies(mock, asset_id)
        url = f"{config.BENCHMARKS_BACKEND_URL}/sdk/benchmarks/{asset_id}/start"
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            mock_json = json.load(f)['benchmarkJob']
        mock.post(url, headers=FIXED_HEADER, json=mock_json)
        benchmark = BenchmarkFactory.create_asset_from_id(asset_id)
        benchmarkJob = BenchmarkFactory.start_benchmark_job(benchmark)
    
    assert benchmarkJob.parentBenchmarkId == benchmark.id


def test_download_benchmark_results():
    asset_id = "test_asset_id"
    with requests_mock.Mocker() as mock:
        __mock_benchmark_create_dependecies(mock, asset_id)
        benchmarkJob = BenchmarkFactory.create_asset_from_id(asset_id)
        with open(Path("tests/mock_responses/get_asset_info_responses.json")) as f:
            download_url = json.load(f)['benchmarkJob']['reportUrl']
        dummy_result_path = Path("tests/mock_responses/dummy_result.csv")
        with open(dummy_result_path, "rb") as f:
            dummy_content = f.read()
        mock.get(download_url, headers=FIXED_HEADER, content=dummy_content)
        result_path_without_save_path = BenchmarkFactory.download_results_as_csv(benchmarkJob)
        result_path_with_save_path = BenchmarkFactory.download_results_as_csv(benchmarkJob, "test_save_results.csv")
        result_df_without_save_path = BenchmarkFactory.download_results_as_csv(benchmarkJob, returnDataFrame=True)
    
    with open(result_path_without_save_path, 'rb') as f:
        result_path_without_save_path_content = f.read()
    Path(result_path_without_save_path).unlink()
    with  open(result_path_with_save_path, 'rb') as f:
        result_path_with_save_path_content = f.read()
    Path(result_path_with_save_path).unlink()
    assert dummy_content == result_path_without_save_path_content
    assert dummy_content == result_path_with_save_path_content
    assert pd.read_csv(dummy_result_path).equals(result_df_without_save_path)

    


        


