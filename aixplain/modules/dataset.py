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
Date: October 28th 2022
Description:
    Datasets Class
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
from urllib.parse import urljoin
from typing import Any, Dict, List, Optional, Text


class Dataset(Asset):
    """Dataset is a collection of data intended to be used for a specific function.
            Different from corpus, a dataset is a representative sample of a specific phenomenon to a specific AI task.
            aiXplain also counts with an extensive collection of datasets for training, infer and benchmark various tasks like
            Translation, Speech Recognition, Diacritization, Sentiment Analysis, and much more.

    Attributes:
        id (Text): Dataset ID
        name (Text): Dataset Name
        description (Text): Dataset description
        function (Function): Function for which the dataset is intented to
        source_data (Dict[Any, Data]): List of input Data to the function
        target_data (Dict[Any, List[Data]]): List of Multi-reference Data which is expected to be outputted by the function
        onboard_status (OnboardStatus): onboard status
        hypotheses (Dict[Any, Data], optional): dataset's hypotheses, i.e. model outputs based on the source data. Defaults to {}.
        metadata (Dict[Any, Data], optional): dataset's metadata. Defaults to {}.
        tags (List[Text], optional): tags that describe the dataset. Defaults to [].
        license (Optional[License], optional): Dataset License. Defaults to None.
        privacy (Privacy, optional): Dataset Privacy. Defaults to Privacy.PRIVATE.
        supplier (Text, optional): Dataset Supplier. Defaults to "aiXplain".
        version (Text, optional): Dataset Version. Defaults to "1.0".
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        function: Function,
        source_data: Dict[Any, Data],
        target_data: Dict[Any, List[Data]],
        onboard_status: OnboardStatus,
        hypotheses: Dict[Any, Data] = {},
        metadata: Dict[Any, Data] = {},
        tags: List[Text] = [],
        license: Optional[License] = None,
        privacy: Privacy = Privacy.PRIVATE,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        length: Optional[int] = None,
        **kwargs,
    ) -> None:
        """Dataset Class.

        Description:
            Dataset is a collection of data intended to be used for a specific function.
            Different from corpus, a dataset is a representative sample of a specific phenomenon to a specific AI task.
            aiXplain also counts with an extensive collection of datasets for training, infer and benchmark various tasks like
            Translation, Speech Recognition, Diacritization, Sentiment Analysis, and much more.

        Args:
            id (Text): Dataset ID
            name (Text): Dataset Name
            description (Text): Dataset description
            function (Function): Function for which the dataset is intented to
            source_data (Dict[Any, Data]): List of input Data to the function
            target_data (Dict[Any, List[Data]]): List of Multi-reference Data which is expected to be outputted by the function
            onboard_status (OnboardStatus): onboard status
            hypotheses (Dict[Any, Data], optional): dataset's hypotheses, i.e. model outputs based on the source data. Defaults to {}.
            metadata (Dict[Any, Data], optional): dataset's metadata. Defaults to {}.
            tags (List[Text], optional): tags that describe the dataset. Defaults to [].
            license (Optional[License], optional): Dataset License. Defaults to None.
            privacy (Privacy, optional): Dataset Privacy. Defaults to Privacy.PRIVATE.
            supplier (Text, optional): Dataset Supplier. Defaults to "aiXplain".
            version (Text, optional): Dataset Version. Defaults to "1.0".
            length (Optional[int], optional): Number of rows in the Dataset. Defaults to None.
        """
        super().__init__(
            id=id, name=name, description=description, supplier=supplier, version=version, license=license, privacy=privacy
        )
        if isinstance(onboard_status, str):
            onboard_status = OnboardStatus(onboard_status)
        self.onboard_status = onboard_status
        self.function = function
        self.source_data = source_data
        self.target_data = target_data
        self.hypotheses = hypotheses
        self.metadata = metadata
        self.tags = tags
        self.length = length
        self.kwargs = kwargs

    def __repr__(self) -> str:
        """Return a string representation of the Dataset instance.

        Returns:
            str: A string in the format "<Dataset: name>".
        """
        return f"<Dataset: {self.name}>"

    def delete(self) -> None:
        """Delete this dataset from the aiXplain platform.

        This method permanently removes the dataset from the platform. The operation
        can only be performed by the dataset owner.

        Returns:
            None

        Raises:
            Exception: If the deletion fails, either because:
                - The dataset doesn't exist
                - The user is not the owner
                - There's a network/server error
        """
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/datasets/{self.id}")
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start service for DELETE Dataset  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = "Dataset Deletion Error: Make sure the dataset exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")
