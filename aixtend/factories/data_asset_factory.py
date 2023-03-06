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
    Dataset Factory Class
"""

import aixtend.utils.config as config
import aixtend.processes.data_onboarding as data_onboarding
import logging
import shutil

from aixtend.factories.asset_factory import AssetFactory
from aixtend.modules.corpus import Corpus
from aixtend.modules.data import Data
from aixtend.modules.dataset import Dataset
from aixtend.modules.metadata import MetaData
from aixtend.enums.function import Function
from aixtend.enums.license import License
from aixtend.enums.privacy import Privacy
from aixtend.utils.file_utils import _request_with_retry, download_data
from aixtend.utils import config
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class DataAssetFactory(AssetFactory):
    api_key = config.TEAM_API_KEY
    backend_url = config.BENCHMARKS_BACKEND_URL

    @classmethod
    def _create_dataset_from_response(cls, response: dict) -> Dataset:
        """Converts response Json to 'Dataset' object

        Args:
            response (dict): Json from API

        Returns:
            Dataset: Coverted 'Dataset' object
        """
        return Dataset(
            response["id"],
            response["name"],
            response["description"],
            field_info=response["attributes"],
            size_info=response["info"],
        )

    @classmethod
    def get(cls, dataset_id: str) -> Dataset:
        """Create a 'Dataset' object from dataset id

        Args:
            dataset_id (str): Dataset ID of required dataset.

        Returns:
            Dataset: Created 'Dataset' object
        """
        url = f"{cls.backend_url}/sdk/datasets/{dataset_id}"
        headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        dataset = cls._create_dataset_from_response(resp)
        return dataset

    @classmethod
    def get_assets_from_page(
        cls, page_number: int, task: str, input_language: str = None, output_language: str = None
    ) -> List[Dataset]:
        """Get the list of datasets from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int): Page from which datasets are to be listed
            task (str): Task of listed datasets
            input_language (str, optional): Input language of listed datasets. Defaults to None.
            output_language (str, optional): Output language of listed datasets. Defaults to None.

        Returns:
            List[Dataset]: List of datasets based on given filters
        """
        try:
            url = f"{cls.backend_url}/sdk/datasets?pageNumber={page_number}&function={task}"
            if input_language is not None:
                url += f"&input={input_language}"
            if output_language is not None:
                url += f"&output={output_language}"
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            logging.info(f"Listing Datasets: Status of getting Datasets on Page {page_number} for {task} : {resp}")
            all_datasets = resp["results"]
            dataset_list = [cls._create_dataset_from_response(dataset_info_json) for dataset_info_json in all_datasets]
            return dataset_list
        except Exception as e:
            error_message = f"Listing Datasets: Error in getting Datasets on Page {page_number} for {task} : {e}"
            logging.error(error_message)
            return []

    @classmethod
    def get_first_k_assets(cls, k: int, task: str, input_language: str = None, output_language: str = None) -> List[Dataset]:
        """Gets the first k given datasets based on the provided task and language filters

        Args:
            k (int): Number of datasets to get
            task (str): Task of listed datasets
            input_language (str, optional): Input language of listed datasets. Defaults to None.
            output_language (str, optional): Output language of listed datasets. Defaults to None.

        Returns:
            List[Dataset]: List of datasets based on given filters
        """
        try:
            dataset_list = []
            assert k > 0
            for page_number in range(k // 10 + 1):
                dataset_list += cls.get_assets_from_page(page_number, task, input_language, output_language)
            return dataset_list
        except Exception as e:
            error_message = f"Listing Datasets: Error in getting {k} Datasets for {task} : {e}"
            logging.error(error_message)
            return []

    @classmethod
    def create_corpus(
        self,
        name: str,
        description: str,
        license: License,
        content_path: Union[Union[str, Path], List[Union[str, Path]]],
        schema: List[Union[Dict, MetaData]],
        tags: Optional[List[str]] = [],
        functions: Optional[List[Function]] = [],
        privacy: Optional[Privacy] = Privacy.PRIVATE,
    ) -> Corpus:
        """Asynchronous call to Upload a dataset to the user's dashboard.

        Args:
            name (str): dataset name
            description (str): dataset description
            license (str): dataset license
            functions (List[str]): AI functions for which the dataset is designed
            data_paths: List[str]: data paths
            field_names: List[str],: data field names
            field_types: List[FieldType],: data field types
            file_format (FileFormat): format of the file
        """
        # check team key
        folder = None
        try:
            if config.TEAM_API_KEY.strip() == "":
                raise Exception(
                    "Data Asset Onboarding Error: Update your team key on the environment variable TEAM_API_KEY before the corpus onboarding process."
                )

            content_paths = content_path
            if isinstance(content_path, list) is False:
                content_paths = [content_path]

            if isinstance(schema[0], MetaData) is False:
                try:
                    schema = [MetaData(**metadata) for metadata in schema]
                except:
                    raise Exception("Data Asset Onboarding Error: Make sure the elements of your schema follows the MetaData class.")
            
            # check whether reserved names are used as data/column names
            for metadata in schema:
                for forbidden_name in data_onboarding.FORBIDDEN_COLUMN_NAMES:
                    if forbidden_name in [metadata.name, metadata.data_column]:
                        raise Exception(f"Data Asset Onboarding Error: {forbidden_name} is reserved name and must not be used as the name of a data or a column.")

            # get file extension paths to process
            paths = data_onboarding.get_paths(content_paths)

            # process data and create files
            folder = Path(name)
            folder.mkdir(exist_ok=True)

            dataset = []
            for metadata in schema:
                if metadata.privacy is None:
                    metadata.privacy = privacy

                files, data_column_idx, start_column_idx, end_column_idx = data_onboarding.process_data_files(data_asset_name=name, metadata=metadata, paths=paths, folder=name)

                dataset.append(
                    Data(id="", 
                         name=metadata.name, 
                         dtype=metadata.dtype, 
                         privacy=metadata.privacy, 
                         data_column=data_column_idx, 
                         start_column=start_column_idx,
                         end_column=end_column_idx,
                         files=files)
                )

            corpus = Corpus(
                id="",
                name=name,
                description=description,
                data=dataset,
                functions=functions,
                tags=tags,
                license=license,
                privacy=privacy,
            )
            corpus_payload = data_onboarding.create_payload_corpus(corpus)
            shutil.rmtree(folder)
        except Exception as e:
            if folder is not None:
                shutil.rmtree(folder)
            raise Exception(e)
        return corpus_payload
