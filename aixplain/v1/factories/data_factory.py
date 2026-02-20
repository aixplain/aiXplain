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
Date: May 15th 2023
Description:
    Data Factory Class
"""

import aixplain.utils.config as config
import logging

from aixplain.factories.asset_factory import AssetFactory
from aixplain.modules.data import Data
from aixplain.enums.data_subtype import DataSubtype
from aixplain.enums.data_type import DataType
from aixplain.enums.language import Language
from aixplain.enums.privacy import Privacy
from aixplain.utils.request_utils import _request_with_retry
from typing import Dict, Text
from urllib.parse import urljoin


class DataFactory(AssetFactory):
    """Factory class for creating and managing data assets.

    This class provides functionality for creating, retrieving, and managing
    data assets in the aiXplain platform. Data assets represent individual
    pieces of data (e.g., text, audio) that can be used in corpora or
    directly with models.

    Attributes:
        backend_url (str): Base URL for the aiXplain backend API.
    """

    backend_url = config.BACKEND_URL

    @classmethod
    def __from_response(cls, response: Dict) -> Data:
        """Convert API response into a Data object.

        This method creates a Data object from an API response, handling the
        conversion of languages, data types, and other attributes.

        Args:
            response (Dict): API response containing:
                - id: Data asset identifier
                - name: Data asset name
                - dataType: Type of data (e.g., text, audio)
                - dataSubtype: Subtype of data
                - metadata: Dictionary containing language configurations
                - status: Onboarding status
                - segmentsCount: Optional number of segments

        Returns:
            Data: Instantiated data asset object with all attributes set.
        """
        languages = []
        if "languages" in response["metadata"]:
            languages = []
            for lng in response["metadata"]["languages"]:
                if "dialect" not in lng:
                    lng["dialect"] = ""
                languages.append(Language(lng))

        data = Data(
            id=response["id"],
            name=response["name"],
            dtype=DataType(response["dataType"]),
            dsubtype=DataSubtype(response["dataSubtype"]),
            privacy=Privacy.PRIVATE,
            languages=languages,
            onboard_status=response["status"],
            length=int(response["segmentsCount"])
            if "segmentsCount" in response and response["segmentsCount"] is not None
            else None,
        )
        return data

    @classmethod
    def get(cls, data_id: Text, api_key: str = None) -> Data:
        """Retrieve a data asset by its ID.

        This method fetches a data asset from the platform using its unique
        identifier.

        Args:
            data_id (Text): Unique identifier of the data asset to retrieve.
            api_key (str): Optional API key for authentication.

        Returns:
            Data: Retrieved data asset object with its configuration.

        Raises:
            Exception: If:
                - Data asset ID is invalid or not found
                - Authentication fails
                - Service is unavailable
        """
        url = urljoin(cls.backend_url, f"sdk/data/{data_id}/overview")
        api_key = api_key or config.TEAM_API_KEY
        headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Data  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if "statusCode" in resp and resp["statusCode"] == 404:
            raise Exception(f"Data GET Error: Data {data_id} not found.")
        return cls.__from_response(resp)
