from .resource import (
    BaseResource,
    GetResourceMixin,
    BareGetParams,
)

from typing_extensions import Unpack


class Data(
    BaseResource,
    GetResourceMixin[BareGetParams, "Data"],
):
    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Data":
        from aixplain.factories import DataFactory

        api_key = cls._get_api_key(kwargs)
        return DataFactory.get(data_id=id, api_key=api_key)
