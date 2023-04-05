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
from aixplain.modules.metric import Metric
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry

class MetricFactory:
    """A static class for creating and exploring Metric Objects.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """
    api_key = config.TEAM_API_KEY
    backend_url = config.BENCHMARKS_BACKEND_URL
    

    @classmethod
    def _create_metric_from_response(cls, response: dict) -> Metric:
        """Converts response Json to 'Metric' object

        Args:
            response (dict): Json from API

        Returns:
            Metric: Coverted 'Metric' object
        """
        return Metric(response['id'], response['name'], response['description'])
    

    @classmethod
    def create_asset_from_id(cls, metric_id: str) -> Metric:
        """Create a 'Metric' object from metric id

        Args:
            model_id (str): Model ID of required metric.

        Returns:
            Metric: Created 'Metric' object
        """
        try:
            resp = None
            url = f"{cls.backend_url}/sdk/scores/{metric_id}"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            metric = cls._create_metric_from_response(resp)
        except Exception as e:
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Metric Creation: Status {status_code} - {message}"
            else:
                message = "Metric Creation: Unspecified Error"
            logging.error(message)
            raise Exception(f"Status {status_code}: {message}")
        return metric


    @classmethod
    def list_assets(cls, task:str) -> List[Metric]:
        """Get list of supported metrics for a given task

        Args:
            task (str): Task to get metric for

        Returns:
            List[Metric]: List of supported metrics
        """
        try:
            url = f"{cls.backend_url}/sdk/scores?function={task}"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Metrics: Status of getting metrics for {task} : {resp}")
            all_metrics = resp["results"]
            metric_list = [cls._create_metric_from_response(metric_info_json) for metric_info_json in all_metrics]
            return metric_list
        except Exception as e:
            error_message = f"Listing Metrics: Error in getting metrics for {task} : {e}"
            logging.error(error_message)
            return []