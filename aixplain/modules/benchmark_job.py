import logging
from typing import Text, Dict, Optional, Union
from aixplain.utils import config
from urllib.parse import urljoin
import pandas as pd
import json
from pathlib import Path
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.file_utils import save_file


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
        """Create a BenchmarkJob instance from an API response.

        Args:
            response (Dict): The API response containing benchmark job information.
                Must contain 'jobId', 'status', and 'benchmark.id' fields.

        Returns:
            BenchmarkJob: A new BenchmarkJob instance initialized with the response data.
        """
        return BenchmarkJob(response["jobId"], response["status"], response["benchmark"]["id"])

    @classmethod
    def _fetch_current_response(cls, job_id: Text) -> dict:
        """Fetch the current state of a benchmark job from the API.

        Args:
            job_id (Text): The ID of the benchmark job to fetch.

        Returns:
            dict: The API response containing the current state of the benchmark job.

        Raises:
            Exception: If the API request fails.
        """
        url = urljoin(config.BACKEND_URL, f"sdk/benchmarks/jobs/{job_id}")
        headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        return resp

    def _update_from_response(self, response: dict):
        """Update the benchmark job's state from an API response.

        Args:
            response (dict): The API response containing updated benchmark job information.
                Must contain a 'status' field.
        """
        self.status = response["status"]

    def __repr__(self) -> str:
        return f"<Benchmark Job({self.id})>"

    def check_status(self) -> Text:
        """Check the current status of the benchmark job.

        Fetches the latest status from the API and updates the local state.

        Returns:
            Text: The current status of the benchmark job.
        """
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
            if "reportUrl" not in resp or resp["reportUrl"] == "":
                logging.error(
                    "Downloading Benchmark Results: Can't get download results as they aren't generated yet. Please wait for a while."
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

    def __simplify_scores(self, scores: Dict) -> list:
        """Simplify the raw scores into a more readable format.

        Args:
            scores (Dict): Raw scores dictionary containing model IDs as keys and
                score information as values.

        Returns:
            list: A list of dictionaries, each containing a model's scores in a simplified format.
                Each dictionary has 'Model' as a key and metric names as additional keys.
        """
        simplified_score_list = []
        for model_id, model_info in scores.items():
            model_scores = model_info["rawScores"]
            # model = Mode
            row = {"Model": model_id}
            for score_info in model_scores:
                row[score_info["longName"]] = score_info["average"]
            simplified_score_list.append(row)
        return simplified_score_list

    def get_scores(self, return_simplified: bool = True, return_as_dataframe: bool = True) -> Union[Dict, pd.DataFrame, list]:
        """Get the benchmark scores for all models.

        Args:
            return_simplified (bool, optional): If True, returns a simplified version of scores.
                Defaults to True.
            return_as_dataframe (bool, optional): If True and return_simplified is True,
                returns results as a pandas DataFrame. Defaults to True.

        Returns:
            Union[Dict, pd.DataFrame, list]: The benchmark scores in the requested format.
                - If return_simplified=False: Returns a dictionary with detailed model scores
                - If return_simplified=True and return_as_dataframe=True: Returns a pandas DataFrame
                - If return_simplified=True and return_as_dataframe=False: Returns a list of dictionaries

        Raises:
            Exception: If there's an error fetching or processing the scores.
        """
        try:
            resp = self._fetch_current_response(self.id)
            iterations = resp.get("iterations", [])
            scores = {}
            for iteration_info in iterations:
                model_id = iteration_info["pipeline"]
                pipeline_json = json.loads(iteration_info["pipelineJson"])
                if "benchmark" in pipeline_json:
                    model_id = pipeline_json["benchmark"]["displayName"]

                model_info = {
                    "creditsUsed": round(iteration_info.get("credits", 0), 5),
                    "timeSpent": round(iteration_info.get("runtime", 0), 2),
                    "status": iteration_info["status"],
                    "rawScores": iteration_info["scores"],
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

    def get_failuire_rate(self, return_as_dataframe: bool = True) -> Union[Dict, pd.DataFrame]:
        """Calculate the failure rate for each model in the benchmark.

        Args:
            return_as_dataframe (bool, optional): If True, returns results as a pandas DataFrame.
                Defaults to True.

        Returns:
            Union[Dict, pd.DataFrame]: The failure rates for each model.
                - If return_as_dataframe=True: Returns a DataFrame with 'Model' and 'Failure Rate' columns
                - If return_as_dataframe=False: Returns a dictionary with model IDs as keys and failure rates as values

        Raises:
            Exception: If there's an error calculating the failure rates.
        """
        try:
            scores = self.get_scores(return_simplified=False)
            failure_rates = {}
            for model_id, model_info in scores.items():
                if len(model_info["rawScores"]) == 0:
                    failure_rates[model_id] = 0
                    continue
                score_info = model_info["rawScores"][0]
                num_successful = score_info["count"]
                num_failed = score_info["failedSegmentsCount"]
                failure_rate = (num_failed * 100) / (num_successful + num_failed)
                failure_rates[model_id] = failure_rate
            if return_as_dataframe:
                df = pd.DataFrame()
                df["Model"] = list(failure_rates.keys())
                df["Failure Rate"] = list(failure_rates.values())
                return df
            else:
                return failure_rates
        except Exception as e:
            error_message = f"Benchmark scores: Error in Getting benchmark failure rate: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)

    def get_all_explanations(self) -> Dict:
        """Get all explanations for the benchmark results.

        Returns:
            Dict: A dictionary containing both metric-dependent and metric-independent explanations.
                The dictionary has two keys:
                - 'metricInDependent': List of metric-independent explanations
                - 'metricDependent': List of metric-dependent explanations

        Raises:
            Exception: If there's an error fetching the explanations.
        """
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

    def get_localized_explanations(self, metric_dependant: bool, group_by_task: bool = False) -> Dict:
        """Get localized explanations for the benchmark results.

        Args:
            metric_dependant (bool): If True, returns metric-dependent explanations.
                If False, returns metric-independent explanations.
            group_by_task (bool, optional): If True and metric_dependant is True,
                groups explanations by task. Defaults to False.

        Returns:
            Dict: A dictionary containing the localized explanations.
                The structure depends on the input parameters:
                - If metric_dependant=False: Returns metric-independent explanations
                - If metric_dependant=True and group_by_task=False: Returns explanations grouped by score ID
                - If metric_dependant=True and group_by_task=True: Returns explanations grouped by task

        Raises:
            Exception: If there's an error fetching or processing the explanations.
        """
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
                    localized_explanations = {}
                else:
                    localized_explanations = localized_explanations[0]
            return localized_explanations

        except Exception as e:
            error_message = f"Benchmark scores: Error in Getting benchmark explanations: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
