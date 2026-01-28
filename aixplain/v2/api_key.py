"""API Key management module for aiXplain v2 API.

This module provides classes for managing API keys and their rate limits
using the V2 SDK foundation with proper mixin usage.
"""

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config as dj_config
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any, TYPE_CHECKING

from .resource import (
    BaseResource,
    SearchResourceMixin,
    GetResourceMixin,
    DeleteResourceMixin,
    DeleteResult,
    Page,
    BaseSearchParams,
    BaseGetParams,
    BaseDeleteParams,
)
from .exceptions import ResourceError, ValidationError

if TYPE_CHECKING:
    from .core import Aixplain


class TokenType(Enum):
    """Token type for rate limiting."""

    INPUT = "input"
    OUTPUT = "output"
    TOTAL = "total"


@dataclass_json
@dataclass
class APIKeyLimits:
    """Rate limits configuration for an API key.

    Uses dataclass_json field mappings to handle API field names:
    - tpm -> token_per_minute
    - tpd -> token_per_day
    - rpm -> request_per_minute
    - rpd -> request_per_day
    - assetId -> model_id
    - tokenType -> token_type
    """

    token_per_minute: int = field(default=0, metadata=dj_config(field_name="tpm"))
    token_per_day: int = field(default=0, metadata=dj_config(field_name="tpd"))
    request_per_minute: int = field(default=0, metadata=dj_config(field_name="rpm"))
    request_per_day: int = field(default=0, metadata=dj_config(field_name="rpd"))
    model_id: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))
    token_type: Optional[TokenType] = field(
        default=None,
        metadata=dj_config(
            field_name="tokenType",
            encoder=lambda x: x.value if x else None,
            decoder=lambda x: TokenType(x) if x else None,
        ),
    )

    def __post_init__(self) -> None:
        """Handle string token_type conversion."""
        if isinstance(self.token_type, str):
            self.token_type = TokenType(self.token_type)

    def validate(self) -> None:
        """Validate rate limit values are non-negative."""
        if self.token_per_minute < 0:
            raise ValidationError("Token per minute must be >= 0")
        if self.token_per_day < 0:
            raise ValidationError("Token per day must be >= 0")
        if self.request_per_minute < 0:
            raise ValidationError("Request per minute must be >= 0")
        if self.request_per_day < 0:
            raise ValidationError("Request per day must be >= 0")


@dataclass_json
@dataclass
class APIKeyUsageLimit:
    """Usage statistics for an API key.

    Uses dataclass_json field mappings to handle API field names.
    All fields are Optional since the API may return null values.
    """

    daily_request_count: Optional[int] = field(default=None, metadata=dj_config(field_name="requestCount"))
    daily_request_limit: Optional[int] = field(default=None, metadata=dj_config(field_name="requestCountLimit"))
    daily_token_count: Optional[int] = field(default=None, metadata=dj_config(field_name="tokenCount"))
    daily_token_limit: Optional[int] = field(default=None, metadata=dj_config(field_name="tokenCountLimit"))
    model_id: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))


class APIKeySearchParams(BaseSearchParams):
    """Search parameters for API keys (not used - endpoint returns all keys)."""

    pass


class APIKeyGetParams(BaseGetParams):
    """Get parameters for API keys."""

    pass


class APIKeyDeleteParams(BaseDeleteParams):
    """Delete parameters for API keys."""

    pass


