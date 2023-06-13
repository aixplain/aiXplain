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
Date: September 1st 2022
Description:
    Cost Class
"""

from typing import Dict

class Cost:
    """This is ready-to-use AI model. This model can be run in both synchronous and asynchronous manner.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        description (Text, optional): description of the model. Defaults to "".
        api_key (Text, optional): API key of the Model. Defaults to None.
        url (Text, optional): endpoint of the model. Defaults to config.MODELS_RUN_URL.
        supplier (Text, optional): model supplier. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        **additional_info: Any additional Model info to be saved
    """

    def __init__(
        self,
        training: Dict,
        inference: Dict,
        hosting: Dict,
    ) -> None:
        self.training = training
        self.inference = inference
        self.hosting = hosting

    def to_dict(self) -> Dict:
        """Get the model info as a Dictionary

        Returns:
            Dict: Cost Information
        """
        return {"training_cost": self.training, "inference_cost": self.inference, "hosting_cost": self.hosting, "additional_info": clean_additional_info}