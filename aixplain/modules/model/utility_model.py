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
from aixplain.enums import Function, Supplier, DataType
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from aixplain.modules.model.utils import parse_code_decorated
from dataclasses import dataclass
from typing import Callable, Union, Optional, List, Text, Dict
from urllib.parse import urljoin


@dataclass
class UtilityModelInput:
    name: Text
    description: Text
    type: DataType = DataType.TEXT

    def validate(self):
        if self.type not in [DataType.TEXT, DataType.BOOLEAN, DataType.NUMBER]:
            raise ValueError("Utility Model Input type must be TEXT, BOOLEAN or NUMBER")

    def to_dict(self):
        return {"name": self.name, "description": self.description, "type": self.type.value}

# Tool decorator
def utility_tool(name: Text, description: Text, inputs: List[UtilityModelInput] = None, output_examples: Text = "", status = AssetStatus.DRAFT):
    """Decorator for utility tool functions
    
    Args:
        name: Name of the utility tool
        description: Description of what the utility tool does
        inputs: List of input parameters, must be UtilityModelInput objects
        output_examples: Examples of expected outputs
        status: Asset status
        
    Raises:
        ValueError: If name or description is empty
        TypeError: If inputs contains non-UtilityModelInput objects
    """
    # Validate name and description
    if not name or not name.strip():
        raise ValueError("Utility tool name cannot be empty")
    if not description or not description.strip():
        raise ValueError("Utility tool description cannot be empty")
    
    # Validate inputs
    if inputs is not None:
        if not isinstance(inputs, list):
            raise TypeError("Inputs must be a list of UtilityModelInput objects")
        for input_param in inputs:
            if not isinstance(input_param, UtilityModelInput):
                raise TypeError(f"Invalid input parameter: {input_param}. All inputs must be UtilityModelInput objects")
        
    def decorator(func):
        func._is_utility_tool = True  # Mark function as utility tool
        func._tool_name = name.strip()
        func._tool_description = description.strip()
        func._tool_inputs = inputs if inputs else []
        func._tool_output_examples = output_examples
        func._tool_status = status
        return func
    return decorator


class UtilityModel(Model):
    """Ready-to-use Utility Model.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        code (Union[Text, Callable]): code of the model.
        description (Text): description of the model. Defaults to "".
        inputs (List[UtilityModelInput]): inputs of the model. Defaults to [].
        output_examples (Text): output examples. Defaults to "".
        api_key (Text, optional): API key of the Model. Defaults to None.
        supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        function (Function, optional): model AI function. Defaults to None.
        is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
        cost (Dict, optional): model price. Defaults to None.
        **additional_info: Any additional Model info to be saved
    """

    def __init__(
        self,
        id: Text,
        name: Optional[Text] = None,
        code: Union[Text, Callable] = None,
        description: Optional[Text] = None,
        inputs: List[UtilityModelInput] = [],
        output_examples: Text = "",
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        status: AssetStatus = AssetStatus.ONBOARDED,# TODO: change to draft when we have the backend ready
        **additional_info,
    ) -> None:
        """Utility Model Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            code (Union[Text, Callable]): code of the model.
            description (Text): description of the model. Defaults to "".
            inputs (List[UtilityModelInput]): inputs of the model. Defaults to [].
            output_examples (Text): output examples. Defaults to "".
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
        self.output_examples = output_examples
        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.DRAFT
        self.status = status

    def validate(self):
        """Validate the Utility Model."""
        description = None
        name = None
        inputs = []
        # check if the model exists and if the code is strring with s3://
        # if not, parse the code and update the description and inputs and do the validation
        # if yes, just do the validation on the description and inputs
        if not (self._model_exists() and str(self.code).startswith("s3://")):
            self.code, inputs, description, name = parse_code_decorated(self.code)
            if self.name is None:
                self.name = name
            if self.description is None:
                self.description = description
            if len(self.inputs) == 0:
                self.inputs = inputs
            for input in self.inputs:
                input.validate()
        else:
            logging.info("Utility Model Already Exists, skipping code validation")

        assert description is not None or self.description is not None, "Utility Model Error: Model description is required"
        assert self.name and self.name.strip() != "", "Name is required"
        assert self.description and self.description.strip() != "", "Description is required"
        assert self.code and self.code.strip() != "", "Code is required"


    def _model_exists(self):
        if self.id is None or self.id == "":
            return False
        url = urljoin(self.backend_url, f"sdk/models/{self.id}")
        headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Model  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        if r.status_code != 200:
            raise Exception()
        return True

      
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputs": [input.to_dict() for input in self.inputs],
            "code": self.code,
            "function": self.function.value,
            "outputDescription": self.output_examples,
            "status": self.status.value,
        }

    def update(self):
        """Update the Utility Model."""
        import warnings
        import inspect

        # Get the current call stack
        stack = inspect.stack()
        if len(stack) > 2 and stack[1].function != "save":
            warnings.warn(
                "update() is deprecated and will be removed in a future version. " "Please use save() instead.",
                DeprecationWarning,
                stacklevel=2,
            )

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

    def save(self):
        """Save the Utility Model."""
        self.update()

    def delete(self):
        """Delete the Utility Model."""
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

    def deploy(self) -> None:
        assert self.status == AssetStatus.DRAFT, "Utility Model must be in draft status to be deployed."
        assert self.status != AssetStatus.ONBOARDED, "Utility Model is already deployed."
        self.status = AssetStatus.ONBOARDED
        self.update()
