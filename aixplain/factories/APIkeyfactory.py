import logging
from typing import Text, List, Dict
import aixplain.utils.config as config
from aixplain.utils.file_utils import _request_with_retry


class APIKey:
    def __init__(
        self,
        name: Text,
        budget: int,
        global_limits: Dict,
        asset_limits: list,
        expires_at: str,
        id: int = None,
        access_key: Text = None,
        is_admin: bool = None,
    ):
        self.name = name
        self.budget = budget
        self.global_limits = global_limits
        self.asset_limits = asset_limits
        self.expires_at = expires_at

        self.id = id
        self.access_key = access_key
        self.is_admin = is_admin

    def to_dict(self) -> Dict:
        """Convert the APIKey object to a dictionary to send to the API"""
        return {
            "name": self.name,
            "budget": self.budget,
            "globalLimits": self.global_limits,
            "assetLimits": self.asset_limits,
            "expiresAt": self.expires_at,
        }


class APIkeyfactory:
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    @classmethod
    def list(cls, api_key: Text = aixplain_key) -> List[APIKey]:
        """List all API keys"""
        try:
            url = "https://dev-platform-api.aixplain.com//sdk/api-keys"
            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            logging.info(f"Start fetching API keys from - {url}")
            r = _request_with_retry("GET", url, headers=headers)
            resp = r.json()
            # This will only return "id": 0,access key, admin, global limits
            # How do we find the rest of the values to make an api key list and return it?
            api_keys = [
                APIKey(
                    name=key["name"],
                    budget=key["budget"],
                    global_limits=key["globalLimits"],
                    asset_limits=key["assetLimits"],
                    expires_at=key["expiresAt"],
                )
                for key in resp
            ]

            logging.info(r.headers)
            return api_keys
        except Exception as e:
            raise Exception(f"Failed to list API keys. Error: {str(e)}")

    @classmethod
    def create(cls, name: Text, api_key: Text, budget: int, global_limits: Dict, asset_limits: list, expires_at: str) -> Dict:
        """Create a new API key"""
        try:
            api_key_obj = APIKey(
                name=name, budget=budget, global_limits=global_limits, asset_limits=asset_limits, expires_at=expires_at
            )

            url = f"{cls.backend_url}/sdk/api-keys"
            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            payload = api_key_obj.to_dict()

            logging.info(f"Creating new API key with name {name}")
            r = _request_with_retry("post", url, json=payload, headers=headers)
            resp = r.json()

            return resp
        except Exception as e:
            raise Exception(f"Failed to create a new API key. Error: {str(e)}")

    @classmethod
    def update(
        cls, id: Text, name: Text, api_key: Text, budget: int, global_limits: Dict, asset_limits: list, expires_at: str
    ) -> Dict:
        """Update an existing API key"""
        try:
            api_key_obj = APIKey(
                name=name, budget=budget, global_limits=global_limits, asset_limits=asset_limits, expires_at=expires_at
            )

            url = f"{cls.backend_url}/sdk/api-keys/{id}"
            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            payload = api_key_obj.to_dict()

            logging.info(f"Updating API key with ID {id} and new values")
            r = _request_with_retry("put", url, json=payload, headers=headers)
            resp = r.json()

            return resp
        except Exception as e:
            raise Exception(f"Failed to update API key with ID {id}. Error: {str(e)}")

    @classmethod
    def delete(cls, id: Text, api_key: Text = aixplain_key):
        """Delete an API key by its ID"""
        try:
            url = f"{cls.backend_url}/sdk/api-keys"
            headers = {"Content-Type": "application/json", "x-api-key": api_key}
            logging.info(f"Deleting API key with ID {id}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code == 204:
                logging.info(f"Successfully deleted API key with ID {id}")
                return {"message": "API key successfully deleted."}
            else:
                return {"message": f"Failed to delete API key with ID {id}", "status_code": r.status_code}
        except Exception as e:
            raise Exception(f"Failed to delete API key with ID {id}. Error: {str(e)}")
