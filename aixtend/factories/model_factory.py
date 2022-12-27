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
Date: September 1st 2022
Description:
    Model Factory Class
"""
from typing import List
import json
import logging
from aixtend.modules.model import Model
from aixtend.utils.config import MODELS_RUN_URL
from aixtend.utils import config
from aixtend.utils.file_utils import _request_with_retry


class ModelFactory:
    api_key = config.TEAM_API_KEY
    backend_url = config.BENCHMARKS_BACKEND_URL

    @classmethod
    def _create_model_from_response(cls, response: dict) -> Model:
        """Converts response Json to 'Model' object

        Args:
            response (dict): Json from API

        Returns:
            Model: Coverted 'Model' object
        """
        sub_api_key = response["subscription"].get("apiKey", None) if "subscription" in response else None
        sub_id = response["subscription"].get("id", None) if "subscription" in response else None
        return Model(response["id"], response["name"], response["supplier"]["id"], api_key=sub_api_key, subscription_id=sub_id)

    @classmethod
    def create_asset_from_id(cls, model_id: str) -> Model:
        """Create a 'Model' object from model id

        Args:
            model_id (str): Model ID of required model.

        Returns:
            Model: Created 'Model' object
        """
        try:
            url = f"{cls.backend_url}/sdk/inventory/models/{model_id}"
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            model = cls._create_model_from_response(resp)
            return model
        except Exception as e:
            if "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Model Creation: Status {status_code} - {message}"
            else:
                message = "Model Creation: Unspecified Error"
            logging.error(message)
            raise Exception(f"{message}")

    @classmethod
    def subscribe_to_asset(cls, model: Model) -> None:
        """Subscribe to the given model

        Args:
            model (Model): 'Model' object to subscribe to
        """
        if model._is_subscribed():
            logging.info(f"Model Subscription: {model.name} is already subscribed.")
            return
        url = f"{cls.backend_url}/sdk/inventory/models/{model.id}/enable"
        headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("post", url, headers=headers)
        resp = r.json()
        model.subscription_id = resp["id"]
        model.api_key = resp["apiKey"]

    @classmethod
    def unsubscribe_to_asset(cls, model: Model) -> None:
        """Unsubscribe to the given model

        Args:
            model (Model): 'Model' object to unsubscribe to
        """
        if not model._is_subscribed():
            logging.info(f"Model Unsubscription: {model.name} is not subsribed to.")
            return
        url = f"{cls.backend_url}/sdk/inventory/models/{model.subscription_id}/disable"
        headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("post", url, headers=headers)
        resp = r.json()
        model.subscription_id = None
        model.api_key = None

    @classmethod
    def get_assets_from_page(
        cls, page_number: int, task: str, input_language: str = None, output_language: str = None
    ) -> List[Model]:
        """Get the list of models from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int): Page from which models are to be listed
            task (str): Task of listed model
            input_language (str, optional): Input language of listed model. Defaults to None.
            output_language (str, optional): Output langugage of listed model. Defaults to None.

        Returns:
            List[Model]: List of models based on given filters
        """
        try:
            url = f"{cls.backend_url}/sdk/inventory/models/?pageNumber={page_number}&function={task}"
            filter_params = []
            task_param_mapping = {
                "input": {"translation": "sourcelanguage", "speech-recognition": "language", "sentiment-analysis": "language"},
                "ouput": {"translation": "targetlanguage"},
            }
            if input_language is not None:
                if task in task_param_mapping["input"]:
                    filter_params.append({"code": task_param_mapping["input"][task], "value": input_language})
            if output_language is not None:
                if task in task_param_mapping["ouput"]:
                    filter_params.append({"code": task_param_mapping["ouput"][task], "value": output_language})
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers, params={"ioFilter": json.dumps(filter_params)})
            resp = r.json()
            logging.info(f"Listing Models: Status of getting Models on Page {page_number} for {task} : {resp}")
            all_models = resp["items"]
            model_list = [cls._create_model_from_response(model_info_json) for model_info_json in all_models]
            return model_list
        except Exception as e:
            error_message = f"Listing Models: Error in getting Models on Page {page_number} for {task} : {e}"
            logging.error(error_message)
            return []

    @classmethod
    def get_first_k_assets(cls, k: int, task: str, input_language: str = None, output_language: str = None) -> List[Model]:
        """Gets the first k given models based on the provided task and language filters

        Args:
            k (int): Number of models to get
            task (str): Task of listed model
            input_language (str, optional): Input language of listed model. Defaults to None.
            output_language (str, optional): Output language of listed model. Defaults to None.

        Returns:
            List[Model]: List of models based on given filters
        """
        try:
            model_list = []
            assert k > 0
            for page_number in range(k // 10 + 1):
                model_list += cls.get_models_from_page(page_number, task, input_language, output_language)
            return model_list
        except Exception as e:
            error_message = f"Listing Models: Error in getting {k} Models for {task} : {e}"
            logging.error(error_message)
            return []
