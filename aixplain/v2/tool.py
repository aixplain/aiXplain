from typing_extensions import Unpack

from .resource import (
    BaseListParams,
    BaseResource,
    ListResourceMixin,
    GetResourceMixin,
    BareGetParams,
    Page,
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
