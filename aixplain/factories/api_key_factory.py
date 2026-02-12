import json
import logging
import aixplain.utils.config as config
from datetime import datetime
from typing import Text, List, Optional, Dict, Union
from aixplain.utils.request_utils import _request_with_retry
from aixplain.modules.api_key import APIKey, APIKeyLimits, APIKeyUsageLimit


class APIKeyFactory:
    """Factory class for managing API keys in the aiXplain platform.

    This class provides functionality for creating, retrieving, updating, and
    monitoring API keys, including their usage limits and budgets.

    Attributes:
        backend_url (str): Base URL for the aiXplain backend API.
    """
    backend_url = config.BACKEND_URL

    @classmethod
    def get(cls, api_key: Text, **kwargs) -> APIKey:
        """Retrieve an API key by its value.

        This method searches for an API key by matching the first and last 4
        characters of the provided key.

        Args:
            api_key (Text): The API key value to search for.

        Returns:
            APIKey: The matching API key object.

        Raises:
            Exception: If no matching API key is found.
        """
        for api_key_obj in cls.list(**kwargs):
            if (str(api_key_obj.access_key).startswith(api_key[:4]) and
                    str(api_key_obj.access_key).endswith(api_key[-4:])):
                return api_key_obj
        raise Exception(f"API Key Error: API key {api_key} not found")

    @classmethod
    def list(cls, **kwargs) -> List[APIKey]:
        """List all API keys accessible to the current user.

        This method retrieves all API keys that the authenticated user has access to,
        using the configured TEAM_API_KEY.

        Returns:
            List[APIKey]: List of API key objects.

        Raises:
            Exception: If the API request fails or returns an error, including cases
                where authentication fails or the service is unavailable.
        """
        resp = "Unspecified error"
        api_key = kwargs.get("api_key", config.TEAM_API_KEY)
        try:
            url = f"{cls.backend_url}/sdk/api-keys"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Token {api_key}"
            }
            logging.info(
                f"Start service for GET API List  - {url} - {headers}"
            )
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
                    global_limits=(
                        key["globalLimits"] if "globalLimits" in key else None
                    ),
                    asset_limits=(
                        key["assetsLimits"] if "assetsLimits" in key else []
                    ),
                    expires_at=(
                        key["expiresAt"] if "expiresAt" in key else None
                    ),
                    access_key=key["accessKey"],
                    is_admin=key["isAdmin"],
                )
                for key in resp
            ]
        else:
            raise Exception(
                f"API Key List Error: Failed to list API keys. "
                f"Error: {str(resp)}"
            )
        return api_keys

    @classmethod
    def create(
        cls,
        name: Text,
        budget: int,
        global_limits: Union[Dict, APIKeyLimits],
        asset_limits: List[Union[Dict, APIKeyLimits]],
        expires_at: datetime,
        **kwargs
    ) -> APIKey:
        """Create a new API key with specified limits and budget.

        This method creates a new API key with configured usage limits, budget,
        and expiration date.

        Args:
            name (Text): Name or description for the API key.
            budget (int): Total budget allocated to this API key.
            global_limits (Union[Dict, APIKeyLimits]): Global usage limits for the key,
                either as a dictionary or APIKeyLimits object.
            asset_limits (List[Union[Dict, APIKeyLimits]]): List of per-asset usage
                limits, each either as a dictionary or APIKeyLimits object.
            expires_at (datetime): Expiration date and time for the API key.

        Returns:
            APIKey: Created API key object with its access key and configuration.

        Raises:
            Exception: If the API request fails or returns an error, including cases
                where validation fails or the service is unavailable.
        """
        resp = "Unspecified error"
        api_key = kwargs.get("api_key", config.TEAM_API_KEY)
        url = f"{cls.backend_url}/sdk/api-keys"
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Token {api_key}"
        }

        payload = APIKey(
            name=name, budget=budget, global_limits=global_limits, 
            asset_limits=asset_limits, expires_at=expires_at
        ).to_dict()

        try:
            logging.info(
                f"Start service for POST API Creation  - {url} - {headers} - "
                f"{json.dumps(payload)}"
            )
            r = _request_with_retry("post", url, json=payload, headers=headers)
            resp = r.json()
        except Exception as e:
            raise Exception(
                f"API Key Creation Error: Failed to create a new API key. "
                f"Error: {str(e)}"
            )

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
            raise Exception(
                f"API Key Creation Error: Failed to create a new API key. "
                f"Error: {str(resp)}"
            )

    @classmethod
    def update(cls, api_key_obj: APIKey, **kwargs) -> APIKey:
        """Update an existing API key's configuration.

        This method updates an API key's settings such as limits, budget, and
        expiration date. The API key must be validated before update.

        Args:
            api_key (APIKey): API key object with updated configuration.
                Must have a valid ID of an existing key.

        Returns:
            APIKey: Updated API key object with new configuration.

        Raises:
            Exception: If:
                - API key validation fails
                - API key ID is invalid
                - Update request fails
                - Service is unavailable
        """
        api_key_obj.validate()
        api_key = kwargs.get("api_key", config.TEAM_API_KEY)
        try:
            resp = "Unspecified error"
            url = f"{cls.backend_url}/sdk/api-keys/{api_key_obj.id}"
            headers = {
                "Content-Type": "application/json", 
                "Authorization": f"Token {api_key}"
            }
            payload = api_key_obj.to_dict()

            logging.info(
                f"Updating API key with ID {api_key_obj.id} and new values"
            )
            r = _request_with_retry("put", url, json=payload, headers=headers)
            resp = r.json()
        except Exception as e:
            raise Exception(
                f"API Key Update Error: Failed to update API key with ID "
                f"{api_key_obj.id}. Error: {str(e)}"
            )

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
            raise Exception(
                f"API Key Update Error: Failed to update API key with ID "
                f"{api_key_obj.id}. Error: {str(resp)}"
            )

    @classmethod
    def get_usage_limits(
        cls, api_key: Text = None, asset_id: Optional[Text] = None, **kwargs
    ) -> List[APIKeyUsageLimit]:
        """Retrieve current usage limits and counts for an API key.

        This method fetches the current usage statistics and limits for an API key,
        optionally filtered by a specific asset.

        Args:
            api_key (Text, optional): API key to check usage for. Defaults to
                config.TEAM_API_KEY.
            asset_id (Optional[Text], optional): Filter usage limits for a specific
                asset. Defaults to None, showing all assets.

        Returns:
            List[APIKeyUsageLimit]: List of usage limit objects containing:
                - daily_request_count: Current number of requests today
                - daily_request_limit: Maximum allowed requests per day
                - daily_token_count: Current number of tokens used today
                - daily_token_limit: Maximum allowed tokens per day
                - model: Asset ID if limit is asset-specific, None if global

        Raises:
            Exception: If:
                - API key is invalid
                - User is not the key owner
                - Service is unavailable
        """
        api_key = api_key or kwargs.get("api_key", config.TEAM_API_KEY)
        try:
            url = f"{config.BACKEND_URL}/sdk/api-keys/usage-limits"
            headers = {
                "Authorization": f"Token {api_key}", 
                "Content-Type": "application/json"
            }
            logging.info(f"Start service for GET API Key Usage  - {url} - {headers}")
            r = _request_with_retry("GET", url, headers=headers)
            resp = r.json()
        except Exception:
            message = (
                "API Key Usage Error: Make sure the API Key exists and you "
                "are the owner."
            )
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
                if asset_id is None or (
                    "assetId" in limit and limit["assetId"] == asset_id
                )
            ]
        else:
            raise Exception(
                f"API Key Usage Error: Failed to get usage. "
                f"Error: {str(resp)}"
            )
