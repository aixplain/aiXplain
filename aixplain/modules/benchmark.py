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
from typing import List, Text
from aixplain.modules.asset import Asset
from aixplain.modules.benchmark_job import BenchmarkJob
from aixplain.modules.dataset import Dataset
from aixplain.modules.metric import Metric
from aixplain.modules.model import Model


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
