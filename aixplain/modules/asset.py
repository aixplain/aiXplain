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
from aixplain.enums.supplier import Supplier
from aixplain.enums.privacy import Privacy
from typing import Dict, Optional, Text, Union


class Asset:
    """A class representing an aiXplain Asset.

    This class provides functionality to create and manage assets in the aiXplain platform.
    Assets can be models, datasets, or other resources with associated metadata like
    supplier information, version, license, privacy settings, and cost.

    Attributes:
        id (Text): The unique identifier of the asset.
        name (Text): The name of the asset.
        description (Text): A detailed description of the asset.
        supplier (Union[Dict, Text, Supplier, int]): The supplier of the asset.
        version (Text): The version of the asset.
        license (Optional[License]): The license associated with the asset.
        privacy (Privacy): The privacy setting of the asset.
        cost (Optional[Union[Dict, float]]): The cost associated with the asset.
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        supplier: Union[Dict, Text, Supplier, int] = Supplier.AIXPLAIN,
        version: Text = "1.0",
        license: Optional[License] = None,
        privacy: Privacy = Privacy.PRIVATE,
        cost: Optional[Union[Dict, float]] = None,
    ) -> None:
        """Initialize a new Asset instance.

        Args:
            id (Text): Unique identifier of the asset.
            name (Text): Name of the asset.
            description (Text): Detailed description of the asset.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier of the asset. 
                Can be a Supplier enum, dictionary, text, or integer. Defaults to Supplier.AIXPLAIN.
            version (Text, optional): Version of the asset. Defaults to "1.0".
            license (Optional[License], optional): License associated with the asset. Defaults to None.
            privacy (Privacy, optional): Privacy setting of the asset. Defaults to Privacy.PRIVATE.
            cost (Optional[Union[Dict, float]], optional): Cost of the asset. Can be a dictionary
                with pricing details or a float value. Defaults to None.
        """
        self.id = id
        self.name = name
        self.description = description
        try:
            if isinstance(supplier, Supplier) is True:
                self.supplier = supplier
            elif isinstance(supplier, Dict) is True:
                self.supplier = Supplier(supplier)
            else:
                self.supplier = None
                for supplier_ in Supplier:
                    if supplier.lower() in [supplier_.value["code"].lower(), supplier_.value["name"].lower()]:
                        self.supplier = supplier_
                        break
                if self.supplier is None:
                    self.supplier = supplier
        except Exception:
            self.supplier = Supplier.AIXPLAIN
        self.version = version
        self.license = license
        self.privacy = privacy
        self.cost = cost

    def to_dict(self) -> dict:
        """Convert the Asset instance to a dictionary representation.

        This method serializes all attributes of the Asset instance into a dictionary
        format, which can be useful for data transmission or storage.

        Returns:
            dict: A dictionary containing all attributes of the Asset instance.
                Keys are attribute names and values are their corresponding values.
        """
        return self.__dict__
