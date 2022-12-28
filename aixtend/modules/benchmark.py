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
from typing import List
from aixtend.modules.asset import Asset
from aixtend.modules.benchmark_job import BenchmarkJob
from aixtend.modules.dataset import Dataset
from aixtend.modules.metric import Metric
from aixtend.modules.model import Model
from aixtend.utils.file_utils import save_file, _request_with_retry


class Benchmark(Asset):
    def __init__(
        self,
        id: str,
        name: str,
        model_list: List[Model],
        dataset_list: List[Dataset],
        metric_list: List[Metric],
        job_list: List[BenchmarkJob],
        description: str = "",
        **additional_info
    ) -> None:
        """Create a Benchmark with the necessary information.

        Args:
            id (str): ID of the Benchmark.
            name (str): Name of the Benchmark.
            model_list (List[Model]): List of Models to be used for benchmarking
            dataset_list (List[Dataset]): List of Datasets to be used for benchmarking
            metric_list (List[Metric]): List of Metrics to be used for benchmarking
            job_list (List[BenchmarkJob]): List of associated Benchmark Jobs
            **additional_info: Any additional dataset info to be saved
        """
        super().__init__(id, name, description)
        self.model_list = model_list
        self.dataset_list = dataset_list
        self.metric_list = metric_list
        self.job_list = job_list
        self.additional_info = additional_info
