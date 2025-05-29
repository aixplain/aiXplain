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

from aixplain.enums import AssetStatus, Function, Supplier
from aixplain.modules.agent.tool import Tool
from aixplain.modules.model import Model


def set_tool_name(function: Function, supplier: Supplier = None, model: Model = None) -> Text:
    """Sets the name of the tool based on the function, supplier, and model.

    Args:
        function (Function): The function to be used in the tool.
        supplier (Supplier): The supplier to be used in the tool.
        model (Model): The model to be used in the tool.

    Returns:
        Text: The name of the tool.
    """
    function_name = function.value.lower().replace(" ", "_")
    tool_name = f"{function_name}"

    if supplier is not None:
        supplier_name = supplier.name.lower().replace(" ", "_")
        tool_name += f"-{supplier_name}"

    if model is not None and supplier is not None:
        model_name = model.name.lower().replace(" ", "_")
        tool_name += f"-{model_name}"
    return tool_name


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
        status = AssetStatus.ONBOARDED if model is None else AssetStatus.DRAFT
        model_id = model  # if None,  Set id to None as default
        self.model_object = None  # Store the actual model object for parameter access

        if isinstance(model, Model):
            model_id = model.id
            status = model.status
            self.model_object = model  # Store the Model object
        elif isinstance(model, Text):
            # get model from id
            try:
                self.model_object = self._get_model(model)  # Store the Model object
                model_id = self.model_object.id
                status = self.model_object.status
            except Exception:
                raise Exception(f"Model Tool Unavailable. Make sure Model '{model}' exists or you have access to it.")

        self.supplier = supplier
        self.model = model_id
        self.status = status
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
            "status": self.status,
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
                    self.model = self._get_model()
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
                    self.description = FunctionInputOutput[self.function.value]["spec"]["description"]
                except Exception:
                    self.description = ""

        self.parameters = self.validate_parameters(self.parameters)
        self.name = self.name if self.name else set_tool_name(self.function, self.supplier, self.model)


    def get_parameters(self) -> Dict:
        # If parameters were not explicitly provided, get them from the model
        if (
            self.parameters is None
            and self.model_object is not None  # noqa: W503
            and hasattr(self.model_object, "model_params")  # noqa: W503
            and self.model_object.model_params is not None  # noqa: W503
        ):
            return self.model_object.model_params.to_list()
        return self.parameters

    def _get_model(self, model_id: Text = None):
        from aixplain.factories.model_factory import ModelFactory

        model_id = model_id or self.model
        return ModelFactory.get(model_id, api_key=self.api_key)

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
            if (
                self.model_object is not None
                and hasattr(self.model_object, "model_params")  # noqa: W503
                and self.model_object.model_params is not None  # noqa: W503
            ):
                return self.model_object.model_params.to_list()
    
            elif self.function is not None:
                function_params = self.function.get_parameters()
                if function_params is not None:
                    return function_params.to_list()
            return None

        # Get expected parameters
        expected_params = None
        if (
            self.model_object is not None
            and hasattr(self.model_object, "model_params")  # noqa: W503
            and self.model_object.model_params is not None  # noqa: W503
        ):
            expected_params = self.model_object.model_params
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

    def __repr__(self) -> Text:
        supplier_str = self.supplier.value if self.supplier is not None else None
        model_str = self.model.id if self.model is not None else None
        return f"ModelTool(name={self.name}, function={self.function}, supplier={supplier_str}, model={model_str})"

    def deploy(self):
        pass
