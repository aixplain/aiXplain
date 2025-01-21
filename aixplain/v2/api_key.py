from .resource import (
    BaseResource,
    BareListParams,
    BareGetParams,
    GetResourceMixin,
    ListResourceMixin,
    CreateResourceMixin,
    BareCreateParams,
)
from aixplain.factories import APIKeyFactory
from aixplain.modules import APIKeyLimits, APIKeyUsageLimit
from aixplain.utils import config
from datetime import datetime
from typing_extensions import Unpack
from typing import Dict, List, Optional, Text, Union


class APIKey(
    BaseResource,
    GetResourceMixin[BareGetParams, "APIKey"],
    ListResourceMixin[BareListParams, "APIKey"],
    CreateResourceMixin[Dict, "APIKey"],
):
    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "APIKey":
        import aixplain.utils.config as config

        api_key = kwargs.get("api_key", config.TEAM_API_KEY)
        return APIKeyFactory.get(api_key=api_key)

    @classmethod
    def list(cls) -> List["APIKey"]:
        raw_response = APIKeyFactory.list()
        api_keys_data = raw_response.get("results", [])
        return [cls(obj) for obj in api_keys_data]

    def create(cls, **kwargs: Unpack[BareCreateParams]) -> "APIKey":
        from aixplain.factories import APIKeyFactory

        return APIKey(APIKeyFactory.init(**kwargs))

    @classmethod
    def update(cls, api_key: "APIKey") -> "APIKey":
        return APIKeyFactory.update(api_key)

    @classmethod
    def get_usage_limits(cls, api_key: Text = config.TEAM_API_KEY, asset_id: Optional[Text] = None) -> List[APIKeyUsageLimit]:
        return APIKeyFactory.get_usage_limits(api_key, asset_id)
