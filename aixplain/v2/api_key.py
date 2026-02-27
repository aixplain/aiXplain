"""API Key management module for aiXplain v2 API.

This module provides classes for managing API keys and their rate limits
using the V2 SDK foundation with proper mixin usage.
"""

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config as dj_config
from datetime import datetime
from enum import Enum
from typing import ClassVar, Dict, List, Optional, Union, Any, TYPE_CHECKING

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


def _resolve_model(model: Any) -> str:
    """Resolve a model reference to an asset ID string.

    Accepts a string (ID or path) or any object with ``path`` or ``id``
    attributes (e.g. a :class:`Model` instance).
    """
    if isinstance(model, str):
        return model
    path = getattr(model, "path", None)
    if path:
        return path
    model_id = getattr(model, "id", None)
    if model_id:
        return model_id
    return str(model)


class TokenType(Enum):
    """Token type for rate limiting."""

    INPUT = "input"
    OUTPUT = "output"
    TOTAL = "total"


@dataclass_json
@dataclass
class APIKeyLimits:
    """Rate limits configuration for an API key.

    Args:
        token_per_minute: Maximum tokens per minute (maps to API ``tpm``).
        token_per_day: Maximum tokens per day (maps to API ``tpd``).
        request_per_minute: Maximum requests per minute (maps to API ``rpm``).
        request_per_day: Maximum requests per day (maps to API ``rpd``).
        model: The model to rate-limit.  Accepts a model path string, a model
            ID, or a :class:`Model` object (maps to API ``assetId``).
        token_type: Which tokens to count (input, output, or total).
    """

    token_per_minute: int = field(default=0, metadata=dj_config(field_name="tpm"))
    token_per_day: int = field(default=0, metadata=dj_config(field_name="tpd"))
    request_per_minute: int = field(default=0, metadata=dj_config(field_name="rpm"))
    request_per_day: int = field(default=0, metadata=dj_config(field_name="rpd"))
    model: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))
    token_type: Optional[TokenType] = field(
        default=None,
        metadata=dj_config(
            field_name="tokenType",
            encoder=lambda x: x.value if x else None,
            decoder=lambda x: TokenType(x) if x else None,
        ),
    )

    def __post_init__(self) -> None:
        """Handle string token_type conversion and model object resolution."""
        if isinstance(self.token_type, str):
            self.token_type = TokenType(self.token_type)
        if self.model is not None and not isinstance(self.model, str):
            self.model = _resolve_model(self.model)

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


def _api_key_limits_to_dict(self, encode_json=False) -> dict:
    """Return a snake_case dictionary representation."""
    result = {
        "token_per_minute": self.token_per_minute,
        "token_per_day": self.token_per_day,
        "request_per_minute": self.request_per_minute,
        "request_per_day": self.request_per_day,
    }
    if self.model is not None:
        result["model"] = self.model
    if self.token_type is not None:
        result["token_type"] = self.token_type.value
    return result


APIKeyLimits.to_dict = _api_key_limits_to_dict


@dataclass_json
@dataclass
class APIKeyUsageLimit:
    """Usage statistics for an API key.

    All fields are Optional since the API may return null values.
    """

    daily_request_count: Optional[int] = field(
        default=None, metadata=dj_config(field_name="requestCount")
    )
    daily_request_limit: Optional[int] = field(
        default=None, metadata=dj_config(field_name="requestCountLimit")
    )
    daily_token_count: Optional[int] = field(
        default=None, metadata=dj_config(field_name="tokenCount")
    )
    daily_token_limit: Optional[int] = field(
        default=None, metadata=dj_config(field_name="tokenCountLimit")
    )
    model: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))


def _api_key_usage_limit_to_dict(self, encode_json=False) -> dict:
    """Return a snake_case dictionary representation."""
    return {
        "daily_request_count": self.daily_request_count,
        "daily_request_limit": self.daily_request_limit,
        "daily_token_count": self.daily_token_count,
        "daily_token_limit": self.daily_token_limit,
        "model": self.model,
    }


