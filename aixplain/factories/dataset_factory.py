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

import aixplain.utils.config as config
import aixplain.processes.data_onboarding.onboard_functions as onboard_functions
import logging
import shutil

from aixplain.factories.asset_factory import AssetFactory
from aixplain.modules.data import Data
from aixplain.modules.dataset import Dataset
from aixplain.modules.metadata import MetaData
from aixplain.enums.data_type import DataType
from aixplain.enums.function import Function
from aixplain.enums.language import Language
from aixplain.enums.license import License
from aixplain.enums.privacy import Privacy
from aixplain.utils.file_utils import _request_with_retry
from aixplain.utils import config
from pathlib import Path
from tqdm import tqdm
from typing import Any, Dict, List, Optional, Text, Union
from urllib.parse import urljoin
from uuid import uuid4
from warnings import warn


class DatasetFactory(AssetFactory):
    """A static class for creating and exploring Dataset Objects.

    Attributes:
        api_key (str): The TEAM API key used for authentication.
        backend_url (str): The URL for the backend.
    """

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
        url = urljoin(cls.backend_url, f"sdk/inventory/dataset/{dataset_id}/overview")
        headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Dataset  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()

        # process data
        data = {}
        for d in resp["data"]:
            languages = []
            if "languages" in d["metadata"]:
                languages = [Language(lng) for lng in d["metadata"]["languages"]]
            data[d["id"]] = Data(
                id=d["id"],
                name=d["name"],
                dtype=DataType(d["dataType"]),
                privacy=Privacy.PRIVATE,
                languages=languages,
                onboard_status=d["status"],
            )

        # process input data
        source_data = {}
        for inp in resp["input"]:
            data_id = inp["dataId"]
            source_data[data[data_id].name] = data[data_id]

        # process output data
        target_data = {}
        for out in resp["output"]:
            target_data_list = [data[data_id] for data_id in out["dataIds"]]
            data_name = target_data_list[0].name
            target_data[data_name] = target_data_list

        # process function
        function = Function(resp["function"])

        # process license
        try:
            license = License(resp["license"]["typeId"])
        except:
            license = None

        dataset = Dataset(
            id=resp["id"],
            name=resp["name"],
            description=resp["description"],
            function=function,
            license=license,
            source_data=source_data,
            target_data=target_data,
            onboard_status=resp["status"],
        )
        return dataset

    @classmethod
    def create_asset_from_id(cls, dataset_id: Text) -> Dataset:
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "get" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.get(dataset_id)

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
            url = urljoin(cls.backend_url, f"sdk/datasets?pageNumber={page_number}&function={task}")
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
    def create(
        cls,
        name: Text,
        description: Text,
        license: License,
        function: Function,
        content_path: Union[Union[Text, Path], List[Union[Text, Path]]],
        input_schema: List[Union[Dict, MetaData]],
        output_schema: List[Union[Dict, MetaData]],
        input_ref_data: Dict[Text, Any] = {},
        output_ref_data: Dict[Text, List[Any]] = {},
        tags: List[Text] = [],
        privacy: Privacy = Privacy.PRIVATE,
    ) -> Dict:

        folder, return_dict = None, {}
        # check team key
        try:
            if config.TEAM_API_KEY.strip() == "":
                message = "Data Asset Onboarding Error: Update your team key on the environment variable TEAM_API_KEY before the corpus onboarding process."
                logging.exception(message)
                raise Exception(message)

            content_paths = content_path
            if isinstance(content_path, list) is False:
                content_paths = [content_path]

            if isinstance(input_schema[0], MetaData) is False:
                input_schema = [MetaData(**dict(metadata)) for metadata in input_schema]

            if isinstance(output_schema[0], MetaData) is False:
                output_schema = [MetaData(**dict(metadata)) for metadata in output_schema]

            for input_data in input_ref_data:
                if len(input_ref_data[input_data]) > 0:
                    if isinstance(input_ref_data[input_data][0], Data):
                        input_ref_data[input_data] = [w.id for w in input_ref_data[input_data]]
                    # TO DO: check whether the referred data exist. Otherwise, raise an exception

            for output_data in output_ref_data:
                if len(output_ref_data[output_data]) > 0:
                    if isinstance(output_ref_data[output_data][0], Data):
                        output_ref_data[output_data] = [w.id for w in output_ref_data[output_data]]
                    # TO DO: check whether the referred data exist. Otherwise, raise an exception

            # check whether reserved names are used as data/column names
            for schema in [input_schema, output_schema]:
                for metadata in schema:
                    for forbidden_name in onboard_functions.FORBIDDEN_COLUMN_NAMES:
                        if forbidden_name in [metadata.name, metadata.data_column]:
                            message = f"Data Asset Onboarding Error: {forbidden_name} is reserved name and must not be used as the name of a data or a column."
                            logging.exception(message)
                            raise Exception(message)

            # get file extension paths to process
            paths = onboard_functions.get_paths(content_paths)

            # process data and create files
            folder = Path(name)
            folder.mkdir(exist_ok=True)

            datasets = {}
            for (key, schema) in [("inputs", input_schema), ("outputs", output_schema)]:
                datasets[key] = {}
                for i in tqdm(range(len(schema)), desc=f" Dataset's {key} onboard progress", position=0):
                    metadata = schema[i]
                    if metadata.privacy is None:
                        metadata.privacy = privacy

                    files, data_column_idx, start_column_idx, end_column_idx = onboard_functions.process_data_files(
                        data_asset_name=name, metadata=metadata, paths=paths, folder=name
                    )

                    if metadata.name not in datasets[key]:
                        datasets[key][metadata.name] = []

                    datasets[key][metadata.name].append(
                        Data(
                            id=str(uuid4()).replace("-", ""),
                            name=metadata.name,
                            dtype=metadata.dtype,
                            privacy=metadata.privacy,
                            onboard_status="onboarding",
                            data_column=data_column_idx,
                            start_column=start_column_idx,
                            end_column=end_column_idx,
                            files=files,
                            languages=metadata.languages,
                        )
                    )

            # validate and flat inputs
            for input_data in datasets["inputs"]:
                assert len(datasets["inputs"][input_data]) == 1
                datasets["inputs"][input_data] = datasets["inputs"][input_data][0]

            dataset = Dataset(
                id="",
                name=name,
                description=description,
                function=function,
                source_data=datasets["inputs"],
                target_data=datasets["outputs"],
                tags=tags,
                license=license,
                privacy=privacy,
                onboard_status="onboarding",
            )
            dataset_payload = onboard_functions.build_payload_dataset(dataset, input_ref_data, output_ref_data, tags)
            assert (
                len(dataset_payload["input"]) > 0
            ), "Data Asset Onboarding Error: Please specify the input data of your dataset."
            assert (
                len(dataset_payload["output"]) > 0
            ), "Data Asset Onboarding Error: Please specify the output data of your dataset."

            response = onboard_functions.create_data_asset(dataset_payload, data_asset_type="dataset")
            if response["success"] is True:
                return_dict = {"status": response["status"], "asset_id": response["asset_id"]}
            else:
                raise Exception(response["error"])
            shutil.rmtree(folder)
        except Exception as e:
            if folder is not None:
                shutil.rmtree(folder)
            raise Exception(e)
        return return_dict
