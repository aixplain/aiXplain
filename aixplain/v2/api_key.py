from .resource import (
    BaseResource,
    BareListParams,
    BareGetParams,
    GetResourceMixin,
    ListResourceMixin,
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
):
    @classmethod
    def get(cls, **kwargs: Unpack[BareGetParams]) -> "APIKey":
        import aixplain.utils.config as config

        api_key = kwargs.get("api_key", config.TEAM_API_KEY)
        return APIKeyFactory.get(api_key=api_key)

    @classmethod
    def list(cls) -> Dict:
        return APIKeyFactory.list()

    @classmethod
    def create(
        cls,
        name: Text,
        budget: int,
        global_limits: Union[Dict, APIKeyLimits],
        asset_limits: List[Union[Dict, APIKeyLimits]],
        expires_at: datetime,
    ) -> "APIKey":
        return APIKeyFactory.create(
            name=name, budget=budget, global_limits=global_limits, asset_limits=asset_limits, expires_at=expires_at
        )

    @classmethod
    def update(cls, api_key: "APIKey") -> "APIKey":
        return APIKeyFactory.update(api_key)

    @classmethod
    def get_usage_limits(cls, api_key: Text = config.TEAM_API_KEY, asset_id: Optional[Text] = None) -> List[APIKeyUsageLimit]:
        return APIKeyFactory.get_usage_limits(api_key, asset_id)
