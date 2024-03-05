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
    Finetune Factory Class
"""

import logging
from typing import Dict, List, Optional, Text, Union
import json
from aixplain.factories.dataset_factory import DatasetFactory
from aixplain.factories.finetune_factory.prompt_validator import validate_prompt
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules.finetune import Finetune
from aixplain.modules.finetune.cost import FinetuneCost
from aixplain.modules.finetune.hyperparameters import Hyperparameters
from aixplain.modules.dataset import Dataset
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin


class FinetuneFactory:
    """A static class for creating and managing the FineTune experience.

    Attributes:
        backend_url (str): The URL for the backend.
    """

    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def _create_cost_from_response(cls, response: Dict) -> FinetuneCost:
        """Create a Cost object from the response dictionary.

        Args:
            response (Dict): The response dictionary containing cost information.

        Returns:
            Cost: The Cost object created from the response.
        """
        return FinetuneCost(response["trainingCost"], response["inferenceCost"], response["hostingCost"])

    @classmethod
    def create(
        cls,
        name: Text,
        dataset_list: List[Union[Dataset, Text]],
        model: Union[Model, Text],
        prompt_template: Optional[Text] = None,
        hyperparameters: Optional[Hyperparameters] = None,
        train_percentage: Optional[float] = 100,
        dev_percentage: Optional[float] = 0,
    ) -> Finetune:
        """Create a Finetune object with the provided information.

        Args:
            name (Text): Name of the Finetune.
            dataset_list (List[Dataset]): List of Datasets (or dataset IDs) to be used for fine-tuning.
            model (Model): Model (Model ID) to be fine-tuned.
            prompt_template (Text, optional): Fine-tuning prompt_template. Should reference columns in the dataset using format <<COLUMN_NAME>>. Defaults to None.
            hyperparameters (Hyperparameters, optional): Hyperparameters for fine-tuning. Defaults to None.
            train_percentage (float, optional): Percentage of training samples. Defaults to 100.
            dev_percentage (float, optional): Percentage of development samples. Defaults to 0.
        Returns:
            Finetune: The Finetune object created with the provided information or None if there was an error.
        """
        payload = {}
        assert train_percentage > 0, f"Create FineTune: Train percentage ({train_percentage}) must be greater than zero"
        assert (
            train_percentage + dev_percentage <= 100
        ), f"Create FineTune: Train percentage + dev percentage ({train_percentage + dev_percentage}) must be less than or equal to one"
        
        for i, dataset in enumerate(dataset_list):
            if isinstance(dataset, str) is True:
                dataset_list[i] = DatasetFactory.get(dataset_id=dataset)
        
        if isinstance(model, str) is True:
            model = ModelFactory.get(model_id=model)

        if prompt_template is not None:
            prompt_template = validate_prompt(prompt_template, dataset_list)
        try:
            url = urljoin(cls.backend_url, f"sdk/finetune/cost-estimation")
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            payload = {
                "datasets": [
                    {"datasetId": dataset.id, "trainPercentage": train_percentage, "devPercentage": dev_percentage}
                    for dataset in dataset_list
                ],
                "sourceModelId": model.id,
            }
            parameters = {}
            if prompt_template is not None:
                parameters["prompt"] = prompt_template
            if hyperparameters is not None:
                parameters["hyperparameters"] = hyperparameters.to_dict()
            payload["parameters"] = parameters
            logging.info(f"Start service for POST Create FineTune - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()
            logging.info(f"Response for POST Create FineTune - Status {resp}")
            cost = cls._create_cost_from_response(resp)
            return Finetune(
                name,
                dataset_list,
                model,
                cost,
                train_percentage=train_percentage,
                dev_percentage=dev_percentage,
                prompt_template=prompt_template,
                hyperparameters=hyperparameters,
            )
        except Exception:
            error_message = f"Create FineTune: Error with payload {json.dumps(payload)}"
            logging.exception(error_message)
            return None
