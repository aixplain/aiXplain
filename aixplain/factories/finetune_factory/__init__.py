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
from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin


class FinetuneFactory:
    """Factory class for creating and managing model fine-tuning operations.

    This class provides static methods to create and manage fine-tuning jobs
    for machine learning models. It handles cost estimation, dataset preparation,
    and fine-tuning configuration.

    Attributes:
        backend_url (str): Base URL for the aiXplain backend API.
    """

    backend_url = config.BACKEND_URL

    @classmethod
    def _create_cost_from_response(cls, response: Dict) -> FinetuneCost:
        """Create a FinetuneCost object from an API response.

        Args:
            response (Dict): API response dictionary containing cost information
                with 'trainingCost', 'inferenceCost', and 'hostingCost' fields.

        Returns:
            FinetuneCost: Object containing the parsed cost information for
                training, inference, and hosting.
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
        """Create a new fine-tuning job with the specified configuration.

        This method sets up a fine-tuning job by validating the configuration,
        estimating costs, and preparing the datasets and model. It supports both
        direct Dataset/Model objects and their IDs as inputs.

        Args:
            name (Text): Name for the fine-tuning job.
            dataset_list (List[Union[Dataset, Text]]): List of Dataset objects or dataset IDs
                to use for fine-tuning.
            model (Union[Model, Text]): Model object or model ID to be fine-tuned.
            prompt_template (Text, optional): Template for formatting training examples.
                Use <<COLUMN_NAME>> to reference dataset columns. Defaults to None.
            hyperparameters (Hyperparameters, optional): Fine-tuning hyperparameters
                configuration. Defaults to None.
            train_percentage (float, optional): Percentage of data to use for training.
                Must be > 0. Defaults to 100.
            dev_percentage (float, optional): Percentage of data to use for validation.
                train_percentage + dev_percentage must be <= 100. Defaults to 0.

        Returns:
            Finetune: Configured fine-tuning job object, or None if creation failed.

        Raises:
            AssertionError: If train_percentage <= 0 or train_percentage + dev_percentage > 100.
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
            url = urljoin(cls.backend_url, "sdk/finetune/cost-estimation")
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
