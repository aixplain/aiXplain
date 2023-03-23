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
from aixtend.enums.function import Function
from aixtend.enums.license import License
from aixtend.enums.onboard_status import OnboardStatus
from aixtend.enums.privacy import Privacy
from aixtend.modules.asset import Asset
from aixtend.modules.data import Data
from aixtend.utils.file_utils import _request_with_retry, save_file
from typing import Any, List, Optional, Text


class Corpus(Asset):
    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        data: List[Data],
        onboard_status: OnboardStatus,
        functions: Optional[List[Function]] = [],
        tags: Optional[List[Text]] = [],
        license: Optional[License] = None,
        privacy: Optional[Privacy] = Privacy.PRIVATE,
        supplier: Optional[Text] = "aiXplain",
        version: Optional[Text] = "1.0",
        **kwargs,
    ) -> None:
        super().__init__(
            id=id, name=name, description=description, supplier=supplier, version=version, license=license, privacy=privacy
        )
        if isinstance(onboard_status, str):
            onboard_status = OnboardStatus(onboard_status)
        self.onboard_status = onboard_status
        self.functions = functions
        self.tags = tags
        self.data = data
        self.kwargs = kwargs
