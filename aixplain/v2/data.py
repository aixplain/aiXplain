from .resource import (
    BaseResource,
    GetResourceMixin,
    BareGetParams,
)
from aixplain.factories import DataFactory
from typing_extensions import Unpack


class Data(
    BaseResource,
    GetResourceMixin[BareGetParams, "Data"],
):
    @classmethod
    def get(cls, id: str, **kwargs: Unpack[BareGetParams]) -> "Data":
        return DataFactory.get(data_id=id)
