"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: November 25th 2024
Description:
    Utility Model Class
"""
import logging
import os
import validators
from aixplain.enums import Function, Supplier, DataType
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from dataclasses import dataclass
from typing import Union, Optional, List, Text, Dict
from urllib.parse import urljoin


@dataclass
class UtilityModelInput:
    name: Text
    description: Text
    type: DataType = DataType.TEXT

    def __post_init__(self):
        self.validate_type()

    def validate_type(self):
        if self.type not in [DataType.TEXT, DataType.BOOLEAN, DataType.NUMBER]:
            raise ValueError("Utility Model Input type must be TEXT, BOOLEAN or NUMBER")

    def to_dict(self):
        return {"name": self.name, "description": self.description, "type": self.type.value}


class UtilityModel(Model):
    """Ready-to-use Utility Model.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        description (Text, optional): description of the model. Defaults to "".
        api_key (Text, optional): API key of the Model. Defaults to None.
        url (Text, optional): endpoint of the model. Defaults to config.MODELS_RUN_URL.
        supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        function (Text, optional): model AI function. Defaults to None.
        url (str): URL to run the model.
        backend_url (str): URL of the backend.
        pricing (Dict, optional): model price. Defaults to None.
        **additional_info: Any additional Model info to be saved
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text,
        code: Text,
        inputs: List[UtilityModelInput],
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        **additional_info,
    ) -> None:
        """Utility Model Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text): description of the model.
            code (Text): code of the model.
            inputs (List[UtilityModelInput]): inputs of the model.
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Function, optional): model AI function. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): model price. Defaults to None.
            **additional_info: Any additional Model info to be saved
        """
        assert function == Function.UTILITIES, "Utility Model only supports 'utilities' function"
        super().__init__(
            id=id,
            name=name,
            description=description,
            supplier=supplier,
            version=version,
            cost=cost,
            function=function,
            is_subscribed=is_subscribed,
            api_key=api_key,
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.code = code
        self.inputs = inputs
        self.validate()

    def validate(self):
        from aixplain.factories.file_factory import FileFactory
        from uuid import uuid4

        assert self.name and self.name.strip() != "", "Name is required"
        assert self.description and self.description.strip() != "", "Description is required"
        assert self.code and self.code.strip() != "", "Code is required"
        assert self.inputs and len(self.inputs) > 0, "At least one input is required"

        self.code = FileFactory.to_link(self.code)
        # store code in a temporary local path if it is not a valid URL or S3 path
        if not validators.url(self.code) and not self.code.startswith("s3:"):
            local_path = str(uuid4())
            with open(local_path, "w") as f:
                f.write(self.code)
            self.code = FileFactory.upload(local_path=local_path, is_temp=True)
            os.remove(local_path)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputs": [input.to_dict() for input in self.inputs],
            "code": self.code,
            "function": self.function.value,
        }

    def update(self):
        self.validate()
        url = urljoin(self.backend_url, f"sdk/utilities/{self.id}")
        headers = {"x-api-key": f"{self.api_key}", "Content-Type": "application/json"}
        payload = self.to_dict()
        try:
            logging.info(f"Start service for PUT Utility Model - {url} - {headers} - {payload}")
            r = _request_with_retry("put", url, headers=headers, json=payload)
            response = r.json()
        except Exception as e:
            message = f"Utility Model Update Error: {e}"
            logging.error(message)
            raise Exception(f"{message}")

        if not 200 <= r.status_code < 300:
            message = f"Utility Model Update Error: {response}"
            logging.error(message)
            raise Exception(f"{message}")

    def delete(self):
        url = urljoin(self.backend_url, f"sdk/utilities/{self.id}")
        headers = {"x-api-key": f"{self.api_key}", "Content-Type": "application/json"}
        try:
            logging.info(f"Start service for DELETE Utility Model  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            response = r.json()
        except Exception:
            message = "Utility Model Deletion Error: Make sure the utility model exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")

        if r.status_code != 200:
            message = f"Utility Model Deletion Error: {response}"
            logging.error(message)
            raise Exception(f"{message}")
