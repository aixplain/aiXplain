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

from aixplain.enums.function import Function
from aixplain.enums.license import License
from aixplain.enums.onboard_status import OnboardStatus
from aixplain.enums.privacy import Privacy
from aixplain.modules.asset import Asset
from aixplain.modules.data import Data
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from typing import List, Optional, Text
from urllib.parse import urljoin


class Corpus(Asset):
    """A class representing a general-purpose collection of data in the aiXplain platform.

    This class extends Asset to provide functionality for managing corpora, which are
    collections of data that can be processed and used to create task-specific datasets.
    A corpus can contain various types of data and is used as a foundation for creating
    specialized datasets.

    Attributes:
        id (Text): ID of the corpus.
        name (Text): Name of the corpus.
        description (Text): Detailed description of the corpus.
        data (List[Data]): List of data objects that make up the corpus.
        onboard_status (OnboardStatus): Current onboarding status of the corpus.
        functions (List[Function]): AI functions the corpus is suitable for.
        tags (List[Text]): Descriptive tags for the corpus.
        license (Optional[License]): License associated with the corpus.
        privacy (Privacy): Privacy settings for the corpus.
        supplier (Text): The supplier/author of the corpus.
        version (Text): Version of the corpus.
        length (Optional[int]): Number of rows/items in the corpus.
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        data: List[Data],
        onboard_status: OnboardStatus,
        functions: List[Function] = [],
        tags: List[Text] = [],
        license: Optional[License] = None,
        privacy: Privacy = Privacy.PRIVATE,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        length: Optional[int] = None,
        **kwargs,
    ) -> None:
        """Corpus Class.

        Description:
            Corpus is general-purpose collection of data that can be processed and used to create task-specific datasets.

        Args:
            id (Text): Corpus ID
            name (Text): Corpus Name
            description (Text): description of the corpus
            data (List[Data]): List of data which the corpus consists of
            onboard_status (OnboardStatus): onboard status
            functions (List[Function], optional): AI functions in which the corpus is suggested to be used to. Defaults to [].
            tags (List[Text], optional): description tags. Defaults to [].
            license (Optional[License], optional): Corpus license. Defaults to None.
            privacy (Privacy, optional): Corpus privacy info. Defaults to Privacy.PRIVATE.
            supplier (Text, optional): Corpus supplier. Defaults to "aiXplain".
            version (Text, optional): Corpus version. Defaults to "1.0".
            length (Optional[int], optional): Number of rows in the Corpus. Defaults to None.
        """
        super().__init__(
            id=id, name=name, description=description, supplier=supplier, version=version, license=license, privacy=privacy
        )
        if isinstance(onboard_status, str):
            onboard_status = OnboardStatus(onboard_status)
        self.onboard_status = onboard_status
        self.functions = functions
        self.tags = tags
        self.data = data
        self.length = length
        self.kwargs = kwargs

    def __repr__(self) -> str:
        """Return a string representation of the Corpus instance.

        Returns:
            str: A string in the format "<Corpus: name>".
        """
        return f"<Corpus: {self.name}>"

    def delete(self) -> None:
        """Delete this corpus from the aiXplain platform.

        This method permanently removes the corpus from the platform. The operation
        can only be performed by the corpus owner.

        Returns:
            None

        Raises:
            Exception: If the deletion fails, either because:
                - The corpus doesn't exist
                - The user is not the owner
                - There's a network/server error
        """
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/corpora/{self.id}")
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start service for DELETE Corpus  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = "Corpus Deletion Error: Make sure the corpus exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")
