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
from aixplain.enums.function import Function
from aixplain.enums.language import Language
from aixplain.enums.license import License
from aixplain.enums.privacy import Privacy
from aixplain.utils.file_utils import _request_with_retry
from aixplain.utils import config
from typing import Any, Dict, List, Text
from urllib.parse import urljoin
from uuid import uuid4


class DataFactory(AssetFactory):
    """A static class for creating and exploring Dataset Objects.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """

    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def __from_response(cls, response: Dict) -> Data:
        """Converts Json response to 'Data' object

        Args:
            response (dict): Json from API

        Returns:
            Data: Converted 'Data' object
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
    def get(cls, data_id: Text) -> Data:
        """Create a 'Data' object from dataset id

        Args:
            data_id (Text): Data ID of required dataset.

        Returns:
            Data: Created 'Data' object
        """
        url = urljoin(cls.backend_url, f"sdk/data/{data_id}/overview")
        if cls.aixplain_key != "":
            headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Data  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if "statusCode" in resp and resp["statusCode"] == 404:
            raise Exception(f"Data GET Error: Data {data_id} not found.")
        return cls.__from_response(resp)
