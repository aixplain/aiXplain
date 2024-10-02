from aixplain.modules import Model
from datetime import datetime
from typing import Dict, List, Optional, Text, Union


class APIKeyGlobalLimits:
    def __init__(
        self,
        token_per_minute: int,
        token_per_day: int,
        request_per_minute: int,
        request_per_day: int,
        model: Optional[Union[Text, Model]] = None,
    ):
        self.token_per_minute = token_per_minute
        self.token_per_day = token_per_day
        self.request_per_minute = request_per_minute
        self.request_per_day = request_per_day
        self.model = model
        if model is not None and isinstance(model, str):
            from aixplain.factories import ModelFactory

            self.model = ModelFactory.get(model)


class APIKey:
    def __init__(
        self,
        name: Text,
        expires_at: Union[datetime, Text],
        budget: Optional[float] = None,
        asset_limits: List[APIKeyGlobalLimits] = [],
        global_limits: Optional[Union[Dict, APIKeyGlobalLimits]] = None,
        id: int = "",
        access_key: Optional[Text] = None,
        is_admin: bool = False,
    ):
        self.id = id
        self.name = name
        self.budget = budget
        self.global_limits = global_limits
        if global_limits is not None and isinstance(global_limits, dict):
            self.global_limits = APIKeyGlobalLimits(
                token_per_minute=global_limits["tpm"],
                token_per_day=global_limits["tpd"],
                request_per_minute=global_limits["rpm"],
                request_per_day=global_limits["rpd"],
            )
        self.asset_limits = asset_limits
        for i, asset_limit in enumerate(self.asset_limits):
            if isinstance(asset_limit, dict):
                self.asset_limits[i] = APIKeyGlobalLimits(
                    token_per_minute=asset_limit["tpm"],
                    token_per_day=asset_limit["tpd"],
                    request_per_minute=asset_limit["rpm"],
                    request_per_day=asset_limit["rpd"],
                    model=asset_limit["model"],
                )
        self.expires_at = expires_at
        self.access_key = access_key
        self.is_admin = is_admin
        self.validate()

    def validate(self) -> None:
        """Validate the APIKey object"""
        from aixplain.factories import ModelFactory

        if self.budget is not None:
            assert self.budget > 0, "Budget must be greater than 0"
        if self.global_limits is not None:
            assert self.global_limits.request_per_day > 0, "Request per day must be greater than 0"
            assert self.global_limits.request_per_minute > 0, "Request per minute must be greater than 0"
            assert self.global_limits.token_per_day > 0, "Token per day must be greater than 0"
            assert self.global_limits.token_per_minute > 0, "Token per minute must be greater than 0"
        for i, asset_limit in enumerate(self.asset_limits):
            assert asset_limit.model is not None, f"Asset limit {i} must have a model."
            assert asset_limit.request_per_day > 0, f"Asset limit {i} request per day must be greater than 0"
            assert asset_limit.request_per_minute > 0, f"Asset limit {i} request per minute must be greater than 0"
            assert asset_limit.token_per_day > 0, f"Asset limit {i} token per day must be greater than 0"
            assert asset_limit.token_per_minute > 0, f"Asset limit {i} token per minute must be greater than 0"

            if isinstance(asset_limit.model, str):
                try:
                    self.asset_limits[i].model = ModelFactory.get(asset_limit.model)
                except Exception:
                    raise Exception(f"Asset {asset_limit.model} is not a valid aiXplain model.")

    def to_dict(self) -> Dict:
        """Convert the APIKey object to a dictionary"""
        payload = {
            "id": self.id,
            "name": self.name,
            "budget": self.budget,
            "assetLimits": [],
            "expiresAt": self.expires_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }

        if self.global_limits is not None:
            payload["globalLimits"] = {
                "tpm": self.global_limits.token_per_minute,
                "tpd": self.global_limits.token_per_day,
                "rpm": self.global_limits.request_per_minute,
                "rpd": self.global_limits.request_per_day,
            }

        for i, asset_limit in enumerate(self.asset_limits):
            payload["assetLimits"].append(
                {
                    "tpm": asset_limit.token_per_minute,
                    "tpd": asset_limit.token_per_day,
                    "rpm": asset_limit.request_per_minute,
                    "rpd": asset_limit.request_per_day,
                    "model": asset_limit.model.id,
                }
            )
        return payload

    def delete(self) -> None:
        """Delete an API key by its ID"""
        import logging
        from aixplain.utils import config
        from aixplain.utils.file_utils import _request_with_retry

        try:
            url = f"{config.BACKEND_URL}/sdk/api-keys/{self.id}"
            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start service for DELETE API Key  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            if r.status_code != 200:
                raise Exception()
        except Exception:
            message = "Dataset Deletion Error: Make sure the API Key exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")
