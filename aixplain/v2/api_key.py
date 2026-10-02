"""API Key management module for aiXplain v2 API.

This module provides classes for managing API keys and their rate limits
using the V2 SDK foundation with proper mixin usage.
"""

import re
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config as dj_config
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional, Union, Any, TYPE_CHECKING
from typing_extensions import Literal, TypedDict

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
from .exceptions import APIError, ResourceError, ValidationError

if TYPE_CHECKING:
    from .core import Aixplain


def _resolve_model(model: Any) -> str:
    """Resolve a model reference to a string identifier.

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


#: HTTP statuses on the by-ID fetch that mean "this argument is not a key ID".
#: Anything else -- 401, 403, a 5xx, a dropped connection -- is a failure of the
#: request and says nothing about the argument.
#:
#: Used only to choose which error to report once nothing has matched, never to
#: decide whether to look. The fallback runs unconditionally: which status a
#: backend returns for a non-ObjectId path segment is its business (a 500 would
#: be unsurprising), and gating the lookup on this set would silently break
#: ``get()`` by name the day that changed.
_NOT_AN_ID_STATUSES = frozenset({400, 404, 422})

#: What a resource ID looks like: a 24-character hex ObjectId, as every ``id`` the
#: backend issues is. Used to keep anything that is *not* one out of a request URL
#: -- ``get()`` accepts a key value, and a key value in a path segment lands in
#: access logs, proxies and error-tracking breadcrumbs. A non-matching argument is
#: resolved from the listing first, and only reaches the by-ID endpoint once the
#: listing has proved it is not a key on this account.
_RESOURCE_ID = re.compile(r"[0-9a-fA-F]{24}")


def _mask(value: str) -> str:
    """Render a key value as ``abcd...wxyz`` so errors never echo a live key."""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def _coerce_token_type(value: Any) -> TokenType:
    """Coerce ``"output"`` (or a :class:`TokenType`) into a :class:`TokenType`.

    Raises:
        ValidationError: If *value* is not one of the three accepted strings.
            ``TokenType(value)`` on its own raises a bare ``ValueError`` whose
            message does not say what is accepted.
    """
    if isinstance(value, TokenType):
        return value
    try:
        return TokenType(value)
    except ValueError:
        accepted = ", ".join(repr(member.value) for member in TokenType)
        raise ValidationError(f"Unknown token_type {value!r}. Accepted values: {accepted}.") from None


#: The string form of :class:`TokenType`, accepted anywhere the enum is. Spelled
#: as a ``Literal`` so a type checker rejects a typo without the caller importing
#: the enum.
TokenTypeValue = Literal["input", "output", "total"]


class APIKeyLimitsDict(TypedDict, total=False):
    """The dict form of :class:`APIKeyLimits`, on the user-facing field names.

    Every key is optional; an omitted dimension is left unrestricted rather than
    set to zero. Declared as a ``TypedDict`` so a caller writing a plain dict
    still gets autocomplete and a type error on a misspelled key, with nothing to
    import.
    """

    token_per_minute: int
    token_per_day: int
    request_per_minute: int
    request_per_day: int
    model: Any
    token_type: Union[TokenTypeValue, TokenType]


#: What ``global_limits`` and every element of ``asset_limits`` accept.
APIKeyLimitsInput = Union["APIKeyLimits", APIKeyLimitsDict, Dict[str, Any]]

#: The user-facing field names, in declaration order. Named in the error raised
#: for an unknown key, so the message teaches the shape rather than only
#: rejecting it.
LIMIT_FIELDS = (
    "token_per_minute",
    "token_per_day",
    "request_per_minute",
    "request_per_day",
    "model",
    "token_type",
)

#: Wire spelling -> user-facing field. Accepted on input as an undocumented
#: alias: ``create(global_limits={"tpm": 100})`` worked before this module took
#: the user-facing names, and silently rejecting it would break callers for no
#: gain. Everything outside both sets raises.
_WIRE_ALIASES = {
    "tpm": "token_per_minute",
    "tpd": "token_per_day",
    "rpm": "request_per_minute",
    "rpd": "request_per_day",
    "assetId": "model",
    "tokenType": "token_type",
}


@dataclass_json
@dataclass
class APIKeyLimits:
    """Rate limits configuration for an API key.

    Each dimension defaults to ``None``, meaning *unset*: it is left out of the
    save payload entirely, so setting one dimension cannot disturb the other
    three. A deliberate ``0`` is a distinct value and is sent as ``0``.

    This is the internal representation, and stays usable directly --
    ``APIKeyLimits(token_per_minute=10_000)``. Callers who would rather not
    import it can pass an :class:`APIKeyLimitsDict` anywhere one is accepted.

    Args:
        token_per_minute: Maximum tokens per minute (maps to API ``tpm``).
        token_per_day: Maximum tokens per day (maps to API ``tpd``).
        request_per_minute: Maximum requests per minute (maps to API ``rpm``).
        request_per_day: Maximum requests per day (maps to API ``rpd``).
        model: The model to rate-limit.  Accepts a model path string, a model
            ID, or a :class:`Model` object (maps to API ``assetId``).
        token_type: Which tokens to count -- a :class:`TokenType` or one of
            ``"input"``, ``"output"``, ``"total"``.
    """

    token_per_minute: Optional[int] = field(default=None, metadata=dj_config(field_name="tpm"))
    token_per_day: Optional[int] = field(default=None, metadata=dj_config(field_name="tpd"))
    request_per_minute: Optional[int] = field(default=None, metadata=dj_config(field_name="rpm"))
    request_per_day: Optional[int] = field(default=None, metadata=dj_config(field_name="rpd"))
    model: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))
    token_type: Optional[TokenType] = field(
        default=None,
        metadata=dj_config(
            field_name="tokenType",
            encoder=lambda x: x.value if x else None,
            decoder=lambda x: TokenType(x) if x else None,
        ),
    )

    def __setattr__(self, name: str, value: Any) -> None:
        """Coerce ``token_type`` strings and ``model`` objects on every assignment.

        Doing it here rather than in ``__post_init__`` alone means
        ``limits.token_type = "output"`` behaves the same as passing it to the
        constructor -- the alternative is a field that accepts a string on the
        way in and silently keeps a raw string afterwards, which then reaches
        ``_limits_to_api_dict`` as something without a ``.value``.
        """
        if name == "token_type" and value is not None and not isinstance(value, TokenType):
            value = _coerce_token_type(value)
        elif name == "model" and value is not None and not isinstance(value, str):
            value = _resolve_model(value)
        super().__setattr__(name, value)

    def validate(self) -> None:
        """Validate that every *set* rate limit is non-negative."""
        for field_name in ("token_per_minute", "token_per_day", "request_per_minute", "request_per_day"):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValidationError(f"{field_name.replace('_', ' ').capitalize()} must be >= 0")


def coerce_limits(data: Optional[APIKeyLimitsInput]) -> Optional[APIKeyLimits]:
    """Turn user-supplied limits into an :class:`APIKeyLimits`, or ``None``.

    Accepts ``None``, an :class:`APIKeyLimits` (returned unchanged), or a dict
    on the user-facing field names -- see :class:`APIKeyLimitsDict`. The wire
    spellings (``tpm``, ``tpd``, ``rpm``, ``rpd``, ``assetId``, ``tokenType``)
    are accepted as aliases so dicts written against the old behaviour keep
    working; anything else raises rather than being dropped on the floor, which
    is how a misspelled ``tokens_per_minute`` used to become no limit at all.

    Args:
        data: The limits to coerce.

    Returns:
        Optional[APIKeyLimits]: The coerced limits, or ``None`` for ``None``.

    Raises:
        ValidationError: If *data* is not a dict or ``APIKeyLimits``, or carries
            a key that is neither a user-facing field nor a wire alias.
    """
    if data is None or isinstance(data, APIKeyLimits):
        return data
    if not isinstance(data, dict):
        raise ValidationError(
            f"Limits must be an APIKeyLimits or a dict, got {type(data).__name__}. "
            f"Accepted dict fields: {', '.join(LIMIT_FIELDS)}."
        )

    kwargs: Dict[str, Any] = {}
    unknown = []
    for key, value in data.items():
        field_name = key if key in LIMIT_FIELDS else _WIRE_ALIASES.get(key)
        if field_name is None:
            unknown.append(key)
            continue
        kwargs[field_name] = value
    if unknown:
        raise ValidationError(
            f"Unknown limit field(s): {', '.join(sorted(unknown))}. Accepted fields: {', '.join(LIMIT_FIELDS)}."
        )
    return APIKeyLimits(**kwargs)


def coerce_limits_list(data: Optional[Iterable[APIKeyLimitsInput]]) -> List[APIKeyLimits]:
    """Coerce a sequence of limits (dicts, objects, or a mix) into a list.

    Args:
        data: The per-asset limits to coerce, or ``None``.

    Returns:
        List[APIKeyLimits]: One entry per input element; empty for ``None``.

    Raises:
        ValidationError: If *data* is a single limits value rather than a
            sequence of them -- a dict iterates as its keys, so without this the
            mistake would surface as "Unknown limit field(s): t, o, k, e, n".
    """
    if data is None:
        return []
    if isinstance(data, (APIKeyLimits, dict)):
        raise ValidationError(
            "asset_limits must be a list of limits, not a single one. Wrap it in a list: asset_limits=[{...}]."
        )
    return [limit for limit in (coerce_limits(entry) for entry in data) if limit is not None]


# Override the dataclass_json-generated to_dict with a user-friendly
# snake_case version.  This is necessary because @dataclass_json generates
# to_dict at decoration time using camelCase field_name mappings, and any
# method defined inside the class body is overwritten by the decorator.
def _api_key_limits_to_dict(self, encode_json=False) -> dict:
    """Return a user-facing snake_case dictionary, omitting unset dimensions.

    An unset dimension is absent rather than ``None``: the dict this returns is
    the same shape the caller may hand back to ``asset_limits``, and a ``None``
    there would read as "set this to nothing" rather than "leave it alone".
    """
    result = {}
    for field_name in ("token_per_minute", "token_per_day", "request_per_minute", "request_per_day", "model"):
        value = getattr(self, field_name)
        if value is not None:
            result[field_name] = value
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

    daily_request_count: Optional[int] = field(default=None, metadata=dj_config(field_name="requestCount"))
    daily_request_limit: Optional[int] = field(default=None, metadata=dj_config(field_name="requestCountLimit"))
    daily_token_count: Optional[int] = field(default=None, metadata=dj_config(field_name="tokenCount"))
    daily_token_limit: Optional[int] = field(default=None, metadata=dj_config(field_name="tokenCountLimit"))
    model: Optional[str] = field(default=None, metadata=dj_config(field_name="assetId"))


def _api_key_usage_limit_to_dict(self, encode_json=False) -> dict:
    """Return a user-facing snake_case dictionary."""
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

    # Core fields
    budget: Optional[float] = field(default=None)
    expires_at: Optional[Union[datetime, str]] = field(default=None, metadata=dj_config(field_name="expiresAt"))
    key: Optional[str] = field(default=None, metadata=dj_config(field_name="accessKey"))
    is_admin: bool = field(default=False, metadata=dj_config(field_name="isAdmin"))

    # Nested limit objects - dataclass_json handles deserialization automatically
    # exclude=lambda x: True prevents to_dict() from including these (we build payload manually)
    global_limits: Optional[APIKeyLimitsInput] = field(
        default=None,
        metadata=dj_config(field_name="globalLimits", exclude=lambda x: True),
    )
    asset_limits: List[APIKeyLimitsInput] = field(
        default_factory=list,
        metadata=dj_config(field_name="assetsLimits", exclude=lambda x: True),
    )

    def __setattr__(self, name: str, value: Any) -> None:
        """Coerce dict limits into :class:`APIKeyLimits` on every assignment.

        ``key.asset_limits = [{"model": ..., "token_per_minute": ...}]`` has to
        behave the same as passing the same list to the constructor, and reading
        it back has to give ``APIKeyLimits`` objects -- so the coercion lives
        here rather than in ``__post_init__``, which the generated ``__init__``
        runs once and a later assignment never reaches. Mirrors how
        ``Agent.__setattr__`` coerces ``budget``.
        """
        if name == "global_limits":
            value = coerce_limits(value)
        elif name == "asset_limits":
            value = coerce_limits_list(value)
        super().__setattr__(name, value)

    def __post_init__(self) -> None:
        """Validate limits and restore cached model paths."""
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
        """Switch to update mode when a key with the same name already exists."""
        if not self.id and self.name:
            try:
                for existing in self.list():
                    if existing.name == self.name:
                        self.id = existing.id
                        break
            except Exception:
                pass
        return None

    def build_save_payload(self, **kwargs: Any) -> Dict:
        """Build the payload for save operations.

        Override because:
        1. Nested limits need manual serialization to API format.
        2. Default to_dict() excludes global_limits and asset_limits.
        3. Model paths must be resolved to IDs before sending to the backend.
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

        payload["assetsLimits"] = [self._limits_to_api_dict(limit, include_asset=True) for limit in self.asset_limits]

        self._resolve_asset_ids(payload)

        return payload

    def _create(self, resource_path: str, payload: dict) -> None:
        """Create the resource, falling back to lookup on name conflict (HTTP 422)."""
        try:
            super()._create(resource_path, payload)
        except (APIError, ResourceError) as e:
            status = (
                getattr(e, "status_code", 0) or getattr(e, "__cause__", None) and getattr(e.__cause__, "status_code", 0)
            )
            if status != 422:
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
        """Update and populate instance from response."""
        result = self.context.client.request("PUT", f"{resource_path}/{self.encoded_id}", json=payload)
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
    def _build_page(cls, response: Any, context: "Aixplain", **kwargs: Any) -> Page["APIKey"]:
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
    def get(cls, id: Any, **kwargs: Any) -> "APIKey":
        """Retrieve an API key by its ID, its key value, or its name.

        v1's ``APIKeyFactory.get`` took a key *value*; v2's inherited ``get``
        took an ID, and key-value lookup moved to :meth:`get_by_access_key`. A
        renamed call therefore failed with "not found" rather than "you passed
        the wrong kind of thing". All three forms now resolve here, and an
        argument matching none of them says so.

        An ID-shaped argument goes straight to the by-ID endpoint, which is both
        the cheapest path and the one that yields a fully hydrated resource. A
        name or a key value is resolved from a single listing *first*, so it
        never becomes a URL path segment -- a key value there would be recorded
        by every access log and proxy on the way. Such an argument only reaches
        the by-ID endpoint as a last resort, once the listing has established it
        is not a key on this account.

        Args:
            id: A key ID, a full key value, or a key name.
            **kwargs: Forwarded to the underlying request.

        Returns:
            APIKey: The matching key.

        Raises:
            ResourceError: If nothing matches, or if a name or masked key value
                matches more than one key.
            Exception: Whatever the by-ID fetch raised, if that failure was not a
                verdict on the argument (an expired credential, a 5xx) and no
                key matched the other two forms.
        """
        if not isinstance(id, str) or _RESOURCE_ID.fullmatch(id):
            try:
                return super().get(id, **kwargs)
            except Exception as by_id_error:
                if not isinstance(id, str):
                    raise
                # ``except ... as`` unbinds the name when the block ends, so keep
                # a reference for the decision made after the fallback.
                id_lookup_error = by_id_error
                try:
                    candidates = cls.list(**kwargs)
                except Exception:
                    # The listing is the fallback; if it fails too, the original
                    # per-ID failure is the more useful one to surface.
                    raise by_id_error from None
        else:
            id_lookup_error = None
            candidates = cls.list(**kwargs)

        found = cls._resolve_from_listing(id, candidates)
        if found is not None:
            return found

        if id_lookup_error is None:
            # Not ID-shaped and absent from the listing, so it is not a live key
            # of this account -- the by-ID endpoint is now safe to try, and is
            # the only thing that would still find a key the listing omitted.
            try:
                return super().get(id, **kwargs)
            except Exception as late_error:
                id_lookup_error = late_error

        # Nothing matched. If the by-ID fetch failed for its own reasons rather
        # than because the argument was not an ID, that failure is the answer:
        # reporting "no API key matches" would send the caller hunting for a key
        # that is still there. The backend error is built from the response body,
        # never the request URL, so surfacing it cannot echo the argument.
        status = getattr(id_lookup_error, "status_code", None) or None
        if status is not None and status not in _NOT_AN_ID_STATUSES:
            raise id_lookup_error

        # ``_mask`` rather than the argument itself: it may be a live key value,
        # and error text gets pasted into bug reports.
        raise ResourceError(
            f"No API key matches {_mask(id)!r}. APIKey.get() accepts a key ID, a full key value, "
            "or a key name; this matched none of them. Use APIKey.list() to see the keys on this account."
        )

    @classmethod
    def _resolve_from_listing(cls, value: str, candidates: List["APIKey"]) -> Optional["APIKey"]:
        """Resolve *value* against ``candidates`` as an ID, a key value, then a name.

        Exact comparisons come first and the masked-key *guess* comes last, so a
        name can never be resolved by a four-character prefix/suffix coincidence
        while an exact match for it sits further down the list.

        Args:
            value: The ID, key value or name to resolve.
            candidates: The keys to resolve against, from ``list()``.

        Returns:
            Optional[APIKey]: The matching key, or ``None`` if nothing matched.

        Raises:
            ResourceError: If the value is ambiguous across names or masked keys.
        """
        by_id = [key for key in candidates if key.id is not None and str(key.id) == value]
        if by_id:
            return by_id[0]

        exact_key = cls._resolve_by_key_value(value, candidates, required=False, allow_masked=False)
        if exact_key is not None:
            return exact_key

        by_name = [key for key in candidates if key.name == value]
        if len(by_name) == 1:
            return by_name[0]
        if len(by_name) > 1:
            raise ResourceError(
                f"{len(by_name)} API keys are named {value!r}: {', '.join(str(key.id) for key in by_name)}. "
                "Pass the key ID instead."
            )

        return cls._resolve_by_key_value(value, candidates, required=False)

    @classmethod
    def get_by_access_key(cls, access_key: str, **kwargs: Any) -> "APIKey":
        """Find an API key by its value.

        Args:
            access_key: The full access key (at least 8 characters).
            **kwargs: Additional arguments passed to ``list()``.

        Returns:
            APIKey: The matching APIKey instance.

        Raises:
            ValidationError: If ``access_key`` is too short.
            ResourceError: If no key matches, or if the account returns masked
                keys and more than one of them is consistent with this value.
        """
        if len(access_key) < 8:
            raise ValidationError("Access key must be at least 8 characters for matching")
        return cls._resolve_by_key_value(access_key, cls.list(**kwargs), required=True)

    @classmethod
    def _resolve_by_key_value(
        cls,
        value: str,
        candidates: List["APIKey"],
        required: bool,
        allow_masked: bool = True,
    ) -> Optional["APIKey"]:
        """Resolve a key *value* against ``candidates``, exactly.

        The full value is compared first. The previous implementation compared
        only the first and last four characters, so two keys sharing both
        resolved to whichever the backend listed first -- and limits written
        through the returned object landed on a key the caller never named.

        A backend that returns the key *masked* leaves nothing to compare
        exactly, so a masked entry is matched on its visible prefix and suffix
        instead. That is a guess, and it is treated as one: two masked keys
        consistent with the same value raise rather than silently picking one.

        Args:
            value: The key value to resolve.
            candidates: The keys to resolve against, from ``list()``.
            required: Raise when nothing matches, rather than returning ``None``.
            allow_masked: Fall back to the prefix/suffix guess. ``get()`` turns
                this off for its first pass so that an exact *name* match is
                preferred over a guess against a masked key value.

        Returns:
            Optional[APIKey]: The matching key, or ``None`` when *required* is
            ``False`` and nothing matched.

        Raises:
            ResourceError: If nothing matches and *required* is ``True``, or if
                the value is ambiguous across masked keys.
        """
        exact = [key for key in candidates if key.key is not None and str(key.key) == value]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise ResourceError(
                f"{len(exact)} API keys report the same key value: "
                f"{', '.join(str(key.id) for key in exact)}. Pass the key ID instead."
            )

        # The guess needs at least 8 characters, or the prefix and the suffix
        # overlap and a 3-character name would "match" almost anything.
        # ``get_by_access_key`` enforces this up front; ``get()`` reaches here
        # with arbitrary strings, so the floor lives here too.
        if not allow_masked or len(value) < 8:
            if required:
                raise ResourceError(f"API key with access key {_mask(value)} not found")
            return None

        prefix, suffix = value[:4], value[-4:]
        masked = [
            key
            for key in candidates
            if key.key is not None
            and str(key.key) != value
            and str(key.key).startswith(prefix)
            and str(key.key).endswith(suffix)
        ]
        if len(masked) == 1:
            return masked[0]
        if len(masked) > 1:
            raise ResourceError(
                f"{len(masked)} API keys are consistent with the masked value {_mask(value)!r}: "
                f"{', '.join(str(key.id) for key in masked)}. The backend does not return the full "
                "key value, so this cannot be resolved -- pass the key ID or name instead."
            )

        if required:
            raise ResourceError(f"API key with access key {_mask(value)} not found")
        return None

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
    def get_usage_limits(cls, model: Optional[Any] = None, **kwargs) -> List[APIKeyUsageLimit]:
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
        global_limits: Optional[APIKeyLimitsInput] = None,
        asset_limits: Optional[List[APIKeyLimitsInput]] = None,
        expires_at: Optional[Union[datetime, str]] = None,
        **kwargs,
    ) -> "APIKey":
        """Create a new API key with specified limits and budget.

        Args:
            name: Name for the API key
            budget: Budget limit
            global_limits: Global rate limits. A dict on the user-facing field
                names (see :class:`APIKeyLimitsDict`) or an :class:`APIKeyLimits`.
            asset_limits: Optional per-asset rate limits, in the same two forms
            expires_at: Optional expiration datetime
            **kwargs: Additional arguments passed to save()

        Returns:
            The created APIKey instance
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for API key operations")

        parsed_global = coerce_limits(global_limits)
        parsed_assets = coerce_limits_list(asset_limits)

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
        """Resolve path-style assetIds to model IDs in the payload.

        The backend requires model IDs (not paths) in ``assetId``.
        Uses ``self.context.Model`` for resolution (the standard V2 bound-class pattern).
        Raises ``ValidationError`` when a path cannot be resolved.

        Also stores the ID-to-path mapping on ``self.context`` so that keys
        fetched later via ``list()`` / ``get()`` can restore readable paths.
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
                resolved = self.context.Model.get(asset_id)
                cache[asset_id] = resolved.id
                self._id_to_path[resolved.id] = asset_id
                self._get_path_cache()[resolved.id] = asset_id
                asset_limit["assetId"] = resolved.id
            except Exception:
                raise ValidationError(
                    f"Could not resolve model path '{asset_id}'. "
                    "Use a valid model path (e.g. 'openai/gpt-4o-mini/openai') or a model ID."
                )

    def _restore_model_paths(self) -> None:
        """Replace resolved model IDs with the original user-provided paths.

        Checks the instance-level mapping first (populated during save),
        then falls back to the context-level cache (populated by any prior
        save in this session).
        """
        instance_map = getattr(self, "_id_to_path", {})
        context_map = self._get_path_cache()
        for limit in self.asset_limits:
            if not limit.model:
                continue
            if limit.model in instance_map:
                limit.model = instance_map[limit.model]
            elif limit.model in context_map:
                limit.model = context_map[limit.model]

    def _get_path_cache(self) -> Dict[str, str]:
        """Return the model-ID-to-path cache stored on the context.

        Scoped per ``Aixplain`` instance so it doesn't bleed across clients.
        """
        ctx = getattr(self, "context", None)
        if ctx is None:
            return {}
        cache = getattr(ctx, "_model_path_cache", None)
        if not isinstance(cache, dict):
            cache = {}
            ctx._model_path_cache = cache
        return cache

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
        """Convert APIKeyLimits to a camelCase dictionary for API requests.

        Every dimension is sent, with ``0`` standing in for one the caller never
        set. That is the payload shape shipped before 0.3.0, and the backend
        rejects anything less with a 500, so a partial write is not available to
        send even though the SDK can now express one.

        The in-memory distinction PROD-2917 asked for is unaffected: an unset
        dimension is still ``None`` on :class:`APIKeyLimits`, ``validate()``
        still skips it, and ``to_dict()`` still leaves it out. Only this
        encoding fills the gaps.

        **This is the one place to change** once the backend accepts a partial
        limits payload -- and what ``0`` means to it is still unconfirmed, which
        is why nothing here depends on the answer today.
        """
        result: Dict[str, Any] = {}
        for wire_name, field_name in (
            ("tpm", "token_per_minute"),
            ("tpd", "token_per_day"),
            ("rpm", "request_per_minute"),
            ("rpd", "request_per_day"),
        ):
            value = getattr(limits, field_name)
            result[wire_name] = 0 if value is None else value
        result["tokenType"] = limits.token_type.value if limits.token_type else None
        if include_asset and limits.model:
            result["assetId"] = limits.model
        return result

    @staticmethod
    def _parse_limits(data: Optional[APIKeyLimitsInput]) -> Optional[APIKeyLimits]:
        """Parse limits data into an APIKeyLimits instance.

        Thin alias for :func:`coerce_limits`, kept because it is referenced from
        outside this class.
        """
        return coerce_limits(data)


def _api_key_to_dict(self, encode_json=False) -> dict:
    """Return a user-facing snake_case dictionary including limits."""
    result = {
        "id": self.id,
        "name": self.name,
        "description": self.description,
        "path": self.path,
        "budget": self.budget,
        "expires_at": self.expires_at.isoformat() if isinstance(self.expires_at, datetime) else self.expires_at,
        "key": self.key,
        "is_admin": self.is_admin,
    }
    if self.global_limits is not None:
        result["global_limits"] = self.global_limits.to_dict()
    if self.asset_limits:
        result["asset_limits"] = [limit.to_dict() for limit in self.asset_limits]
    return result


APIKey.to_dict = _api_key_to_dict
