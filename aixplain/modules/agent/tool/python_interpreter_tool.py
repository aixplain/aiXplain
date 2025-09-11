"""Python interpreter tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute Python code
using an interpreter in a controlled environment.

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

from aixplain.modules.agent.tool import Tool
from aixplain.enums import AssetStatus

from typing import Text


class PythonInterpreterTool(Tool):
    """A tool that provides a Python shell for executing Python commands.

    This tool allows direct execution of Python code within the aiXplain platform.
    It acts as an interface to a Python interpreter, enabling dynamic code execution
    and computation.

    Attributes:
        name (Text): Always set to "Python Interpreter".
        description (Text): Description of the tool's functionality.
        status (AssetStatus): The current status of the tool (ONBOARDED or DRAFT).
    """

    def __init__(self, **additional_info) -> None:
        """Initialize a new PythonInterpreterTool instance.

        This initializes a Python interpreter tool with a fixed name and description.
        The tool is set to ONBOARDED status by default.

        Args:
            **additional_info: Additional keyword arguments for tool configuration.
        """
        description = "A Python shell. Use this to execute python commands. Input should be a valid python command."
        super().__init__(name="Python Interpreter", description=description, **additional_info)
        self.status = AssetStatus.ONBOARDED  # TODO: change to DRAFT when we have a way to onboard the tool

    def to_dict(self):
        """Convert the tool instance to a dictionary representation.

        Returns:
            dict: A dictionary containing the tool's configuration with keys:
                - description: The tool's description
                - type: Always "utility"
                - utility: Always "custom_python_code"
        """
        return {
            "description": self.description,
            "type": "utility",
            "utility": "custom_python_code",
        }

    def validate(self):
        """Validate the tool's configuration.

        This is a placeholder method as the Python interpreter tool has a fixed
        configuration that doesn't require validation.
        """
        pass

    def __repr__(self) -> Text:
        """Return a string representation of the tool.

        Returns:
            Text: A string in the format "PythonInterpreterTool()".
        """
        return "PythonInterpreterTool()"
