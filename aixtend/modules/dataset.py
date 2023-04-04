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

from aixtend.enums.function import Function
from aixtend.enums.license import License
from aixtend.enums.privacy import Privacy
from aixtend.modules.asset import Asset
from aixtend.modules.data import Data
from aixtend.utils.file_utils import _request_with_retry, save_file
from typing import Any, List, Optional, Text


class Dataset(Asset):
    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        function: Function,
        source_data: List[Data],
        target_data: List[Data],
        tags: Optional[List[Text]] = [],
        license: Optional[License] = None,
        privacy: Optional[Privacy] = Privacy.PRIVATE,
        supplier: Optional[Text] = "aiXplain",
        version: Optional[Text] = "1.0",
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
            source_data (List[Data]): List of input Data to the function
            target_data (List[Data]): List of Data which expected to be outputted by the function
            tags (Optional[List[Text]], optional): tags that describe the dataset. Defaults to [].
            license (Optional[License], optional): Dataset License. Defaults to None.
            privacy (Optional[Privacy], optional): Dataset Privacy. Defaults to Privacy.PRIVATE.
            supplier (Optional[Text], optional): Dataset Supplier. Defaults to "aiXplain".
            version (Optional[Text], optional): Dataset Version. Defaults to "1.0".
        """
        super().__init__(
            id=id, name=name, description=description, supplier=supplier, version=version, license=license, privacy=privacy
        )
        self.function = function
        self.source_data = source_data
        self.target_data = target_data
        self.tags = tags
        self.kwargs = kwargs
