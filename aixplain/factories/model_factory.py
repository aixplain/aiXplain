__author__ = "aiXplain"

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
from typing import Dict, List, Optional, Text
import json
import logging
from aixplain.modules.model import Model
from aixplain.utils.config import MODELS_RUN_URL
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin
from warnings import warn
import click

class ModelFactory:
    """A static class for creating and exploring Model Objects.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """

    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def _create_model_from_response(cls, response: Dict) -> Model:
        """Converts response Json to 'Model' object

        Args:
            response (Dict): Json from API

        Returns:
            Model: Coverted 'Model' object
        """
        if "api_key" not in response:
            response["api_key"] = cls.api_key
        return Model(response["id"], response["name"], supplier=response["supplier"]["id"], api_key=response["api_key"])

    @classmethod
    def get(cls, model_id: Text, api_key: Optional[Text] = None) -> Model:
        """Create a 'Model' object from model id

        Args:
            model_id (Text): Model ID of required model.
            api_key (Optional[Text], optional): Model API key. Defaults to None.

        Returns:
            Model: Created 'Model' object
        """
        resp = None
        try:
            url = urljoin(cls.backend_url, f"sdk/models/{model_id}")
            if cls.aixplain_key != "":
                headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET Metric  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            # set api key
            resp["api_key"] = cls.api_key
            if api_key is not None:
                resp["api_key"] = api_key
            model = cls._create_model_from_response(resp)
            logging.info(f"Model Creation: Model {model_id} instantiated.")
            return model
        except Exception as e:
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Model Creation: Status {status_code} - {message}"
            else:
                message = "Model Creation: Unspecified Error"
            logging.error(message)
            raise Exception(f"{message}")

    @classmethod
    def create_asset_from_id(cls, model_id: Text) -> Model:
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "get" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.get(model_id)

    @classmethod
    def get_assets_from_page(
        cls, page_number: int, task: Text, input_language: Optional[Text] = None, output_language: Optional[Text] = None
    ) -> List[Model]:
        """Get the list of models from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int): Page from which models are to be listed
            task (Text): Task of listed model
            input_language (Text, optional): Input language of listed model. Defaults to None.
            output_language (Text, optional): Output langugage of listed model. Defaults to None.

        Returns:
            List[Model]: List of models based on given filters
        """
        try:
            url = urljoin(cls.backend_url, f"sdk/models/?pageNumber={page_number}&function={task}")
            filter_params = []
            if input_language is not None:
                if task == "translation":
                    code = "sourcelanguage"
                else:
                    code = "language"
                filter_params.append({"code": code, "value": input_language})
            if output_language is not None:
                if task == "translation":
                    code = "targetlanguage"
                    filter_params.append({"code": code, "value": output_language})
            if cls.aixplain_key != "":
                headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers, params={"ioFilter": json.dumps(filter_params)})
            resp = r.json()
            logging.info(f"Listing Models: Status of getting Models on Page {page_number} for {task}: {resp}")
            all_models = resp["items"]
            model_list = [cls._create_model_from_response(model_info_json) for model_info_json in all_models]
            return model_list
        except Exception as e:
            error_message = f"Listing Models: Error in getting Models on Page {page_number} for {task}: {e}"
            logging.error(error_message)
            return []

    @classmethod
    def get_first_k_assets(
        cls, k: int, task: Text, input_language: Optional[Text] = None, output_language: Optional[Text] = None
    ) -> List[Model]:
        """Gets the first k given models based on the provided task and language filters

        Args:
            k (int): Number of models to get
            task (Text): Task of listed model
            input_language (Text, optional): Input language of listed model. Defaults to None.
            output_language (Text, optional): Output language of listed model. Defaults to None.

        Returns:
            List[Model]: List of models based on given filters
        """
        try:
            model_list = []
            assert k > 0
            for page_number in range(k // 10 + 1):
                model_list += cls.get_assets_from_page(page_number, task, input_language, output_language)
            return model_list[0:k]
        except Exception as e:
            error_message = f"Listing Models: Error in getting {k} Models for {task} : {e}"
            logging.error(error_message)
            return []
    
    @classmethod
    def list_host_machines(cls, api_key: Optional[Text] = None) -> List[Dict]:
        """Lists available hosting machines for model.

        Args:
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            List[Dict]: List of dictionaries containing information about
            each hosting machine.
        """
        machines_url = f"{config.BACKEND_URL}sdk/hosting-machines"
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        response = _request_with_retry("get", machines_url, headers=headers)
        return response.json()
    
    @classmethod
    def list_functions(cls, api_key: Optional[Text] = None) -> List[Dict]:
        """Lists supported model functions on platform.

        Args:
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            List[Dict]: List of dictionaries containing information about
            each supported function.
        """
        functions_url = f"{config.BACKEND_URL}sdk/functions"
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        response = _request_with_retry("get", functions_url, headers=headers)
        return response.json()
    
    @classmethod
    def create_asset_repo(cls, name: Text, hosting_machine: Text, always_on: bool, version: Text, 
                          description: Text, function: Text, is_async: bool, api_key: Optional[Text] = None) -> Dict:
        """Creates an image repository for this model and registers it in the 
        platform backend.

        Args:
            name (Text): Model name
            hosting_machine (Text): Hosting machine ID obtained via list_host_machines
            always_on (bool): Whether the model should always be on
            version (Text): Model version
            description (Text): Model description
            function (Text): Model function obtained via #TODO add function endpoint
            is_async (bool): Whether the model is asynchronous or not
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            Dict: Backend response
        """
        create_url = f"{config.BACKEND_URL}sdk/models/register"
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        payload = {
            "name": name,
            "hostingMachine": hosting_machine,
            "alwaysOn": always_on,
            "version": version,
            "description": description,
            "function": function,
            "isAsync": is_async
        }
        payload = json.dumps(payload)
        response = _request_with_retry("post", create_url, headers=headers, data=payload)
        return response.json()
    
    @classmethod
    def asset_repo_login(cls, api_key: Optional[Text] = None) -> Dict:
        """Return login credentials for the image repository that corresponds with 
        the given API_KEY.

        Args:
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            Dict: Backend response
        """
        login_url = f"{config.BACKEND_URL}sdk/ecr/login" 
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        response = _request_with_retry("post", login_url, headers=headers)
        return response.json()
    
    @classmethod
    def onboard_model(cls, model_id: Text, image_tag: Text, image_hash: Text, api_key: Optional[Text] = None) -> Dict:
        """Onboard a model after its image has been pushed to ECR.

        Args:
            model_id (Text): Model ID obtained from CREATE_ASSET_REPO.
            image_tag (Text): Image tag to be onboarded.
            api_key (Text, optional): Team API key. Defaults to None.
        Returns:
            Dict: Backend response
        """ 
        onboard_url = f"{config.BACKEND_URL}sdk/inventory/models/{model_id}/onboarding"
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        payload = {
            "image": image_tag,
            "sha": image_hash
        }
        payload = json.dumps(payload)
        response = _request_with_retry("post", onboard_url, headers=headers, data=payload)
        return response
    
    @classmethod
    def is_onboarded(cls, model_id: Text, host: Text, version: Text, api_key: Optional[Text] = None):
        """Check whether a model has been onboarded.

        Args:
            model_id (Text): Model ID obtained from CREATE_ASSET_REPO.
            api_key (Text, optional): Team API key. Defaults to None.
        Returns:
            Dict: Backend response
        """ 
        is_onboarded_url = f"{config.BACKEND_URL}webhook/models/onboarding"
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        payload = {
            "id": model_id,
            "host": host,
            "version": version
        }
        payload = json.dumps(payload)
        response = _request_with_retry("post", is_onboarded_url, headers=headers, data=payload)
        return response.json()

    @classmethod
    def list_image_repo_tags(cls, model_id: Text, api_key: Optional[Text] = None) -> Dict:
        """List the contents of the image repository corresponding to API_KEY.

        Args:
            model_id (Text): Model ID obtained from CREATE_ASSET_REPO.
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            Dict: Backend response
        """
        list_url = f"{config.BACKEND_URL}sdk/models/{model_id}/images"
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        response = _request_with_retry("get", list_url, headers=headers)
        return response.json()