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
from aixplain.factories import APIKeyFactory
from aixplain.modules import APIKeyLimits, APIKeyUsageLimit
from aixplain.utils import config
from datetime import datetime
from typing_extensions import Unpack, NotRequired
from typing import Dict, List, Optional, Text, Union


class APIKeyCreateParams(BaseCreateParams):
    name: Text
    budget: int
    global_limits: Union[Dict, APIKeyLimits]
    asset_limits: List[Union[Dict, APIKeyLimits]]
    expires_at: datetime


class APIKeyGetParams(BareGetParams):
    api_key: NotRequired[str]


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
    def list(cls, **kwargs: Unpack[BareListParams]) -> List["APIKey"]:
        from aixplain.factories import APIKeyFactory

        kwargs.setdefault("page_number", cls.PAGINATE_DEFAULT_PAGE_NUMBER)
        kwargs.setdefault("page_size", cls.PAGINATE_DEFAULT_PAGE_SIZE)

        results = APIKeyFactory.list(**kwargs)
        return Page[APIKey](
            results=[APIKey(obj) for obj in results],
            total=len(results),
            page_number=1,
            page_total=len(results),
        )

    @classmethod
    def create(cls, **kwargs: Unpack[APIKeyCreateParams]) -> "APIKey":
        from aixplain.factories import APIKeyFactory

        return APIKey(APIKeyFactory.create(**kwargs))

    @classmethod
    def update(cls, api_key: "APIKey") -> "APIKey":
        return APIKeyFactory.update(api_key)

    @classmethod
    def get_usage_limits(
        cls, api_key: Text = config.TEAM_API_KEY, asset_id: Optional[Text] = None
    ) -> List[APIKeyUsageLimit]:
        return APIKeyFactory.get_usage_limits(api_key, asset_id)
