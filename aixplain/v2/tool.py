from typing import Callable, Optional, Union
from typing_extensions import Unpack

from .resource import BaseResource, BaseCreateParams, CreateResourceMixin


class ToolCreateParams(BaseCreateParams):
    name: str
    code: Union[str, Callable]
    description: Optional[str]


class Tool(BaseResource, CreateResourceMixin[ToolCreateParams, "Tool"]):
    """Resource for tools."""

    RESOURCE_PATH = "sdk/tools"

    @classmethod
    def create(cls, *args, **kwargs: Unpack[ToolCreateParams]) -> "Tool":
        return super().create(*args, **kwargs)
