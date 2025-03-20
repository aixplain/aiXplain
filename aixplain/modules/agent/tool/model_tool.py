__author__ = "aiXplain"

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

Author: Lucas Pavanelli and Thiago Castro Ferreira
Date: May 16th 2024
Description:
    Agentification Class
"""
from typing import Optional, Union, Text, Dict, List

from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.modules.agent.tool import Tool
from aixplain.modules.model import Model


class ModelTool(Tool):
    """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

    Attributes:
        function (Optional[Function]): task that the tool performs.
        supplier (Optional[Supplier]): Preferred supplier to perform the task.
        model (Optional[Text]): Model function.
    """

    def __init__(
        self,
        function: Optional[Union[Function, Text]] = None,
        supplier: Optional[Union[Dict, Supplier]] = None,
        model: Optional[Union[Text, Model]] = None,
        name: Optional[Text] = None,
        description: Text = "",
        parameters: Optional[Dict] = None,
        **additional_info,
    ) -> None:
        """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

        Args:
            function (Optional[Union[Function, Text]]): task that the tool performs. Defaults to None.
            supplier (Optional[Union[Dict, Supplier]]): Preferred supplier to perform the task. Defaults to None. Defaults to None.
            model (Optional[Union[Text, Model]]): Model function. Defaults to None.
            name (Optional[Text]): Name of the tool. Defaults to None.
            description (Text): Description of the tool. Defaults to "".
            parameters (Optional[Dict]): Parameters of the tool. Defaults to None.
        """
        name = name or ""
        super().__init__(name=name, description=description, **additional_info)
        self.supplier = supplier
        self.model = model
        self.function = function
        self.parameters = parameters
        self.validate()

    def to_dict(self) -> Dict:
        """Converts the tool to a dictionary."""
        supplier = self.supplier
        if supplier is not None:
            if isinstance(supplier, dict):
                supplier = supplier["code"]
            elif isinstance(supplier, Supplier):
                supplier = supplier.value["code"]
            else:
                supplier = str(supplier)

        return {
            "function": self.function.value if self.function is not None else None,
            "type": "model",
            "name": self.name,
            "description": self.description,
            "supplier": supplier,
            "version": self.version if self.version else None,
            "assetId": self.model.id if self.model is not None and isinstance(self.model, Model) else self.model,
            "parameters": self.parameters,
        }

    def validate(self) -> None:
        """
        Validates the tool.
        Notes:
            - Checks if the tool has a function or model.
            - If the function is a string, it converts it to a Function enum.
            - Checks if the function is a utility function and if it has an associated model.
            - Validates the supplier.
            - Validates the model.
            - If the description is empty, it sets the description to the function description or the model description.
        """
        from aixplain.enums import FunctionInputOutput
        from aixplain.factories.model_factory import ModelFactory

        assert (
            self.function is not None or self.model is not None
        ), "Agent Creation Error: Either function or model must be provided when instantiating a tool."

        if self.function is not None:
            if isinstance(self.function, str):
                self.function = Function(self.function)
        assert (
            self.function is None or self.function is not Function.UTILITIES or self.model is not None
        ), "Agent Creation Error: Utility function must be used with an associated model."

        try:
            if isinstance(self.supplier, dict):
                self.supplier = Supplier(self.supplier)
        except Exception:
            self.supplier = None

        if self.model is not None:
            if isinstance(self.model, Text) is True:
                try:
                    self.model = ModelFactory.get(self.model, api_key=self.api_key)
                except Exception:
                    raise Exception(f"Model Tool Unavailable. Make sure Model '{self.model}' exists or you have access to it.")
            self.function = self.model.function
            if isinstance(self.model.supplier, Supplier):
                self.supplier = self.model.supplier

        if self.description == "":
            if self.model is not None:
                self.description = self.model.description
            elif self.function is not None:
                try:
                    self.description = FunctionInputOutput[self.function.value]["spec"]["metaData"]["description"]
                except Exception:
                    self.description = ""

        self.parameters = self.validate_parameters(self.parameters)

    def get_parameters(self) -> Dict:
        return self.parameters

    def validate_parameters(self, received_parameters: Optional[List[Dict]] = None) -> Optional[List[Dict]]:
        """Validates and formats the parameters for the tool.

        Args:
            received_parameters (Optional[List[Dict]]): List of parameter dictionaries in format [{"name": "param_name", "value": param_value}]

        Returns:
            Optional[List[Dict]]: Validated parameters in the required format

        Raises:
            ValueError: If received parameters don't match the expected parameters from model or function
        """
        if received_parameters is None:
            # Get default parameters if none provided
            if self.model is not None and self.model.model_params is not None:
                return self.model.model_params.to_list()
            elif self.function is not None:
                function_params = self.function.get_parameters()
                if function_params is not None:
                    return function_params.to_list()
            return None

        # Get expected parameters
        expected_params = None
        if self.model is not None and self.model.model_params is not None:
            expected_params = self.model.model_params
        elif self.function is not None:
            expected_params = self.function.get_parameters()

        if expected_params is None:
            return received_parameters

        # Validate received parameters
        if not isinstance(received_parameters, list):
            raise TypeError("Parameters must be provided as a list of dictionaries")

        # Get expected parameter names from BaseParameters object
        expected_param_names = set(expected_params.parameters.keys())
        received_param_names = {param["name"] for param in received_parameters}

        invalid_params = received_param_names - expected_param_names
        if invalid_params:
            raise ValueError(f"Invalid parameters provided: {invalid_params}. Expected parameters are: {expected_param_names}")

        return received_parameters
