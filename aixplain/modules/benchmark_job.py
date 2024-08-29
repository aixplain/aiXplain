import logging
from typing import List, Text, Dict, Optional
from aixplain.utils import config
from aixplain.modules import Asset, Dataset, Metric, Model
from urllib.parse import urljoin
import pandas as pd
from pathlib import Path
import json
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
            resp = self._fetch_current_response(self.id)
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
                        if task not in ["scoreId", "datasetId", "normalizationOptions", "longName"]:
                            task_list.append(task)

                    if group_by_task:
                        for task in task_list:
                            task_explanation = {}
                            for explanation_item in localized_explanations:
                                item_task_explanation = explanation_item[task]
                                identifier = explanation_item["longName"]
                                task_explanation[identifier] = item_task_explanation
                            grouped_explanations[task] = task_explanation
                    else:
                        for explanation_item in localized_explanations:
                            identifier = explanation_item["longName"]
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
    
    @classmethod
    def __convert_list_to_dict(cls, input_list):
        converted_dict = {}
        for item in input_list:
            key = item["name"]
            value = item.get("values", item.get("value", None))
            if type(value) is list:
                value = cls.__convert_list_to_dict(value)
            converted_dict[key] = value
        return converted_dict

    def fetch_dataset_breakdown(self):
        """Fetch metadata breakdown based on categorical information of the input dataset

        Returns:
            dict: dataset metadata breakdown dictionary
        """
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/benchmarks/reports/{self.id}/breakdown")
            if  config.AIXPLAIN_API_KEY != "":
                headers = {"x-aixplain-key": f"{config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            metadata_dict = self.__convert_list_to_dict(resp)
            return metadata_dict
        except Exception as e:
            error_message = f"Benchmark Job: Error in Getting benchmark metadata: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
        
    def fetch_filtered_bias_analysis(self, category: str, metric: Metric, model: Model = None):
        """Fetch filtered bias analysis based on category, metric and model(optional)

        Args:
            category (str): Category Name to be filetered upon
            metric (Metric): Metric to be filtered upon
            model (Model, optional): Model to be fileterd upon. Defaults to None and returns analysis for all models.
        """
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/benchmarks/reports/{self.id}/bias-analysis")
            if  config.AIXPLAIN_API_KEY != "":
                headers = {"x-aixplain-key": f"{config.AIXPLAIN_API_KEY}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            payload = json.dumps({
                "metadata": category,
                "metric": metric.id,
                "normalizationOption": metric.normalization_options
                })
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()
            if model is not None:
                filtered_resp = []
                for bias_item in resp:
                    if bias_item["modelId"] == model.id:
                        filtered_resp.append(bias_item)
                resp = filtered_resp
            return resp
        except Exception as e:
            error_message = f"Benchmark Job: Error in Getting filtered benchmark bias analysis: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)

    

    def fetch_bias_analysis(self, group_by="category", return_as_dataframe=False):
        """get the bias analysis of the benchmark report, grouped by a particular field

        Args:
            group_by (str, optional): Group the bias info by this field. Allowed values are {'category', 'model', 'metric'}. Defaults to "category".
        """
        try:
            dataset_breakdown = self.fetch_dataset_breakdown()
            categories = dataset_breakdown.keys()
            metric_list = self.additional_info['metric_list']
            bias_analaysis_response = {}
            record_list = []
            if group_by == "category":
                for category in categories:
                    category_bias_analysis = {}
                    for metric in metric_list:
                        normalizations = metric.normalization_options
                        if len(normalizations) == 0:
                            normalizations = [[]]
                        for normalization in normalizations:
                            metric.normalization_options = [normalization]
                            metric_partial_name = f"{metric.name} by {metric.supplier}"
                            metric_full_name = metric_partial_name if len(normalization) == 0 else f"{metric_partial_name} ({', '.join(normalization)})"
                            filtered_bias_response = self.fetch_filtered_bias_analysis(category, metric)
                            cleaned_bias_response = {}
                            for item in filtered_bias_response:
                                cleaned_bias_response[item["modelId"]] = item["items"]
                                for item_rec in item["items"]:
                                    record = {
                                        "metricName": metric_full_name,
                                        "modelID": item["modelId"]
                                    }
                                    record.update(item_rec)
                                    record_list.append(record)
                            category_bias_analysis[metric_full_name] = cleaned_bias_response
                    bias_analaysis_response[category] = category_bias_analysis
            if return_as_dataframe:
                return pd.DataFrame(record_list)
            else:
                return bias_analaysis_response
        except Exception as e:
            error_message = f"Benchmark Job: Error in Getting benchmark bias analysis: {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)