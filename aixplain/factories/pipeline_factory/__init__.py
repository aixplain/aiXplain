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
    Pipeline Factory Class
"""
import json
import os
import logging
from typing import Dict, List, Optional, Text, Union
from aixplain.factories.pipeline_factory.utils import build_from_response
from aixplain.enums.data_type import DataType
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.modules.model import Model
from aixplain.modules.pipeline import Pipeline
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin
from warnings import warn


class PipelineFactory:
    """A static class for creating and exploring Pipeline Objects.

    Attributes:
        backend_url (str): The URL for the backend.
    """

    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, pipeline_id: Text, api_key: Optional[Text] = None) -> Pipeline:
        """Create a 'Pipeline' object from pipeline id

        Args:
            pipeline_id (Text): Pipeline ID of required pipeline.
            api_key (Optional[Text], optional): Pipeline API key. Defaults to None.

        Returns:
            Pipeline: Created 'Pipeline' object
        """
        resp = None
        try:
            url = urljoin(cls.backend_url, f"sdk/pipelines/{pipeline_id}")
            if api_key is not None:
                headers = {
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "application/json",
                }
            elif cls.aixplain_key != "":
                headers = {
                    "x-aixplain-key": f"{cls.aixplain_key}",
                    "Content-Type": "application/json",
                }
            else:
                headers = {
                    "Authorization": f"Token {config.TEAM_API_KEY}",
                    "Content-Type": "application/json",
                }
            logging.info(f"Start service for GET Pipeline  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            # set api key
            resp["api_key"] = config.TEAM_API_KEY
            if api_key is not None:
                resp["api_key"] = api_key
            pipeline = build_from_response(resp, load_architecture=True)
            return pipeline
        except Exception as e:
            logging.exception(e)
            status_code = 400
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Pipeline Creation: Status {status_code} - {message}"
            else:
                message = f"Pipeline Creation: Unspecified Error {e}"
            logging.error(message)
            raise Exception(f"Status {status_code}: {message}")

    @classmethod
    def create_asset_from_id(cls, pipeline_id: Text) -> Pipeline:
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "get" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.get(pipeline_id)

    @classmethod
    def get_assets_from_page(cls, page_number: int) -> List[Pipeline]:
        """Get the list of pipelines from a given page

        Args:
            page_number (int): Page from which pipelines are to be listed
        Returns:
            List[Pipeline]: List of pipelines based on given filters
        """
        try:
            url = urljoin(cls.backend_url, f"sdk/pipelines/?pageNumber={page_number}")
            if cls.aixplain_key != "":
                headers = {
                    "x-aixplain-key": f"{cls.aixplain_key}",
                    "Content-Type": "application/json",
                }
            else:
                headers = {
                    "Authorization": f"Token {config.TEAM_API_KEY}",
                    "Content-Type": "application/json",
                }
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Pipelines: Status of getting Pipelines on Page {page_number}: {resp}")
            all_pipelines = resp["items"]
            pipeline_list = [build_from_response(pipeline_info_json) for pipeline_info_json in all_pipelines]
            return pipeline_list
        except Exception as e:
            error_message = f"Listing Pipelines: Error in getting Pipelines on Page {page_number}: {e}"
            logging.error(error_message, exc_info=True)
            return []

    @classmethod
    def get_first_k_assets(cls, k: int) -> List[Pipeline]:
        """Gets the first k given pipelines based on the provided task and language filters

        Args:
            k (int): Number of pipelines to get
        Returns:
            List[Pipeline]: List of pipelines based on given filters
        """
        try:
            pipeline_list = []
            assert k > 0
            for page_number in range(k // 10 + 1):
                pipeline_list += cls.get_assets_from_page(page_number)
            return pipeline_list
        except Exception as e:
            error_message = f"Listing Pipelines: Error in getting {k} Pipelines: {e}"
            logging.error(error_message, exc_info=True)
            return []

    @classmethod
    def list(
        cls,
        query: Optional[Text] = None,
        functions: Optional[Union[Function, List[Function]]] = None,
        suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
        models: Optional[Union[Model, List[Model]]] = None,
        input_data_types: Optional[Union[DataType, List[DataType]]] = None,
        output_data_types: Optional[Union[DataType, List[DataType]]] = None,
        page_number: int = 0,
        page_size: int = 20,
        drafts_only: bool = False,
    ) -> Dict:

        url = urljoin(cls.backend_url, "sdk/pipelines/paginate")
        if cls.aixplain_key != "":
            headers = {
                "x-aixplain-key": f"{cls.aixplain_key}",
                "Content-Type": "application/json",
            }
        else:
            headers = {
                "Authorization": f"Token {config.TEAM_API_KEY}",
                "Content-Type": "application/json",
            }

        assert 0 < page_size <= 100, "Pipeline List Error: Page size must be greater than 0 and not exceed 100."
        payload = {
            "pageSize": page_size,
            "pageNumber": page_number,
            # "sort": [{"field": "createdAt", "dir": -1}],
            "draftsOnly": drafts_only,
        }

        if query is not None:
            payload["q"] = str(query)

        if functions is not None:
            if isinstance(functions, Function) is True:
                functions = [functions]
            payload["functions"] = [function.value for function in functions]

        if suppliers is not None:
            if isinstance(suppliers, Supplier) is True:
                suppliers = [suppliers]
            payload["suppliers"] = [supplier.value for supplier in suppliers]

        if models is not None:
            if isinstance(models, Model) is True:
                models = [models]
            payload["models"] = [model.id for model in models]

        if input_data_types is not None:
            if isinstance(input_data_types, DataType) is True:
                input_data_types = [input_data_types]
            payload["inputDataTypes"] = [data_type.value for data_type in input_data_types]

        if output_data_types is not None:
            if isinstance(output_data_types, DataType) is True:
                output_data_types = [output_data_types]
            payload["inputDataTypes"] = [data_type.value for data_type in output_data_types]

        logging.info(f"Start service for POST List Pipeline - {url} - {headers} - {json.dumps(payload)}")
        r = _request_with_retry("post", url, headers=headers, json=payload)
        resp = r.json()

        pipelines, page_total, total = [], 0, 0
        if "items" in resp:
            results = resp["items"]
            page_total = resp["pageTotal"]
            total = resp["total"]
            logging.info(f"Response for POST List Pipeline - Page Total: {page_total} / Total: {total}")
            for pipeline in results:
                pipelines.append(build_from_response(pipeline))
        return {
            "results": pipelines,
            "page_total": page_total,
            "page_number": page_number,
            "total": total,
        }

    @classmethod
    def init(cls, name: Text, api_key: Optional[Text] = None) -> Pipeline:
        """Initialize a new Pipeline

        Args:
            name (Text): Pipeline Name
            api_key (Optional[Text], optional): Team API Key to create the Pipeline. Defaults to None.

        Returns:
            Pipeline: instance of the new pipeline
        """
        if api_key is None:
            api_key = config.TEAM_API_KEY
        return Pipeline(
            id="",
            name=name,
            api_key=api_key,
            nodes=[],
            links=[],
            instance=None,
        )

    @classmethod
    def create(
        cls,
        name: Text,
        pipeline: Union[Text, Dict],
        api_key: Optional[Text] = None,
    ) -> Pipeline:
        """Draft Pipeline Creation

        Args:
            name (Text): Pipeline Name
            pipeline (Union[Text, Dict]): Pipeline as a Python dictionary or in a JSON file
            api_key (Optional[Text], optional): Team API Key to create the Pipeline. Defaults to None.

        Raises:
            Exception: Currently just the creation of draft pipelines are supported

        Returns:
            Pipeline: instance of the new pipeline
        """
        try:
            if isinstance(pipeline, str) is True:
                _, ext = os.path.splitext(pipeline)
                assert (
                    os.path.exists(pipeline) and ext == ".json"
                ), "Pipeline Creation Error: Make sure the pipeline to be saved is in a JSON file."
                with open(pipeline) as f:
                    pipeline = json.load(f)

            for i, node in enumerate(pipeline["nodes"]):
                if "functionType" in node:
                    pipeline["nodes"][i]["functionType"] = pipeline["nodes"][i]["functionType"].lower()
            # prepare payload
            payload = {
                "name": name,
                "status": "draft",
                "architecture": pipeline,
            }
            url = urljoin(cls.backend_url, "sdk/pipelines")
            api_key = api_key if api_key is not None else config.TEAM_API_KEY
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json",
            }
            logging.info(f"Start service for POST Create Pipeline - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            response = r.json()

            return Pipeline(response["id"], name, api_key)
        except Exception as e:
            raise Exception(e)
