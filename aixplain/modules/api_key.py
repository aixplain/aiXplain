"""API Key management module for aiXplain services.

This module provides classes for managing API keys and their rate limits.
"""

import logging
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.modules import Model
from datetime import datetime
from typing import Dict, List, Optional, Text, Union


from enum import Enum


class TokenType(Enum):
    """Token type for rate limiting.

    Specifies which type of tokens to count for rate limiting purposes.

    Attributes:
        INPUT: Count only input tokens.
        OUTPUT: Count only output tokens.
        TOTAL: Count total tokens (input + output).
    """

    INPUT = "input"
    OUTPUT = "output"
    TOTAL = "total"


class APIKeyLimits:
    """Rate limits configuration for an API key.

    This class defines the rate limits that can be applied either globally
    to an API key or specifically to a model.

    Attributes:
        token_per_minute (int): Maximum number of tokens allowed per minute.
        token_per_day (int): Maximum number of tokens allowed per day.
        request_per_minute (int): Maximum number of requests allowed per minute.
        request_per_day (int): Maximum number of requests allowed per day.
        model (Optional[Model]): The model these limits apply to, if any.
        token_type (Optional[TokenType]): Type of token limit ('input', 'output', 'total'), or None for default.
    """

    def __init__(
        self,
        token_per_minute: int,
        token_per_day: int,
        request_per_minute: int,
        request_per_day: int,
        model: Optional[Union[Text, Model]] = None,
        token_type: Optional[TokenType] = None,
    ):
        """Initialize an APIKeyLimits instance.

        Args:
            token_per_minute (int): Maximum number of tokens per minute.
            token_per_day (int): Maximum number of tokens per day.
            request_per_minute (int): Maximum number of requests per minute.
            request_per_day (int): Maximum number of requests per day.
            model (Optional[Union[Text, Model]], optional): The model to apply
                limits to. Can be a model ID or Model instance. Defaults to None.
            token_type (Optional[TokenType], optional): The type of token to apply the limit to. Defaults to None.
        """
        self.token_per_minute = token_per_minute
        self.token_per_day = token_per_day
        self.request_per_minute = request_per_minute
        self.request_per_day = request_per_day
        self.model = model
        self.token_type = token_type
        if model is not None and isinstance(model, str):
            from aixplain.factories import ModelFactory

            self.model = ModelFactory.get(model)


class APIKeyUsageLimit:
    """Usage limits and current usage for an API key.

    This class tracks the current usage counts against the configured limits
    for an API key, either globally or for a specific model.

    Attributes:
        daily_request_count (int): Number of requests made today.
        daily_request_limit (int): Maximum requests allowed per day.
        daily_token_count (int): Number of tokens used today.
        daily_token_limit (int): Maximum tokens allowed per day.
        model (Optional[Model]): The model these limits apply to, if any.
    """

    def __init__(
        self,
        daily_request_count: int,
        daily_request_limit: int,
        daily_token_count: int,
        daily_token_limit: int,
        model: Optional[Union[Text, Model]] = None,
    ):
        """Initialize an APIKeyUsageLimit instance.

        Args:
            daily_request_count (int): number of requests made
            daily_request_limit (int): limit of requests
            daily_token_count (int): number of tokens used
            daily_token_limit (int): limit of tokens
            model (Optional[Union[Text, Model]], optional): Model which the limits apply. Defaults to None.
        """
        self.daily_request_count = daily_request_count
        self.daily_request_limit = daily_request_limit
        self.daily_token_count = daily_token_count
        self.daily_token_limit = daily_token_limit
        if model is not None and isinstance(model, str):
            from aixplain.factories import ModelFactory

            self.model = ModelFactory.get(model)


