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
from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin
from warnings import warn


class PipelineFactory:
    """Factory class for creating, managing, and exploring pipeline objects.

    This class provides functionality for creating new pipelines, retrieving existing
    pipelines, and managing pipeline configurations in the aiXplain platform.

    Attributes:
        backend_url (str): Base URL for the aiXplain backend API.
    """

    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, pipeline_id: Text, api_key: Optional[Text] = None) -> Pipeline:
        """Retrieve a pipeline by its ID.

        This method fetches an existing pipeline from the aiXplain platform using
        its unique identifier.

        Args:
            pipeline_id (Text): Unique identifier of the pipeline to retrieve.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            Pipeline: Retrieved pipeline object with its configuration and architecture.

        Raises:
            Exception: If the pipeline cannot be retrieved, including cases where:
                - Pipeline ID is invalid
                - Network error occurs
                - Authentication fails
        """
        resp = None
        try:
            url = urljoin(cls.backend_url, f"sdk/pipelines/{pipeline_id}")
            if api_key is not None:
                headers = {
                    "Authorization": f"Token {api_key}",
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
        if 200 <= r.status_code < 300:
            resp["api_key"] = config.TEAM_API_KEY
            if api_key is not None:
                resp["api_key"] = api_key
            pipeline = build_from_response(resp, load_architecture=True)
            logging.info(f"Pipeline {pipeline_id} retrieved successfully.")
            return pipeline

        else:
            error_message = (
                f"Pipeline GET Error: Failed to retrieve pipeline {pipeline_id}. Status Code: {r.status_code}. Error: {resp}"
            )
            logging.error(error_message)
            raise Exception(error_message)

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
        """Retrieve a paginated list of pipelines.

        This method fetches a page of pipelines from the aiXplain platform.
        Each page contains up to 10 pipelines.

        Args:
            page_number (int): Zero-based page number to retrieve.

        Returns:
            List[Pipeline]: List of pipeline objects on the specified page.
                Returns an empty list if an error occurs or no pipelines are found.

        Note:
            This method is primarily used internally by get_first_k_assets.
            For more control over pipeline listing, use the list method instead.
        """
        try:
            url = urljoin(cls.backend_url, f"sdk/pipelines/?pageNumber={page_number}")

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
        """Retrieve the first K pipelines from the platform.

        This method fetches up to K pipelines by making multiple paginated requests
        as needed (10 pipelines per page).

        Args:
            k (int): Number of pipelines to retrieve. Must be positive.

        Returns:
            List[Pipeline]: List of up to K pipeline objects.
                Returns an empty list if an error occurs.

        Note:
            For more control over pipeline listing, use the list method instead.
            This method is maintained for backwards compatibility.
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
        api_key: Optional[Text] = None,
    ) -> Dict:
        """List and filter pipelines with pagination support.

        This method provides comprehensive filtering and pagination capabilities
        for retrieving pipelines from the aiXplain platform.

        Args:
            query (Optional[Text], optional): Search query to filter pipelines by name
                or description. Defaults to None.
            functions (Optional[Union[Function, List[Function]]], optional): Filter by
                function type(s). Defaults to None.
            suppliers (Optional[Union[Supplier, List[Supplier]]], optional): Filter by
                supplier(s). Defaults to None.
            models (Optional[Union[Model, List[Model]]], optional): Filter by specific
                model(s) used in pipelines. Defaults to None.
            input_data_types (Optional[Union[DataType, List[DataType]]], optional):
                Filter by input data type(s). Defaults to None.
            output_data_types (Optional[Union[DataType, List[DataType]]], optional):
                Filter by output data type(s). Defaults to None.
            page_number (int, optional): Zero-based page number. Defaults to 0.
            page_size (int, optional): Number of items per page (1-100).
                Defaults to 20.
            drafts_only (bool, optional): If True, only return draft pipelines.
                Defaults to False.

        Returns:
            Dict: Response containing:
                - results (List[Pipeline]): List of pipeline objects
                - page_total (int): Total items in current page
                - page_number (int): Current page number
                - total (int): Total number of items across all pages

        Raises:
            Exception: If the request fails or if page_size is invalid.
            AssertionError: If page_size is not between 1 and 100.
        """

        url = urljoin(cls.backend_url, "sdk/pipelines/paginate")

        api_key = api_key or config.TEAM_API_KEY
        headers = {
            "Authorization": f"Token {api_key}",
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
        try:
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()

        except Exception as e:
            error_message = f"Pipeline List Error: {str(e)}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
        if 200 <= r.status_code < 300:
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
        else:
            error_message = f"Pipeline List Error: Failed to retrieve pipelines. Status Code: {r.status_code}. Error: {resp}"
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def init(cls, name: Text, api_key: Optional[Text] = None) -> Pipeline:
        """Initialize a new empty pipeline.

        This method creates a new pipeline instance with no nodes or links,
        ready for configuration.

        Args:
            name (Text): Name of the pipeline.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            Pipeline: New pipeline instance with empty configuration.
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
        """Create a new draft pipeline.

        This method creates a new pipeline in draft status from a configuration
        provided either as a Python dictionary or a JSON file.

        Args:
            name (Text): Name of the pipeline.
            pipeline (Union[Text, Dict]): Pipeline configuration either as:
                - Dict: Python dictionary containing nodes and links
                - Text: Path to a JSON file containing the configuration
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            Pipeline: Created pipeline instance in draft status.

        Raises:
            Exception: If:
                - JSON file path is invalid
                - File extension is not .json
                - Pipeline creation request fails
                - Pipeline configuration is invalid
            AssertionError: If the pipeline file doesn't exist or isn't a JSON file.
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