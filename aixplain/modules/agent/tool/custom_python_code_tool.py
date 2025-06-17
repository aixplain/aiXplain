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

from typing import Text, Union, Callable, Optional
from aixplain.modules.agent.tool import Tool
import logging
from aixplain.enums import AssetStatus
from aixplain.enums.code_interpeter import CodeInterpreterModel


class CustomPythonCodeTool(Tool):
    """Custom Python Code Tool"""

    def __init__(
        self, code: Union[Text, Callable], description: Text = "", name: Optional[Text] = None, **additional_info
    ) -> None:
        """Custom Python Code Tool"""
        super().__init__(name=name or "", description=description, **additional_info)
        self.code = code
        self.status = AssetStatus.ONBOARDED  # TODO: change to DRAFT when we have a way to onboard the tool
        self.id = CodeInterpreterModel.PYTHON_AZURE

        self.validate()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": "utility",
            "utility": "custom_python_code",
            "utilityCode": self.code,
        }

    def validate(self):
        from aixplain.modules.model.utils import parse_code_decorated

        if not str(self.code).startswith("s3://"):
            self.code, _, description, name = parse_code_decorated(self.code)
        else:
            logging.info("Utility Model Already Exists, skipping code validation")
            return

        # Set description from parsed code if not already set
        if not self.description or self.description.strip() == "":
            self.description = description
        # Set name from parsed code if could find it
        if name and name.strip() != "":
            self.name = name

        assert (
            self.description and self.description.strip() != ""
        ), "Custom Python Code Tool Error: Tool description is required"
        assert self.code and self.code.strip() != "", "Custom Python Code Tool Error: Code is required"
        assert self.name and self.name.strip() != "", "Custom Python Code Tool Error: Name is required"
        assert self.status in [
            AssetStatus.DRAFT,
            AssetStatus.ONBOARDED,
        ], "Custom Python Code Tool Error: Status must be DRAFT or ONBOARDED"

    def __repr__(self) -> Text:
        return f"CustomPythonCodeTool(name={self.name})"

    def deploy(self):
        pass
