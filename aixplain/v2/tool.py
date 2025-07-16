from dataclasses import dataclass, field
from typing import Callable, Optional, Union

from .resource import BaseResource


@dataclass
class Tool(BaseResource):
    """Resource for tools."""

    RESOURCE_PATH = "sdk/tools"

    code: Optional[Union[str, Callable]] = field(default=None)
