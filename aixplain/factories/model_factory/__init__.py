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
import json
import logging
from aixplain.modules.model.utility_model import UtilityModel, UtilityModelInput
from aixplain.enums import Function
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin
from aixplain.factories.model_factory.mixins import ModelGetterMixin, ModelListMixin
from typing import Callable, Dict, List, Optional, Text, Union

class ModelFactory(ModelGetterMixin, ModelListMixin):
    """A static class for creating and exploring Model Objects.

    Attributes:
        backend_url (str): The URL for the backend.
    """

    backend_url = config.BACKEND_URL

    @classmethod
    def create_utility_model(
        cls,
        name: Optional[Text] = None,
        code: Union[Text, Callable] = None,
        inputs: List[UtilityModelInput] = [],
        description: Optional[Text] = None,
        output_examples: Text = "",
        api_key: Optional[Text] = None,
    ) -> UtilityModel:
        """Create a utility model

        Args:
            name (Text): name of the model
            code (Union[Text, Callable]): code of the model
            description (Text, optional): description of the model
            inputs (List[UtilityModelInput], optional): inputs of the model
            output_examples (Text, optional): output examples
            api_key (Text, optional): Team API key. Defaults to None.
        Returns:
            UtilityModel: created utility model
        """
        api_key = config.TEAM_API_KEY if api_key is None else api_key
        utility_model = UtilityModel(
            id="",
            name=name,
            description=description,
            inputs=inputs,
            code=code,
            function=Function.UTILITIES,
            api_key=api_key,
            output_examples=output_examples,
        )
        utility_model.validate()
        payload = utility_model.to_dict()
        url = urljoin(cls.backend_url, "sdk/utilities")
        headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        try:
            logging.info(
                f"Start service for POST Utility Model - {url} - {headers} - {payload}"
            )
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()
        except Exception as e:
            logging.error(f"Error creating utility model: {e}")
            raise e

        if 200 <= r.status_code < 300:
            utility_model.id = resp["id"]
            logging.info(
                f"Utility Model Creation: Model {utility_model.id} instantiated."
            )
            return utility_model
        else:
            error_message = f"Utility Model Creation: Failed to create utility model. Status Code: {r.status_code}. Error: {resp}"
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def list_host_machines(cls, api_key: Optional[Text] = None) -> List[Dict]:
        """Lists available hosting machines for model.

        Args:
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            List[Dict]: List of dictionaries containing information about
            each hosting machine.
        """
        machines_url = urljoin(config.BACKEND_URL, "sdk/hosting-machines")
        logging.debug(f"URL: {machines_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {
                "x-api-key": f"{config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
        response = _request_with_retry("get", machines_url, headers=headers)
        response_dicts = json.loads(response.text)
        for dictionary in response_dicts:
            del dictionary["id"]
        return response_dicts

    @classmethod
    def list_gpus(cls, api_key: Optional[Text] = None) -> List[List[Text]]:
        """List GPU names on which you can host your language model.

        Args:
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            List[List[Text]]: List of all available GPUs and their prices.
        """
        gpu_url = urljoin(config.BACKEND_URL, "sdk/model-onboarding/gpus")
        if api_key:
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
        else:
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
        response = _request_with_retry("get", gpu_url, headers=headers)
        response_list = json.loads(response.text)
        return response_list

    @classmethod
    def list_functions(
        cls, verbose: Optional[bool] = False, api_key: Optional[Text] = None
    ) -> List[Dict]:
        """Lists supported model functions on platform.

        Args:
            verbose (Boolean, optional): Set to True if a detailed response
                is desired; is otherwise False by default.
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            List[Dict]: List of dictionaries containing information about
            each supported function.
        """
        functions_url = urljoin(config.BACKEND_URL, "sdk/functions")
        logging.debug(f"URL: {functions_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {
                "x-api-key": f"{config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
        response = _request_with_retry("get", functions_url, headers=headers)
        response_dict = json.loads(response.text)
        if verbose:
            return response_dict
        del response_dict["results"]
        function_list = response_dict["items"]
        for function_dict in function_list:
            del function_dict["output"]
            del function_dict["params"]
            del function_dict["id"]
        return response_dict

    # Will add "always_on" and "is_async" when we support them.
    # def create_asset_repo(cls, name: Text, hosting_machine: Text, version: Text,
    #                       description: Text, function: Text, is_async: bool,
    #                       source_language: Text, api_key: Optional[Text] = None) -> Dict:
    @classmethod
    def create_asset_repo(
        cls,
        name: Text,
        description: Text,
        function: Text,
        source_language: Text,
        input_modality: Text,
        output_modality: Text,
        documentation_url: Optional[Text] = "",
        api_key: Optional[Text] = None,
    ) -> Dict:
        """Creates an image repository for this model and registers it in the
        platform backend.

        Args:
            name (Text): Model name
            hosting_machine (Text): Hosting machine ID obtained via list_host_machines
            always_on (bool): Whether the model should always be on
            version (Text): Model version
            description (Text): Model description
            function (Text): Model function name obtained via LIST_HOST_MACHINES
            is_async (bool): Whether the model is asynchronous or not (False in first release)
            source_language (Text): 2-character 639-1 code or 3-character 639-3 language code.
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            Dict: Backend response
        """
        # Reconcile function name to be function ID in the backend
        function_list = cls.list_functions(True, config.TEAM_API_KEY)["items"]
        function_id = None
        for function_dict in function_list:
            if function_dict["name"] == function:
                function_id = function_dict["id"]
        if function_id is None:
            raise Exception(f"Invalid function name {function}")
        create_url = urljoin(config.BACKEND_URL, "sdk/models/onboard")
        logging.debug(f"URL: {create_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {
                "x-api-key": f"{config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }

        payload = {
            "model": {
                "name": name,
                "description": description,
                "connectionType": ["synchronous"],
                "function": function_id,
                "modalities": [f"{input_modality}-{output_modality}"],
                "documentationUrl": documentation_url,
                "sourceLanguage": source_language,
            },
            "source": "aixplain-ecr",
            "onboardingParams": {},
        }
        logging.debug(f"Body: {str(payload)}")
        response = _request_with_retry(
            "post", create_url, headers=headers, json=payload
        )

        assert response.status_code == 201

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
        login_url = urljoin(config.BACKEND_URL, "sdk/ecr/login")
        logging.debug(f"URL: {login_url}")
        if api_key:
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
        else:
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
        response = _request_with_retry("post", login_url, headers=headers)
        response_dict = json.loads(response.text)
        return response_dict

    @classmethod
    def onboard_model(
        cls,
        model_id: Text,
        image_tag: Text,
        image_hash: Text,
        host_machine: Optional[Text] = "",
        api_key: Optional[Text] = None,
    ) -> Dict:
        """Onboard a model after its image has been pushed to ECR.

        Args:
            model_id (Text): Model ID obtained from CREATE_ASSET_REPO.
            image_tag (Text): Image tag to be onboarded.
            image_hash (Text): Image digest.
            host_machine (Text, optional): Machine on which to host model.
            api_key (Text, optional): Team API key. Defaults to None.
        Returns:
            Dict: Backend response
        """
        onboard_url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}/onboarding")
        logging.debug(f"URL: {onboard_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {
                "x-api-key": f"{config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
        payload = {"image": image_tag, "sha": image_hash, "hostMachine": host_machine}
        logging.debug(f"Body: {str(payload)}")
        response = _request_with_retry(
            "post", onboard_url, headers=headers, json=payload
        )
        if response.status_code == 201:
            message = "Your onboarding request has been submitted to an aiXplain specialist for finalization. We will notify you when the process is completed."
            logging.info(message)
        else:
            message = "An error has occurred. Please make sure your model_id is valid and your host_machine, if set, is a valid option from the LIST_GPUS function."
        return response

    @classmethod
    def deploy_huggingface_model(
        cls,
        name: Text,
        hf_repo_id: Text,
        revision: Optional[Text] = "",
        hf_token: Optional[Text] = "",
        api_key: Optional[Text] = None,
    ) -> Dict:
        """Onboards and deploys a Hugging Face large language model.

        Args:
            name (Text): The user's name for the model.
            hf_repo_id (Text): The Hugging Face repository ID for this model ({author}/{model name}).
            hf_token (Text, optional): Hugging Face access token. Defaults to None.
            api_key (Text, optional): Team API key. Defaults to None.
        Returns:
            Dict: Backend response
        """
        supplier, model_name = hf_repo_id.split("/")
        deploy_url = urljoin(config.BACKEND_URL, "sdk/model-onboarding/onboard")
        if api_key:
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
        else:
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
        body = {
            "model": {
                "name": name,
                "description": "A user-deployed Hugging Face model",
                "connectionType": ["synchronous"],
                "function": "text-generation",
                "documentationUrl": "aiXplain",
                "sourceLanguage": "en",
            },
            "source": "huggingface",
            "onboardingParams": {
                "hf_supplier": supplier,
                "hf_model_name": model_name,
                "hf_token": hf_token,
                "revision": revision,
            },
        }
        response = _request_with_retry("post", deploy_url, headers=headers, json=body)
        logging.debug(response.text)
        response_dicts = json.loads(response.text)
        return response_dicts

    @classmethod
    def get_huggingface_model_status(
        cls, model_id: Text, api_key: Optional[Text] = None
    ):
        """Gets the on-boarding status of a Hugging Face model with ID MODEL_ID.

        Args:
            model_id (Text): The model's ID as returned by DEPLOY_HUGGINGFACE_MODEL
            api_key (Text, optional): Team API key. Defaults to None.
        Returns:
            Dict: Backend response
        """
        status_url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")
        if api_key:
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
        else:
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }
        response = _request_with_retry("get", status_url, headers=headers)
        logging.debug(response.text)
        response_dicts = json.loads(response.text)
        ret_dict = {
            "status": response_dicts["status"],
            "name": response_dicts["name"],
            "id": response_dicts["id"],
            "pricing": response_dicts["pricing"],
        }
        return ret_dict
