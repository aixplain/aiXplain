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
from aixplain.enums.supplier import Supplier
from aixplain.modules.model import Model
from aixplain.modules.agent.tool import Tool
from typing import Dict, List, Text, Optional, Union

from aixplain.utils import config


class Agent(Model):
    """Advanced AI system capable of performing tasks by leveraging specialized software tools and resources from aiXplain marketplace.

    Attributes:
        id (Text): ID of the Agent
        name (Text): Name of the Agent
        tools (List[Tool]): List of tools that the Agent uses.
        description (Text, optional): description of the Agent. Defaults to "".
        supplier (Text): Supplier of the Agent.
        version (Text): Version of the Agent.
        backend_url (str): URL of the backend.
        api_key (str): The TEAM API key used for authentication.
        cost (Dict, optional): model price. Defaults to None.
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        tools: List[Tool] = [],
        description: Text = "",
        api_key: Optional[Text] = config.TEAM_API_KEY,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        cost: Optional[Dict] = None,
        **additional_info,
    ) -> None:
        """Create a FineTune with the necessary information.

        Args:
            id (Text): ID of the Agent
            name (Text): Name of the Agent
            tools (List[Tool]): List of tools that the Agent uses.
            description (Text, optional): description of the Agent. Defaults to "".
            supplier (Text): Supplier of the Agent.
            version (Text): Version of the Agent.
            backend_url (str): URL of the backend.
            api_key (str): The TEAM API key used for authentication.
            cost (Dict, optional): model price. Defaults to None.
            **additional_info: Additional information to be saved with the FineTune.
        """
        assert len(tools) > 0, "At least one tool must be provided."
        super().__init__(id, name, description, api_key, supplier, version, cost=cost)
        self.additional_info = additional_info
        self.tools = tools
