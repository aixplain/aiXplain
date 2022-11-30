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
Date: October 28th 2022
Description:
    Datasets Class
"""
import time
import json
import requests
import logging
import traceback
from collections import namedtuple
from typing import List
from aixtend.utils.file_utils import _request_with_retry

DatasetInfo = namedtuple('DatasetInfo', ['name', 'id', 'description'])

class Datasets:
    def __init__(self, api_key: str, backend_url: str) -> None:
        """
        params:
        ---
            api_key: API key of the team
            backend_url: backend endpoint
        """
        self.api_key = api_key
        self.backend_url = backend_url

    def __get_dataset_info(self, dataset_info_json):
        """Coverts Json to DatasetInfo object

        Args:
            dataset_info_json (_type_): Json from API

        Returns:
            DatasetInfo: Coverted DatasetInfo object
        """
        d_info = DatasetInfo(dataset_info_json['name'], dataset_info_json['id'], dataset_info_json['description'])
        return d_info

    def get_datasets_from_page(self, page_number: int, task: str, input_language: str = None, output_language: str = None) -> List:
        """Get the list of datasets from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int): Page from which datasets are to be listed
            task (str): Task of listed datasets
            input_language (str, optional): Input language of listed datasets. Defaults to None.
            output_language (str, optional): Output language of listed datasets. Defaults to None.

        Returns:
            List: List of datasets based on given filters
        """
        try:
            url = f"{self.backend_url}/sdk/datasets?pageNumber={page_number}&function={task}"
            if input_language is not None:
                url += f"&input={input_language}"
            if output_language is not None:
                url += f"&output={output_language}"
            headers = {
            'Authorization': f"Token {self.api_key}",
            'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Datasets: Status of getting Datasets on Page {page_number} for {task}: {resp}")
            all_datasets = resp["results"]
            dataset_info_list = [self.__get_dataset_info(dataset_info_json) for dataset_info_json in all_datasets]
            return dataset_info_list
        except Exception as e:
            error_message = f"Listing Datasets: Error in getting Datasets on Page {page_number} for {task} : {e}"
            logging.error(error_message)
            return []

    def get_first_k_datasets(self, k: int, task: str, input_language: str = None, output_language: str = None) -> List:
        """Gets the first k given datasets based on the provided task and language filters

        Args:
            k (int): Number of datasets to get
            task (str): Task of listed datasets
            input_language (str, optional): Input language of listed datasets. Defaults to None.
            output_language (str, optional): Output language of listed datasets. Defaults to None.

        Returns:
            List: List of datasets based on given filters
        """
        try:
            dataset_info_list = []
            assert k > 0
            for page_number in range(k//10 + 1):
                dataset_info_list += self.get_datasets_from_page(page_number, task, input_language, output_language)
            return dataset_info_list
        except Exception as e:
            error_message = f"Listing Datasets: Error in getting {k} Datasets for {task} : {e}"
            logging.error(error_message)
            return []