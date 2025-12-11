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
import warnings
from aixplain.enums import Function, Supplier, DataType, FunctionType
from aixplain.enums import AssetStatus
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.modules.model.utils import parse_code_decorated
from dataclasses import dataclass
from typing import Callable, Union, Optional, List, Text, Dict
from urllib.parse import urljoin
from aixplain.modules.mixins import DeployableMixin
from pydantic import BaseModel


class BaseUtilityModelParams(BaseModel):
    """Base model for utility model parameters.

    This class defines the basic parameters required to create or update a utility model.

    Attributes:
        name (Text): The name of the utility model.
        code (Union[Text, Callable]): The implementation code, either as a string or
            a callable function.
        description (Optional[Text]): A description of what the utility model does.
            Defaults to None.
    """

    name: Text
    code: Union[Text, Callable]
    description: Optional[Text] = None


@dataclass
class UtilityModelInput:
    """A class representing an input parameter for a utility model.

    This class defines the structure and validation rules for input parameters
    that can be used with utility models.

    Attributes:
        name (Text): The name of the input parameter.
        description (Text): A description of what this input parameter represents.
        type (DataType): The data type of the input parameter. Must be one of:
            TEXT, BOOLEAN, or NUMBER. Defaults to DataType.TEXT.
    """

    name: Text
    description: Text
    type: DataType = DataType.TEXT

    def validate(self):
        """Validate that the input parameter has a supported data type.

        Raises:
            ValueError: If the type is not one of: TEXT, BOOLEAN, or NUMBER.
        """
        if self.type not in [DataType.TEXT, DataType.BOOLEAN, DataType.NUMBER]:
            raise ValueError("Utility Model Input type must be TEXT, BOOLEAN or NUMBER")

    def to_dict(self):
        """Convert the input parameter to a dictionary representation.

        Returns:
            dict: A dictionary containing the input parameter's name, description,
                and type (as a string value).
        """
        return {"name": self.name, "description": self.description, "type": self.type.value}


# Tool decorator
def utility_tool(
    name: Text, description: Text, inputs: List[UtilityModelInput] = None, output_examples: Text = "", status=AssetStatus.DRAFT
):
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


class UtilityModel(Model, DeployableMixin):
    """Ready-to-use Utility Model.

    Note: Non-deployed utility models (status=DRAFT) will expire after 24 hours after creation.
    Use the .deploy() method to make the model permanent.

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
        status (AssetStatus, optional): status of the model. Defaults to AssetStatus.DRAFT.
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
        status: AssetStatus = AssetStatus.DRAFT,
        function_type: Optional[FunctionType] = FunctionType.UTILITY,
        **additional_info,
    ) -> None:
        """Initialize a new UtilityModel instance.

        Args:
            id (Text): ID of the utility model.
            name (Optional[Text], optional): Name of the utility model. If not provided,
                will be extracted from the code if decorated. Defaults to None.
            code (Union[Text, Callable], optional): Implementation code, either as a string
                or a callable function. Defaults to None.
            description (Optional[Text], optional): Description of what the model does.
                If not provided, will be extracted from the code if decorated.
                Defaults to None.
            inputs (List[UtilityModelInput], optional): List of input parameters the
                model accepts. If not provided, will be extracted from the code if
                decorated. Defaults to [].
            output_examples (Text, optional): Examples of the model's expected outputs.
                Defaults to "".
            api_key (Optional[Text], optional): API key for accessing the model.
                Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier of the model.
                Defaults to "aiXplain".
            version (Optional[Text], optional): Version of the model. Defaults to None.
            function (Optional[Function], optional): Function type. Must be
                Function.UTILITIES. Defaults to None.
            is_subscribed (bool, optional): Whether the user is subscribed.
                Defaults to False.
            cost (Optional[Dict], optional): Cost information for the model.
                Defaults to None.
            status (AssetStatus, optional): Current status of the model.
                Defaults to AssetStatus.DRAFT.
            function_type (Optional[FunctionType], optional): Type of the function.
                Defaults to FunctionType.UTILITY.
            **additional_info: Any additional model info to be saved.

        Raises:
            AssertionError: If function is not Function.UTILITIES.

        Note:
            Non-deployed utility models (status=DRAFT) will expire after 24 hours.
            Use the .deploy() method to make the model permanent.
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
            status=status,
            function_type=function_type,
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

        if status == AssetStatus.DRAFT:
            warnings.warn(
                "WARNING: Non-deployed utility models (status=DRAFT) will expire after 24 hours after creation. "
                "Use .deploy() method to make the model permanent.",
                UserWarning,
            )

    def validate(self):
        """Validate the Utility Model.

        This method checks if the utility model exists in the backend and if the code is a string with s3://.
        If not, it parses the code and updates the description and inputs and does the validation.
        If yes, it just does the validation on the description and inputs.
        """
        description = None
        name = None
        # check if the model exists and if the code is strring with s3://
        # if not, parse the code and update the description and inputs and do the validation
        # if yes, just do the validation on the description and inputs
        if not (self._model_exists() and str(self.code).startswith("s3://")):
            self.code, self.inputs, description, name = parse_code_decorated(self.code)
            if self.name is None:
                self.name = name
            if self.description is None:
                self.description = description
            for input in self.inputs:
                input.validate()
        else:
            logging.info("Utility Model Already Exists, skipping code validation")

        assert description is not None or self.description is not None, "Utility Model Error: Model description is required"
        assert self.name and self.name.strip() != "", "Name is required"
        assert self.description and self.description.strip() != "", "Description is required"
        assert self.code and self.code.strip() != "", "Code is required"

    def _model_exists(self):
        """Check if the utility model exists in the backend.

        This internal method verifies whether a model with the current ID exists
        by making a GET request to the backend API.

        Returns:
            bool: True if the model exists and is accessible, False if the ID is
                empty or None.

        Raises:
            Exception: If the API request fails or returns a non-200 status code.
        """
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
        """Convert the utility model to a dictionary representation.

        This method creates a dictionary containing all the essential information
        about the utility model, suitable for API requests or serialization.

        Returns:
            dict: A dictionary containing:
                - name (str): The model's name
                - description (str): The model's description
                - inputs (List[dict]): List of input parameters as dictionaries
                - code (Union[str, Callable]): The model's implementation code
                - function (str): The function type as a string value
                - outputDescription (str): Examples of expected outputs
                - status (str): Current status as a string value
        """
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
        """Update the Utility Model.

        This method validates the utility model and updates it in the backend.

        Raises:
            Exception: If the update fails.
        """
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
        """Save the Utility Model.

        This method updates the utility model in the backend.
        """
        self.update()

    def delete(self):
        """Delete the Utility Model.

        This method deletes the utility model from the backend.
        """
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

    def __repr__(self):
        """Return a string representation of the UtilityModel instance.

        Returns:
            str: A string in the format "UtilityModel: <name> by <supplier> (id=<id>)".
                If supplier is a dictionary, uses supplier['name'], otherwise uses
                supplier directly.
        """
        try:
            return f"UtilityModel: {self.name} by {self.supplier['name']} (id={self.id})"
        except Exception:
            return f"UtilityModel: {self.name} by {self.supplier} (id={self.id})"
