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
        
    def __simplify_scores(self, scores):
        simplified_score_list  = []
        for model_id, model_info in scores.items():
            model_scores = model_info["rawScores"]
            # model = Mode
            row = {"Model": model_id}
            for score_info in model_scores:
                row[score_info["longName"]] = score_info["average"]
            simplified_score_list.append(row)
        return simplified_score_list




    def get_scores(self, return_simplified=True, return_as_dataframe=True):
        try:
            resp = self._fetch_current_response(self.id)
            iterations = resp.get("iterations", [])
            scores = {}
            for iteration_info in iterations:
                model_id = iteration_info["pipeline"]
                model_info = {
                    "creditsUsed" : round(iteration_info.get("credits", 0),5),
                    "timeSpent" : round(iteration_info.get("runtime", 0),2),
                    "status" : iteration_info["status"],
                    "rawScores" : iteration_info["scores"],
                }
                scores[model_id] = model_info
            
            if return_simplified:
                simplified_scores = self.__simplify_scores(scores)
                if return_as_dataframe:
                    simplified_scores = pd.DataFrame(simplified_scores)
                return simplified_scores
            else:
                return scores
        except Exception as e:
            error_message = f"Benchmark scores: Error in Getting benchmark scores: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
        
    
    def get_failuire_rate(self, return_as_dataframe=True):
        try:
            scores = self.get_scores(return_simplified=False)
            failure_rates = {}
            for model_id, model_info in scores.items():
                if len(model_info["rawScores"]) == 0:
                    failure_rates[model_id] = 0
                    continue
                score_info = model_info["rawScores"][0] 
                num_succesful = score_info["count"]
                num_failed = score_info["failedSegmentsCount"]
                failuire_rate =  (num_failed * 100) / (num_succesful+num_failed)
                failure_rates[model_id] = failuire_rate
            if return_as_dataframe:
                df = pd.DataFrame()
                df["Model"] = list(failure_rates.keys())
                df["Failuire Rate"] = list(failure_rates.values())
                return df
            else:
                return failure_rates
        except Exception as e:
            error_message = f"Benchmark scores: Error in Getting benchmark failuire rate: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
        
    def get_all_explanations(self):
        try:
            resp = self._fetch_current_response(self)
            raw_explanations = resp.get("explanation", {})
            if "metricInDependent" not in raw_explanations:
                raw_explanations["metricInDependent"] = []
            if "metricDependent" not in raw_explanations:
                raw_explanations["metricDependent"] = []
            return raw_explanations
        except Exception as e:
            error_message = f"Benchmark scores: Error in Getting benchmark explanations: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
    
    def get_localized_explanations(self, metric_dependant: bool, group_by_task: bool = False):
        try:
            raw_explanations = self.get_all_explanations()
            if metric_dependant:
                localized_explanations = raw_explanations["metricDependent"]
                if len(localized_explanations) == 0:
                    localized_explanations = {}
                else:
                    grouped_explanations = {}
                    task_list = []
                    first_explanation = localized_explanations[0]
                    for task in first_explanation:
                        if task not in ["scoreId", "datasetId"]:
                            task_list.append(task)

                    if group_by_task:
                        for task in task_list:
                            task_explanation = {}
                            for explanation_item in localized_explanations:
                                item_task_explanation = explanation_item[task]
                                identifier = explanation_item["scoreId"]
                                task_explanation[identifier] = item_task_explanation
                            grouped_explanations[task] = task_explanation
                    else:
                        for explanation_item in localized_explanations:
                            identifier = explanation_item["scoreId"]
                            grouped_explanations[identifier] = explanation_item
                    localized_explanations = grouped_explanations
            else:
                localized_explanations = raw_explanations["metricInDependent"]
                if len(localized_explanations) == 0:
                    localized_explanations =  {}
                else:
                    localized_explanations = localized_explanations[0]
            return localized_explanations

        except Exception as e:
            error_message = f"Benchmark scores: Error in Getting benchmark explanations: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)