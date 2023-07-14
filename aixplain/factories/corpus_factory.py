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
Date: March 27th 2023
Description:
    Corpus Factory Class
"""

import aixplain.utils.config as config
import aixplain.processes.data_onboarding.onboard_functions as onboard_functions
import json
import logging
import shutil

from aixplain.factories.asset_factory import AssetFactory
from aixplain.factories.data_factory import DataFactory
from aixplain.modules.corpus import Corpus
from aixplain.modules.data import Data
from aixplain.modules.metadata import MetaData
from aixplain.enums.data_subtype import DataSubtype
from aixplain.enums.data_type import DataType
from aixplain.enums.error_handler import ErrorHandler
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
from warnings import warn


class CorpusFactory(AssetFactory):
    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def __from_response(cls, response: Dict) -> Corpus:
        """Converts Json response to 'Corpus' object

        Args:
            response (dict): Json from API

        Returns:
            Dataset: Coverted 'Dataset' object
        """
        data = []
        for d in response["data"]:
            languages = []
            if "languages" in d["metadata"]:
                languages = []
                for lng in d["metadata"]["languages"]:
                    if "dialect" not in lng:
                        lng["dialect"] = ""
                    languages.append(Language(lng))
            data.append(
                Data(
                    id=d["id"],
                    name=d["name"],
                    dtype=DataType(d["dataType"]),
                    dsubtype=DataSubtype(d["dataSubtype"]),
                    privacy=Privacy.PRIVATE,
                    languages=languages,
                    onboard_status=d["status"],
                )
            )
        functions = [Function(f) for f in response["suggestedFunction"]]

        try:
            license = License(response["license"]["typeId"])
        except:
            license = None

        try:
            length = int(response["segmentsCount"])
        except:
            length = None

        corpus = Corpus(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            functions=functions,
            license=license,
            data=data,
            onboard_status=response["status"],
            length=length,
        )
        return corpus

    @classmethod
    def get(cls, corpus_id: Text) -> Corpus:
        """Create a 'Corpus' object from corpus id

        Args:
            corpus_id (Text): Corpus ID of required corpus.

        Returns:
            Corpus: Created 'Corpus' object
        """
        url = urljoin(cls.backend_url, f"sdk/corpus/{corpus_id}/overview")
        if cls.aixplain_key != "":
            headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Corpus  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        if "statusCode" in resp and resp["statusCode"] == 404:
            raise Exception(f"Corpus GET Error: Dataset {corpus_id} not found.")
        return cls.__from_response(resp)

    @classmethod
    def create_asset_from_id(cls, corpus_id: Text) -> Corpus:
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "get" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.get(corpus_id)

    @classmethod
    def list(
        cls,
        query: Optional[Text] = None,
        function: Optional[Function] = None,
        language: Optional[Union[Language, List[Language]]] = None,
        data_type: Optional[DataType] = None,
        license: Optional[License] = None,
        page_number: int = 0,
        page_size: int = 20,
    ) -> Dict:
        """Corpus Listing

        Args:
            query (Optional[Text], optional): search query. Defaults to None.
            function (Optional[Function], optional): function filter. Defaults to None.
            language (Optional[Union[Language, List[Language]]], optional): language filter. Defaults to None.
            data_type (Optional[DataType], optional): data type filter. Defaults to None.
            license (Optional[License], optional): license filter. Defaults to None.
            page_number (int, optional): page number. Defaults to 0.
            page_size (int, optional): page size. Defaults to 20.

        Returns:
            Dict: list of corpora in agreement with the filters, page number, page total and total elements
        """
        url = urljoin(cls.backend_url, "sdk/corpus/paginate")
        if cls.aixplain_key != "":
            headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
        else:
            headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}

        assert 0 < page_size <= 100, f"Corpus List Error: Page size must be greater than 0 and not exceed 100."
        payload = {"pageSize": page_size, "pageNumber": page_number, "sort": [{"field": "createdAt", "dir": -1}]}

        if query is not None:
            payload["q"] = str(query)

        if function is not None:
            payload["function"] = function.value

        if license is not None:
            payload["license"] = license.value

        if data_type is not None:
            payload["dataType"] = data_type.value

        if language is not None:
            if isinstance(language, Language):
                language = [language]
            payload["language"] = [lng.value["language"] for lng in language]

        logging.info(f"Start service for POST List Corpus - {url} - {headers} - {json.dumps(payload)}")
        r = _request_with_retry("post", url, headers=headers, json=payload)
        resp = r.json()
        corpora, page_total, total = [], 0, 0
        if "results" in resp:
            results = resp["results"]
            page_total = resp["pageTotal"]
            total = resp["total"]
            logging.info(f"Response for POST List Corpus - Page Total: {page_total} / Total: {total}")
            for corpus in results:
                corpus_ = cls.__from_response(corpus)
                # add languages
                languages = []
                for lng in corpus["languages"]:
                    if "dialect" not in lng:
                        lng["dialect"] = ""
                    languages.append(Language(lng))
                corpus_.kwargs["languages"] = languages
                corpora.append(corpus_)
        return {"results": corpora, "page_total": page_total, "page_number": page_number, "total": total}

    @classmethod
    def get_assets_from_page(
        cls, page_number: int = 1, task: Optional[Function] = None, language: Optional[Text] = None
    ) -> List[Corpus]:
        """Get the list of corpora from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int, optional): Page from which corpora are to be listed. Defaults to 1.
            task (Function, optional): Task of listed corpora. Defaults to None.
            language (Text, optional): language of listed corpora. Defaults to None.

        Returns:
            List[Corpus]: List of corpora based on given filters
        """
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "list" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        if language is not None:
            language = [language]
        return cls.list(function=task, page_number=page_number, languages=language)

    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        license: License,
        content_path: Union[Union[Text, Path], List[Union[Text, Path]]],
        schema: List[Union[Dict, MetaData]],
        ref_data: List[Any] = [],
        tags: List[Text] = [],
        functions: List[Function] = [],
        privacy: Privacy = Privacy.PRIVATE,
        error_handler: ErrorHandler = ErrorHandler.SKIP,
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
            error_handler (ErrorHandler, optional): how to handle failed rows in the data asset. Defaults to ErrorHandler.SKIP.

        Returns:
            Dict: response dict
        """
        folder, return_dict = None, {}
        # check team key
        try:
            assert (
                len(schema) > 0 or len(ref_data) > 0
            ), "Data Asset Onboarding Error: You must specify a data to onboard a corpus."

            content_paths = content_path
            if isinstance(content_path, list) is False:
                content_paths = [content_path]

            for i, metadata in enumerate(schema):
                if isinstance(metadata, dict):
                    schema[i] = MetaData(**metadata)

            if len(ref_data) > 0:
                if isinstance(ref_data[0], Data):
                    ref_data = [w.id for w in ref_data]
                # check whether the referred data exist. Otherwise, raise an exception
                for i, data_id in enumerate(ref_data):
                    if onboard_functions.is_data(data_id) is False:
                        message = f"Data Asset Onboarding Error: Referenced Data {data_id} does not exist."
                        logging.exception(message)
                        raise Exception(message)
                    ref_data[i] = DataFactory.get(data_id=data_id)

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
            for i in tqdm(range(len(schema)), desc=" Corpus onboarding progress", position=0):
                metadata = schema[i]
                if metadata.privacy is None:
                    metadata.privacy = privacy

                files, data_column_idx, start_column_idx, end_column_idx, nrows = onboard_functions.process_data_files(
                    data_asset_name=name, metadata=metadata, paths=paths, folder=name
                )

                dataset.append(
                    Data(
                        id="",
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

            # check alignment
            sizes = [d.length for d in dataset] + [d.length for d in ref_data]
            assert (
                len(set(sizes)) == 1
            ), f"Data Asset Onboarding Error: All data must have the same number of rows. Lengths: {str(set(sizes))}"

            corpus = Corpus(
                id="",
                name=name,
                description=description,
                data=dataset,
                functions=functions,
                tags=tags,
                license=license,
                privacy=privacy,
                onboard_status="onboarding",
            )

            corpus_payload = onboard_functions.build_payload_corpus(corpus, [ref.id for ref in ref_data], error_handler)

            response = onboard_functions.create_data_asset(corpus_payload)
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
