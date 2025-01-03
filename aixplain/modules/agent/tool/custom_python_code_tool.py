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

from typing import Text, Union, Callable
from aixplain.modules.agent.tool import Tool


class CustomPythonCodeTool(Tool):
    """Custom Python Code Tool"""

    def __init__(self, code: Union[Text, Callable], description: Text = "", **additional_info) -> None:
        """Custom Python Code Tool"""
        super().__init__(name="Custom Python Code", description=description, **additional_info)
        self.code = code

    def to_dict(self):
        return {
            "description": self.description,
            "type": "utility",
            "utility": "custom_python_code",
            "utilityCode": self.code,
        }

    def validate(self):
        from aixplain.modules.model.utils import parse_code

        self.code, _, description = parse_code(self.code)

        assert (
            description is not None or self.description is not None
        ), "Custom Python Code Tool Error: Tool description is required"
        if self.description is None or self.description.strip() == "":
            self.description = description
        assert self.name and self.name.strip() != "", "Name is required"
        assert self.description and self.description.strip() != "", "Description is required"
        assert self.code and self.code.strip() != "", "Code is required"
