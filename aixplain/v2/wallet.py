from .resource import (
    BaseResource,
    GetResourceMixin,
    BareGetParams,
)
from typing_extensions import Unpack, NotRequired


class WalletGetParams(BareGetParams):
    api_key: NotRequired[str]


class Wallet(
    BaseResource,
    GetResourceMixin[WalletGetParams, "Wallet"],
):
    @classmethod
    def get(cls, **kwargs: Unpack[WalletGetParams]) -> "Wallet":
        from aixplain.factories import WalletFactory
        import aixplain.utils.config as config

        api_key = kwargs.get("api_key", config.TEAM_API_KEY)
        return WalletFactory.get(api_key=api_key)
