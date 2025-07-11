from .resource import (
    BaseResource,
    BareListParams,
    BareGetParams,
    GetResourceMixin,
    ListResourceMixin,
    CreateResourceMixin,
    BaseCreateParams,
    Page,
)
from datetime import datetime
from typing_extensions import Unpack, NotRequired, TYPE_CHECKING
from typing import Dict, List, Optional, Text, Union

if TYPE_CHECKING:
    from aixplain.modules import APIKeyLimits, APIKeyUsageLimit


class APIKeyCreateParams(BaseCreateParams):
    name: Text
    budget: int
    global_limits: Union[Dict, "APIKeyLimits"]
    asset_limits: List[Union[Dict, "APIKeyLimits"]]
    expires_at: datetime


class APIKeyGetParams(BareGetParams):
    api_key: NotRequired[str]


class APIKey(
    BaseResource,
    GetResourceMixin[APIKeyGetParams, "APIKey"],
    ListResourceMixin[BareListParams, "APIKey"],
    CreateResourceMixin[APIKeyCreateParams, "APIKey"],
):
    @classmethod
    def get(cls, **kwargs: Unpack[APIKeyGetParams]) -> "APIKey":
        from aixplain.factories import APIKeyFactory

        api_key = cls._get_api_key(kwargs)
        return APIKeyFactory.get(api_key=api_key)

    @classmethod
    def list(cls, **kwargs: Unpack[BareListParams]) -> Page["APIKey"]:
        from aixplain.factories import APIKeyFactory

        api_key = cls._get_api_key(kwargs)
        return APIKeyFactory.list(api_key=api_key)

    @classmethod
    def create(cls, *args, **kwargs: Unpack[APIKeyCreateParams]) -> "APIKey":
        from aixplain.factories import APIKeyFactory

        api_key = cls._get_api_key(kwargs)
        return APIKeyFactory.create(*args, api_key=api_key)

    @classmethod
    def update(cls, api_key: "APIKey") -> "APIKey":
        from aixplain.factories import APIKeyFactory

        api_key_param = cls._get_api_key({})
        return APIKeyFactory.update(api_key, api_key=api_key_param)

    @classmethod
    def get_usage_limits(
        cls, api_key: Text = None, asset_id: Optional[Text] = None
    ) -> List["APIKeyUsageLimit"]:
        from aixplain.factories import APIKeyFactory

        api_key_param = api_key or cls._get_api_key({})

        return APIKeyFactory.get_usage_limits(api_key, asset_id, api_key=api_key_param)
