__author__ = "lucaspavanelli"

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
Date: December 2nd 2022
Description:
    Finetune Factory Class
"""

import logging
from typing import Dict, List, Optional, Text
import json
import pandas as pd
from pathlib import Path
from aixplain.modules.cost import Cost
from aixplain.modules.dataset import Dataset
from aixplain.modules.model import Model
from aixplain.factories.model_factory import ModelFactory
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry, save_file
from urllib.parse import urljoin
from warnings import warn


class FinetuneFactory:
    """A static class for creating and managing the FineTune experience.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """

    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def _create_cost_from_response(cls, response: Dict) -> Cost:
        return Cost(response["trainingCost"], response["inferenceCost"], response["hostingCost"])


    @classmethod
    def create_finetune(
        cls, name: str, dataset_list: List[Dataset], model: Model, train_percentage: float = 1, dev_percentage: float = 0
    ) -> Model:
        """Creates a finetune based on the information provided like name, dataset list, model list and score list.
        Note: This only creates a finetune. It needs to run seperately using start_finetune_job.

        Args:
            name (str): Unique Name of Finetune model
            dataset_list (List[Dataset]): List of Datasets to be used for fine-tuning
            model_list (Model): Model to be used for fine-tuning

        Returns:
            Model: _description_
        """
        payload = {}
        try:
            url = urljoin(cls.backend_url, f"sdk/finetune")
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            payload = json.dumps(
                {
                    "name": name,
                    "datasets": [{"datasetId": dataset.id, "trainPercentage": train_percentage, "devPercentage": dev_percentage} for dataset in dataset_list],
                    "sourceModelId": model.id,
                }
            )
            print(f"Payload: {payload}")
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()
            print(resp)
            logging.info(f"Creating Finetune Job: Status for {name}: {resp}")
            # TODO check if all >= 400 errors should be treated this way
            if "id" not in resp and "statusCode" in resp and resp["statusCode"] >= 400 and "message" in resp:
                error_message = f"Creating Finetune Job: Error in Creating Finetune with payload {payload} - Status code: {resp['statusCode']} | Message: {resp['message']}"
                logging.error(error_message)
                return None
            return ModelFactory().get(resp["id"])
        except Exception as e:
            error_message = f"Creating Finetune Job: Error in Creating Finetune with payload {payload} : {e}"
            logging.error(error_message)
            return None

    @classmethod
    def estimate_cost(
        cls, dataset_list: List[Dataset], model: Model, train_percentage: float = 1, dev_percentage: float = 0
    ) -> Cost:
        payload = {}
        # try:
        url = urljoin(cls.backend_url, f"sdk/finetune/cost-estimation")
        headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        payload = json.dumps(
            {
                "datasets": [{"datasetId": dataset.id, "trainPercentage": train_percentage, "devPercentage": dev_percentage} for dataset in dataset_list],
                "sourceModelId": model.id,
            }
        )
        print(f"Payload: {payload}")
        r = _request_with_retry("post", url, headers=headers, data=payload)
        resp = r.json()
        print(resp)
        logging.info(f"Creating Finetune Job: Status for: {resp}")
        return cls._create_cost_from_response(resp)
        # except Exception as e:
        #     error_message = f"Estimating cost: Error in cost estimation with payload {payload} : {e}"
        #     logging.error(error_message)
        #     return None