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
from aixplain.enums.function import Function
from aixplain.enums.license import License
from aixplain.enums.onboard_status import OnboardStatus
from aixplain.enums.privacy import Privacy
from aixplain.modules.asset import Asset
from aixplain.modules.data import Data
from typing import Any, List, Optional, Text


class Corpus(Asset):
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
