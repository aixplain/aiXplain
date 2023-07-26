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
from urllib.parse import urljoin
import pandas as pd
from pathlib import Path
from aixplain.utils.file_utils import _request_with_retry, save_file



class BenchmarkJob:
    """ "Benchmark Job Represents a single run of an already created Benchmark.

    Attributes:
        id (str): ID of the Benchmark Job.
        status (str): Status of the Benchmark Job.
        parentBenchmarkId (str): ID of the associated parent Benchmark.
        additional_info (dict): Any additional information to be saved with the Benchmark Job.

    """

    def __init__(self, id: Text, status: Text, parentBenchmarkId: Text, **additional_info) -> None:
        """Create a Benchmark Job with the necessary information. Each Job is a run of a parent Benchmark

        Args:
            id (Text): ID of the Benchmark Job
            status (Text): Status of the Benchmark Job
            parentBenchmarkId (Text): ID of the associated parent Benchmark
            **additional_info: Any additional Benchmark Job info to be saved
        """
        self.id = id
        self.status = status
        self.parentBenchmarkId = parentBenchmarkId
        self.additional_info = additional_info

    @classmethod
    def _create_benchmark_job_from_response(cls, response: Dict):
        return BenchmarkJob(response["jobId"], response["status"], response["benchmark"]["id"])
    
    @classmethod
    def _fetch_current_response(cls, job_id: Text) -> dict:
        url = urljoin(config.BACKEND_URL, f"sdk/benchmarks/jobs/{job_id}")
        if  config.AIXPLAIN_API_KEY != "":
            headers = {"x-aixplain-key": f"{config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        return resp
    
    def _update_from_response(self, response: dict):
        self.status = response['status']

    def __repr__(self) -> str:
        return f"<Benchmark Job({self.id})>"
    
    def check_status(self):
        response = self._fetch_current_response(self.id)
        self._update_from_response(response)
        return self.status
    
    def download_results_as_csv(self, save_path: Optional[Text] = None, returnDataFrame: Optional[bool] = False):
        """Get the results of the benchmark job in a CSV format.
        The results can either be downloaded locally or returned in the form of pandas.DataFrame.


        Args:
            save_path (Text, optional): Path to save the CSV if returnDataFrame is False. If None, a ranmdom path is generated. defaults to None.
            returnDataFrame (bool, optional): If True, the result is returned as pandas.DataFrame else saved as a CSV file. defaults to False.

        Returns:
            str/pandas.DataFrame: results as path of locally saved file if returnDataFrame is False else as a pandas dataframe
        """
        try:
            resp = self._fetch_current_response(self.id)
            logging.info(f"Downloading Benchmark Results: Status of downloading results for {self.id}: {resp}")
            if "reportUrl" not in resp:
                logging.error(
                    f"Downloading Benchmark Results: Can't get download results as they aren't generated yet. Please wait for a while."
                )
                return None
            csv_url = resp["reportUrl"]
            if returnDataFrame:
                downloaded_path = save_file(csv_url, save_path)
                df = pd.read_csv(downloaded_path)
                if save_path is None:
                    Path(downloaded_path).unlink()
                return df
            else:
                downloaded_path = save_file(csv_url, save_path)
                return downloaded_path
        except Exception as e:
            error_message = f"Downloading Benchmark Results: Error in Downloading Benchmark Results : {e}"
            logging.error(error_message)
            raise Exception(error_message)


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

    def __repr__(self) -> str:
        return f"<Metric {self.name}>"

    
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
            resp = r.json()
            logging.info(f"Starting Benchmark Job: Status for {benhchmark_id}: {resp}")
            return BenchmarkJob(resp["jobId"], resp["status"], resp["benchmark"]["id"])
        except Exception as e:
            error_message = f"Starting Benchmark Job: Error in Creating Benchmark {benhchmark_id} : {e}"
            logging.error(error_message)
            return None