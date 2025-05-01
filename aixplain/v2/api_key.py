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
        import aixplain.utils.config as config

        api_key = kwargs.get("api_key", config.TEAM_API_KEY)
        return APIKeyFactory.get(api_key=api_key)

    @classmethod
    def list(cls, **kwargs: Unpack[BareListParams]) -> Page["APIKey"]:
        from aixplain.factories import APIKeyFactory

        return APIKeyFactory.list(**kwargs)

    @classmethod
    def create(cls, *args, **kwargs: Unpack[APIKeyCreateParams]) -> "APIKey":
        from aixplain.factories import APIKeyFactory

        return APIKeyFactory.create(*args, **kwargs)

    @classmethod
    def update(cls, api_key: "APIKey") -> "APIKey":
        from aixplain.factories import APIKeyFactory

        return APIKeyFactory.update(api_key)

    @classmethod
    def get_usage_limits(cls, api_key: Text = None, asset_id: Optional[Text] = None) -> List["APIKeyUsageLimit"]:
        from aixplain.factories import APIKeyFactory
        from aixplain.utils import config

        api_key = api_key or config.TEAM_API_KEY

        return APIKeyFactory.get_usage_limits(api_key, asset_id)
