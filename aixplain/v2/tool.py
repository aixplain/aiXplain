from typing import Dict, Any, Union
from typing_extensions import Unpack, NotRequired

from .resource import (
    BaseListParams,
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    RunnableMixin,
    BaseRunnableResponse,
    BaseRunParams,
)


class ToolListParams(BaseListParams):
    """Parameters for listing tools."""

    pass


class ToolRunParams(BaseRunParams):
    """Parameters for Tool.run() method."""

    data: Union[str, Dict[str, Any]]
    name: NotRequired[str]
    parameters: NotRequired[Dict[str, Any]]


class ToolRunnableResponse(BaseRunnableResponse):
    """Response class for Tool resources.

    Provides Tool-specific fields and behavior while maintaining compatibility
    with the legacy tool execution response format.
    """

    def _parse_response(self, response_data: Dict[str, Any]) -> None:
        """Parse Tool-specific response fields."""
        super()._parse_response(response_data)

        # Tool-specific fields
        self.tool_id: str = response_data.get("toolId", "")
        self.function_type: str = response_data.get("functionType", "")

    def _get_known_fields(self) -> set:
        """Include Tool-specific fields in known fields."""
        base_fields = super()._get_known_fields()
        return base_fields | {"toolId", "functionType"}


class Tool(
    BaseResource,
    ListResourceMixin[ToolListParams, "Tool"],
    GetResourceMixin[BareGetParams, "Tool"],
    RunnableMixin[ToolRunParams],
):
    """Resource for tools.

    Tools are executable resources that can perform various tasks.
    They can be models, integrations, or other runnable assets.
    """

    RESOURCE_PATH = "sdk/models"  # Tools are backed by models
    RESPONSE_CLASS = ToolRunnableResponse

    def _build_run_payload(self, **kwargs: Unpack[ToolRunParams]) -> Dict[str, Any]:
        """Build Tool-specific run payload."""
        data = kwargs.get("data")
        name = kwargs.get("name", "tool-run")
        parameters = kwargs.get("parameters", {})

        payload = {
            "data": data,
            "name": name,
        }

        # Add Tool-specific parameters
        if parameters:
            payload["parameters"] = parameters

        return payload
