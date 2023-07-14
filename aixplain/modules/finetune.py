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
Date: June 14th 2023
Description:
    FineTune Class
"""
from typing import List, Text
import logging
from aixplain.utils.file_utils import _request_with_retry
import json
from urllib.parse import urljoin
from aixplain.utils import config
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules.asset import Asset
from aixplain.modules.dataset import Dataset
from aixplain.modules.model import Model
from aixplain.modules.finetune_cost import FinetuneCost


class Finetune(Asset):
    """FineTune is a powerful tool for fine-tuning machine learning models and using your own datasets for specific tasks.

    Attributes:
        name (Text): Name of the FineTune.
        dataset_list (List[Dataset]): List of Datasets to be used for fine-tuning.
        model (Model): Model to be fine-tuned.
        cost (Cost): Cost of the FineTune.
        id (Text): ID of the FineTune.
        description (Text): Description of the FineTune.
        supplier (Text): Supplier of the FineTune.
        version (Text): Version of the FineTune.
        train_percentage (float): Percentage of training samples.
        dev_percentage (float): Percentage of development samples.
        additional_info (dict): Additional information to be saved with the FineTune.
        backend_url (str): URL of the backend.
        api_key (str): The TEAM API key used for authentication.
    """

    def __init__(
        self,
        name: Text,
        dataset_list: List[Dataset],
        model: Model,
        cost: FinetuneCost,
        id: Text = "",
        description: Text = "",
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        train_percentage: float = 100,
        dev_percentage: float = 0,
        **additional_info,
    ) -> None:
        """Create a FineTune with the necessary information.

        Args:
            name (Text): Name of the FineTune.
            dataset_list (List[Dataset]): List of Datasets to be used for fine-tuning.
            model (Model): Model to be fine-tuned.
            cost (Cost): Cost of the FineTune.
            id (Text, optional): ID of the FineTune. Defaults to "".
            description (Text, optional): Description of the FineTune. Defaults to "".
            supplier (Text, optional): Supplier of the FineTune. Defaults to "aiXplain".
            version (Text, optional): Version of the FineTune. Defaults to "1.0".
            train_percentage (float, optional): Percentage of training samples. Defaults to 100.
            dev_percentage (float, optional): Percentage of development samples. Defaults to 0.
            **additional_info: Additional information to be saved with the FineTune.
        """
        super().__init__(id, name, description, supplier, version)
        self.model = model
        self.dataset_list = dataset_list
        self.cost = cost
        self.train_percentage = train_percentage
        self.dev_percentage = dev_percentage
        self.additional_info = additional_info
        self.backend_url = config.BACKEND_URL
        self.api_key = config.TEAM_API_KEY
        self.aixplain_key = config.AIXPLAIN_API_KEY

    def start(self) -> Model:
        """Start the Finetune job.

        Returns:
            Model: The model object representing the Finetune job.
        """
        payload = {}
        try:
            url = urljoin(self.backend_url, f"sdk/finetune")
            headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}
            payload = json.dumps(
                {
                    "name": self.name,
                    "datasets": [
                        {
                            "datasetId": dataset.id,
                            "trainSamplesPercentage": self.train_percentage,
                            "devSamplesPercentage": self.dev_percentage,
                        }
                        for dataset in self.dataset_list
                    ],
                    "sourceModelId": self.model.id,
                }
            )
            logging.info(f"Start service for POST Start FineTune - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, data=payload)
            resp = r.json()
            logging.info(f"Response for POST Start FineTune - Name: {self.name} / Status {resp}")
            return ModelFactory().get(resp["id"])
        except Exception:
            message = ""
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Status {status_code} - {message}"
            error_message = f"Start FineTune: Error with payload {json.dumps(payload)}: {message}"
            logging.exception(error_message)
            return None
