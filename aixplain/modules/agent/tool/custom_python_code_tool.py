"""Custom Python code tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute custom Python code
in a controlled environment.

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

__author__ = "aiXplain"

from typing import Text, Union, Callable, Optional
from aixplain.modules.agent.tool import Tool
import logging
from aixplain.enums import AssetStatus
from aixplain.enums.code_interpreter import CodeInterpreterModel


class CustomPythonCodeTool(Tool):
    """A tool for executing custom Python code in the aiXplain platform.

    This tool allows users to define and execute custom Python functions or code snippets
    as part of their workflow. It supports both direct code input and callable functions.

    Attributes:
        code (Union[Text, Callable]): The Python code to execute, either as a string or callable.
        id (str): The identifier for the code interpreter model.
        status (AssetStatus): The current status of the tool (DRAFT or ONBOARDED).
    """

    def __init__(
        self, code: Union[Text, Callable], description: Text = "", name: Optional[Text] = None, **additional_info
    ) -> None:
        """Initialize a new CustomPythonCodeTool instance.

        Args:
            code (Union[Text, Callable]): The Python code to execute, either as a string or callable function.
            description (Text, optional): Description of what the code does. Defaults to "".
            name (Optional[Text], optional): Name of the tool. Defaults to None.
            **additional_info: Additional keyword arguments for tool configuration.

        Note:
            If description or name are not provided, they may be automatically extracted
            from the code's docstring if available.
        """
        super().__init__(name=name or "", description=description, **additional_info)
        self.code = code
        self.status = AssetStatus.ONBOARDED  # TODO: change to DRAFT when we have a way to onboard the tool
        self.id = CodeInterpreterModel.PYTHON_AZURE

        self.validate()

    def to_dict(self):
        """Convert the tool instance to a dictionary representation.

        Returns:
            dict: A dictionary containing the tool's configuration with keys:
                - id: The tool's identifier
                - name: The tool's name
                - description: The tool's description
                - type: Always "utility"
                - utility: Always "custom_python_code"
                - utilityCode: The Python code to execute
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": "utility",
            "utility": "custom_python_code",
            "utilityCode": self.code,
        }

    def validate(self):
        """Validate the tool's configuration and code.

        This method performs several checks:
        1. Parses and validates the Python code if it's not an S3 URL
        2. Extracts description and name from code's docstring if not provided
        3. Ensures all required fields (description, code, name) are non-empty
        4. Verifies the tool status is either DRAFT or ONBOARDED

        Raises:
            AssertionError: If any validation check fails, with a descriptive error message.
        """
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

        assert self.description and self.description.strip() != "", (
            "Custom Python Code Tool Error: Tool description is required"
        )
        assert self.code and self.code.strip() != "", "Custom Python Code Tool Error: Code is required"
        assert self.name and self.name.strip() != "", "Custom Python Code Tool Error: Name is required"
        assert self.status in [
            AssetStatus.DRAFT,
            AssetStatus.ONBOARDED,
        ], "Custom Python Code Tool Error: Status must be DRAFT or ONBOARDED"

    def __repr__(self) -> Text:
        """Return a string representation of the tool.

        Returns:
            Text: A string in the format "CustomPythonCodeTool(name=<tool_name>)".
        """
        return f"CustomPythonCodeTool(name={self.name})"
