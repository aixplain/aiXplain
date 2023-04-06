__author__='shreyassharma'

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
from typing import List
import json
import pandas as pd
from pathlib import Path
from aixplain.modules.benchmark import Benchmark, Dataset, Model, Metric
from aixplain.modules.benchmark_job import BenchmarkJob
from aixplain.factories.dataset_factory import DatasetFactory
from aixplain.factories.metric_factory import MetricFactory
from aixplain.factories.model_factory import ModelFactory
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry, save_file


class BenchmarkFactory:
    """A static class for creating and managing the Benchmarking experience.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """
    api_key = config.TEAM_API_KEY
    backend_url = config.BENCHMARKS_BACKEND_URL

    
    @classmethod
    def _create_benchmark_job_from_response(cls, response: dict) -> BenchmarkJob:
        """Converts response Json to 'BenchmarkJob' object

        Args:
            response (dict): Json from API

        Returns:
            BenchmarkJob: Coverted 'BenchmarkJob' object
        """
        return BenchmarkJob(response['jobId'], response['status'], response['benchmark']['id'])


    @classmethod
    def _get_benchmark_jobs_from_benchmark_id(cls, benchmark_id: str) -> List[BenchmarkJob]:
        """Get list of benchmark jobs from benchmark id

        Args:
            benchmark_id (str): ID of benchmark

        Returns:
            List[BenchmarkJob]: List of associated benchmark jobs
        """
        url = f"{cls.backend_url}/sdk/benchmarks/{benchmark_id}/jobs"
        headers = {
            'Authorization': f"Token {cls.api_key}",
            'Content-Type': 'application/json'
        }
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        job_list = [cls._create_benchmark_job_from_response(job_info) for job_info in resp]
        return job_list

    
    @classmethod
    def _create_benchmark_from_response(cls, response: dict) -> Benchmark:
        """Converts response Json to 'Benchmark' object

        Args:
            response (dict): Json from API

        Returns:
            Benchmark: Coverted 'Benchmark' object
        """
        model_list = [ModelFactory().create_asset_from_id(model_info["id"]) for model_info in response['model']]
        dataset_list = [DatasetFactory().create_asset_from_id(dataset_id) for dataset_id in response["target"]]
        metric_list = [MetricFactory().create_asset_from_id(metric_info["id"]) for metric_info in response['score']]
        job_list = cls._get_benchmark_jobs_from_benchmark_id(response['id'])
        return Benchmark(response['id'], response['name'], model_list, dataset_list, metric_list, job_list)

    
    @classmethod
    def create_asset_from_id(cls, benchmark_id: str) -> Benchmark:
        """Create a 'Benchmark' object from Benchmark id

        Args:
            benchmark_id (str): Benchmark ID of required Benchmark.

        Returns:
            Benchmark: Created 'Benchmark' object
        """
        try:
            resp = None
            url = f"{cls.backend_url}/sdk/benchmarks/{benchmark_id}"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            benchmark = cls._create_benchmark_from_response(resp)
        except Exception as e:
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Benchmark Creation: Status {status_code} - {message}"
            else:
                message = "Benchmark Creation: Unspecified Error"
            logging.error(message)
            raise Exception(f"Status {status_code}: {message}")
        return benchmark


    @classmethod
    def create_benchmark_job_from_id(cls, job_id: str) -> BenchmarkJob:
        """Create a 'BenchmarkJob' object from job id

        Args:
            job_id (str): ID of the required BenchmarkJob.

        Returns:
            BenchmarkJob: Created 'BenchmarkJob' object
        """
        url = f"{cls.backend_url}/sdk/benchmarks/jobs/{job_id}"
        headers = {
            'Authorization': f"Token {cls.api_key}",
            'Content-Type': 'application/json'
        }
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        benchmarkJob = cls._create_benchmark_job_from_response(resp)
        return benchmarkJob


    @classmethod
    def update_benchmark_job_info(cls, benchmarkJob: BenchmarkJob) -> BenchmarkJob:
        """Updates 'BenchmarkJob' with the latest info

        Args:
            benchmarkJob (BenchmarkJob): 'BenchmarkJob' to update

        Returns:
            BenchmarkJob: updated 'BenchmarkJob'
        """
        return cls.create_benchmark_job_from_id(benchmarkJob.id)


    @classmethod
    def update_benchmark_info(cls, benchmark: Benchmark) -> Benchmark:
        """Updates 'Benchmark' with the latest info

        Args:
            benchmark (Benchmark): 'Benchmark' to update

        Returns:
            Benchmark: updated 'Benchmark'
        """
        return cls.create_asset_from_id(benchmark.id)


    @classmethod
    def create_benchmark(cls, name: str, dataset_list: List[Dataset], model_list: List[Model], metric_list:  List[Metric]) -> Benchmark:
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
        try: 
            url = f"{cls.backend_url}/sdk/benchmarks"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            payload = json.dumps({
                "name": name,
                "target": [dataset.id for dataset in dataset_list],
                "model": [model.id for model in model_list],
                "score": [metric.id for metric in metric_list],
                "shapScores": [],
                "humanEvaluationReport": False,
                "automodeTraining": False,
                })
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()
            logging.info(f"Creating Benchmark Job: Status for {name}: {resp}")
            return cls.create_asset_from_id(resp['id'])
        except Exception as e:
            error_message = f"Creating Benchmark Job: Error in Creating Benchmark with payload {payload} : {e}"
            logging.error(error_message)
            return None
    

    @classmethod
    def start_benchmark_job(cls, benchmark: Benchmark) -> BenchmarkJob:
        """Start a new benchmarking job(run) from a already created benchmark. 

        Args:
            benchmark (Benchmark): 'Benchmark' object to start the run for

        Returns:
            BenchmarkJob: 'BenchmarkJob' created after starting the run
        """ 
        try: 
            benhchmark_id = benchmark.id
            url = f"{cls.backend_url}/sdk/benchmarks/{benhchmark_id}/start"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("post", url, headers=headers)
            resp = r.json()
            logging.info(f"Starting Benchmark Job: Status for {benhchmark_id}: {resp}")
            return cls.create_benchmark_job_from_id(resp['jobId'])
        except Exception as e:
            error_message = f"Starting Benchmark Job: Error in Creating Benchmark {benhchmark_id} : {e}"
            logging.error(error_message)
            return None

    
    @classmethod
    def download_results_as_csv(cls, benchmarkJob: BenchmarkJob, save_path:str = None , returnDataFrame: bool = False):
        """Get the results of the benchmark job in a CSV format.
        The results can either be downloaded locally or returned in the form of pandas.DataFrame.


        Args:
            benchmarkJob (BenchmarkJob): 'BenchmarkJob' to get the results for
            save_path (str, optional): Path to save the CSV if returnDataFrame is False. If None, a ranmdom path is generated. @classmethod
    defaults to None.
            returnDataFrame (bool, optional): If True, the result is returned as pandas.DataFrame else saved as a CSV file. @classmethod
    defaults to False.

        Returns:
            str/pandas.DataFrame: results as path of locally saved file if returnDataFrame is False else as a pandas dataframe 
        """
        try:
            job_id = benchmarkJob.id
            url = f"{cls.backend_url}/sdk/benchmarks/jobs/{job_id}"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Downloading Benchmark Results: Status of downloading results for {job_id}: {resp}")
            if "reportUrl" not in resp:
                logging.error(f"Downloading Benchmark Results: Can't get download results as they aren't generated yet. Please wait for a while.")
                return None
            csv_url = resp['reportUrl']
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
            return None


