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
    Dataset Factory Class
"""

import logging
from typing import List
from aixplain.modules.dataset import Dataset
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry

class DatasetFactory:
    """A static class for creating and exploring Dataset Objects.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """
    api_key = config.TEAM_API_KEY
    backend_url = config.BENCHMARKS_BACKEND_URL
    

    @classmethod
    def _create_dataset_from_response(cls, response: dict) -> Dataset:
        """Converts response Json to 'Dataset' object

        Args:
            response (dict): Json from API

        Returns:
            Dataset: Coverted 'Dataset' object
        """
        return Dataset(response['id'], response['name'], response['description'])

    
    @classmethod
    def create_asset_from_id(cls, dataset_id: str) -> Dataset:
        """Create a 'Dataset' object from dataset id

        Args:
            dataset_id (str): Dataset ID of required dataset.

        Returns:
            Dataset: Created 'Dataset' object
        """
        try:
            resp = None
            url = f"{cls.backend_url}/sdk/datasets/{dataset_id}"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            dataset = cls._create_dataset_from_response(resp)
        except Exception as e:
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Datset Creation: Status {status_code} - {message}"
            else:
                message = "Dataset Creation: Unspecified Error"
            logging.error(message)
            raise Exception(f"Status {status_code}: {message}")
        return dataset
    

    @classmethod
    def get_assets_from_page(cls, page_number: int, task: str, input_language: str = None, output_language: str = None) -> List[Dataset]:
        """Get the list of datasets from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int): Page from which datasets are to be listed
            task (str): Task of listed datasets
            input_language (str, optional): Input language of listed datasets. Defaults to None.
            output_language (str, optional): Output language of listed datasets. Defaults to None.

        Returns:
            List[Dataset]: List of datasets based on given filters
        """
        try:
            url = f"{cls.backend_url}/sdk/datasets?pageNumber={page_number}&function={task}"
            if input_language is not None:
                url += f"&input={input_language}"
            if output_language is not None:
                url += f"&output={output_language}"
            headers = {
                'Authorization': f"Token {cls.api_key}",
                'Content-Type': 'application/json'
            }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Datasets: Status of getting Datasets on Page {page_number} for {task} : {resp}")
            all_datasets = resp["results"]
            dataset_list = [cls._create_dataset_from_response(dataset_info_json) for dataset_info_json in all_datasets]
            return dataset_list
        except Exception as e:
            error_message = f"Listing Datasets: Error in getting Datasets on Page {page_number} for {task} : {e}"
            logging.error(error_message)
            return []


    @classmethod
    def get_first_k_assets(cls, k: int, task: str, input_language: str = None, output_language: str = None) -> List[Dataset]:
        """Gets the first k given datasets based on the provided task and language filters

        Args:
            k (int): Number of datasets to get
            task (str): Task of listed datasets
            input_language (str, optional): Input language of listed datasets. Defaults to None.
            output_language (str, optional): Output language of listed datasets. Defaults to None.

        Returns:
            List[Dataset]: List of datasets based on given filters
        """
        try:
            dataset_list = []
            assert k > 0
            for page_number in range(k//10 + 1):
                dataset_list += cls.get_assets_from_page(page_number, task, input_language, output_language)
            return dataset_list[0:k]
        except Exception as e:
            error_message = f"Listing Datasets: Error in getting {k} Datasets for {task} : {e}"
            logging.error(error_message)
            return []