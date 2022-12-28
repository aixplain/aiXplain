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
Date: October 25th 2022
Description:
    Metric Class
"""

from typing import List, Optional
from aixtend.modules.asset import Asset
from aixtend.utils.file_utils import _request_with_retry


class Metric(Asset):
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        supplier: Optional[str] = "aiXplain",
        version: Optional[str] = "1.0",
        **additional_info
    ) -> None:
        """Create a Metric with the necessary information

        Args:
            id (str): ID of the Metric
            name (str): Name of the Metric
            description (str): Description of the Metric
            supplier (Optional[str], optional): author of the Metric. Defaults to "aiXplain".
            version (Optional[str], optional): Metric version. Defaults to "1.0".
            **additional_info: Any additional Metric info to be saved
        """
        super().__init__(id, name, description, supplier, version)
        self.additional_info = additional_info