APIKeyUsageLimit.to_dict = _api_key_usage_limit_to_dict


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

    # Class-level cache: model ID → model path.  Populated by
    # _resolve_asset_ids so that keys fetched via list()/get() can
    # restore human-readable paths on their asset_limits.
    _model_id_cache: ClassVar[Dict[str, str]] = {}

    # Core fields
    budget: Optional[float] = field(default=None)
    expires_at: Optional[Union[datetime, str]] = field(
        default=None, metadata=dj_config(field_name="expiresAt")
    )
    key: Optional[str] = field(default=None, metadata=dj_config(field_name="accessKey"))
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
        """Validate limits and restore cached model paths after initialization."""
        if self.global_limits:
            self.global_limits.validate()
        for limit in self.asset_limits:
            limit.validate()
        self._restore_model_paths()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"APIKey(id={self.id}, name={self.name})"

    # =========================================================================
    # BaseResource overrides for save operations
    # =========================================================================

    def before_save(self, *args: Any, **kwargs: Any) -> None:
        """Delete an existing key with the same name so the create succeeds.

        The backend's update endpoint rejects path-style ``assetId`` values
        that the create endpoint accepts, making a reliable update impossible.
        Instead we remove the stale key and let ``save()`` re-create it.
        """
        if not self.id and self.name:
            try:
                for existing in self.list():
                    if existing.name == self.name:
                        existing.delete()
                        break
            except Exception:
                pass
        return None

    def build_save_payload(self, **kwargs: Any) -> Dict:
        """Build the payload for save operations.

        Override because:
        1. Nested limits need manual serialization to API format
        2. Default to_dict() excludes global_limits and asset_limits
        3. On updates the backend requires model IDs (not paths) in assetId
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
            payload["globalLimits"] = self._limits_to_api_dict(self.global_limits)

        payload["assetsLimits"] = [
            self._limits_to_api_dict(limit, include_asset=True)
            for limit in self.asset_limits
        ]

        self._resolve_asset_ids(payload)

        return payload

    def _create(self, resource_path: str, payload: dict) -> None:
        """Create the resource, populating from existing if backend returns a conflict."""
        try:
            super()._create(resource_path, payload)
        except Exception as e:
            if "already in use" not in str(e):
                raise
            for existing in self.list():
                if existing.name == self.name:
                    for f in self.__dataclass_fields__:
                        if hasattr(existing, f):
                            setattr(self, f, getattr(existing, f))
                    break
            else:
                raise
        self._restore_model_paths()

    def _update(self, resource_path: str, payload: dict) -> None:
        """Update with fallback to create when the key no longer exists.

        Falls back to ``_create`` on 404 so that stale references (e.g.
        after the creation cell was re-run and the old key deleted) don't
        crash.
        """
        try:
            result = self.context.client.request(
                "PUT", f"{resource_path}/{self.encoded_id}", json=payload
            )
        except Exception as e:
            if "Not Found" not in str(e):
                raise
            self.id = None
            payload.pop("id", None)
            self._create(resource_path, payload)
            return
        if result and isinstance(result, dict):
            updated = self.from_dict(result)
            for field_name in self.__dataclass_fields__:
                if hasattr(updated, field_name):
                    setattr(self, field_name, getattr(updated, field_name))
        self._restore_model_paths()

    # =========================================================================
    # SearchResourceMixin overrides for non-paginated list endpoint
    # =========================================================================

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """Override: API key list endpoint doesn't use filters or pagination."""
        return {}

    @classmethod
    def _build_page(
        cls, response: Any, context: "Aixplain", **kwargs: Any
    ) -> Page["APIKey"]:
        """Override: Fix page_total for non-paginated list response.

        The base implementation sets page_total=len(items) for list responses,
        but it should be 1 (there's only one page when all results are returned).
        """
        page = super()._build_page(response, context, **kwargs)
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
            raise ValidationError(
                "Access key must be at least 8 characters for matching"
            )

        prefix, suffix = access_key[:4], access_key[-4:]
        api_keys = cls.list(**kwargs)
        for api_key in api_keys:
            if api_key.key and (
                str(api_key.key).startswith(prefix)
                and str(api_key.key).endswith(suffix)
            ):
                return api_key
        raise ResourceError(f"API key with access key {prefix}...{suffix} not found")

    # =========================================================================
    # Usage methods (API-specific endpoints, no mixin available)
    # =========================================================================

    def get_usage(self, model: Optional[Any] = None) -> List[APIKeyUsageLimit]:
        """Get usage statistics for this API key.

        Args:
            model: Optional model to filter usage by (string path/ID or Model object)

        Returns:
            List of usage limit objects
        """
        self._ensure_valid_state()
        resolved = _resolve_model(model) if model else None
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}/usage-limits"
        response = self.context.client.get(path)

        results = []
        for item in response:
            if resolved is None or item.get("assetId") == resolved:
                results.append(APIKeyUsageLimit.from_dict(item))
        return results

    @classmethod
    def get_usage_limits(
        cls, model: Optional[Any] = None, **kwargs
    ) -> List[APIKeyUsageLimit]:
        """Get usage limits for the current API key (the one used for authentication).

        Args:
            model: Optional model to filter usage by (string path/ID or Model object)
            **kwargs: Additional arguments (unused, for API consistency)

        Returns:
            List of usage limit objects
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for API key operations")

        resolved = _resolve_model(model) if model else None
        path = f"{cls.RESOURCE_PATH}/usage-limits"
        response = context.client.get(path)

        results = []
        for item in response:
            if resolved is None or item.get("assetId") == resolved:
                results.append(APIKeyUsageLimit.from_dict(item))
        return results

    # =========================================================================
    # Convenience methods for setting rate limits
    # =========================================================================

    def set_token_per_day(self, value: int, model: Optional[Any] = None) -> None:
        """Set token per day limit."""
        self._set_limit(value, model, "token_per_day")

    def set_token_per_minute(self, value: int, model: Optional[Any] = None) -> None:
        """Set token per minute limit."""
        self._set_limit(value, model, "token_per_minute")

    def set_request_per_day(self, value: int, model: Optional[Any] = None) -> None:
        """Set request per day limit."""
        self._set_limit(value, model, "request_per_day")

    def set_request_per_minute(self, value: int, model: Optional[Any] = None) -> None:
        """Set request per minute limit."""
        self._set_limit(value, model, "request_per_minute")

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

    def _resolve_asset_ids(self, payload: dict) -> None:
        """Resolve path-style assetIds to actual model IDs in the payload.

        The backend requires model IDs (not paths) in ``assetId``.
        Raises ``ValidationError`` when a path cannot be resolved.

        Populates ``self._id_to_path`` so that the original user-facing
        model paths can be restored on the instance after the API round-trip.
        """
        self._id_to_path: Dict[str, str] = {}
        cache: Dict[str, str] = {}
        for asset_limit in payload.get("assetsLimits", []):
            asset_id = asset_limit.get("assetId", "")
            if not asset_id or "/" not in str(asset_id):
                continue
            if asset_id in cache:
                asset_limit["assetId"] = cache[asset_id]
                continue
            try:
                from .model import Model

                BoundModel = type("Model", (Model,), {"context": self.context})
                model = BoundModel.get(asset_id)
                cache[asset_id] = model.id
                self._id_to_path[model.id] = asset_id
                APIKey._model_id_cache[model.id] = asset_id
                asset_limit["assetId"] = model.id
            except Exception:
                raise ValidationError(
                    f"Could not resolve model path '{asset_id}'. "
                    "Use a valid model path (e.g. 'openai/gpt-4o-mini/openai') "
                    "or a model ID."
                )

    def _restore_model_paths(self) -> None:
        """Replace resolved model IDs with the original user-provided paths.

        Uses the instance-level ``_id_to_path`` mapping first, then falls
        back to the class-level ``_model_id_cache`` so that keys fetched
        via ``list()`` or ``get()`` also get human-readable paths.
        """
        instance_map = getattr(self, "_id_to_path", {})
        for limit in self.asset_limits:
            if not limit.model:
                continue
            if limit.model in instance_map:
                limit.model = instance_map[limit.model]
            elif limit.model in APIKey._model_id_cache:
                limit.model = APIKey._model_id_cache[limit.model]

    def _validate_limits(self) -> None:
        """Validate the API key configuration."""
        if self.budget is not None and self.budget < 0:
            raise ValidationError("Budget must be >= 0")
        if self.global_limits:
            self.global_limits.validate()
        for limit in self.asset_limits:
            if limit.model is None:
                raise ValidationError("Asset limit must have a model")
            limit.validate()

    def _set_limit(self, value: int, model: Optional[Any], attr: str) -> None:
        """Set a rate limit value on global or asset limits."""
        if model is None:
            if self.global_limits is None:
                self.global_limits = APIKeyLimits()
            setattr(self.global_limits, attr, value)
        else:
            resolved = _resolve_model(model)
            for limit in self.asset_limits:
                if limit.model == resolved:
                    setattr(limit, attr, value)
                    return
            raise ResourceError(f"Limit for model {resolved} not found in the API key")

    @staticmethod
    def _limits_to_api_dict(limits: APIKeyLimits, include_asset: bool = False) -> Dict:
        """Convert APIKeyLimits to camelCase dictionary for API requests."""
        result = {
            "tpm": limits.token_per_minute,
            "tpd": limits.token_per_day,
            "rpm": limits.request_per_minute,
            "rpd": limits.request_per_day,
            "tokenType": limits.token_type.value if limits.token_type else None,
        }
        if include_asset and limits.model:
            result["assetId"] = limits.model
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


def _api_key_to_dict(self, encode_json=False) -> dict:
    """Return a snake_case dictionary representation including limits."""
    result = {
        "id": self.id,
        "name": self.name,
        "description": self.description,
        "path": self.path,
        "budget": self.budget,
        "expires_at": (
            self.expires_at.isoformat()
            if isinstance(self.expires_at, datetime)
            else self.expires_at
        ),
        "key": self.key,
        "is_admin": self.is_admin,
    }
    if self.global_limits is not None:
        result["global_limits"] = self.global_limits.to_dict()
    if self.asset_limits:
        result["asset_limits"] = [limit.to_dict() for limit in self.asset_limits]
    return result


APIKey.to_dict = _api_key_to_dict
