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

from aixplain.modules.agent.tool import Tool
from aixplain.enums import AssetStatus


class PythonInterpreterTool(Tool):
    """Python Interpreter Tool"""

    def __init__(self, **additional_info) -> None:
        """Python Interpreter Tool"""
        super().__init__(name="Python Interpreter", description="", **additional_info)
        self.status = AssetStatus.ONBOARDED  # TODO: change to DRAFT when we have a way to onboard the tool

    def to_dict(self):
        return {
            "description": "",
            "type": "utility",
            "utility": "custom_python_code",
        }

    def validate(self):
        pass
