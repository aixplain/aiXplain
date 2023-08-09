__author__ = "shreyassharma"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: December 2nd 2022
Description:
    Benchmark Factory Class
"""

import logging
from typing import Dict, List, Optional, Text
import json
import pandas as pd
from pathlib import Path
from aixplain.modules import Dataset, Metric, Model
from aixplain.modules.benchmark_job import BenchmarkJob
from aixplain.modules.benchmark import Benchmark
from aixplain.factories.metric_factory import MetricFactory
from aixplain.factories.dataset_factory import DatasetFactory
from aixplain.factories.model_factory import ModelFactory
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry, save_file
from urllib.parse import urljoin
from warnings import warn


class BenchmarkFactory:
    """A static class for creating and managing the Benchmarking experience.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """

    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def _create_benchmark_job_from_response(cls, response: Dict) -> BenchmarkJob:
        """Converts response Json to 'BenchmarkJob' object

        Args:
            response (Dict): Json from API

        Returns:
            BenchmarkJob: Coverted 'BenchmarkJob' object
        """
        return BenchmarkJob(response["jobId"], response["status"], response["benchmark"]["id"])

    @classmethod
    def _get_benchmark_jobs_from_benchmark_id(cls, benchmark_id: Text) -> List[BenchmarkJob]:
        """Get list of benchmark jobs from benchmark id

        Args:
            benchmark_id (Text): ID of benchmark

        Returns:
            List[BenchmarkJob]: List of associated benchmark jobs
        """
        url = urljoin(cls.backend_url, f"sdk/benchmarks/{benchmark_id}/jobs")
        if cls.aixplain_key != "":
            headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        job_list = [cls._create_benchmark_job_from_response(job_info) for job_info in resp]
        return job_list

    @classmethod
    def _create_benchmark_from_response(cls, response: Dict) -> Benchmark:
        """Converts response Json to 'Benchmark' object

        Args:
            response (Dict): Json from API

        Returns:
            Benchmark: Coverted 'Benchmark' object
        """
        model_list = [ModelFactory().get(model_info["id"]) for model_info in response["model"]]
        dataset_list = [DatasetFactory().get(dataset_id) for dataset_id in response["datasets"]]
        metric_list = [MetricFactory().get(metric_info["id"]) for metric_info in response["metrics"]]
        job_list = cls._get_benchmark_jobs_from_benchmark_id(response["id"])
        return Benchmark(response["id"], response["name"], dataset_list, model_list, metric_list, job_list)

    @classmethod
    def get(cls, benchmark_id: str) -> Benchmark:
        """Create a 'Benchmark' object from Benchmark id

        Args:
            benchmark_id (Text): Benchmark ID of required Benchmark.

        Returns:
            Benchmark: Created 'Benchmark' object
        """
        resp = None
        try:
            url = urljoin(cls.backend_url, f"sdk/benchmarks/{benchmark_id}")
            if cls.aixplain_key != "":
                headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET Benchmark  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            benchmark = cls._create_benchmark_from_response(resp)
        except Exception as e:
            status_code = 400
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Benchmark Creation: Status {status_code} - {message}"
            else:
                message = f"Benchmark Creation: Unspecified Error"
            logging.error(f"Benchmark Creation Failed: {e}")
            raise Exception(f"Status {status_code}: {message}")
        return benchmark

    @classmethod
    def get_job(cls, job_id: Text) -> BenchmarkJob:
        """Create a 'BenchmarkJob' object from job id

        Args:
            job_id (Text): ID of the required BenchmarkJob.

        Returns:
            BenchmarkJob: Created 'BenchmarkJob' object
        """
        url = urljoin(cls.backend_url, f"sdk/benchmarks/jobs/{job_id}")
        if cls.aixplain_key != "":
            headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        benchmarkJob = cls._create_benchmark_job_from_response(resp)
        return benchmarkJob

    @classmethod
    def _validate_create_benchmark_payload(cls, payload):
        if len(payload["datasets"]) != 1:
            raise Exception("Please use exactly one dataset")
        if len(payload["metrics"]) == 0:
            raise Exception("Please use exactly one metric")
        if len(payload["model"]) == 0:
            raise Exception("Please use exactly one model")
        clean_metrics_info = {}
        for metric_info in payload["metrics"]:
            metric_id = metric_info["id"]
            if metric_id not in clean_metrics_info:
                clean_metrics_info[metric_id] = metric_info["configurations"]
            else:
                clean_metrics_info[metric_id] += metric_info["configurations"]
            clean_metrics_info[metric_id] = list(set(clean_metrics_info[metric_id]))
            if len(clean_metrics_info[metric_id]) == 0:
                clean_metrics_info[metric_id] = [[]]
        payload["metrics"] = [
            {"id": metric_id, "configurations": metric_config} for metric_id, metric_config in clean_metrics_info.items()
        ]
        return payload

    @classmethod
    def create(cls, name: str, dataset_list: List[Dataset], model_list: List[Model], metric_list: List[Metric]) -> Benchmark:
        """Creates a benchmark based on the information provided like name, dataset list, model list and score list.
        Note: This only creates a benchmark. It needs to run seperately using start_benchmark_job.

        Args:
            name (str): Unique Name of benchmark
            dataset_list (List[Dataset]): List of Datasets to be used for benchmarking
            model_list (List[Model]): List of Models to be used for benchmarking
            metric_list (List[Metric]): List of Metrics to be used for benchmarking

        Returns:
            Benchmark: _description_
        """
        payload = {}
        try:
            url = urljoin(cls.backend_url, f"sdk/benchmarks")
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            payload = {
                "name": name,
                "datasets": [dataset.id for dataset in dataset_list],
                "model": [model.id for model in model_list],
                "metrics": [{"id": metric.id, "configurations": metric.normalization_options} for metric in metric_list],
                "shapScores": [],
                "humanEvaluationReport": False,
                "automodeTraining": False,
            }
            clean_payload = cls._validate_create_benchmark_payload(payload)
            payload = json.dumps(clean_payload)
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()
            logging.info(f"Creating Benchmark Job: Status for {name}: {resp}")
            return cls.get(resp["id"])
        except Exception as e:
            error_message = f"Creating Benchmark Job: Error in Creating Benchmark with payload {payload} : {e}"
            logging.error(error_message, exc_info=True)
            return None

    @classmethod
    def list_normalization_options(cls, metric: Metric, model: Model) -> List[str]:
        """Get list of supported normalization options for a metric and model to be used in benchmarking

        Args:
            metric (Metric): Metric for which normalization options are to be listed
            model(Model): Model to be used in benchmarking

        Returns:
            List[str]: List of supported normalization options
        """
        try:
            url = urljoin(cls.backend_url, f"sdk/benchmarks/normalization-options")
            if cls.aixplain_key != "":
                headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            payload = json.dumps({"metricId": metric.id, "modelIds": [model.id]})
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()
            logging.info(f"Listing Normalization Options: Status of listing options: {resp}")
            normalization_options = [item["value"] for item in resp]
            return normalization_options
        except Exception as e:
            error_message = f"Listing Normalization Options: Error in getting Normalization Options: {e}"
            logging.error(error_message, exc_info=True)
            return []
