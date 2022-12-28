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


class Dataset(Asset):
    def __init__(
        self, id: str, name: str, description: str, data_url: str = None, field_names: List[str] = None, **additional_info
    ) -> None:
        """Create a Dataset with the necessary information

        Args:
            id (str): ID of the Dataset
            name (str): Name of the Dataset
            description (str): Description of the Dataset
            data_url (str, optional): link to the dataset. Defaults to "".
            **additional_info: Any additional dataset info to be saved
        """
        super().__init__(id, name, description)
        self.data_url = data_url
        self.data = None
        self.field_names = field_names
        self.additional_info = additional_info
    
    def upload_file(self, file_url: str, file_type:str):
        """Asynchronous call to Upload a file to the user's dashboard. 
        Based on the file type, this finctions also compute and
        upload the meta inforamtion of the file (EX: Number of characters,
        duration, size, ...etc.) 
        Args:
            file_url (str): link to the file to be uploaded.
            file_type (str): type of the file (text, audio, ...etc. Shoould be an enum)
        
        It returns the file ID at the end. 
        """
          
    def upload_dataset(self, dataset_url: str, columns_types:dict):
        """Asynchronous call to Upload a dataset to the user's dashboard. 
        The fucntion will compute the meta inforamtion of each row/column in 
        the dataset and the overall aggregate meta inforamtion before uploading
        Args:
            dataset_url (str): link to the dataset to be uploaded.
            columns_types (dict): The key is the column name. The value is a tuple of the column type (text, audio,...etc.) and a boolean (is_url) 
        
        It returns the dataset ID at the end. 
        """
    def check_upload_status(self, data_id: str):
          """ returns the upload status (in progress, compleated, or error)"""
     
    def get_data(self, dataset_id: str, columns: list = None, range_start: int = 0, range_end: int = None):
        """returns a url of specific range of a datset  
        Args:
            dataset_id (str): the id of the dataset.
            columns (list, optional): columns to be retrieved. if empty, return all the columns  
            range_start (int, optional): the index to start from. If not given, start from 0
            range_end (int, optional): the index to end at. If not given, end at the last row           
        
        """
     
    def get_data_meta(self, data_id: str):
        """returns the meta inforamtion about the given data id """
     
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