@dataclass_json
@dataclass(repr=False)
class APIKey(
    BaseResource,
    SearchResourceMixin[APIKeySearchParams, "APIKey"],
    GetResourceMixin[APIKeyGetParams, "APIKey"],
    DeleteResourceMixin[APIKeyDeleteParams, DeleteResult],
):
    """An API key for accessing aiXplain services.

    Inherits from V2 foundation:
    - BaseResource: provides save() with _create/_update, clone(), _action()
    - SearchResourceMixin: provides search() for listing with pagination
    - GetResourceMixin: provides get() class method
    - DeleteResourceMixin: provides delete() instance method

    Configuration for non-paginated list endpoint:
    - PAGINATE_PATH = "": Direct GET to RESOURCE_PATH (no /paginate suffix)
    - PAGINATE_METHOD = "get": Use GET instead of POST
    - Override _populate_filters: Return empty dict (no pagination params)
    - Override _build_page: Fix page_total for non-paginated response
    """

    RESOURCE_PATH = "sdk/api-keys"

    # SearchResourceMixin configuration for simple list endpoint
    PAGINATE_PATH = ""  # No /paginate suffix - direct GET to RESOURCE_PATH
    PAGINATE_METHOD = "get"  # GET request instead of POST

    # Core fields
    budget: Optional[float] = field(default=None)
    expires_at: Optional[Union[datetime, str]] = field(default=None, metadata=dj_config(field_name="expiresAt"))
    access_key: Optional[str] = field(default=None, metadata=dj_config(field_name="accessKey"))
    is_admin: bool = field(default=False, metadata=dj_config(field_name="isAdmin"))

    # Nested limit objects - dataclass_json handles deserialization automatically
    # exclude=lambda x: True prevents to_dict() from including these (we build payload manually)
    global_limits: Optional[APIKeyLimits] = field(
        default=None,
        metadata=dj_config(field_name="globalLimits", exclude=lambda x: True),
    )
    asset_limits: List[APIKeyLimits] = field(
        default_factory=list,
        metadata=dj_config(field_name="assetsLimits", exclude=lambda x: True),
    )

    def __post_init__(self) -> None:
        """Validate limits after initialization."""
        if self.global_limits:
            self.global_limits.validate()
        for limit in self.asset_limits:
            limit.validate()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"APIKey(id={self.id}, name={self.name})"

    # =========================================================================
    # BaseResource overrides for save operations
    # =========================================================================

    def build_save_payload(self, **kwargs: Any) -> Dict:
        """Build the payload for save operations.

        Override because:
        1. Nested limits need manual serialization to API format
        2. Default to_dict() excludes global_limits and asset_limits
        """
        self._validate_limits()

        payload: Dict[str, Any] = {"name": self.name, "budget": self.budget}

        if self.id:
            payload["id"] = self.id

        if self.expires_at:
            if isinstance(self.expires_at, datetime):
                payload["expiresAt"] = self.expires_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            else:
                payload["expiresAt"] = self.expires_at

        if self.global_limits:
            payload["globalLimits"] = self._limits_to_dict(self.global_limits)

        payload["assetsLimits"] = [self._limits_to_dict(limit, include_model_id=True) for limit in self.asset_limits]

        return payload

    def _update(self, resource_path: str, payload: dict) -> None:
        """Override to update instance from response.

        BaseResource._update doesn't read the response, but API key update
        returns the updated object which we want to reflect in the instance.
        """
        result = self.context.client.request("PUT", f"{resource_path}/{self.encoded_id}", json=payload)
        # Update instance from response using from_dict pattern
        if result and isinstance(result, dict):
            updated = self.from_dict(result)
            for field_name in self.__dataclass_fields__:
                if hasattr(updated, field_name):
                    setattr(self, field_name, getattr(updated, field_name))

    # =========================================================================
    # SearchResourceMixin overrides for non-paginated list endpoint
    # =========================================================================

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """Override: API key list endpoint doesn't use filters or pagination."""
        return {}

    @classmethod
    def _build_page(cls, response: Any, context: "Aixplain", **kwargs: Any) -> Page["APIKey"]:
        """Override: Fix page_total for non-paginated list response.

        The base implementation sets page_total=len(items) for list responses,
        but it should be 1 (there's only one page when all results are returned).
        """
        # Let base handle most of the work
        page = super()._build_page(response, context, **kwargs)
        # Fix page_total - there's only 1 page for this endpoint
        page.page_total = 1
        return page

    @classmethod
    def list(cls, **kwargs) -> List["APIKey"]:
        """List all API keys.

        Convenience wrapper around search() that returns the results list directly.
        """
        page = cls.search(**kwargs)
        return page.results

    @classmethod
    def get_by_access_key(cls, access_key: str, **kwargs) -> "APIKey":
        """Find an API key by matching first/last 4 chars of access key.

        Args:
            access_key: The full access key to match against (must be at least 8 chars)
            **kwargs: Additional arguments passed to list()

        Returns:
            The matching APIKey instance

        Raises:
            ValidationError: If access_key is too short
            ResourceError: If no matching key is found
        """
        if len(access_key) < 8:
            raise ValidationError("Access key must be at least 8 characters for matching")

        prefix, suffix = access_key[:4], access_key[-4:]
        api_keys = cls.list(**kwargs)
        for key in api_keys:
            if key.access_key and (str(key.access_key).startswith(prefix) and str(key.access_key).endswith(suffix)):
                return key
        raise ResourceError(f"API key with access key {prefix}...{suffix} not found")

    # =========================================================================
    # Usage methods (API-specific endpoints, no mixin available)
    # =========================================================================

    def get_usage(self, model_id: Optional[str] = None) -> List[APIKeyUsageLimit]:
        """Get usage statistics for this API key.

        Args:
            model_id: Optional model ID to filter usage by

        Returns:
            List of usage limit objects
        """
        self._ensure_valid_state()
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}/usage-limits"
        response = self.context.client.get(path)

        results = []
        for item in response:
            if model_id is None or item.get("assetId") == model_id:
                results.append(APIKeyUsageLimit.from_dict(item))
        return results

    @classmethod
    def get_usage_limits(cls, model_id: Optional[str] = None, **kwargs) -> List[APIKeyUsageLimit]:
        """Get usage limits for the current API key (the one used for authentication).

        Args:
            model_id: Optional model ID to filter usage by
            **kwargs: Additional arguments (unused, for API consistency)

        Returns:
            List of usage limit objects
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for API key operations")

        path = f"{cls.RESOURCE_PATH}/usage-limits"
        response = context.client.get(path)

        results = []
        for item in response:
            if model_id is None or item.get("assetId") == model_id:
                results.append(APIKeyUsageLimit.from_dict(item))
        return results

    # =========================================================================
    # Convenience methods for setting rate limits
    # =========================================================================

    def set_token_per_day(self, value: int, model_id: Optional[str] = None) -> None:
        """Set token per day limit."""
        self._set_limit(value, model_id, "token_per_day")

    def set_token_per_minute(self, value: int, model_id: Optional[str] = None) -> None:
        """Set token per minute limit."""
        self._set_limit(value, model_id, "token_per_minute")

    def set_request_per_day(self, value: int, model_id: Optional[str] = None) -> None:
        """Set request per day limit."""
        self._set_limit(value, model_id, "request_per_day")

    def set_request_per_minute(self, value: int, model_id: Optional[str] = None) -> None:
        """Set request per minute limit."""
        self._set_limit(value, model_id, "request_per_minute")

    # =========================================================================
    # Class methods for create/update (following V2 patterns)
    # =========================================================================

    @classmethod
    def create(
        cls,
        name: str,
        budget: float,
        global_limits: Union[Dict, APIKeyLimits],
        asset_limits: Optional[List[Union[Dict, APIKeyLimits]]] = None,
        expires_at: Optional[Union[datetime, str]] = None,
        **kwargs,
    ) -> "APIKey":
        """Create a new API key with specified limits and budget.

        Args:
            name: Name for the API key
            budget: Budget limit
            global_limits: Global rate limits (dict or APIKeyLimits)
            asset_limits: Optional per-asset rate limits
            expires_at: Optional expiration datetime
            **kwargs: Additional arguments passed to save()

        Returns:
            The created APIKey instance
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for API key operations")

        # Parse limits if provided as dicts
        parsed_global = cls._parse_limits(global_limits) if global_limits else None
        parsed_assets = []
        if asset_limits:
            for limit in asset_limits:
                parsed = cls._parse_limits(limit)
                if parsed:
                    parsed_assets.append(parsed)

        api_key = cls(
            name=name,
            budget=budget,
            global_limits=parsed_global,
            asset_limits=parsed_assets,
            expires_at=expires_at,
        )
        setattr(api_key, "context", context)
        return api_key.save(**kwargs)

    # =========================================================================
    # Private helper methods
    # =========================================================================

    def _validate_limits(self) -> None:
        """Validate the API key configuration."""
        if self.budget is not None and self.budget < 0:
            raise ValidationError("Budget must be >= 0")
        if self.global_limits:
            self.global_limits.validate()
        for limit in self.asset_limits:
            if limit.model_id is None:
                raise ValidationError("Asset limit must have a model_id")
            limit.validate()

    def _set_limit(self, value: int, model_id: Optional[str], attr: str) -> None:
        """Set a rate limit value on global or asset limits."""
        if model_id is None:
            if self.global_limits is None:
                self.global_limits = APIKeyLimits()
            setattr(self.global_limits, attr, value)
        else:
            for limit in self.asset_limits:
                if limit.model_id == model_id:
                    setattr(limit, attr, value)
                    return
            raise ResourceError(f"Limit for model {model_id} not found in the API key")

    @staticmethod
    def _limits_to_dict(limits: APIKeyLimits, include_model_id: bool = False) -> Dict:
        """Convert APIKeyLimits to dictionary for API requests."""
        result = {
            "tpm": limits.token_per_minute,
            "tpd": limits.token_per_day,
            "rpm": limits.request_per_minute,
            "rpd": limits.request_per_day,
            "tokenType": limits.token_type.value if limits.token_type else None,
        }
        if include_model_id and limits.model_id:
            result["assetId"] = limits.model_id
        return result

    @staticmethod
    def _parse_limits(data: Union[Dict, APIKeyLimits, None]) -> Optional[APIKeyLimits]:
        """Parse limits data into APIKeyLimits instance."""
        if data is None:
            return None
        if isinstance(data, APIKeyLimits):
            return data
        if isinstance(data, dict):
            return APIKeyLimits.from_dict(data)
        return None
