__author__ = "lucaspavanelli"

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
Date: June 14th 2023
Description:
    FinetuneCost Class
"""

from typing import Dict


class FinetuneCost:
    def __init__(
        self,
        training: Dict,
        inference: Dict,
        hosting: Dict,
    ) -> None:
        """Create a FinetuneCost object with training, inference, and hosting cost information.

        Args:
            training (Dict): Dictionary containing training cost information.
            inference (Dict): Dictionary containing inference cost information.
            hosting (Dict): Dictionary containing hosting cost information.
        """
        self.training = training
        self.inference = inference
        self.hosting = hosting

    def to_dict(self) -> Dict:
        """Convert the FinetuneCost object to a dictionary.

        Returns:
            Dict: A dictionary representation of the FinetuneCost object.
        """
        return {"trainingCost": self.training, "inferenceCost": self.inference, "hostingCost": self.hosting}
