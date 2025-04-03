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

        status = AssetStatus.DRAFT
        if isinstance(pipeline, Pipeline):
            pipeline_id = pipeline.id
            status = pipeline.status
        else:
            # get pipeline from id
            try:
                pipeline_obj = self._get_pipeline(pipeline)
                pipeline_id = pipeline_obj.id
                status = pipeline_obj.status
            except Exception:
                raise Exception(f"Pipeline Tool Unavailable. Make sure Pipeline '{pipeline}' exists or you have access to it.")

        self.pipeline = pipeline_id
        self.status = status

    def to_dict(self):
        return {
            "assetId": self.pipeline,
            "name": self.name,
            "description": self.description,
            "type": "pipeline",
            "status": self.status,
        }

    def _get_pipeline(self, pipeline_id: Text = None):
        from aixplain.factories.pipeline_factory import PipelineFactory

        pipeline_id = pipeline_id or self.pipeline
        return PipelineFactory.get(pipeline_id, api_key=self.api_key)

    def validate(self):
        try:
            self._get_pipeline()
        except Exception:
            raise Exception(f"Pipeline Tool Unavailable. Make sure Pipeline '{self.pipeline}' exists or you have access to it.")
