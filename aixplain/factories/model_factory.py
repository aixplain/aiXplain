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
from aixplain.enums import Function, Language, License, Privacy
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
        page_number: int,
        function: Function,
        source_languages: Union[Language, List[Language]],
        target_languages: Union[Language, List[Language]],
        is_finetunable: bool = None,
    ) -> List[Model]:
        try:
            url = urljoin(cls.backend_url, f"sdk/models")
            filter_params = {"pageNumber": page_number}
            if is_finetunable is not None:
                filter_params["isFineTunable"] = str(is_finetunable).lower()
            if function is not None:
                filter_params["function"] = function.value
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
                filter_params["ioFilter"] = json.dumps(lang_filter_params)
            if cls.aixplain_key != "":
                headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}

            r = _request_with_retry("get", url, headers=headers, params=filter_params)
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
        function: Optional[Function] = None,
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
        try:
            model_list = []
            starting_model_index_overall = page_number * page_size
            ending_model_index_overall = starting_model_index_overall + page_size - 1
            starting_model_page_number = starting_model_index_overall // 10
            ending_model_page_number = ending_model_index_overall // 10
            starting_model_index_filtered = starting_model_index_overall - (starting_model_page_number * 10)
            ending_model_index_filtered = starting_model_index_filtered + page_size - 1
            for current_page_number in range(starting_model_page_number, ending_model_page_number + 1):
                models_on_current_page, total = cls._get_assets_from_page(
                    current_page_number, function, source_languages, target_languages, is_finetunable
                )
                model_list += models_on_current_page
            filtered_model_list = model_list[starting_model_index_filtered : ending_model_index_filtered + 1]
            return {
                "results": filtered_model_list,
                "page_total": min(page_size, len(filtered_model_list)),
                "page_number": page_number,
                "total": total,
            }
        except Exception as e:
            error_message = f"Listing Models: Error in Listing Models : {e}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
