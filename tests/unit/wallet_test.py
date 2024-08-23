__author__ = "aixplain"

from aixplain.factories import WalletFactory
import aixplain.utils.config as config
import requests_mock


def test_wallet_service():
    with requests_mock.Mocker() as mock:
        url = f"{config.BACKEND_URL}/sdk/billing/wallet"
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"totalBalance": 5, "reservedBalance": "0"}
        mock.get(url, headers=headers, json=ref_response)
        wallet = WalletFactory.get(config.AIXPLAIN_API_KEY)
    assert wallet.total_balance == ref_response["totalBalance"]
    assert wallet.reserved_balance == ref_response["reservedBalance"]
