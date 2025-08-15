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
    Asset Factory Class
"""

from abc import abstractmethod
from typing import Text
from aixplain.modules.asset import Asset
from aixplain.utils import config


class AssetFactory:
    """Base class for asset factories.

    This class provides a common interface for creating and retrieving assets
    from the aiXplain platform. Subclasses should implement the abstract methods
    to define specific asset types.

    Attributes:
        backend_url (str): Base URL for the aiXplain backend API.
    """

    backend_url = config.BACKEND_URL
    @abstractmethod
    def get(self, asset_id: Text) -> Asset:
        """Create a 'Asset' object from id

        Args:
            asset_id (str): ID of required asset.

        Returns:
            Asset: Created 'Asset' object
        """
        pass
