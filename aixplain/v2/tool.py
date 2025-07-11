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

    RESOURCE_PATH = "sdk/tools"

    @classmethod
    def list(cls, **kwargs: Unpack[ToolListParams]) -> Page["Tool"]:
        from aixplain.factories import ToolFactory

        api_key = cls._get_api_key(kwargs)
        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        return ToolFactory.list(**kwargs, api_key=api_key)

    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Tool":
        from aixplain.factories import ToolFactory

        api_key = cls._get_api_key(kwargs)
        return ToolFactory.get(model_id=id, api_key=api_key)
