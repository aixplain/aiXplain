__author__ = "shreyassharma"

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
Date: December 1st 2022
Description:
    Metric Factory Class
"""

import logging
from typing import List, Optional
from aixplain.modules import Metric
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from typing import Dict, Text
from urllib.parse import urljoin


class MetricFactory:
    """A static factory class for creating and managing Metric objects.

    This class provides functionality to create, retrieve, and list Metric objects
    through the backend API. It includes methods for fetching individual metrics
    by ID and listing metrics with various filtering options.

    Attributes:
        backend_url (str): The URL endpoint for the backend API.
    """

    backend_url = config.BACKEND_URL

    @classmethod
    def _create_metric_from_response(cls, response: Dict) -> Metric:
        """Converts response JSON to a Metric object.

        Args:
            response (Dict): JSON response from the API containing metric data.

        Returns:
            Metric: A new Metric object created from the response data.
        """
        return Metric(
            id=response["id"],
            name=response["name"],
            supplier=response["supplier"],
            is_reference_required=response["referenceRequired"],
            is_source_required=response["sourceRequired"],
            cost=response["normalizedPrice"],
            function=response["function"],
        )

    @classmethod
    def get(cls, metric_id: Text, api_key: str = None) -> Metric:
        """Create a Metric object from a metric ID.

        Args:
            metric_id (Text): The unique identifier of the metric to retrieve.
            api_key (str, optional): API key for authentication. Defaults to None.

        Returns:
            Metric: The retrieved Metric object.

        Raises:
            Exception: If the metric creation fails, with status code and error message.
        """

        resp, status_code = None, 200
        api_key = api_key or config.TEAM_API_KEY
        try:
            url = urljoin(cls.backend_url, f"sdk/metrics/{metric_id}")
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET Metric  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            metric = cls._create_metric_from_response(resp)
        except Exception as e:
            if resp is not None and "statusCode" in resp:
                status_code = resp["statusCode"]
                message = resp["message"]
                message = f"Metric Creation: Status {status_code} - {message}"
            else:
                message = "Metric Creation: Unspecified Error"
            logging.error(f"Metric Creation Failed: {e}")
            raise Exception(f"Status {status_code}: {message}")
        return metric

    @classmethod
    def list(
        cls,
        model_id: Text = None,
        is_source_required: Optional[bool] = None,
        is_reference_required: Optional[bool] = None,
        page_number: int = 0,
        page_size: int = 20,
        api_key: str = None
    ) -> List[Metric]:
        """Get a list of supported metrics based on the given filters.

        Args:
            model_id (Text, optional): ID of model for which metric is to be used. Defaults to None.
            is_source_required (bool, optional): Should the metric use source. Defaults to None.
            is_reference_required (bool, optional): Should the metric use reference. Defaults to None.
            page_number (int, optional): page number. Defaults to 0.
            page_size (int, optional): page size. Defaults to 20.
            api_key (str, optional): API key for authentication. Defaults to None.

        Returns:
            Dict: A dictionary containing:
                - results (List[Metric]): List of filtered metrics
                - page_total (int): Number of items in the current page
                - page_number (int): Current page number
                - total (int): Total number of items matching the filters

        Raises:
            Exception: If there is an error retrieving the metrics list.
        """
        try:
            url = urljoin(cls.backend_url, "sdk/metrics")
            filter_params = {}
            if model_id is not None:
                filter_params["modelId"] = model_id
            if is_source_required is not None:
                filter_params["sourceRequired"] = 1 if is_source_required else 0
            if is_reference_required is not None:
                filter_params["referenceRequired"] = 1 if is_reference_required else 0
            api_key = api_key or config.TEAM_API_KEY
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers, params=filter_params)
            resp = r.json()
            logging.info(f"Listing Metrics: Status of getting metrics: {resp}")
            all_metrics = resp["results"]
            starting_model_index_overall = page_number * page_size
            ending_model_index_overall = starting_model_index_overall + page_size - 1
            filtered_metrics = all_metrics[starting_model_index_overall : ending_model_index_overall + 1]
            total = len(filtered_metrics)
            metric_list = [cls._create_metric_from_response(metric_info_json) for metric_info_json in filtered_metrics]
            return {
                "results": metric_list,
                "page_total": min(page_size, len(metric_list)),
                "page_number": page_number,
                "total": total,
            }
        except Exception as e:
            error_message = f"Listing Metrics: Error in getting metrics: {e}"
            logging.error(error_message, exc_info=True)
            return []
