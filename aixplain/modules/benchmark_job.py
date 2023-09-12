import logging
from typing import List, Text, Dict, Optional
from aixplain.utils import config
from aixplain.modules import Asset, Dataset, Metric, Model
from urllib.parse import urljoin
import pandas as pd
from pathlib import Path
from aixplain.utils.file_utils import _request_with_retry, save_file

class BenchmarkJob:
    """Benchmark Job Represents a single run of an already created Benchmark.

    Attributes:
        id (str): ID of the Benchmark Job.
        status (str): Status of the Benchmark Job.
        benchmark_id (str): ID of the associated parent Benchmark.
        additional_info (dict): Any additional information to be saved with the Benchmark Job.

    """

    def __init__(self, id: Text, status: Text, benchmark_id: Text, **additional_info) -> None:
        """Create a Benchmark Job with the necessary information. Each Job is a run of a parent Benchmark

        Args:
            id (Text): ID of the Benchmark Job
            status (Text): Status of the Benchmark Job
            benchmark_id (Text): ID of the associated parent Benchmark
            **additional_info: Any additional Benchmark Job info to be saved
        """
        self.id = id
        self.status = status
        self.benchmark_id = benchmark_id
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
    
    def download_results_as_csv(self, save_path: Optional[Text] = None, return_dataframe: bool = False):
        """Get the results of the benchmark job in a CSV format.
        The results can either be downloaded locally or returned in the form of pandas.DataFrame.


        Args:
            save_path (Text, optional): Path to save the CSV if return_dataframe is False. If None, a ranmdom path is generated. defaults to None.
            return_dataframe (bool): If True, the result is returned as pandas.DataFrame else saved as a CSV file. defaults to False.

        Returns:
            str/pandas.DataFrame: results as path of locally saved file if return_dataframe is False else as a pandas dataframe
        """
        try:
            resp = self._fetch_current_response(self.id)
            logging.info(f"Downloading Benchmark Results: Status of downloading results for {self.id}: {resp}")
            if "reportUrl" not in resp or resp['reportUrl'] == "":
                logging.error(
                    f"Downloading Benchmark Results: Can't get download results as they aren't generated yet. Please wait for a while."
                )
                return None
            csv_url = resp["reportUrl"]
            if return_dataframe:
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
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
