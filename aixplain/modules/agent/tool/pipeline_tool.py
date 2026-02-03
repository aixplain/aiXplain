"""Pipeline tool for aiXplain SDK agents.

This module provides a tool that allows agents to execute AI pipelines
and chain multiple AI operations together.

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

from typing import Text, Union, Optional

from aixplain.modules.agent.tool import Tool
from aixplain.modules.pipeline import Pipeline
from aixplain.enums import AssetStatus


class PipelineTool(Tool):
    """A tool that wraps aiXplain pipelines to execute complex workflows based on user commands.

    This class provides an interface for using aiXplain pipelines as tools, allowing them
    to be integrated into agent workflows. It handles pipeline validation, status management,
    and execution.

    Attributes:
        description (Text): A description of what the pipeline tool does.
        pipeline (Union[Text, Pipeline]): The pipeline to execute, either as a Pipeline instance
            or a pipeline ID string.
        status (AssetStatus): The current status of the pipeline tool.
        name (Text): The name of the tool, defaults to pipeline name if not provided.
    """

    def __init__(
        self,
        description: Text,
        pipeline: Union[Text, Pipeline],
        name: Optional[Text] = None,
        **additional_info,
    ) -> None:
        """Initialize a new PipelineTool instance.

        Args:
            description (Text): A description of what the pipeline tool does.
            pipeline (Union[Text, Pipeline]): The pipeline to execute, either as a Pipeline instance
                or a pipeline ID string.
            name (Optional[Text], optional): The name of the tool. If not provided, will use
                the pipeline's name. Defaults to None.
            **additional_info: Additional keyword arguments for tool configuration.

        Raises:
            Exception: If the specified pipeline doesn't exist or is inaccessible.
        """
        name = name or ""
        super().__init__(name=name, description=description, **additional_info)

        self.status = AssetStatus.DRAFT

        self.pipeline = pipeline
        self.validate()

    def to_dict(self):
        """Convert the tool instance to a dictionary representation.

        Returns:
            dict: A dictionary containing the tool's configuration with keys:
                - assetId: The pipeline ID
                - name: The tool's name
                - description: The tool's description
                - type: Always "pipeline"
                - status: The tool's status
        """
        return {
            "assetId": self.pipeline,
            "name": self.name,
            "description": self.description,
            "type": "pipeline",
            "status": self.status,
        }

    def __repr__(self) -> Text:
        """Return a string representation of the tool.

        Returns:
            Text: A string in the format "PipelineTool(name=<name>, pipeline=<pipeline>)".
        """
        return f"PipelineTool(name={self.name}, pipeline={self.pipeline})"

    def validate(self):
        """Validate the pipeline tool's configuration.

        This method performs several checks:
        1. Verifies the pipeline exists and is accessible
        2. Sets the tool name to the pipeline name if not provided
        3. Updates the tool status to match the pipeline status

        Raises:
            Exception: If the pipeline doesn't exist or is inaccessible.
        """
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
