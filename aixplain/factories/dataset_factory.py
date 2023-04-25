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
import json
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
    def __from_response(cls, response: Dict) -> Dataset:
        """Converts response Json to 'Dataset' object

        Args:
            response (dict): Json from API

        Returns:
            Dataset: Coverted 'Dataset' object
        """
        # process data
        data = {}
        for d in response["data"]:
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
        for inp in response["input"]:
            data_id = inp["dataId"]
            if data_id in data:
                source_data[data[data_id].name] = data[data_id]

        # process output data
        target_data = {}
        for out in response["output"]:
            try:
                target_data_list = [data[data_id] for data_id in out["dataIds"]]
                data_name = target_data_list[0].name
                target_data[data_name] = target_data_list
            except:
                pass

        # process function
        function = Function(response["function"])

        # process license
        try:
            license = License(response["license"]["typeId"])
        except:
            license = None

        dataset = Dataset(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            function=function,
            license=license,
            source_data=source_data,
            target_data=target_data,
            onboard_status=response["status"],
        )
        return dataset

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

        return cls.__from_response(resp)

    @classmethod
    def create_asset_from_id(cls, dataset_id: Text) -> Dataset:
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "get" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.get(dataset_id)

    @classmethod
    def list(
        cls,
        query: Optional[Text] = None,
        function: Optional[Function] = None,
        languages: List[Language] = [],
        data_type: Optional[DataType] = None,
        license: Optional[License] = None,
        page_number: int = 0,
        page_size: int = 20,
    ) -> List[Dataset]:
        """Listing Datasets

        Args:
            query (Optional[Text], optional): search query. Defaults to None.
            function (Optional[Function], optional): function filter. Defaults to None.
            languages (List[Language], optional): language filter. Defaults to [].
            data_type (Optional[DataType], optional): data type filter. Defaults to None.
            license (Optional[License], optional): license filter. Defaults to None.
            page_number (int, optional): page number. Defaults to 0.
            page_size (int, optional): page size. Defaults to 20.

        Returns:
            List[Dataset]: list of datasets which are in agreement with the filters
        """
        url = urljoin(config.BACKEND_URL, "sdk/inventory/dataset/paginate")
        headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}

        assert 0 < page_size <= 100, f"Dataset List Error: Page size must be greater than 0 and not exceed 100."
        payload = {"pageSize": page_size, "pageNumber": page_number, "sort": [{"field": "createdAt", "dir": -1}]}

        if query is not None:
            payload["q"] = str(query)

        if function is not None:
            payload["function"] = function.value

        if license is not None:
            payload["license"] = license.value

        if data_type is not None:
            payload["dataType"] = data_type.value

        if len(languages) > 0:
            payload["language"] = [lng.value["language"] for lng in languages]

        logging.info(f"Start service for POST List Dataset - {url} - {headers} - {json.dumps(payload)}")
        r = _request_with_retry("post", url, headers=headers, json=payload)
        resp = r.json()

        datasets = []
        if "results" in resp:
            results = resp["results"]
            page_total = resp["pageTotal"]
            total = resp["total"]
            logging.info(f"Response for POST List Dataset - Page Total: {page_total} / Total: {total}")
            for dataset in results:
                datasets.append(cls.__from_response(dataset))
        return datasets

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
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "list" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.list(function=task, page_number=page_number)

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
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "list" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.list(function=task, page_size=k)

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
        split_schema: Optional[Union[Dict, MetaData]] = None,
    ) -> Dict:
        """Dataset Onboard

        Args:
            name (Text): dataset name
            description (Text): dataset description
            license (License): dataset license
            function (Function): dataset function
            content_path (Union[Union[Text, Path], List[Union[Text, Path]]]): path to files which contain the data content
            input_schema (List[Union[Dict, MetaData]]): metadata of inputs
            output_schema (List[Union[Dict, MetaData]]): metadata of outputs
            input_ref_data (Dict[Text, Any], optional): reference to input data which is already in the platform. Defaults to {}.
            output_ref_data (Dict[Text, List[Any]], optional): reference to output data which is already in the platform. Defaults to {}.
            tags (List[Text], optional): datasets description tags. Defaults to [].
            privacy (Privacy, optional): dataset privacy. Defaults to Privacy.PRIVATE.
            split_schema (Optional[Union[Dict, MetaData]], optional): meta data for data splitting. Defaults to None.

        Returns:
            Dict: dataset onboard status
        """
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

            if split_schema is not None and isinstance(split_schema, MetaData) is False:
                split_schema = MetaData(**dict(split_schema))

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
                        data_asset_name=name, metadata=metadata, paths=paths, folder=name, split_data=split_schema
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
