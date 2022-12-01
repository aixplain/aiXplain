__author__='shreyassharma'

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

import time
import json
from typing import List
import requests
import logging
import traceback
from aixtend.utils.file_utils import _request_with_retry

class Metric:
    def __init__(self, id:str, name:str, description:str, **additional_info) -> None:
        """Create a Metric with the necessary information

        Args:
            id (str): ID of the Metric
            name (str): Name of the Metric
            description (str): Description of the Metric
            **additional_info: Any additional Metric info to be saved
        """
        self.id = id
        self.name = name
        self.description = description
        self.additional_info = additional_info

    def get_dataset_info(self) -> dict:
        """Get the Metric info as a Dictionary

        Returns:
            dict: Metric Information
        """
        return self.__dict__

    

    
    