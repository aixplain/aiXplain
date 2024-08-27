import aixplain.utils.config as config
from aixplain.modules.wallet import Wallet
from aixplain.utils.file_utils import _request_with_retry
import logging
from typing import Text


class WalletFactory:
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, api_key: Text = config.TEAM_API_KEY) -> Wallet:     
        """Get wallet information"""
        try:
            resp = None
            url = f"{cls.backend_url}/sdk/billing/wallet"
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start fetching billing information from - {url} - {headers}")
            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            total_balance = float(resp.get("totalBalance", 0.0))
            reserved_balance = float(resp.get("reservedBalance", 0.0))
        
            return Wallet(total_balance=total_balance, reserved_balance=reserved_balance)
        except Exception as e:
            raise Exception(f"Failed to get the wallet credit information. Error: {str(e)}")
