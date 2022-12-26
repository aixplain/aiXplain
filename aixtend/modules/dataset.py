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
Date: October 28th 2022
Description:
    Datasets Class
"""
from typing import List
from aixtend.utils.file_utils import _request_with_retry
from aixtend.utils import config


class Dataset:
    def __init__(self, id:str, name:str, description:str, **additional_info) -> None:
        """Create a Dataset with the necessary information

        Args:
            id (str): ID of the Dataset
            name (str): Name of the Dataset
            description (str): Description of the Dataset
            **additional_info: Any additional dataset info to be saved
        """
        self.id = id
        self.name = name
        self.description = description
        self.additional_info = additional_info

    def get_asset_info(self) -> dict:
        """Get the dataset info as a Dictionary

        Returns:
            dict: Dataset Information
        """
        return self.__dict__
