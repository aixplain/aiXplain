import json
import logging
import aixplain.utils.config as config
from datetime import datetime
from typing import Text, List, Dict, Union
from aixplain.utils.file_utils import _request_with_retry
from aixplain.modules.api_key import APIKey, APIKeyGlobalLimits


class APIKeyFactory:
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, api_key_id: Text) -> APIKey:
        """Get an API key by ID"""
        try:
            url = f"{cls.backend_url}/sdk/models/{api_key_id}"
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET API key  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            raise Exception(f"API Key GET Error: Failed to get api key with ID {api_key_id}")

        if r.status_code == 200:
            api_key = APIKey(
                name=resp["name"],
                budget=resp["budget"],
                global_limits=resp["globalLimits"],
                asset_limits=resp["assetLimits"],
                expires_at=resp["expiresAt"],
            )
            return api_key
        else:
            raise Exception(f"API Key GET Error: Failed to get api key with ID {api_key_id}. Error: {str(resp)}")

    @classmethod
    def list(cls) -> List[APIKey]:
        """List all API keys"""
        try:
            url = f"{cls.backend_url}/sdk/api-keys"
            headers = {"Content-Type": "application/json", "Authorization": f"Token {config.TEAM_API_KEY}"}
            logging.info(f"Start service for GET API List  - {url} - {headers}")
            r = _request_with_retry("GET", url, headers=headers)
            resp = r.json()
        except Exception:
            raise Exception("API Key List Error: Failed to list API keys")

        resp = "Unspecified error"
        if r.status_code == 200:
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
        else:
            raise Exception(f"API Key List Error: Failed to list API keys. Error: {str(resp)}")
        return api_keys

    @classmethod
    def create(
        cls,
        name: Text,
        budget: int,
        global_limits: Union[Dict, APIKeyGlobalLimits],
        asset_limits: List[Union[Dict, APIKeyGlobalLimits]],
        expires_at: datetime,
    ) -> APIKey:
        """Create a new API key"""
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

        resp = "Unspecified error"
        if r.status_code == 200:
            api_key = APIKey(
                id=resp["id"],
                name=resp["name"],
                budget=resp["budget"],
                global_limits=resp["globalLimits"],
                asset_limits=resp["assetLimits"],
                expires_at=resp["expiresAt"],
            )
            return api_key
        else:
            raise Exception(f"API Key Creation Error: Failed to create a new API key. Error: {str(resp)}")

    @classmethod
    def update(cls, api_key: APIKey) -> APIKey:
        """Update an existing API key"""
        try:
            url = f"{cls.backend_url}/sdk/api-keys/{api_key.id}"
            headers = {"Content-Type": "application/json", "Authorization": f"Token {config.TEAM_API_KEY}"}
            payload = api_key.to_dict()

            logging.info(f"Updating API key with ID {api_key.id} and new values")
            r = _request_with_retry("put", url, json=payload, headers=headers)
            resp = r.json()
        except Exception as e:
            raise Exception(f"API Key Update Error: Failed to update API key with ID {id}. Error: {str(e)}")

        resp = "Unspecified error"
        if r.status_code == 200:
            api_key = APIKey(
                id=resp["id"],
                name=resp["name"],
                budget=resp["budget"],
                global_limits=resp["globalLimits"],
                asset_limits=resp["assetLimits"],
                expires_at=resp["expiresAt"],
            )
            return api_key
        else:
            raise Exception(f"API Key Update Error: Failed to update API key with ID {api_key.id}. Error: {str(resp)}")
