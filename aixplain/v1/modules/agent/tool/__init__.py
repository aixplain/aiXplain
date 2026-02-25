"""Agent tool module for aiXplain SDK.

This module provides tool classes and functionality for agents to interact with
various services, models, and data sources.

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
from abc import ABC
from typing import Optional, Text
from aixplain.utils import config
from aixplain.enums import AssetStatus


class Tool(ABC):
    """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

    Attributes:
        name (Text): name of the tool
        description (Text): description of the tool
        version (Text): version of the tool
    """

    def __init__(
        self,
        name: Text,
        description: Text,
        version: Optional[Text] = None,
        api_key: Optional[Text] = config.TEAM_API_KEY,
        status: Optional[AssetStatus] = AssetStatus.DRAFT,
        **additional_info,
    ) -> None:
        """Initialize a new Tool instance.

        Args:
            name (Text): The name of the tool.
            description (Text): A description of the tool's functionality.
            version (Optional[Text], optional): The version of the tool. Defaults to None.
            api_key (Optional[Text], optional): The API key for authentication. Defaults to config.TEAM_API_KEY.
            status (Optional[AssetStatus], optional): The current status of the tool. Defaults to AssetStatus.DRAFT.
            **additional_info: Additional keyword arguments for tool configuration.
        """
        self.name = name
        self.description = description
        self.version = version
        self.api_key = api_key
        self.additional_info = additional_info
        self.status = status

    def to_dict(self):
        """Converts the tool instance to a dictionary representation.

        Returns:
            dict: A dictionary containing the tool's attributes and configuration.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
        raise NotImplementedError

    def validate(self):
        """Validates the tool's configuration and settings.

        This method should check if all required attributes are properly set and
        if the tool's configuration is valid.

        Raises:
            NotImplementedError: This is an abstract method that must be implemented by subclasses.
        """
        raise NotImplementedError


class DeployableTool(Tool):
    """Tool that can be deployed."""

    def deploy(self) -> None:
        """Deploy the tool."""
        raise NotImplementedError
