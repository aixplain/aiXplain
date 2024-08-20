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
from typing import Optional, Union, Text

from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.modules.agent.tool import Tool
from aixplain.modules.model import Model


class ModelTool(Tool):
    """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

    Attributes:
        function (Function): task that the tool performs
        supplier (Optional[Union[Dict, Text, Supplier, int]], optional): Preferred supplier to perform the task. Defaults to None.
    """

    def __init__(
        self,
        function: Optional[Function] = None,
        supplier: Optional[Supplier] = None,
        model: Optional[Union[Text, Model]] = None,
        **additional_info,
    ) -> None:
        """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

        Args:
            function (Optional[Function], optional): task that the tool performs. Defaults to None.
            supplier (Optional[Supplier], optional): Preferred supplier to perform the task. Defaults to None.. Defaults to None.
            model (Optional[Union[Text, Model]], optional): Model function. Defaults to None.
        """
        assert (
            function is not None or model is not None
        ), "Agent Creation Error: Either function or model must be provided when instantiating a tool."
        super().__init__("", "", **additional_info)
        if function is not None:
            if isinstance(function, str):
                function = Function(function)

        try:
            if isinstance(supplier, dict):
                supplier = Supplier(supplier)
        except Exception:
            supplier = None

        if model is not None:
            if isinstance(model, Text) is True:
                from aixplain.factories.model_factory import ModelFactory

                model = ModelFactory.get(model)
            function = model.function
            if isinstance(model.supplier, Supplier):
                supplier = model.supplier
            model = model.id
        self.supplier = supplier
        self.model = model
        self.function = function
