import json
import logging
import aixplain.utils.config as config
from datetime import datetime
from typing import Text, List, Optional, Dict, Union
from aixplain.utils.request_utils import _request_with_retry
from aixplain.modules.api_key import APIKey, APIKeyLimits, APIKeyUsageLimit


class APIKeyFactory:
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, api_key: Text) -> APIKey:
        """Get an API key"""
        for api_key_obj in cls.list():
            if str(api_key_obj.access_key).startswith(api_key[:4]) and str(api_key_obj.access_key).endswith(api_key[-4:]):
                return api_key_obj
        raise Exception(f"API Key Error: API key {api_key} not found")

    @classmethod
    def list(cls) -> List[APIKey]:
        """List all API keys"""
        resp = "Unspecified error"
        try:
            url = f"{cls.backend_url}/sdk/api-keys"
            headers = {"Content-Type": "application/json", "Authorization": f"Token {config.TEAM_API_KEY}"}
            logging.info(f"Start service for GET API List  - {url} - {headers}")
            r = _request_with_retry("GET", url, headers=headers)
            resp = r.json()
        except Exception:
            raise Exception("API Key List Error: Failed to list API keys")

        if 200 <= r.status_code < 300:
            api_keys = [
                APIKey(
                    id=key["id"],
                    name=key["name"],
                    budget=key["budget"] if "budget" in key else None,
                    global_limits=key["globalLimits"] if "globalLimits" in key else None,
                    asset_limits=key["assetsLimits"] if "assetsLimits" in key else [],
                    expires_at=key["expiresAt"] if "expiresAt" in key else None,
                    access_key=key["accessKey"],
                    is_admin=key["isAdmin"],
                )
                for key in resp
            ]
        else:
            raise Exception(f"API Key List Error: Failed to list API keys. Error: {str(resp)}")
        return api_keys

    @classmethod
    def create(
        cls,
        name: Text,
        budget: int,
        global_limits: Union[Dict, APIKeyLimits],
        asset_limits: List[Union[Dict, APIKeyLimits]],
        expires_at: datetime,
    ) -> APIKey:
        """Create a new API key"""
        resp = "Unspecified error"
        url = f"{cls.backend_url}/sdk/api-keys"
        headers = {"Content-Type": "application/json", "Authorization": f"Token {config.TEAM_API_KEY}"}

        payload = APIKey(
            name=name, budget=budget, global_limits=global_limits, asset_limits=asset_limits, expires_at=expires_at
        ).to_dict()

        try:
            logging.info(f"Start service for POST API Creation  - {url} - {headers} - {json.dumps(payload)}")
            r = _request_with_retry("post", url, json=payload, headers=headers)
            resp = r.json()
        except Exception as e:
            raise Exception(f"API Key Creation Error: Failed to create a new API key. Error: {str(e)}")

        if 200 <= r.status_code < 300:
            api_key = APIKey(
                id=resp["id"],
                name=resp["name"],
                budget=resp["budget"] if "budget" in resp else None,
                global_limits=resp["globalLimits"] if "globalLimits" in resp else None,
                asset_limits=resp["assetsLimits"] if "assetsLimits" in resp else [],
                expires_at=resp["expiresAt"] if "expiresAt" in resp else None,
                access_key=resp["accessKey"],
                is_admin=resp["isAdmin"],
            )
            return api_key
        else:
            raise Exception(f"API Key Creation Error: Failed to create a new API key. Error: {str(resp)}")

    @classmethod
    def update(cls, api_key: APIKey) -> APIKey:
        """Update an existing API key"""
        api_key.validate()
        try:
            resp = "Unspecified error"
            url = f"{cls.backend_url}/sdk/api-keys/{api_key.id}"
            headers = {"Content-Type": "application/json", "Authorization": f"Token {config.TEAM_API_KEY}"}
            payload = api_key.to_dict()

            logging.info(f"Updating API key with ID {api_key.id} and new values")
            r = _request_with_retry("put", url, json=payload, headers=headers)
            resp = r.json()
        except Exception as e:
            raise Exception(f"API Key Update Error: Failed to update API key with ID {id}. Error: {str(e)}")

        if 200 <= r.status_code < 300:
            api_key = APIKey(
                id=resp["id"],
                name=resp["name"],
                budget=resp["budget"] if "budget" in resp else None,
                global_limits=resp["globalLimits"] if "globalLimits" in resp else None,
                asset_limits=resp["assetsLimits"] if "assetsLimits" in resp else [],
                expires_at=resp["expiresAt"] if "expiresAt" in resp else None,
                access_key=resp["accessKey"],
                is_admin=resp["isAdmin"],
            )
            return api_key
        else:
            raise Exception(f"API Key Update Error: Failed to update API key with ID {api_key.id}. Error: {str(resp)}")

    @classmethod
    def get_usage_limits(cls, api_key: Text = config.TEAM_API_KEY, asset_id: Optional[Text] = None) -> List[APIKeyUsageLimit]:
        """Get API key usage limits"""
        try:
            url = f"{config.BACKEND_URL}/sdk/api-keys/usage-limits"
            headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET API Key Usage  - {url} - {headers}")
            r = _request_with_retry("GET", url, headers=headers)
            resp = r.json()
        except Exception:
            message = "API Key Usage Error: Make sure the API Key exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")

        if 200 <= r.status_code < 300:
            return [
                APIKeyUsageLimit(
                    daily_request_count=limit["requestCount"],
                    daily_request_limit=limit["requestCountLimit"],
                    daily_token_count=limit["tokenCount"],
                    daily_token_limit=limit["tokenCountLimit"],
                    model=limit["assetId"] if "assetId" in limit else None,
                )
                for limit in resp
                if asset_id is None or ("assetId" in limit and limit["assetId"] == asset_id)
            ]
        else:
            raise Exception(f"API Key Usage Error: Failed to get usage. Error: {str(resp)}")
