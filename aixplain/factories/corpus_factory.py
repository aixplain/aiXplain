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
import logging
import shutil

from aixplain.factories.asset_factory import AssetFactory
from aixplain.modules.corpus import Corpus
from aixplain.modules.data import Data
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
from warnings import warn


class CorpusFactory(AssetFactory):
    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, corpus_id: Text) -> Corpus:
        """Create a 'Corpus' object from corpus id

        Args:
            corpus_id (Text): Corpus ID of required corpus.

        Returns:
            Corpus: Created 'Corpus' object
        """
        url = urljoin(cls.backend_url, f"sdk/inventory/corpus/{corpus_id}/overview")
        headers = {"Authorization": f"Token {cls.api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Corpus  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        resp = r.json()
        data = []
        for d in resp["data"]:
            languages = []
            if "languages" in d["metadata"]:
                languages = [Language(lng) for lng in d["metadata"]["languages"]]
            data.append(
                Data(
                    id=d["id"],
                    name=d["name"],
                    dtype=DataType(d["dataType"]),
                    privacy=Privacy.PRIVATE,
                    languages=languages,
                    onboard_status=d["status"],
                )
            )
        functions = [Function(f) for f in resp["suggestedFunction"]]

        try:
            license = License(resp["license"]["typeId"])
        except:
            license = None

        corpus = Corpus(
            id=resp["id"],
            name=resp["name"],
            description=resp["description"],
            functions=functions,
            license=license,
            data=data,
            onboard_status=resp["status"],
        )
        return corpus

    @classmethod
    def create_asset_from_id(cls, corpus_id: Text) -> Corpus:
        warn(
            'This method will be deprecated in the next versions of the SDK. Use "get" instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        return cls.get(corpus_id)

    @classmethod
    def get_assets_from_page(
        cls, page_number: Optional[int] = 1, task: Optional[Function] = None, language: Optional[Text] = None
    ) -> List[Corpus]:
        """Get the list of corpora from a given page. Additional task and language filters can be also be provided

        Args:
            page_number (int, optional): Page from which corpora are to be listed. Defaults to 1.
            task (Function, optional): Task of listed corpora. Defaults to None.
            language (Text, optional): language of listed corpora. Defaults to None.

        Returns:
            List[Corpus]: List of corpora based on given filters
        """
        try:
            url = urljoin(config.BACKEND_URL, "sdk/inventory/corpus")
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}

            payload = {
                # "q": "",
                # "function": task,
                # "dataType": "text",
                # "license": None
            }
            if task is not None:
                payload["function"] = task.value
            r = _request_with_retry("post", url, headers=headers, json=payload)
            resp = r.json()

            corpora = []
            if resp["total"] > 0:
                for corpus_row in resp["results"]:
                    functions = [Function(f) for f in corpus_row["suggestedFunction"]]
                    corpus = Corpus(
                        id=corpus_row["id"],
                        name=corpus_row["name"],
                        description=corpus_row["description"],
                        functions=functions,
                        data=[],
                        onboard_status="onboarded",
                    )
                    corpora.append(corpus)
            return corpora
        except Exception as e:
            error_message = f"Listing Corpora: Error in getting Corpora on Page {page_number} : {e}"
            logging.error(error_message)
            return []

    @classmethod
    def get_first_k_assets(cls, k: int, task: Optional[Function] = None, language: Optional[Text] = None) -> List[Corpus]:
        """Gets the first k given corpora based on the provided task and language filters

        Args:
            k (int): Number of corpora to get
            task (Function, optional): Task of listed corpora. Defaults to None.
            language (Text, optional): language of listed corpora. Defaults to None.

        Returns:
            List[Corpus]: List of datasets based on given filters
        """
        raise NotImplementedError("Not implemented function.")

    @classmethod
    def create_corpus(
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
                logging.exception(message)
                raise Exception(message)

            content_paths = content_path
            if isinstance(content_path, list) is False:
                content_paths = [content_path]

            if isinstance(schema[0], MetaData) is False:
                schema = [MetaData(**dict(metadata)) for metadata in schema]

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
            for i in tqdm(range(len(schema)), desc=" Corpus onboarding progress", position=0):
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
                        onboard_status="onboarding",
                        data_column=data_column_idx,
                        start_column=start_column_idx,
                        end_column=end_column_idx,
                        files=files,
                        languages=metadata.languages,
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
                onboard_status="onboarding",
            )
            corpus_payload = onboard_functions.build_payload_corpus(corpus, ref_data)

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
