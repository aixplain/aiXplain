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
from typing import Text, Union, Optional

from aixplain.modules.agent.tool import Tool
from aixplain.modules.pipeline import Pipeline
from aixplain.enums import AssetStatus


class PipelineTool(Tool):
    """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

    Attributes:
        description (Text): description of the tool
        pipeline (Union[Text, Pipeline]): pipeline
    """

    def __init__(
        self,
        description: Text,
        pipeline: Union[Text, Pipeline],
        name: Optional[Text] = None,
        **additional_info,
    ) -> None:
        """Specialized software or resource designed to assist the AI in executing specific tasks or functions based on user commands.

        Args:
            description (Text): description of the tool
            pipeline (Union[Text, Pipeline]): pipeline
        """
        name = name or ""
        super().__init__(name=name, description=description, **additional_info)

        self.status = AssetStatus.DRAFT

        self.pipeline = pipeline
        self.validate()

    def to_dict(self):
        return {
            "assetId": self.pipeline,
            "name": self.name,
            "description": self.description,
            "type": "pipeline",
            "status": self.status,
        }

    def __repr__(self) -> Text:
        return f"PipelineTool(name={self.name}, pipeline={self.pipeline})"

    def validate(self):
        from aixplain.factories.pipeline_factory import PipelineFactory

        if isinstance(self.pipeline, Pipeline):
            pipeline_obj = self.pipeline
        else:
            try:
                pipeline_obj = PipelineFactory.get(self.pipeline, api_key=self.api_key)
            except Exception:
                raise Exception(
                    f"Pipeline Tool Unavailable. Make sure Pipeline '{self.pipeline}' exists or you have access to it."
                )

        if self.name.strip() == "":
            self.name = pipeline_obj.name
        self.status = pipeline_obj.status

    def deploy(self):
        pass
