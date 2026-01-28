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
from typing import Dict, List, Text, Any, Tuple
import json
from aixplain.enums.supplier import Supplier
from aixplain.modules import Dataset, Metric, Model
from aixplain.modules.benchmark_job import BenchmarkJob
from aixplain.modules.benchmark import Benchmark
from aixplain.factories.metric_factory import MetricFactory
from aixplain.factories.dataset_factory import DatasetFactory
from aixplain.factories.model_factory import ModelFactory
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin


class BenchmarkFactory:
    """Factory class for creating and managing benchmarks in the aiXplain platform.

    This class provides functionality for creating benchmarks, managing benchmark jobs,
    retrieving results, and configuring normalization options. Benchmarks can be used
    to evaluate and compare multiple models using specified datasets and metrics.

    Attributes:
        backend_url (str): Base URL for the aiXplain backend API.
    """

    backend_url = config.BACKEND_URL

    @classmethod
    def _create_benchmark_job_from_response(cls, response: Dict) -> BenchmarkJob:
        """Convert API response into a BenchmarkJob object.

        Args:
            response (Dict): API response containing:
                - jobId: Unique job identifier
                - status: Current job status
                - benchmark: Dictionary containing benchmark information

        Returns:
            BenchmarkJob: Instantiated benchmark job object.
        """
        return BenchmarkJob(response["jobId"], response["status"], response["benchmark"]["id"])

    @classmethod
    def _get_benchmark_jobs_from_benchmark_id(cls, benchmark_id: Text, api_key: str = None) -> List[BenchmarkJob]:
        """Get list of benchmark jobs from benchmark id

        Args:
            benchmark_id (Text): Unique identifier of the benchmark.

        Returns:
            List[BenchmarkJob]: List of benchmark job objects associated with
                the specified benchmark.
        """
        url = urljoin(cls.backend_url, f"sdk/benchmarks/{benchmark_id}/jobs")
        api_key = api_key or config.TEAM_API_KEY
        headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        job_list = [cls._create_benchmark_job_from_response(job_info) for job_info in resp]
        return job_list

    @classmethod
    def _create_benchmark_from_response(cls, response: Dict, api_key: str = None) -> Benchmark:
        """Converts response Json to 'Benchmark' object

        Args:
            response (Dict): API response containing:
                - id: Benchmark identifier
                - name: Benchmark name
                - model: List of model configurations
                - datasets: List of dataset IDs
                - metrics: List of metric configurations

        Returns:
            Benchmark: Instantiated benchmark object with all components loaded.
        """
        model_list = [ModelFactory().get(model_info["id"], api_key=api_key) for model_info in response["model"]]
        dataset_list = [DatasetFactory().get(dataset_id, api_key=api_key) for dataset_id in response["datasets"]]
        metric_list = [MetricFactory().get(metric_info["id"], api_key=api_key) for metric_info in response["metrics"]]
        job_list = cls._get_benchmark_jobs_from_benchmark_id(response["id"], api_key=api_key)
        return Benchmark(response["id"], response["name"], dataset_list, model_list, metric_list, job_list)

    @classmethod
    def get(cls, benchmark_id: str, api_key: str = None) -> Benchmark:
        """Create a 'Benchmark' object from Benchmark id

        Args:
            benchmark_id (str): Unique identifier of the benchmark to retrieve.

        Returns:
            Benchmark: Retrieved benchmark object with all components loaded.

        Raises:
            Exception: If:
                - Benchmark ID is invalid
                - Authentication fails
                - Service is unavailable
        """
        resp = None
        api_key = api_key or config.TEAM_API_KEY
        try:
            url = urljoin(cls.backend_url, f"sdk/benchmarks/{benchmark_id}")
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET Benchmark  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()

        except Exception as e:
            status_code = 400
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Benchmark Creation: Status {status_code} - {message}"
            else:
                message = "Benchmark Creation: Unspecified Error"
            logging.error(f"Benchmark Creation Failed: {e}")
            raise Exception(f"Status {status_code}: {message}")
        if 200 <= r.status_code < 300:
            benchmark = cls._create_benchmark_from_response(resp, api_key=api_key)
            logging.info(f"Benchmark {benchmark_id} retrieved successfully.")
            return benchmark
        else:
            error_message = f"Benchmark GET Error: Status {r.status_code} - {resp}"
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def get_job(cls, job_id: Text, api_key: str = None) -> BenchmarkJob:
        """Create a 'BenchmarkJob' object from job id

        Args:
            job_id (Text): Unique identifier of the benchmark job to retrieve.

        Returns:
            BenchmarkJob: Retrieved benchmark job object with its current status.

        Raises:
            Exception: If the job ID is invalid or the request fails.
        """
        api_key = api_key or config.TEAM_API_KEY
        url = urljoin(cls.backend_url, f"sdk/benchmarks/jobs/{job_id}")
        headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        benchmarkJob = cls._create_benchmark_job_from_response(resp)
        return benchmarkJob

    @classmethod
    def _validate_create_benchmark_payload(cls, payload):
        if len(payload["datasets"]) != 1:
            raise Exception("Please use exactly one dataset")
        if len(payload["metrics"]) == 0:
            raise Exception("Please use at least one metric")
        if len(payload["model"]) == 0 and payload.get("models", None) is None:
            raise Exception("Please use at least one model")
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
    def _reformat_model_list(cls, model_list: List[Model]) -> Tuple[List[Any], List[Any]]:
        """Reformat a list of models for the benchmark creation API.

        This method separates models into two lists based on whether they have
        additional configuration information.

        Args:
            model_list (List[Model]): List of models to be used in the benchmark.

        Returns:
            Tuple[List[Any], List[Any]]: A tuple containing:
                - List of model IDs for models without additional parameters
                - List of model configurations for models with parameters, or None
                  if no models have parameters

        Raises:
            Exception: If some models have additional info and others don't.
        """
        model_list_without_parms, model_list_with_parms = [], []
        for model in model_list:
            if "displayName" in model.additional_info:
                model_list_with_parms.append(
                    {
                        "id": model.id,
                        "displayName": model.additional_info["displayName"],
                        "configurations": json.dumps(model.additional_info["configuration"]),
                    }
                )
            else:
                model_list_without_parms.append(model.id)
        if len(model_list_with_parms) > 0:
            if len(model_list_without_parms) > 0:
                raise Exception("Please provide additional info for all models or for none of the models")
        else:
            model_list_with_parms = None
        return model_list_without_parms, model_list_with_parms

    @classmethod
    def create(
        cls,
        name: str,
        dataset_list: List[Dataset],
        model_list: List[Model],
        metric_list: List[Metric],
    ) -> Benchmark:
        """Create a new benchmark configuration.

        This method creates a new benchmark that can be used to evaluate and compare
        multiple models using specified datasets and metrics. Note that this only
        creates the benchmark configuration - you need to run it separately using
        start_benchmark_job.

        Args:
            name (str): Unique name for the benchmark.
            dataset_list (List[Dataset]): List of datasets to use for evaluation.
                Currently only supports a single dataset.
            model_list (List[Model]): List of models to evaluate. All models must
                either have additional configuration info or none should have it.
            metric_list (List[Metric]): List of metrics to use for evaluation.
                Must provide at least one metric.

        Returns:
            Benchmark: Created benchmark object ready for execution.

        Raises:
            Exception: If:
                - No dataset is provided or multiple datasets are provided
                - No metrics are provided
                - No models are provided
                - Model configuration is inconsistent
                - Request fails or returns an error
        """
        payload = {}
        try:
            url = urljoin(cls.backend_url, "sdk/benchmarks")
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
            model_list_without_parms, model_list_with_parms = cls._reformat_model_list(model_list)
            payload = {
                "name": name,
                "datasets": [dataset.id for dataset in dataset_list],
                "metrics": [{"id": metric.id, "configurations": metric.normalization_options} for metric in metric_list],
                "model": model_list_without_parms,
                "shapScores": [],
                "humanEvaluationReport": False,
                "automodeTraining": False,
            }
            if model_list_with_parms is not None:
                payload["models"] = model_list_with_parms
            clean_payload = cls._validate_create_benchmark_payload(payload)
            payload = json.dumps(clean_payload)
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()

        except Exception as e:
            error_message = f"Creating Benchmark Job: Error in Creating Benchmark with payload {payload} : {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)

        if 200 <= r.status_code < 300:
            logging.info(f"Benchmark {name} created successfully.")
            return cls.get(resp["id"])
        else:
            error_message = f"Benchmark Creation Error: Status {r.status_code} - {resp}"
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def list_normalization_options(cls, metric: Metric, model: Model) -> List[str]:
        """List supported normalization options for a metric-model pair.

        This method retrieves the list of normalization options that can be used
        when evaluating a specific model with a specific metric in a benchmark.

        Args:
            metric (Metric): Metric to get normalization options for.
            model (Model): Model to check compatibility with.

        Returns:
            List[str]: List of supported normalization option identifiers.

        Raises:
            Exception: If:
                - Metric or model is invalid
                - Request fails
                - Service is unavailable
        """
        try:
            url = urljoin(cls.backend_url, "sdk/benchmarks/normalization-options")
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = json.dumps({"metricId": metric.id, "modelIds": [model.id]})
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()

        except Exception as e:
            error_message = f"Listing Normalization Options: Error in getting Normalization Options: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)

        if 200 <= r.status_code < 300:
            logging.info("Listing Normalization Options: ")
            normalization_options = [item["value"] for item in resp]
            return normalization_options
        else:
            error_message = f"Error listing normalization options: Status {r.status_code} - {resp}"
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def get_benchmark_job_scores(cls, job_id: Text) -> Any:
        """Retrieve and format benchmark job scores.

        This method fetches the scores from a benchmark job and formats them into
        a pandas DataFrame, with model names properly formatted to include supplier
        and version information.

        Args:
            job_id (Text): Unique identifier of the benchmark job.

        Returns:
            pandas.DataFrame: DataFrame containing benchmark scores with formatted
                model names.

        Raises:
            Exception: If the job ID is invalid or the request fails.
        """

        def __get_model_name(model_id):
            model = ModelFactory.get(model_id)
            supplier = str(model.supplier)
            try:
                if isinstance(supplier, Supplier):
                    name = f"{supplier.name}"
                else:
                    name = f"{eval(supplier)['name']}"
            except Exception as e:
                logging.error(f"{e}")
                name = f"{supplier}"
            if model.version is not None:
                name = f"{name}({model.version})"
            return name

        benchmarkJob = cls.get_job(job_id)
        scores_df = benchmarkJob.get_scores()
        scores_df["Model"] = scores_df["Model"].apply(lambda x: __get_model_name(x))
        return scores_df