class APIKey:
    """An API key for accessing aiXplain services.

    This class represents an API key with its associated limits, budget,
    and access controls. It can have both global rate limits and
    model-specific rate limits.

    Attributes:
        id (int): The ID of this API key.
        name (Text): A descriptive name for the API key.
        budget (Optional[float]): Maximum spending limit, if any.
        global_limits (Optional[APIKeyLimits]): Rate limits applied globally.
        asset_limits (List[APIKeyLimits]): Rate limits for specific models.
        expires_at (Optional[datetime]): Expiration date and time.
        access_key (Optional[Text]): The actual API key value.
        is_admin (bool): Whether this is an admin API key.
    """

    def __init__(
        self,
        name: Text,
        expires_at: Optional[Union[datetime, Text]] = None,
        budget: Optional[float] = None,
        asset_limits: List[APIKeyLimits] = [],
        global_limits: Optional[Union[Dict, APIKeyLimits]] = None,
        id: int = "",
        access_key: Optional[Text] = None,
        is_admin: bool = False,
    ):
        """Initialize an APIKey instance.

        Args:
            name (Text): A descriptive name for the API key.
            expires_at (Optional[Union[datetime, Text]], optional): When the key
                expires. Can be a datetime or ISO format string. Defaults to None.
            budget (Optional[float], optional): Maximum spending limit.
                Defaults to None.
            asset_limits (List[APIKeyLimits], optional): Rate limits for specific
                models. Defaults to empty list.
            global_limits (Optional[Union[Dict, APIKeyLimits]], optional): Global
                rate limits. Can be a dict with tpm/tpd/rpm/rpd keys or an
                APIKeyLimits instance. Defaults to None.
            id (int, optional): Unique identifier. Defaults to empty string.
            access_key (Optional[Text], optional): The actual API key value.
                Defaults to None.
            is_admin (bool, optional): Whether this is an admin key.
                Defaults to False.

        Note:
            The global_limits dict format should have these keys:
            - tpm: tokens per minute
            - tpd: tokens per day
            - rpm: requests per minute
            - rpd: requests per day
        """
        self.id = id
        self.name = name
        self.budget = budget
        self.global_limits = global_limits
        if global_limits is not None and isinstance(global_limits, dict):
            global_token_type_str = global_limits.get("tokenType")
            global_token_type = TokenType(global_token_type_str) if global_token_type_str else None
            self.global_limits = APIKeyLimits(
                token_per_minute=global_limits["tpm"],
                token_per_day=global_limits["tpd"],
                request_per_minute=global_limits["rpm"],
                request_per_day=global_limits["rpd"],
                token_type=global_token_type,
            )
        self.asset_limits = asset_limits
        for i, asset_limit in enumerate(self.asset_limits):
            if isinstance(asset_limit, dict):
                asset_token_type_str = asset_limit.get("tokenType")
                asset_token_type = TokenType(asset_token_type_str) if asset_token_type_str else None
                self.asset_limits[i] = APIKeyLimits(
                    token_per_minute=asset_limit["tpm"],
                    token_per_day=asset_limit["tpd"],
                    request_per_minute=asset_limit["rpm"],
                    request_per_day=asset_limit["rpd"],
                    model=asset_limit["assetId"],
                    token_type=asset_token_type,
                )
        self.expires_at = expires_at
        self.access_key = access_key
        self.is_admin = is_admin
        self.validate()

    def validate(self) -> None:
        """Validate the APIKey configuration.

        This method checks that all rate limits are non-negative and that
        referenced models exist and are valid.

        Raises:
            AssertionError: If any of these conditions are not met:
                - Budget is negative
                - Global rate limits are negative
                - Asset-specific rate limits are negative
            Exception: If a referenced model ID is not a valid aiXplain model.

        Note:
            - For asset limits, both the model reference and limits are checked
            - Models can be specified by ID or Model instance
            - Model IDs are resolved to Model instances during validation
        """
        from aixplain.factories import ModelFactory

        if self.budget is not None:
            assert self.budget >= 0, "Budget must be greater or equal to 0"
        if self.global_limits is not None:
            assert self.global_limits.request_per_day >= 0, "Request per day must be greater or equal to 0"
            assert self.global_limits.request_per_minute >= 0, "Request per minute must be greater or equal to 0"
            assert self.global_limits.token_per_day >= 0, "Token per day must be greater or equal to 0"
            assert self.global_limits.token_per_minute >= 0, "Token per minute must be greater or equal to 0"
        for i, asset_limit in enumerate(self.asset_limits):
            assert asset_limit.model is not None, f"Asset limit {i} must have a model."
            assert asset_limit.request_per_day >= 0, f"Asset limit {i} request per day must be greater or equal to 0"
            assert asset_limit.request_per_minute >= 0, (
                f"Asset limit {i} request per minute must be greater or equal to 0"
            )
            assert asset_limit.token_per_day >= 0, f"Asset limit {i} token per day must be greater or equal to 0"
            assert asset_limit.token_per_minute >= 0, f"Asset limit {i} token per minute must be greater or equal to 0"

            if isinstance(asset_limit.model, str):
                try:
                    self.asset_limits[i].model = ModelFactory.get(asset_limit.model)
                except Exception:
                    raise Exception(f"Asset {asset_limit.model} is not a valid aiXplain model.")

    def to_dict(self) -> Dict:
        """Convert the APIKey instance to a dictionary representation.

        This method serializes the APIKey and its associated limits into a
        format suitable for API requests or storage.

        Returns:
            Dict: A dictionary containing:
                - id (int): The API key's ID
                - name (Text): The API key's name
                - budget (Optional[float]): The spending limit
                - assetsLimits (List[Dict]): Model-specific limits with:
                    - tpm: tokens per minute
                    - tpd: tokens per day
                    - rpm: requests per minute
                    - rpd: requests per day
                    - tokenType (Optional[Text]): Type of token limit ('input', 'output', 'total')
                    - assetId: model ID
                - expiresAt (Optional[Text]): ISO format expiration date
                - globalLimits (Optional[Dict]): Global limits with tpm/tpd/rpm/rpd

        Note:
            - Datetime objects are converted to ISO format strings
            - Model instances are referenced by their ID
        """
        payload = {
            "id": self.id,
            "name": self.name,
            "budget": self.budget,
            "assetsLimits": [],
            "expiresAt": self.expires_at,
        }

        if self.expires_at is not None and isinstance(self.expires_at, datetime):
            payload["expiresAt"] = self.expires_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if self.global_limits is not None:
            payload["globalLimits"] = {
                "tpm": self.global_limits.token_per_minute,
                "tpd": self.global_limits.token_per_day,
                "rpm": self.global_limits.request_per_minute,
                "rpd": self.global_limits.request_per_day,
                "tokenType": self.global_limits.token_type.value if self.global_limits.token_type else None,
            }

        for asset_limit in self.asset_limits:
            payload["assetsLimits"].append(
                {
                    "tpm": asset_limit.token_per_minute,
                    "tpd": asset_limit.token_per_day,
                    "rpm": asset_limit.request_per_minute,
                    "rpd": asset_limit.request_per_day,
                    "assetId": asset_limit.model.id,
                    "tokenType": asset_limit.token_type.value if asset_limit.token_type else None,
                }
            )
        return payload

    def delete(self) -> None:
        """Delete this API key from the system.

        This method permanently removes the API key from the aiXplain platform.
        The operation cannot be undone.

        Raises:
            Exception: If deletion fails, which can happen if:
                - The API key doesn't exist
                - The user doesn't have permission to delete it
                - The API request fails
                - The server returns a non-200 status code

        Note:
            - This operation is permanent and cannot be undone
            - Only the API key owner can delete it
            - Uses the team API key for authentication
        """
        try:
            url = f"{config.BACKEND_URL}/sdk/api-keys/{self.id}"
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start service for DELETE API Key  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = "API Key Deletion Error: Make sure the API Key exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")

    def get_usage(self, asset_id: Optional[Text] = None) -> APIKeyUsageLimit:
        """Get current usage statistics for this API key.

        This method retrieves the current usage counts and limits for the API key,
        either globally or for a specific model.

        Args:
            asset_id (Optional[Text], optional): The model ID to get usage for.
                If None, returns usage for all models. Defaults to None.

        Returns:
            APIKeyUsageLimit: A list of usage statistics objects containing:
                - daily_request_count: Number of requests made today
                - daily_request_limit: Maximum requests allowed per day
                - daily_token_count: Number of tokens used today
                - daily_token_limit: Maximum tokens allowed per day
                - model: The model ID these stats apply to (None for global)

        Raises:
            Exception: If the request fails, which can happen if:
                - The API key doesn't exist
                - The user doesn't have permission to view usage
                - The API request fails
                - The server returns an error response

        Note:
            - Uses the team API key for authentication
            - Counts reset at the start of each day
            - Filtered by asset_id if provided
        """
        try:
            url = f"{config.BACKEND_URL}/sdk/api-keys/{self.id}/usage-limits"
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
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

    def __set_limit(self, limit: int, model: Optional[Union[Text, Model]], limit_type: Text) -> None:
        """Internal method to set a rate limit value.

        This method updates either a global limit or a model-specific limit
        with the provided value.

        Args:
            limit (int): The new limit value to set.
            model (Optional[Union[Text, Model]]): The model to set limit for.
                If None, sets a global limit.
            limit_type (Text): The type of limit to set (e.g., "token_per_day").

        Raises:
            Exception: If trying to set a limit for a model that isn't
                configured in this API key's asset_limits.

        Note:
            - Model can be specified by ID or Model instance
            - For global limits, model should be None
            - limit_type must match an attribute name in APIKeyLimits
        """
        if model is None:
            setattr(self.global_limits, limit_type, limit)
        else:
            if isinstance(model, Model):
                model = model.id
            is_found = False
            for i, asset_limit in enumerate(self.asset_limits):
                if asset_limit.model.id == model:
                    setattr(self.asset_limits[i], limit_type, limit)
                    is_found = True
                    break
            if is_found is False:
                raise Exception(f"Limit for Model {model} not found in the API key.")

    def set_token_per_day(self, token_per_day: int, model: Optional[Union[Text, Model]] = None) -> None:
        """Set the daily token limit for this API key.

        Args:
            token_per_day (int): Maximum number of tokens allowed per day.
            model (Optional[Union[Text, Model]], optional): The model to set
                limit for. If None, sets global limit. Defaults to None.

        Raises:
            Exception: If the model isn't configured in this API key's
                asset_limits.

        Note:
            - Model can be specified by ID or Model instance
            - For global limits, model should be None
            - The new limit takes effect immediately
        """
        self.__set_limit(token_per_day, model, "token_per_day")

    def set_token_per_minute(self, token_per_minute: int, model: Optional[Union[Text, Model]] = None) -> None:
        """Set the per-minute token limit for this API key.

        Args:
            token_per_minute (int): Maximum number of tokens allowed per minute.
            model (Optional[Union[Text, Model]], optional): The model to set
                limit for. If None, sets global limit. Defaults to None.

        Raises:
            Exception: If the model isn't configured in this API key's
                asset_limits.

        Note:
            - Model can be specified by ID or Model instance
            - For global limits, model should be None
            - The new limit takes effect immediately
        """
        self.__set_limit(token_per_minute, model, "token_per_minute")

    def set_request_per_day(self, request_per_day: int, model: Optional[Union[Text, Model]] = None) -> None:
        """Set the daily request limit for this API key.

        Args:
            request_per_day (int): Maximum number of requests allowed per day.
            model (Optional[Union[Text, Model]], optional): The model to set
                limit for. If None, sets global limit. Defaults to None.

        Raises:
            Exception: If the model isn't configured in this API key's
                asset_limits.

        Note:
            - Model can be specified by ID or Model instance
            - For global limits, model should be None
            - The new limit takes effect immediately
        """
        self.__set_limit(request_per_day, model, "request_per_day")

    def set_request_per_minute(self, request_per_minute: int, model: Optional[Union[Text, Model]] = None) -> None:
        """Set the per-minute request limit for this API key.

        Args:
            request_per_minute (int): Maximum number of requests allowed per minute.
            model (Optional[Union[Text, Model]], optional): The model to set
                limit for. If None, sets global limit. Defaults to None.

        Raises:
            Exception: If the model isn't configured in this API key's
                asset_limits.

        Note:
            - Model can be specified by ID or Model instance
            - For global limits, model should be None
            - The new limit takes effect immediately
        """
        self.__set_limit(request_per_minute, model, "request_per_minute")
