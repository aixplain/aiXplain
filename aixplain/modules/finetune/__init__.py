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
from typing import List, Text, Optional
import logging
import json
from urllib.parse import urljoin
from aixplain.modules.finetune.cost import FinetuneCost
from aixplain.modules.finetune.hyperparameters import Hyperparameters
from aixplain.modules.asset import Asset
from aixplain.modules.dataset import Dataset
from aixplain.modules.model import Model

from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry


class Finetune(Asset):
    """A tool for fine-tuning machine learning models using custom datasets.

    This class provides functionality to customize pre-trained models for specific tasks
    by fine-tuning them on user-provided datasets. It handles the configuration of
    training parameters, data splitting, and job execution.

    Attributes:
        name (Text): Name of the fine-tuning job.
        dataset_list (List[Dataset]): List of datasets to use for fine-tuning.
        model (Model): The base model to be fine-tuned.
        cost (FinetuneCost): Cost information for the fine-tuning job.
        id (Text): ID of the fine-tuning job.
        description (Text): Detailed description of the fine-tuning purpose.
        supplier (Text): Provider/creator of the fine-tuned model.
        version (Text): Version identifier of the fine-tuning job.
        train_percentage (float): Percentage of data to use for training.
        dev_percentage (float): Percentage of data to use for validation.
        prompt_template (Text): Template for formatting training examples, using
            <<COLUMN_NAME>> to reference dataset columns.
        hyperparameters (Hyperparameters): Configuration for the fine-tuning process.
        additional_info (dict): Extra metadata for the fine-tuning job.
        backend_url (str): URL endpoint for the backend API.
        api_key (str): Authentication key for API access.
        aixplain_key (str): aiXplain-specific API key.
    """

    def __init__(
        self,
        name: Text,
        dataset_list: List[Dataset],
        model: Model,
        cost: FinetuneCost,
        id: Optional[Text] = "",
        description: Optional[Text] = "",
        supplier: Optional[Text] = "aiXplain",
        version: Optional[Text] = "1.0",
        train_percentage: Optional[float] = 100,
        dev_percentage: Optional[float] = 0,
        prompt_template: Optional[Text] = None,
        hyperparameters: Optional[Hyperparameters] = None,
        **additional_info,
    ) -> None:
        """Initialize a new Finetune instance.

        Args:
            name (Text): Name of the fine-tuning job.
            dataset_list (List[Dataset]): List of datasets to use for fine-tuning.
            model (Model): The base model to be fine-tuned.
            cost (FinetuneCost): Cost information for the fine-tuning job.
            id (Text, optional): ID of the job. Defaults to "".
            description (Text, optional): Detailed description of the fine-tuning
                purpose. Defaults to "".
            supplier (Text, optional): Provider/creator of the fine-tuned model.
                Defaults to "aiXplain".
            version (Text, optional): Version identifier. Defaults to "1.0".
            train_percentage (float, optional): Percentage of data to use for
                training. Defaults to 100.
            dev_percentage (float, optional): Percentage of data to use for
                validation. Defaults to 0.
            prompt_template (Text, optional): Template for formatting training
                examples. Use <<COLUMN_NAME>> to reference dataset columns.
                Defaults to None.
            hyperparameters (Hyperparameters, optional): Configuration for the
                fine-tuning process. Defaults to None.
            **additional_info: Extra metadata for the fine-tuning job.
        """
        super().__init__(id, name, description, supplier, version)
        self.model = model
        self.dataset_list = dataset_list
        self.cost = cost
        self.train_percentage = train_percentage
        self.dev_percentage = dev_percentage
        self.prompt_template = prompt_template
        self.hyperparameters = hyperparameters
        self.additional_info = additional_info
        self.backend_url = config.BACKEND_URL
        self.api_key = config.TEAM_API_KEY
        self.aixplain_key = config.AIXPLAIN_API_KEY

    def start(self) -> Model:
        """Start the fine-tuning job on the backend.

        This method submits the fine-tuning configuration to the backend and initiates
        the training process. It handles the creation of the training payload,
        including dataset splits and hyperparameters.

        Returns:
            Model: The model object representing the fine-tuning job. Returns None
                if the job submission fails.

        Raises:
            Exception: If there are errors in the API request or response handling.
        """
        payload = {}
        try:
            url = urljoin(self.backend_url, "sdk/finetune")
            headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}
            payload = {
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
            parameters = {}
            if self.prompt_template is not None:
                parameters["prompt"] = self.prompt_template
            if self.hyperparameters is not None:
                parameters["hyperparameters"] = self.hyperparameters.to_dict()
            payload["parameters"] = parameters
            logging.info(f"Start service for POST Start FineTune - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()
            logging.info(f"Response for POST Start FineTune - Name: {self.name} / Status {resp}")
            from aixplain.factories.model_factory import ModelFactory

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
