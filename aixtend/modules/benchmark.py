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
Date: October 25th 2022
Description:
    Benchmark Class
"""
import time
import json
import requests
import logging
import traceback
import pandas as pd
from requests.adapters import HTTPAdapter, Retry
from aixtend.utils.file_handler import download_file

class Benchmark:
    def __init__(self, api_key: str, backend_url: str) -> None:
        """
        params:
        ---
            api_key: API key of the team
            backend_url: backend endpoint
        """
        self.api_key = api_key
        self.backend_url = backend_url

    def create_benchmark(self, name: str, dataset_list: list, model_list: list, score_list:  list) -> str:
        """Creates a benchmark based on the information provided like name, dataset list, model list and score list.
        Note: This only creates a benchmark. It needs to run seperately using start_benchmark_job.

        Args:
            name (str): Unique Name of benchmark
            dataset_list (list): List of dataset ids for benchmark
            model_list (list): List of model ids for benchmark
            score_list (list): List of metric ids for benchmark

        Returns:
            str: ID of the created benchmark
        """
        try: 
            url = f"{self.backend_url}/sdk/benchmarks"
            headers = {
            'Authorization': f"Token {self.api_key}",
            'Content-Type': 'application/json'
            }
            payload = json.dumps({
                "name": name,
                "target": dataset_list,
                "model": model_list,
                "score": score_list,
                "shapScores": [],
                "humanEvaluationReport": False,
                "automodeTraining": False,
                "samplesCount": 10
                })
            session = requests.Session()
            retries = Retry(total=5,
                            backoff_factor=0.1,
                            status_forcelist=[ 500, 502, 503, 504 ])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            r = session.post(url, headers=headers, data=payload)
            resp = r.json()
            logging.info(f"Creating Benchmark Job: Status of polling for {name} ({self.api_key}): {resp}")
            return resp['id']
        except Exception as e:
            error_message = f"Creating Benchmark Job: Error in Creating Benchmark with payload {payload} : {e}"
            logging.error(error_message)
            return None

    def start_benchmark_job(self, benhchmark_id: str) -> str:
        """Start a new benchmarking job(run) from a already created benchmark. 

        Args:
            benhchmark_id (str): ID of benchmark to start

        Returns:
            str: Job ID of benchmark run
        """ 
        try: 
            url = f"{self.backend_url}/sdk/benchmarks/{benhchmark_id}/start"
            headers = {
            'Authorization': f"Token {self.api_key}",
            'Content-Type': 'application/json'
            }
            session = requests.Session()
            retries = Retry(total=5,
                            backoff_factor=0.1,
                            status_forcelist=[ 500, 502, 503, 504 ])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            r = session.post(url, headers=headers)
            resp = r.json()
            logging.info(f"Starting Benchmark Job: Status of polling for {benhchmark_id} ({self.api_key}): {resp}")
            return resp['jobId']
        except Exception as e:
            error_message = f"Starting Benchmark Job: Error in Creating Benchmark {benhchmark_id} : {e}"
            logging.error(error_message)
            return None


    def download_results_as_csv(self, job_id: str, save_path:str = None , returnDataFrame: bool = False):
        """Get the results of the benchmark job in a CSV format.
        The results can either be downloaded locally or returned in the form of pandas.DataFrame.


        Args:
            job_id (str): Job ID of the benchmark run
            save_path (str, optional): Path to save the CSV if returnDataFrame is False. If None, a ranmdom path is generated. Defaults to None.
            returnDataFrame (bool, optional): If True, the result is returned as pandas.DataFrame else saved as a CSV file. Defaults to False.

        Returns:
            str/pandas.DataFrame: results as path of locally saved file if returnDataFrame is False else as a pandas dataframe 
        """
        try:
            url = f"{self.backend_url}/sdk/benchmarks/jobs/{job_id}"
            headers = {
            'Authorization': f"Token {self.api_key}",
            'Content-Type': 'application/json'
            }
            session = requests.Session()
            retries = Retry(total=5,
                            backoff_factor=0.1,
                            status_forcelist=[ 500, 502, 503, 504 ])
            session.mount('https://', HTTPAdapter(max_retries=retries))
            r = session.get(url, headers=headers)
            resp = r.json()
            logging.info(f"Downloading Benchmark Results: Status of downloading results for {job_id} ({self.api_key}): {resp}")
            csv_url = resp['reportUrl']
            if returnDataFrame:
                df = pd.read_csv(csv_url)
                return df
            else:
                downloaded_path = download_file(csv_url, save_path)
                return downloaded_path
        except Exception as e:
            error_message = f"Downloading Benchmark Results: Error in Downloading Benchmark Results : {e}"
            logging.error(error_message)
            return None
    
