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
from typing import Dict, List, Optional, Text, Union
import json
import logging
from aixplain.modules.model import Model
from aixplain.enums import Function, Language, Supplier
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin
from warnings import warn


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

        parameters = {}
        if "params" in response:
            for param in response["params"]:
                if "language" in param["name"]:
                    parameters[param["name"]] = [w["value"] for w in param["values"]]

        return Model(
            response["id"],
            response["name"],
            supplier=response["supplier"]["id"],
            api_key=response["api_key"],
            pricing=response["pricing"],
            function=Function(response["function"]["id"]),
            parameters=parameters,
        )

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
    def _get_assets_from_page(
        cls,
        query,
        page_number: int,
        page_size: int,
        function: Function,
        suppliers: Union[Supplier, List[Supplier]],
        source_languages: Union[Language, List[Language]],
        target_languages: Union[Language, List[Language]],
        is_finetunable: bool = None,
    ) -> List[Model]:
        try:
            url = urljoin(cls.backend_url, f"sdk/models/paginate")
            filter_params = {"q": query, "pageNumber": page_number, "pageSize": page_size}
            if is_finetunable is not None:
                filter_params["isFineTunable"] = is_finetunable
            if function is not None:
                filter_params["functions"] = [function.value]
            if suppliers is not None:
                if isinstance(suppliers, Supplier) is True:
                    suppliers = [suppliers]
                filter_params["suppliers"] = [supplier.value for supplier in suppliers]
            lang_filter_params = []
            if source_languages is not None:
                if isinstance(source_languages, Language):
                    source_languages = [source_languages]
                if function == Function.TRANSLATION:
                    lang_filter_params.append({"code": "sourcelanguage", "value": source_languages[0].value["language"]})
                else:
                    lang_filter_params.append({"code": "language", "value": source_languages[0].value["language"]})
                    if source_languages[0].value["dialect"] != "":
                        lang_filter_params.append({"code": "dialect", "value": source_languages[0].value["dialect"]})
            if target_languages is not None:
                if isinstance(target_languages, Language):
                    target_languages = [target_languages]
                if function == Function.TRANSLATION:
                    code = "targetlanguage"
                    lang_filter_params.append({"code": code, "value": target_languages[0].value["language"]})
            if len(lang_filter_params) != 0:
                filter_params["ioFilter"] = lang_filter_params
            if cls.aixplain_key != "":
                headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}

            r = _request_with_retry("post", url, headers=headers, json=filter_params)
            resp = r.json()
            logging.info(f"Listing Models: Status of getting Models on Page {page_number}: {r.status_code}")
            all_models = resp["items"]
            model_list = [cls._create_model_from_response(model_info_json) for model_info_json in all_models]
            return model_list, resp["total"]
        except Exception as e:
            error_message = f"Listing Models: Error in getting Models on Page {page_number}: {e}"
            logging.error(error_message, exc_info=True)
            return []

    @classmethod
    def list(
        cls,
        query: Optional[Text] = "",
        function: Optional[Function] = None,
        suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
        source_languages: Optional[Union[Language, List[Language]]] = None,
        target_languages: Optional[Union[Language, List[Language]]] = None,
        is_finetunable: Optional[bool] = None,
        page_number: int = 0,
        page_size: int = 20,
    ) -> List[Model]:
        """Gets the first k given models based on the provided task and language filters

        Args:
            function (Optional[Function], optional): function filter. Defaults to None.
            source_languages (Optional[Union[Language, List[Language]]], optional): language filter of input data. Defaults to None.
            target_languages (Optional[Union[Language, List[Language]]], optional): language filter of output data. Defaults to None.
            is_finetunable (Optional[bool], optional): can be finetuned or not. Defaults to None.
            page_number (int, optional): page number. Defaults to 0.
            page_size (int, optional): page size. Defaults to 20.

        Returns:
            List[Model]: List of models based on given filters
        """
        print(f"Function: {function}")
        try:
            models, total = cls._get_assets_from_page(
                query, page_number, page_size, function, suppliers, source_languages, target_languages, is_finetunable
            )
            return {
                "results": models,
                "page_total": min(page_size, len(models)),
                "page_number": page_number,
                "total": total,
            }
        except Exception as e:
            error_message = f"Listing Models: Error in Listing Models : {e}"
            logging.error(error_message, exc_info=True)
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
        machines_url = urljoin(config.BACKEND_URL, f"sdk/hosting-machines")
        logging.debug(f"URL: {machines_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        response = _request_with_retry("get", machines_url, headers=headers)
        response_dicts = json.loads(response.text)
        for dictionary in response_dicts:
            del dictionary["id"]
        return response_dicts
    
    @classmethod
    def list_functions(cls, verbose: Optional[bool] = False, 
                       api_key: Optional[Text] = None) -> List[Dict]:
        """Lists supported model functions on platform.

        Args:
            verbose (Boolean, optional): Set to True if a detailed response 
                is desired; is otherwise False by default.
            api_key (Text, optional): Team API key. Defaults to None.

        Returns:
            List[Dict]: List of dictionaries containing information about
            each supported function.
        """
        functions_url = urljoin(config.BACKEND_URL, f"sdk/functions")
        logging.debug(f"URL: {functions_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
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
    def create_asset_repo(cls, name: Text, hosting_machine: Text, version: Text, 
                          description: Text, function: Text,  source_language: Text,
                          api_key: Optional[Text] = None) -> Dict:
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
        function_list = cls.list_functions(True, cls.api_key)["items"]
        function_id = None
        for function_dict in function_list:
            if function_dict["name"] == function:
                function_id = function_dict["id"]
        if function_id is None:
            raise Exception("Invalid function name")
        create_url = urljoin(config.BACKEND_URL, f"sdk/models/register")
        logging.debug(f"URL: {create_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        always_on = False
        is_async = False # Hard-coded to False for first release
        payload = {
            "name": name,
            "hostingMachine": hosting_machine,
            "alwaysOn": always_on,
            "version": version,
            "description": description,
            "function": function_id,
            "isAsync": is_async,
            "sourceLanguage": source_language
        }
        payload = json.dumps(payload)
        logging.debug(f"Body: {str(payload)}")
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
        login_url = urljoin(config.BACKEND_URL, f"sdk/ecr/login")
        logging.debug(f"URL: {login_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        response = _request_with_retry("post", login_url, headers=headers)
        response_dict = json.loads(response.text)
        return response_dict
    
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
        onboard_url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}/onboarding")
        logging.debug(f"URL: {onboard_url}")
        if api_key:
            headers = {"x-api-key": f"{api_key}", "Content-Type": "application/json"}
        else:
            headers = {"x-api-key": f"{cls.api_key}", "Content-Type": "application/json"}
        payload = {
            "image": image_tag,
            "sha": image_hash
        }
        payload = json.dumps(payload)
        logging.debug(f"Body: {str(payload)}")
        response = _request_with_retry("post", onboard_url, headers=headers, data=payload)
        message = "Your onboarding request has been submitted to an aiXplain specialist for finalization. We will notify you when the process is completed."
        logging.info(message)
        return response
