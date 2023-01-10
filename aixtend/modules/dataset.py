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
import pandas as pd
from pathlib import Path
from aixtend.utils.file_utils import _request_with_retry, save_file
import logging
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
    NUMERICAL = "numerical"
    TEXT = "text"
    VIDEO = "video"


class Dataset(Asset):
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        local_path: str = None,
        field_info: List[dict] = None,
        size_info: dict = None,
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
            local_path (str, optional): Local path of the dataset. Defaults to None.
            field_info (List[dict], optional): info about the fields/columns of the dataset. Defaults to None.
            size_info (dict, optional): info about the size of the dataset. Defaults to None.
            load_data (bool, optional): whether the data should be loaded. Defaults to False.
            data_format (Optional[DataFormat], optional): format in which the data should be loaded. Defaults to DataFormat.HUGGINGFACE_DATASETS.
            supplier (Optional[str], optional): author of the dataset. Defaults to "aiXplain".
            version (Optional[str], optional): dataset version. Defaults to "1.0".
            **additional_info: Any additional dataset info to be saved
        """
        super().__init__(id, name, description, supplier, version)
        self.local_path = local_path
        self.data = None
        self.field_info = field_info
        self.size_info = size_info
        self.load_data = load_data
        self.data_format = data_format
        self.additional_info = additional_info

    def download(self, save_path: str = None, returnDataFrame: bool = False):
        """Downloads the dataset file.
        Args:
            save_path (str, optional): Path to save the CSV if returnDataFrame is False. If None, a ranmdom path is generated. defaults to None.
            returnDataFrame (bool, optional): If True, the result is returned as pandas.DataFrame else saved as a CSV file.defaults to False.

        Returns:
            str/pandas.DataFrame: file as path of locally saved file if returnDataFrame is False else as a pandas dataframe
        """
        try:
            dataset_id = self.id
            api_key = config.TEAM_API_KEY
            backend_url = config.BENCHMARKS_BACKEND_URL
            url = f"{backend_url}/sdk/datasets/{dataset_id}/download"
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            print(resp)
            csv_url = resp["url"]
            if returnDataFrame:
                downloaded_path = save_file(csv_url, save_path)
                self.local_path = downloaded_path
                df = pd.read_csv(downloaded_path)
                if save_path is None:
                    Path(downloaded_path).unlink()
                return df
            else:
                downloaded_path = save_file(csv_url, save_path)
                self.local_path = downloaded_path
                return downloaded_path
        except Exception as e:
            error_message = f"Downloading Dataset: Error in Downloading Dataset: {e}"
            logging.error(error_message)
            return None

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
        if self.local_path is not None and not Path(self.local_path).exists():
            logging.info("Get Data: Did not find local path of dataset. Downloading again")
            self.download()
        try:
            df = pd.read_csv(self.local_path)
            df_select = df[start: start+offset]
            if data_format == DataFormat.PANDAS:
                return df_select
            else:
                raise Exception(f"{data_format} - Data format not supported yet")
        except Exception as e:
            error_message = f"Get Data: Error in geting Dataset: {e}"
            logging.error(error_message)
