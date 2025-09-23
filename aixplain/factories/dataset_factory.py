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

import aixplain.processes.data_onboarding.onboard_functions as onboard_functions
import json
import os
import logging
import shutil

from aixplain.factories.asset_factory import AssetFactory
from aixplain.factories.data_factory import DataFactory
from aixplain.modules.data import Data
from aixplain.modules.dataset import Dataset
from aixplain.modules.metadata import MetaData
from aixplain.enums.data_subtype import DataSubtype
from aixplain.enums.data_type import DataType
from aixplain.enums.error_handler import ErrorHandler
from aixplain.enums.function import Function
from aixplain.enums.language import Language
from aixplain.enums.license import License
from aixplain.enums.privacy import Privacy
from aixplain.utils import config
from aixplain.utils.convert_datatype_utils import dict_to_metadata
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.file_utils import s3_to_csv
from aixplain.utils.validation_utils import dataset_onboarding_validation
from pathlib import Path
from tqdm import tqdm
from typing import Any, Dict, List, Optional, Text, Union
from urllib.parse import urljoin
from uuid import uuid4


class DatasetFactory(AssetFactory):
    """Factory class for creating and managing datasets in the aiXplain platform.

    This class provides functionality for creating, retrieving, and managing
    datasets, which are structured collections of data assets used for training,
    evaluating, and benchmarking AI models. Datasets can include input data,
    target data, hypotheses, and metadata.

    Attributes:
        backend_url (str): Base URL for the aiXplain backend API.
    """

    backend_url = config.BACKEND_URL

    @classmethod
    def __from_response(cls, response: Dict) -> Dataset:
        """Convert API response into a Dataset object.

        This method creates a Dataset object from an API response, handling the
        conversion of data assets, languages, functions, and other attributes.
        It processes input data, hypotheses, metadata, and target data separately.

        Args:
            response (Dict): API response containing:
                - id: Dataset identifier
                - name: Dataset name
                - description: Dataset description
                - data: List of data asset configurations
                - input: Input data configurations
                - hypotheses: Optional hypotheses configurations
                - metadata: Metadata configurations
                - output: Output/target data configurations
                - function: Function identifier
                - license: License configuration
                - status: Onboarding status
                - segmentsCount: Optional number of segments

        Returns:
            Dataset: Instantiated dataset object with all components loaded.
        """
        # process data
        data = {}
        for d in response["data"]:
            languages = []
            if "languages" in d["metadata"]:
                languages = []
                for lng in d["metadata"]["languages"]:
                    if "dialect" not in lng:
                        lng["dialect"] = ""
                    languages.append(Language(lng))

            data[d["id"]] = Data(
                id=d["id"],
                name=d["name"],
                dtype=DataType(d["dataType"]),
                dsubtype=DataSubtype(d["dataSubtype"]),
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

        # process hypotheses
        hypotheses = {}
        if "hypotheses" in response:
            for inp in response["hypotheses"]:
                data_id = inp["dataId"]
                if data_id in data:
                    hypotheses[data[data_id].name] = data[data_id]

        # process metadata
        metadata = {}
        for inp in response["metadata"]:
            data_id = inp["dataId"]
            if data_id in data:
                metadata[data[data_id].name] = data[data_id]

        # process output data
        target_data = {}
        for out in response["output"]:
            try:
                target_data_list = [data[data_id] for data_id in out["dataIds"]]
                data_name = target_data_list[0].name
                target_data[data_name] = target_data_list
            except Exception:
                pass

        # process function
        function = Function(response["function"])

        # process license
        try:
            license = License(response["license"]["typeId"])
        except Exception:
            license = None

        try:
            length = int(response["segmentsCount"])
        except Exception:
            length = None

        dataset = Dataset(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            function=function,
            license=license,
            source_data=source_data,
            target_data=target_data,
            hypotheses=hypotheses,
            metadata=metadata,
            onboard_status=response["status"],
            length=length,
        )
        return dataset

    @classmethod
    def get(cls, dataset_id: Text, api_key: str = None) -> Dataset:
        """Retrieve a dataset by its ID.

        This method fetches a dataset and all its associated data assets from
        the platform.

        Args:
            dataset_id (Text): Unique identifier of the dataset to retrieve.
            api_key (str, optional): Team API key. Defaults to None.

        Returns:
            Dataset: Retrieved dataset object with all components loaded.

        Raises:
            Exception: If:
                - Dataset ID is invalid
                - Authentication fails
                - Service is unavailable
        """
        try:
            url = urljoin(cls.backend_url, f"sdk/datasets/{dataset_id}/overview")
            api_key = api_key or config.TEAM_API_KEY
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET Dataset  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception as e:
            error_message = f"Error retrieving Dataset {dataset_id}: {str(e)}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
        if 200 <= r.status_code < 300:
            logging.info(f"Dataset {dataset_id} retrieved successfully.")
            return cls.__from_response(resp)
        else:
            error_message = f"Dataset GET Error: Status {r.status_code} - {resp}"
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def list(
        cls,
        query: Optional[Text] = None,
        function: Optional[Function] = None,
        source_languages: Optional[Union[Language, List[Language]]] = None,
        target_languages: Optional[Union[Language, List[Language]]] = None,
        data_type: Optional[DataType] = None,
        license: Optional[License] = None,
        is_referenceless: Optional[bool] = None,
        page_number: int = 0,
        page_size: int = 20,
    ) -> Dict:
        """List and filter datasets with pagination support.

        This method provides comprehensive filtering and pagination capabilities
        for retrieving datasets from the aiXplain platform.

        Args:
            query (Optional[Text], optional): Search query to filter datasets by name
                or description. Defaults to None.
            function (Optional[Function], optional): Filter by AI function type.
                Defaults to None.
            source_languages (Optional[Union[Language, List[Language]]], optional):
                Filter by input data language(s). Can be single language or list.
                Defaults to None.
            target_languages (Optional[Union[Language, List[Language]]], optional):
                Filter by output data language(s). Can be single language or list.
                Defaults to None.
            data_type (Optional[DataType], optional): Filter by data type.
                Defaults to None.
            license (Optional[License], optional): Filter by license type.
                Defaults to None.
            is_referenceless (Optional[bool], optional): Filter by whether dataset
                has references. Defaults to None.
            page_number (int, optional): Zero-based page number. Defaults to 0.
            page_size (int, optional): Number of items per page (1-100).
                Defaults to 20.

        Returns:
            Dict: Response containing:
                - results (List[Dataset]): List of dataset objects
                - page_total (int): Total items in current page
                - page_number (int): Current page number
                - total (int): Total number of items across all pages

        Raises:
            Exception: If:
                - page_size is not between 1 and 100
                - Request fails
                - Service is unavailable
            AssertionError: If page_size is invalid.
        """
        url = urljoin(cls.backend_url, "sdk/datasets/paginate")

        headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}

        assert 0 < page_size <= 100, "Dataset List Error: Page size must be greater than 0 and not exceed 100."
        payload = {
            "pageSize": page_size,
            "pageNumber": page_number,
            "sort": [{"field": "createdAt", "dir": -1}],
            "input": {},
            "output": {},
        }

        if query is not None:
            payload["q"] = str(query)

        if function is not None:
            payload["function"] = function.value

        if license is not None:
            payload["license"] = license.value

        if data_type is not None:
            payload["dataType"] = data_type.value

        if is_referenceless is not None:
            payload["isReferenceless"] = is_referenceless

        if source_languages is not None:
            if isinstance(source_languages, Language):
                source_languages = [source_languages]
            payload["input"]["languages"] = [lng.value["language"] for lng in source_languages]

        if target_languages is not None:
            if isinstance(target_languages, Language):
                target_languages = [target_languages]
            payload["output"]["languages"] = [lng.value["language"] for lng in target_languages]

        try:
            logging.info(f"Start service for POST List Dataset - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()

        except Exception as e:
            error_message = f"Error listing datasets: {str(e)}"
            logging.error(error_message, exc_info=True)
            raise Exception(error_message)
        if 200 <= r.status_code < 300:
            datasets, page_total, total = [], 0, 0
            if "results" in resp:
                results = resp["results"]
                page_total = resp["pageTotal"]
                total = resp["total"]
                logging.info(f"Response for POST List Dataset - Page Total: {page_total} / Total: {total}")
                for dataset in results:
                    datasets.append(cls.__from_response(dataset))
                return {"results": datasets, "page_total": page_total, "page_number": page_number, "total": total}
        else:
            error_message = f"Dataset List Error: Status {r.status_code} - {resp}"
            logging.error(error_message)
            raise Exception(error_message)

    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        license: License,
        function: Function,
        input_schema: List[Union[Dict, MetaData]],
        output_schema: List[Union[Dict, MetaData]] = [],
        hypotheses_schema: List[Union[Dict, MetaData]] = [],
        metadata_schema: List[Union[Dict, MetaData]] = [],
        content_path: Union[Union[Text, Path], List[Union[Text, Path]]] = [],
        input_ref_data: Dict[Text, Any] = {},
        output_ref_data: Dict[Text, List[Any]] = {},
        hypotheses_ref_data: Dict[Text, Any] = {},
        meta_ref_data: Dict[Text, Any] = {},
        tags: List[Text] = [],
        privacy: Privacy = Privacy.PRIVATE,
        split_labels: Optional[List[Text]] = None,
        split_rate: Optional[List[float]] = None,
        error_handler: ErrorHandler = ErrorHandler.SKIP,
        s3_link: Optional[Text] = None,
        aws_credentials: Optional[Dict[Text, Text]] = {"AWS_ACCESS_KEY_ID": None, "AWS_SECRET_ACCESS_KEY": None},
        api_key: Optional[Text] = None,
    ) -> Dict:
        """Create a new dataset from data files and references.

        This method processes data files and existing data assets to create a new
        dataset in the platform. It supports various data types, multiple input and
        output configurations, and optional data splitting.

        Args:
            name (Text): Name for the new dataset.
            description (Text): Description of the dataset's contents and purpose.
            license (License): License type for the dataset.
            function (Function): AI function this dataset is suitable for.
            input_schema (List[Union[Dict, MetaData]]): Metadata configurations for
                input data processing.
            output_schema (List[Union[Dict, MetaData]], optional): Metadata configs
                for output/target data. Defaults to [].
            hypotheses_schema (List[Union[Dict, MetaData]], optional): Metadata
                configs for hypothesis data. Defaults to [].
            metadata_schema (List[Union[Dict, MetaData]], optional): Additional
                metadata configurations. Defaults to [].
            content_path (Union[Union[Text, Path], List[Union[Text, Path]]], optional):
                Path(s) to data files. Can be single path or list. Defaults to [].
            input_ref_data (Dict[Text, Any], optional): References to existing
                input data assets. Defaults to {}.
            output_ref_data (Dict[Text, List[Any]], optional): References to
                existing output data assets. Defaults to {}.
            hypotheses_ref_data (Dict[Text, Any], optional): References to
                existing hypothesis data. Defaults to {}.
            meta_ref_data (Dict[Text, Any], optional): References to existing
                metadata assets. Defaults to {}.
            tags (List[Text], optional): Tags describing the dataset.
                Defaults to [].
            privacy (Privacy, optional): Visibility setting.
                Defaults to Privacy.PRIVATE.
            split_labels (Optional[List[Text]], optional): Labels for dataset
                splits (e.g., ["train", "test"]). Defaults to None.
            split_rate (Optional[List[float]], optional): Ratios for dataset
                splits (must sum to 1). Defaults to None.
            error_handler (ErrorHandler, optional): Strategy for handling data
                processing errors. Defaults to ErrorHandler.SKIP.
            s3_link (Optional[Text], optional): S3 URL for data files.
                Defaults to None.
            aws_credentials (Optional[Dict[Text, Text]], optional): AWS credentials
                with access_key_id and secret_access_key. Defaults to None values.
            api_key (Optional[Text], optional): API key for authentication.
                Defaults to None, using the configured TEAM_API_KEY.

        Returns:
            Dict: Response containing:
                - status: Current processing status
                - asset_id: ID of the created dataset

        Raises:
            Exception: If:
                - No input data is provided
                - Referenced data asset doesn't exist
                - Reserved column names are used
                - Data rows are misaligned
                - Split configuration is invalid
                - Processing or upload fails
            AssertionError: If split configuration is invalid.
        """

        for lmd in (hypotheses_schema, input_schema, output_schema, metadata_schema):
            dict_to_metadata(lmd)

        dataset_onboarding_validation(
            input_schema=input_schema,
            output_schema=output_schema,
            function=function,
            input_ref_data=input_ref_data,
            metadata_schema=metadata_schema,
            content_path=content_path,
            split_labels=split_labels,
            split_rate=split_rate,
            s3_link=s3_link,
        )

        folder, return_dict, ref_data, csv_path = None, {}, [], None
        # check team key
        try:
            # process data and create files
            folder = Path(name)
            folder.mkdir(exist_ok=True)

            if isinstance(content_path, list) is False:
                content_paths = [content_path]
            else:
                content_paths = content_path

            if s3_link is not None:
                csv_path = s3_to_csv(s3_link, aws_credentials)
                content_paths.append(csv_path)

            # assert (
            #     len(output_schema) > 0 or len(output_ref_data) > 0
            # ), "Data Asset Onboarding Error: You must specify an output data to onboard a dataset."

            for input_data in input_ref_data:
                if isinstance(input_ref_data[input_data], Data):
                    input_ref_data[input_data] = input_ref_data[input_data].id
                # check whether the referred data exist. Otherwise, raise an exception
                data_id = input_ref_data[input_data]
                if onboard_functions.is_data(data_id) is False:
                    message = f"Data Asset Onboarding Error: Referenced Input Data {data_id} does not exist."
                    logging.exception(message)
                    raise Exception(message)
                ref_data.append(DataFactory.get(data_id=data_id))

            for output_data in output_ref_data:
                if len(output_ref_data[output_data]) > 0:
                    if isinstance(output_ref_data[output_data][0], Data):
                        output_ref_data[output_data] = [w.id for w in output_ref_data[output_data]]
                    # check whether the referred data exist. Otherwise, raise an exception
                    for data_id in output_ref_data[output_data]:
                        if onboard_functions.is_data(data_id) is False:
                            message = f"Data Asset Onboarding Error: Referenced Output Data {data_id} does not exist."
                            logging.exception(message)
                            raise Exception(message)
                        ref_data.append(DataFactory.get(data_id=data_id))

            for hypdata in hypotheses_ref_data:
                if isinstance(hypotheses_ref_data[hypdata], Data):
                    hypotheses_ref_data[hypdata] = hypotheses_ref_data[hypdata].id
                # check whether the referred data exist. Otherwise, raise an exception
                data_id = hypotheses_ref_data[hypdata]
                if onboard_functions.is_data(data_id) is False:
                    message = f"Data Asset Onboarding Error: Referenced Hypotheses Data {data_id} does not exist."
                    logging.exception(message)
                    raise Exception(message)
                ref_data.append(DataFactory.get(data_id=data_id))

            for meta_data in meta_ref_data:
                if isinstance(meta_ref_data[meta_data], Data):
                    meta_ref_data[meta_data] = meta_ref_data[meta_data].id
                # check whether the referred data exist. Otherwise, raise an exception
                data_id = meta_ref_data[meta_data]
                if onboard_functions.is_data(data_id) is False:
                    message = f"Data Asset Onboarding Error: Referenced Meta Data {data_id} does not exist."
                    logging.exception(message)
                    raise Exception(message)
                ref_data.append(DataFactory.get(data_id=data_id))

            # check whether reserved names are used as data/column names
            for schema in [input_schema, output_schema, metadata_schema, hypotheses_schema]:
                for metadata in schema:
                    for forbidden_name in onboard_functions.FORBIDDEN_COLUMN_NAMES:
                        if forbidden_name in [metadata.name, metadata.data_column]:
                            message = f"Data Asset Onboarding Error: {forbidden_name} is reserved name and must not be used as the name of a data or a column."
                            logging.exception(message)
                            raise Exception(message)

            # get file extension paths to process
            paths = onboard_functions.get_paths(content_paths)

            # set dataset split
            if split_labels is not None and split_rate is not None:
                assert len(split_labels) == len(
                    split_rate
                ), "Data Asset Onboarding Error: Make sure you set the *split_labels* and *split_rate* lists must have the same length."
                split_metadata = onboard_functions.split_data(paths=paths, split_labels=split_labels, split_rate=split_rate)
                metadata_schema.append(split_metadata)

            datasets, sizes = {}, []
            for (key, schema) in [
                ("inputs", input_schema),
                ("outputs", output_schema),
                ("hypotheses", hypotheses_schema),
                ("meta", metadata_schema),
            ]:
                datasets[key] = {}
                for i in tqdm(range(len(schema)), desc=f" Dataset's {key} onboard progress", position=0):
                    metadata = schema[i]
                    if metadata.privacy is None:
                        metadata.privacy = privacy

                    files, data_column_idx, start_column_idx, end_column_idx, nrows = onboard_functions.process_data_files(
                        data_asset_name=name, metadata=metadata, paths=paths, folder=name
                    )

                    # save size
                    sizes.append(nrows)

                    if metadata.name not in datasets[key]:
                        datasets[key][metadata.name] = []

                    datasets[key][metadata.name].append(
                        Data(
                            id=str(uuid4()).replace("-", ""),
                            name=metadata.name,
                            dtype=metadata.dtype,
                            dsubtype=metadata.dsubtype,
                            privacy=metadata.privacy,
                            onboard_status="onboarding",
                            data_column=data_column_idx,
                            start_column=start_column_idx,
                            end_column=end_column_idx,
                            files=files,
                            languages=metadata.languages,
                            length=nrows,
                        )
                    )

            # validate and flat inputs, hypotheses and metadata
            for key_schema in ["inputs", "hypotheses", "meta"]:
                for input_data in datasets[key_schema]:
                    assert len(datasets[key_schema][input_data]) == 1
                    datasets[key_schema][input_data] = datasets[key_schema][input_data][0]

            dataset = Dataset(
                id="",
                name=name,
                description=description,
                function=function,
                source_data=datasets["inputs"],
                target_data=datasets["outputs"],
                hypotheses=datasets["hypotheses"],
                metadata=datasets["meta"],
                tags=tags,
                license=license,
                privacy=privacy,
                onboard_status="onboarding",
            )

            # check alignment
            sizes += [d.length for d in ref_data]
            assert (
                len(set(sizes)) == 1
            ), f"Data Asset Onboarding Error: All data must have the same number of rows. Lengths: {str(set(sizes))}"

            dataset_payload = onboard_functions.build_payload_dataset(
                dataset, input_ref_data, output_ref_data, hypotheses_ref_data, meta_ref_data, tags, error_handler
            )
            assert (
                len(dataset_payload["input"]) > 0
            ), "Data Asset Onboarding Error: Please specify the input data of your dataset."
            # assert (
            #     len(dataset_payload["output"]) > 0
            # ), "Data Asset Onboarding Error: Please specify the output data of your dataset."

            response = onboard_functions.create_data_asset(payload=dataset_payload, data_asset_type="dataset", api_key=api_key)
            if response["success"] is True:
                return_dict = {"status": response["status"], "asset_id": response["asset_id"]}
            else:
                raise Exception(response["error"])
            shutil.rmtree(folder)
            if csv_path is not None and os.path.exists(csv_path) is True:
                os.remove(csv_path)
        except Exception as e:
            if folder is not None:
                shutil.rmtree(folder)
            if csv_path is not None and os.path.exists(csv_path) is True:
                os.remove(csv_path)
            raise Exception(e)
        return return_dict
