from typing import Dict, Any
from typing_extensions import Unpack

from .resource import (
    BaseListParams,
    ListResourceMixin,
    GetResourceMixin,
    BaseGetParams,
)
from .model import Model, ModelRunParams, ModelRunnableResponse


class ToolListParams(BaseListParams):
    """Parameters for listing tools."""

    pass


class ToolGetParams(BaseGetParams):
    """Parameters for getting a tool."""

    pass


class ToolRunParams(ModelRunParams):
    """Parameters for Tool.run() method.
    
    Inherits from ModelRunParams since tools use model endpoints.
    """

    # Tools don't support streaming, so we can exclude it
    # but we inherit data, name, parameters from ModelRunParams
    pass


class ToolRunnableResponse(ModelRunnableResponse):
    """Response class for Tool resources.

    Inherits from ModelRunnableResponse since tools use model endpoints,
    but adds tool-specific fields.
    """

    def _parse_response(self, response_data: Dict[str, Any]) -> None:
        """Parse Tool-specific response fields."""
        super()._parse_response(response_data)

        # Tool-specific fields (in addition to model fields)
        self.tool_id: str = response_data.get("toolId", "")
        self.function_type: str = response_data.get("functionType", "")

    def _get_known_fields(self) -> set:
        """Include Tool-specific fields in known fields."""
        base_fields = super()._get_known_fields()
        return base_fields | {"toolId", "functionType"}


class Tool(
    Model,  # Inherit from Model instead of BaseResource + mixins
    ListResourceMixin[ToolListParams, "Tool"],
    GetResourceMixin[ToolGetParams, "Tool"],
):
    """Resource for tools.

    Tools are executable resources that can perform various tasks.
    They are backed by model endpoints, so they inherit from Model
    but provide tool-specific response handling.
    """

    # Override the response class to use tool-specific response
    RESPONSE_CLASS = ToolRunnableResponse
