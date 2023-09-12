__author__ = "aiXplain"

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
Date: December 27th 2022
Description:
    Asset Class
"""
from aixplain.enums.license import License
from aixplain.enums.privacy import Privacy
from typing import Optional, Text


class Asset:
    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        supplier: Text = "aiXplain",
        version: Text = "1.0",
        license: Optional[License] = None,
        privacy: Privacy = Privacy.PRIVATE,
        cost: float = 0
    ) -> None:
        """Create an Asset with the necessary information

        Args:
            id (Text): ID of the Asset
            name (Text): Name of the Asset
            description (Text): Description of the Asset
            supplier (Optional[Text], optional): supplier of the asset. Defaults to "aiXplain".
            version (Optional[Text], optional): asset version. Defaults to "1.0".
        """
        self.id = id
        self.name = name
        self.description = description
        self.supplier = supplier
        self.version = version
        self.license = license
        self.privacy = privacy
        self.cost = cost

    def to_dict(self) -> dict:
        """Get the asset info as a Dictionary

        Returns:
            dict: Asset Information
        """
        return self.__dict__
