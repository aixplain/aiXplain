__author__="aiXplain"

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

class Asset:
    def __init__(self, id:str, name:str, description:str) -> None:
        """Create an Asset with the necessary information

        Args:
            id (str): ID of the Asset
            name (str): Name of the Asset
            description (str): Description of the Asset
        """
        self.id = id
        self.name = name
        self.description = description

    
    def get_asset_info(self) -> dict:
        """Get the asset info as a Dictionary

        Returns:
            dict: Asset Information
        """
        return self.__dict__