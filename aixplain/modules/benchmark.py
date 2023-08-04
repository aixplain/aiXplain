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
Date: October 25th 2022
Description:
    Benchmark Class
"""
import logging
from typing import List, Text, Dict, Optional
from aixplain.utils import config
from aixplain.modules import Asset, Dataset, Metric, Model
from aixplain.modules.benchmark_job import BenchmarkJob
from urllib.parse import urljoin
import pandas as pd
from pathlib import Path
from aixplain.utils.file_utils import _request_with_retry, save_file


class Benchmark(Asset):
    """Benchmark is a powerful tool for benchmarking machine learning models and evaluating their performance on specific tasks.
    It represents a collection of Models, Datasets and Metrics to run associated Benchmark Jobs.

    Attributes:
        id (str): ID of the Benchmark.
        name (str): Name of the Benchmark.
        model_list (List[Model]): List of Models to be used for benchmarking.
        dataset_list (List[Dataset]): List of Datasets to be used for benchmarking.
        metric_list (List[Metric]): List of Metrics to be used for benchmarking.
        job_list (List[BenchmarkJob]): List of associated Benchmark Jobs.
        additional_info (dict): Any additional information to be saved with the Benchmark.
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        dataset_list: List[Dataset],
        model_list: List[Model],
        metric_list: List[Metric],
        job_list: List[BenchmarkJob],
        description: Text = "",
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        **additional_info
    ) -> None:
        """Create a Benchmark with the necessary information.

        Args:
            id (Text): ID of the Benchmark.
            name (Text): Name of the Benchmark.
            model_list (List[Model]): List of Models to be used for benchmarking
            dataset_list (List[Dataset]): List of Datasets to be used for benchmarking
            metric_list (List[Metric]): List of Metrics to be used for benchmarking
            job_list (List[BenchmarkJob]): List of associated Benchmark Jobs
            supplier (Text, optional): author of the Benchmark. Defaults to "aiXplain".
            version (Text, optional): Benchmark version. Defaults to "1.0".
            **additional_info: Any additional Benchmark info to be saved
        """
        super().__init__(id, name, description, supplier, version)
        self.model_list = model_list
        self.dataset_list = dataset_list
        self.metric_list = metric_list
        self.job_list = job_list
        self.additional_info = additional_info
        self.backend_url = config.BACKEND_URL
        self.api_key = config.TEAM_API_KEY
        self.aixplain_key = config.AIXPLAIN_API_KEY

    def __repr__(self) -> str:
        return f"<Benchmark {self.name}>"

    
    def start(self) -> BenchmarkJob:
        """Starts a new benchmark job(run)  for the current benchmark

        Returns:
            BenchmarkJob: Benchmark Job that just got started
        """
        benhchmark_id = None
        try:
            benhchmark_id = self.id
            url = urljoin(self.backend_url, f"sdk/benchmarks/{benhchmark_id}/start")
            headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("post", url, headers=headers)
            response = r.json()
            resp = BenchmarkJob._fetch_current_response(response["jobId"])
            logging.info(f"Starting Benchmark Job: Status for {benhchmark_id}: {resp}")
            return BenchmarkJob(resp["jobId"], resp["status"], resp["benchmark"]["id"])
        except Exception as e:
            error_message = f"Starting Benchmark Job: Error in Creating Benchmark {benhchmark_id} : {e}"
            logging.error(error_message, exc_info=True)
            return None