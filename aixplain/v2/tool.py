from .resource import (
    BaseListParams,
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
)


class ToolListParams(BaseListParams):
    """Parameters for listing tools."""

    pass


class Tool(
    BaseResource,
    ListResourceMixin[ToolListParams, "Tool"],
    GetResourceMixin[BareGetParams, "Tool"],
):
    """Resource for tools."""

    RESOURCE_PATH = "sdk/models"
