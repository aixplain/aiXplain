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
import logging
from typing import List
from aixplain.modules.pipeline import Pipeline
from aixplain.utils.config import PIPELINES_RUN_URL
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry


class PipelineFactory:
    """A static class for creating and exploring Pipeline Objects.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """
    api_key = config.TEAM_API_KEY
    backend_url = config.BENCHMARKS_BACKEND_URL

    @classmethod
    def _create_pipeline_from_response(cls, response: dict) -> Pipeline:
        """Converts response Json to 'Pipeline' object

        Args:
            response (dict): Json from API

        Returns:
            Pipeline: Coverted 'Pipeline' object
        """
        return Pipeline(response["id"], response["name"], cls.api_key)
    
    @classmethod
    def create_asset_from_id(cls, pipeline_id: str) -> Pipeline:
        """Create a 'Pipeline' object from pipeline id

        Args:
            pipeline_id (str): Pipeline ID of required pipeline.

        Returns:
            Pipeline: Created 'Pipeline' object
        """
        try:
            resp = None
            url = f"{cls.backend_url}/sdk/inventory/pipelines/{pipeline_id}"
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            pipeline = cls._create_pipeline_from_response(resp)
            return pipeline
        except Exception as e:
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Pipeline Creation: Status {status_code} - {message}"
            else:
                message = "Pipeline Creation: Unspecified Error"
            logging.error(message)
            raise Exception(f"Status {status_code}: {message}")
        
    @classmethod
    def get_assets_from_page(cls, page_number: int) -> List[Pipeline]:
        """Get the list of pipelines from a given page

        Args:
            page_number (int): Page from which pipelines are to be listed
        Returns:
            List[Pipeline]: List of pipelines based on given filters
        """
        try:
            url = f"{cls.backend_url}/sdk/inventory/pipelines/?pageNumber={page_number}"
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Pipelines: Status of getting Pipelines on Page {page_number}: {resp}")
            all_pipelines = resp["items"]
            pipeline_list = [cls._create_pipeline_from_response(pipeline_info_json) for pipeline_info_json in all_pipelines]
            return pipeline_list
        except Exception as e:
            error_message = f"Listing Pipelines: Error in getting Pipelines on Page {page_number}: {e}"
            logging.error(error_message)
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
            logging.error(error_message)
            return []
