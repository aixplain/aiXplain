import aixplain.utils.config as config
from aixplain.modules.wallet import Wallet
from aixplain.utils.file_utils import _request_with_retry
import logging


class WalletFactory:
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, api_key) -> Wallet:
        """Get wallet information"""
        try:
            resp = None
            url = f"{cls.backend_url}/sdk/billing/wallet"
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start fetching billing information from - {url} - {headers}")
            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            return Wallet(total_balance=resp["totalBalance"], reserved_balance=resp["reservedBalance"])
        except Exception as e:
            raise Exception(f"Failed to get the wallet credit information. Error: {str(e)}")
