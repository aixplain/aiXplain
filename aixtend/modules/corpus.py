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
Date: February 1st 2023
Description:
    Corpus Class
"""
import logging
import pandas as pd
from aixtend.enums.function import Function
from aixtend.enums.license import License
from aixtend.enums.privacy import Privacy
from aixtend.modules.asset import Asset
from aixtend.modules.data import Data
from aixtend.utils.file_utils import _request_with_retry, save_file
from aixtend.utils import config
from pathlib import Path
from typing import Any, List, Optional


class Corpus(Asset):
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        data: List[Data],
        functions: Optional[List[Function]] = [],
        tags: Optional[List[str]] = [],
        license: Optional[License] = None,
        privacy: Optional[Privacy] = Privacy.PRIVATE,
        supplier: Optional[str] = "aiXplain",
        version: Optional[str] = "1.0",
        **kwargs,
    ) -> None:
        super().__init__(
            id=id, name=name, description=description, supplier=supplier, version=version, license=license, privacy=privacy
        )
        self.functions = functions
        self.tags = tags
        self.data = data
        self.kwargs = kwargs

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
