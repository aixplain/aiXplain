import aixplain.utils.config as config
from aixplain.modules.wallet import Wallet
from aixplain.utils.file_utils import _request_with_retry
import logging


class WalletFactory:
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL
    resp = None

    def get(cls) -> Wallet:
        try:
            # Check for code 200, other code will be caught when trying to return a Wallet object
            url = f"{cls.backend_url}/sdk/billing/wallet"
            if cls.aixplain_key != "":
                headers = {"x-aixplain-key": f"{cls.aixplain_key}", "Content-Type": "application/json"}
            else:
                headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start fetching billing information from - {url} ")
            headers = {"Content-Type": "application/json", "x-api-key": config.TEAM_API_KEY}
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
            resp["api_key"] = config.TEAM_API_KEY
            return Wallet(totalBalance=resp["totalBalance"], reservedBalance=resp["reservedBalance"])

        except Exception:
            raise Exception(f"Failed to get wallet. Please check API key.")
