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
import aixtend.processes.data_onboarding.onboard_functions as onboard_functions
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
from aixtend.utils.file_utils import _request_with_retry
from aixtend.utils import config
from pathlib import Path
from tqdm import tqdm
from typing import Any, Dict, List, Optional, Text, Union


class DataAssetFactory(AssetFactory):
    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def _create_dataset_from_response(cls, response: Dict) -> Dataset:
        """Converts response Json to 'Dataset' object

        Args:
            response (dict): Json from API

        Returns:
            Dataset: Coverted 'Dataset' object
        """
        return Dataset(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            function=Function.SPEECH_RECOGNITION,
            source_data=[],
            target_data=[],
        )

    @classmethod
    def get(cls, dataset_id: Text) -> Dataset:
        """Create a 'Dataset' object from dataset id

        Args:
            dataset_id (Text): Dataset ID of required dataset.

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
        cls, page_number: int, task: Text, input_language: Optional[Text] = None, output_language: Optional[Text] = None
    ) -> List[Dataset]:
        """Get the list of datasets from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int): Page from which datasets are to be listed
            task (Text): Task of listed datasets
            input_language (Text, optional): Input language of listed datasets. Defaults to None.
            output_language (Text, optional): Output language of listed datasets. Defaults to None.

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
    def get_first_k_assets(
        cls, k: int, task: Text, input_language: Optional[Text] = None, output_language: Optional[Text] = None
    ) -> List[Dataset]:
        """Gets the first k given datasets based on the provided task and language filters

        Args:
            k (int): Number of datasets to get
            task (Text): Task of listed datasets
            input_language (Text, optional): Input language of listed datasets. Defaults to None.
            output_language (Text, optional): Output language of listed datasets. Defaults to None.

        Returns:
            List[Dataset]: List of datasets based on given filters
        """
        try:
            dataset_list = []
            assert k > 0
            for page_number in range(k // 10 + 1):
                dataset_list += cls.get_assets_from_page(page_number, task, input_language, output_language)
            return dataset_list[0:k]
        except Exception as e:
            error_message = f"Listing Datasets: Error in getting {k} Datasets for {task} : {e}"
            logging.error(error_message)
            return []

    @classmethod
    def create_corpus(
        cls,
        name: Text,
        description: Text,
        license: License,
        content_path: Union[Union[Text, Path], List[Union[Text, Path]]],
        schema: List[Union[Dict, MetaData]],
        ref_data: Optional[List[Any]] = [],
        tags: Optional[List[Text]] = [],
        functions: Optional[List[Function]] = [],
        privacy: Optional[Privacy] = Privacy.PRIVATE,
    ) -> Dict:
        """Asynchronous call to Upload a corpus to the user's dashboard.

        Args:
            name (Text): corpus name
            description (Text): corpus description
            license (License): corpus license
            content_path (Union[Union[Text, Path], List[Union[Text, Path]]]): path to .csv files containing the data
            schema (List[Union[Dict, MetaData]]): meta data
            ref_data (Optional[List[Union[Text, Data]]], optional): referencing data which already exists and should be part of the corpus. Defaults to [].
            tags (Optional[List[Text]], optional): tags that explain the corpus. Defaults to [].
            functions (Optional[List[Function]], optional): AI functions for which the corpus may be used. Defaults to [].
            privacy (Optional[Privacy], optional): visibility of the corpus. Defaults to Privacy.PRIVATE.

        Returns:
            Dict: response dict
        """
        folder, return_dict = None, {}
        # check team key
        try:
            if config.TEAM_API_KEY.strip() == "":
                message = "Data Asset Onboarding Error: Update your team key on the environment variable TEAM_API_KEY before the corpus onboarding process."
                logging.error(message)
                raise Exception(message)

            content_paths = content_path
            if isinstance(content_path, list) is False:
                content_paths = [content_path]

            if isinstance(schema[0], MetaData) is False:
                try:
                    schema = [MetaData(**metadata) for metadata in schema]
                except:
                    message = "Data Asset Onboarding Error: Make sure the elements of your schema follows the MetaData class."
                    logging.error(message)
                    raise Exception(message)

            if len(ref_data) > 0:
                if isinstance(ref_data[0], Data):
                    ref_data = [w.id for w in ref_data]
                # TO DO: check whether the referred data exist. Otherwise, raise an exception

            # check whether reserved names are used as data/column names
            for metadata in schema:
                for forbidden_name in onboard_functions.FORBIDDEN_COLUMN_NAMES:
                    if forbidden_name in [metadata.name, metadata.data_column]:
                        message = f"Data Asset Onboarding Error: {forbidden_name} is reserved name and must not be used as the name of a data or a column."
                        logging.error(message)
                        raise Exception(message)

            # get file extension paths to process
            paths = onboard_functions.get_paths(content_paths)

            # process data and create files
            folder = Path(name)
            folder.mkdir(exist_ok=True)

            dataset = []
            for i in tqdm(range(len(schema)), desc=" Corpus onboarding progress:", position=0):
                metadata = schema[i]
                if metadata.privacy is None:
                    metadata.privacy = privacy

                files, data_column_idx, start_column_idx, end_column_idx = onboard_functions.process_data_files(
                    data_asset_name=name, metadata=metadata, paths=paths, folder=name
                )

                dataset.append(
                    Data(
                        id="",
                        name=metadata.name,
                        dtype=metadata.dtype,
                        privacy=metadata.privacy,
                        data_column=data_column_idx,
                        start_column=start_column_idx,
                        end_column=end_column_idx,
                        files=files,
                    )
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
            corpus_payload = onboard_functions.build_payload_corpus(corpus, ref_data)

            response = onboard_functions.create_corpus(corpus_payload)
            if response["success"] is True:
                return_dict = {"status": response["status"], "corpus_id": response["corpus_id"]}
            else:
                raise Exception(response["error"])
            shutil.rmtree(folder)
        except Exception as e:
            if folder is not None:
                shutil.rmtree(folder)
            raise Exception(e)
        return return_dict
