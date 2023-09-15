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
from aixplain.utils.file_utils import _request_with_retry, s3_to_csv
from aixplain.utils import config
from aixplain.utils.validation_utils import dataset_onboarding_validation
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
    aixplain_key = config.AIXPLAIN_API_KEY
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
            except:
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
    def get(cls, dataset_id: Text) -> Dataset:
        """Create a 'Dataset' object from dataset id

        Args:
            dataset_id (Text): Dataset ID of required dataset.

        Returns:
            Dataset: Created 'Dataset' object
        """
        url = urljoin(cls.backend_url, f"sdk/dataset/{dataset_id}/overview")
        if cls.aixplain_key != "":
            headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Dataset  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if "statusCode" in resp and resp["statusCode"] == 404:
            raise Exception(f"Dataset GET Error: Dataset {dataset_id} not found.")
        return cls.__from_response(resp)

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
        """Listing Datasets

        Args:
            query (Optional[Text], optional): search query. Defaults to None.
            function (Optional[Function], optional): function filter. Defaults to None.
            source_languages (Optional[Union[Language, List[Language]]], optional): language filter of input data. Defaults to None.
            target_languages (Optional[Union[Language, List[Language]]], optional): language filter of output data. Defaults to None.
            data_type (Optional[DataType], optional): data type filter. Defaults to None.
            license (Optional[License], optional): license filter. Defaults to None.
            is_referenceless (Optional[bool], optional): has reference filter. Defaults to None.
            page_number (int, optional): page number. Defaults to 0.
            page_size (int, optional): page size. Defaults to 20.

        Returns:
            Dict: list of datasets in agreement with the filters, page number, page total and total elements
        """
        url = urljoin(cls.backend_url, "sdk/dataset/paginate")
        if cls.aixplain_key != "":
            headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}

        assert 0 < page_size <= 100, f"Dataset List Error: Page size must be greater than 0 and not exceed 100."
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

        logging.info(f"Start service for POST List Dataset - {url} - {headers} - {json.dumps(payload)}")
        r = _request_with_retry("post", url, headers=headers, json=payload)
        resp = r.json()

        datasets, page_total, total = [], 0, 0
        if "results" in resp:
            results = resp["results"]
            page_total = resp["pageTotal"]
            total = resp["total"]
            logging.info(f"Response for POST List Dataset - Page Total: {page_total} / Total: {total}")
            for dataset in results:
                datasets.append(cls.__from_response(dataset))
        return {"results": datasets, "page_total": page_total, "page_number": page_number, "total": total}

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
        s3_link: Optional[str] = None,
        aws_credentials: Optional[Dict[str, str]] = {"AWS_ACCESS_KEY_ID": None, "AWS_SECRET_ACCESS_KEY": None},
    ) -> Dict:
        """Dataset Onboard

        Args:
            name (Text): dataset name
            description (Text): dataset description
            license (License): dataset license
            function (Function): dataset function
            input_schema (List[Union[Dict, MetaData]]): metadata of inputs
            output_schema (List[Union[Dict, MetaData]]): metadata of outputs
            hypotheses_schema (List[Union[Dict, MetaData]], optional): schema of the hypotheses to the references. Defaults to [].
            metadata_schema (List[Union[Dict, MetaData]], optional): metadata of metadata information of the dataset. Defaults to [].
            content_path (Union[Union[Text, Path], List[Union[Text, Path]]]): path to files which contain the data content
            input_ref_data (Dict[Text, Any], optional): reference to input data which is already in the platform. Defaults to {}.
            output_ref_data (Dict[Text, List[Any]], optional): reference to output data which is already in the platform. Defaults to {}.
            hypotheses_ref_data (Dict[Text, Any], optional): hypotheses which are already in the platform. Defaults to {}.
            meta_ref_data (Dict[Text, Any], optional): metadata which is already in the platform. Defaults to {}.
            tags (List[Text], optional): datasets description tags. Defaults to [].
            privacy (Privacy, optional): dataset privacy. Defaults to Privacy.PRIVATE.
            error_handler (ErrorHandler, optional): how to handle failed rows in the data asset. Defaults to ErrorHandler.SKIP.
            s3_link (Optional[str]): s3 url to files or directories
            aws_credentials (Optional[Dict[str, str]]) : credentials for AWS and it should contains these two keys `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
        Returns:
            Dict: dataset onboard status
        """

        dataset_onboarding_validation(input_schema, output_schema, function, content_path, split_labels, split_rate, s3_link)

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

            assert (
                len(input_schema) > 0 or len(input_ref_data) > 0
            ), "Data Asset Onboarding Error: You must specify an input data to onboard a dataset."
            for i, metadata in enumerate(input_schema):
                if isinstance(metadata, dict):
                    input_schema[i] = MetaData(**metadata)

            # assert (
            #     len(output_schema) > 0 or len(output_ref_data) > 0
            # ), "Data Asset Onboarding Error: You must specify an output data to onboard a dataset."
            for i, metadata in enumerate(output_schema):
                if isinstance(metadata, dict):
                    output_schema[i] = MetaData(**metadata)

            for i, hypothesis in enumerate(hypotheses_schema):
                if isinstance(hypothesis, dict):
                    hypotheses_schema[i] = MetaData(**hypothesis)

            for i, metadata in enumerate(metadata_schema):
                if isinstance(metadata, dict):
                    metadata_schema[i] = MetaData(**metadata)

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

            response = onboard_functions.create_data_asset(dataset_payload, data_asset_type="dataset")
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
