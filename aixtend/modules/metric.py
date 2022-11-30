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
    Metric Class
"""

import time
import json
from typing import List
import requests
import logging
import traceback
from collections import namedtuple
MetricInfo = namedtuple('MetricInfo', ['name', 'id', 'description'])
from aixtend.utils.file_utils import _request_with_retry

class Metric:
    def __init__(self, api_key: str, backend_url: str) -> None:
        """
        params:
        ---
            api_key: API key of the team
            backend_url: backend endpoint
        """
        self.api_key = api_key
        self.backend_url = backend_url

    def __get_metric_info(self, metric_info_json):
        """Coverts Json to MetricInfo object

        Args:
            metric_info_json (dict): Json from API

        Returns:
            MetricInfo: Coverted MetricInfo object
        """
        m_info = MetricInfo(metric_info_json['name'], metric_info_json['id'], metric_info_json['description'])
        return m_info


    def list_metrics(self, task:str) -> List:
        """Get list of supported metrics for a given task

        Args:
            task (str): Task to get metric for

        Returns:
            List: List of supported metrics
        """
        try:
            url = f"{self.backend_url}/sdk/scores?function={task}"
            headers = {
            'Authorization': f"Token {self.api_key}",
            'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Metrics: Status of getting metrics for {task}: {resp}")
            all_metrics = resp["results"]
            metric_info_list = [self.__get_metric_info(metric_info_json) for metric_info_json in all_metrics]
            return metric_info_list
        except Exception as e:
            error_message = f"Listing Metrics: Error in getting metrics for {task} : {e}"
            logging.error(error_message)
            return []
    

    
    