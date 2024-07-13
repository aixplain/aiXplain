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
from typing import Text, Optional

from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier


class Tool:
    """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

    Attributes:
        name (Text): name of the tool
        description (Text): descriptiion of the tool
        function (Function): task that the tool performs
        supplier (Optional[Union[Dict, Text, Supplier, int]], optional): Preferred supplier to perform the task. Defaults to None.
    """

    def __init__(
        self,
        name: Text,
        description: Text,
        function: Function,
        supplier: Optional[Supplier] = None,
        **additional_info,
    ) -> None:
        """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

        Args:
            name (Text): name of the tool
            description (Text): descriptiion of the tool
            function (Function): task that the tool performs
            supplier (Optional[Union[Dict, Text, Supplier, int]], optional): Preferred supplier to perform the task. Defaults to None.
        """
        self.name = name
        self.description = description
        self.function = function
        self.supplier = supplier
        self.additional_info = additional_info
