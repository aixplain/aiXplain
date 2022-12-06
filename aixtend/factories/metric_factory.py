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
Date: December 1st 2022
Description:
    Metric Factory Class
"""

import logging
from typing import List
from aixtend.modules.metric import Metric
from aixtend.utils import config
from aixtend.utils.file_utils import _request_with_retry

class MetricFactory:
    def __init__(self) -> None:
        self.api_key = config.TEAM_API_KEY
        self.backend_url = config.BENCHMARKS_BACKEND_URL
    

    @staticmethod
    def _create_metric_from_response(response: dict) -> Metric:
        """Converts response Json to 'Metric' object

        Args:
            response (dict): Json from API

        Returns:
            Metric: Coverted 'Metric' object
        """
        return Metric(response['id'], response['name'], response['description'])
    

    def create_metric_from_id(self, metric_id: str) -> Metric:
        """Create a 'Metric' object from metric id

        Args:
            model_id (str): Model ID of required metric.

        Returns:
            Metric: Created 'Metric' object
        """
        url = f"{self.backend_url}/sdk/scores/{metric_id}"
        headers = {
            'Authorization': f"Token {self.api_key}",
            'Content-Type': 'application/json'
        }
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        metric = self._create_metric_from_response(resp)
        return metric


    def list_metrics(self, task:str) -> List[Metric]:
        """Get list of supported metrics for a given task

        Args:
            task (str): Task to get metric for

        Returns:
            List[Metric]: List of supported metrics
        """
        try:
            url = f"{self.backend_url}/sdk/scores?function={task}"
            headers = {
                'Authorization': f"Token {self.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Metrics: Status of getting metrics for {task} : {resp}")
            all_metrics = resp["results"]
            metric_list = [self._create_metric_from_response(metric_info_json) for metric_info_json in all_metrics]
            return metric_list
        except Exception as e:
            error_message = f"Listing Metrics: Error in getting metrics for {task} : {e}"
            logging.error(error_message)
            return []