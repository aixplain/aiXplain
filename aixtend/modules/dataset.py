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
Date: October 28th 2022
Description:
    Datasets Class
"""
from aixtend.modules.asset import Asset
from aixtend.utils.file_utils import _request_with_retry
from aixtend.utils import config
from typing import Any, Dict, List, Optional
from enum import Enum


class DataFormat(Enum):
    DICT = "dict"
    PANDAS = "pandas"
    HUGGINGFACE_DATASETS = "huggingface_datasets"


class FileFormat(Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    PARQUET = "parquet"


class FieldType(Enum):
    AUDIO = "audio"
    IMAGE = "image"
    LABEL = "label"
    TEXT = "text"
    VIDEO = "video"


class Dataset(Asset):
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        data_url: str = None,
        field_names: List[str] = None,
        load_data: bool = False,
        data_format: Optional[DataFormat] = DataFormat.HUGGINGFACE_DATASETS,
        supplier: Optional[str] = "aiXplain",
        version: Optional[str] = "1.0",
        **additional_info
    ) -> None:
        """Create a Dataset with the necessary information

        Args:
            id (str): ID of the Dataset
            name (str): Name of the Dataset
            description (str): Description of the Dataset
            data_url (str, optional): link to the dataset. Defaults to "".
            field_names (List[str], optional): name of the fields/columns of the dataset. Defaults to None.
            load_data (bool, optional): whether the data should be loaded. Defaults to False.
            data_format (Optional[DataFormat], optional): format in which the data should be loaded. Defaults to DataFormat.HUGGINGFACE_DATASETS.
            supplier (Optional[str], optional): author of the dataset. Defaults to "aiXplain".
            version (Optional[str], optional): dataset version. Defaults to "1.0".
            **additional_info: Any additional dataset info to be saved
        """
        super().__init__(id, name, description, supplier, version)
        self.data_url = data_url
        self.data = None
        self.field_names = field_names
        self.load_data = load_data
        self.data_format = data_format
        self.additional_info = additional_info

    def __download_data(self):
        """Download dataset present in `data_url` to locally handle it"""
        pass

    def get_data(
        self,
        fields: Optional[list] = None,
        start: Optional[int] = 0,
        offset: Optional[int] = 100,
        data_format: Optional[DataFormat] = DataFormat.PANDAS,
    ) -> Any:
        """Get data fields from a dataset sample of size `offset` starting from the `start`th row.

        Args:
            fields (list, optional): list of fields (columns). If None, selects all. Defaults to None.
            start (int, optional): start row index. Defaults to 0.
            offset (int, optional): number of rows. Defaults to 100.

        Returns:
            Any: data
        """
        pass
