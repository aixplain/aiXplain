---
sidebar_label: api_key
title: aixplain.v2.api_key
---

`from aixplain import APIKey, APIKeyLimits, APIKeyLimitsDict, APIKeyLimitsInput, APIKeyUsageLimit, TokenType, TokenTypeValue`


API Key management module for aiXplain v2 API.

This module provides classes for managing API keys and their rate limits
using the V2 SDK foundation with proper mixin usage.

### TokenType Objects

```python
class TokenType(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L49)

Token type for rate limiting.

#### TokenTypeValue

The string form of `TokenType`, accepted anywhere the enum is. Spelled
as a ``Literal`` so a type checker rejects a typo without the caller importing
the enum.

### APIKeyLimitsDict Objects

```python
class APIKeyLimitsDict(TypedDict)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L107)

The dict form of `APIKeyLimits`, on the user-facing field names.

Every key is optional; an omitted dimension is left unrestricted rather than
set to zero. Declared as a ``TypedDict`` so a caller writing a plain dict
still gets autocomplete and a type error on a misspelled key, with nothing to
import.

#### APIKeyLimitsInput

What ``global_limits`` and every element of ``asset_limits`` accept.

#### LIMIT\_FIELDS

The user-facing field names, in declaration order. Named in the error raised
for an unknown key, so the message teaches the shape rather than only
rejecting it.

### APIKeyLimits Objects

```python
@dataclass_json

@dataclass
class APIKeyLimits()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L155)

Rate limits configuration for an API key.

Each dimension defaults to ``None``, meaning *unset*: it is left out of the
save payload entirely, so setting one dimension cannot disturb the other
three. A deliberate ``0`` is a distinct value and is sent as ``0``.

This is the internal representation, and stays usable directly --
``APIKeyLimits(token_per_minute=10_000)``. Callers who would rather not
import it can pass an `APIKeyLimitsDict` anywhere one is accepted.

**Arguments**:

- `token_per_minute` - Maximum tokens per minute (maps to API ``tpm``).
- `token_per_day` - Maximum tokens per day (maps to API ``tpd``).
- `request_per_minute` - Maximum requests per minute (maps to API ``rpm``).
- `request_per_day` - Maximum requests per day (maps to API ``rpd``).
- `model` - The model to rate-limit.  Accepts a model path string, a model
  ID, or a `Model` object (maps to API ``assetId``).
- `token_type` - Which tokens to count -- a `TokenType` or one of
  ``"input"``, ``"output"``, ``"total"``.

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L191)

Coerce ``token_type`` strings and ``model`` objects on every assignment.

Doing it here rather than in ``__post_init__`` alone means
``limits.token_type = "output"`` behaves the same as passing it to the
constructor -- the alternative is a field that accepts a string on the
way in and silently keeps a raw string afterwards, which then reaches
``_limits_to_api_dict`` as something without a ``.value``.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L206)

Validate that every *set* rate limit is non-negative.

#### coerce\_limits

```python
def coerce_limits(data: Optional[APIKeyLimitsInput]) -> Optional[APIKeyLimits]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L214)

Turn user-supplied limits into an `APIKeyLimits`, or ``None``.

Accepts ``None``, an `APIKeyLimits` (returned unchanged), or a dict
on the user-facing field names -- see `APIKeyLimitsDict`. The wire
spellings (``tpm``, ``tpd``, ``rpm``, ``rpd``, ``assetId``, ``tokenType``)
are accepted as aliases so dicts written against the old behaviour keep
working; anything else raises rather than being dropped on the floor, which
is how a misspelled ``tokens_per_minute`` used to become no limit at all.

**Arguments**:

- `data` - The limits to coerce.
  

**Returns**:

- `Optional[APIKeyLimits]` - The coerced limits, or ``None`` for ``None``.
  

**Raises**:

- `ValidationError` - If *data* is not a dict or ``APIKeyLimits``, or carries
  a key that is neither a user-facing field nor a wire alias.

#### coerce\_limits\_list

```python
def coerce_limits_list(
        data: Optional[Iterable[APIKeyLimitsInput]]) -> List[APIKeyLimits]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L257)

Coerce a sequence of limits (dicts, objects, or a mix) into a list.

**Arguments**:

- `data` - The per-asset limits to coerce, or ``None``.
  

**Returns**:

- `List[APIKeyLimits]` - One entry per input element; empty for ``None``.
  

**Raises**:

- `ValidationError` - If *data* is a single limits value rather than a
  sequence of them -- a dict iterates as its keys, so without this the
  mistake would surface as "Unknown limit field(s): t, o, k, e, n".

### APIKeyUsageLimit Objects

```python
@dataclass_json

@dataclass
class APIKeyUsageLimit()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L306)

Usage statistics for an API key.

All fields are Optional since the API may return null values.

### APIKeySearchParams Objects

```python
class APIKeySearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L333)

Search parameters for API keys (not used - endpoint returns all keys).

### APIKeyGetParams Objects

```python
class APIKeyGetParams(BaseGetParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L339)

Get parameters for API keys.

### APIKeyDeleteParams Objects

```python
class APIKeyDeleteParams(BaseDeleteParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L345)

Delete parameters for API keys.

### APIKey Objects

```python
@dataclass_json

@dataclass(repr=False)
class APIKey(BaseResource, SearchResourceMixin[APIKeySearchParams, "APIKey"],
             GetResourceMixin[APIKeyGetParams, "APIKey"],
             DeleteResourceMixin[APIKeyDeleteParams, DeleteResult])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L353)

An API key for accessing aiXplain services.

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

#### PAGINATE\_PATH

No /paginate suffix - direct GET to RESOURCE_PATH

#### PAGINATE\_METHOD

GET request instead of POST

#### \_\_setattr\_\_

```python
def __setattr__(name: str, value: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L397)

Coerce dict limits into `APIKeyLimits` on every assignment.

``key.asset_limits = [{"model": ..., "token_per_minute": ...}]`` has to
behave the same as passing the same list to the constructor, and reading
it back has to give ``APIKeyLimits`` objects -- so the coercion lives
here rather than in ``__post_init__``, which the generated ``__init__``
runs once and a later assignment never reaches. Mirrors how
``Agent.__setattr__`` coerces ``budget``.

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L413)

Validate limits and restore cached model paths.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L421)

Return string representation.

#### before\_save

```python
def before_save(*args: Any, **kwargs: Any) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L429)

Switch to update mode when a key with the same name already exists.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L441)

Build the payload for save operations.

Override because:
1. Nested limits need manual serialization to API format.
2. Default to_dict() excludes global_limits and asset_limits.
3. Model paths must be resolved to IDs before sending to the backend.

#### list

```python
@classmethod
def list(cls, **kwargs) -> List["APIKey"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L522)

List all API keys.

Convenience wrapper around search() that returns the results list directly.

#### get

```python
@classmethod
def get(cls, id: Any, **kwargs: Any) -> "APIKey"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L531)

Retrieve an API key by its ID, its key value, or its name.

v1's ``APIKeyFactory.get`` took a key *value*; v2's inherited ``get``
took an ID, and key-value lookup moved to `get_by_access_key`. A
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

**Arguments**:

- `id` - A key ID, a full key value, or a key name.
- `**kwargs` - Forwarded to the underlying request.
  

**Returns**:

- `APIKey` - The matching key.
  

**Raises**:

- `ResourceError` - If nothing matches, or if a name or masked key value
  matches more than one key.
- `Exception` - Whatever the by-ID fetch raised, if that failure was not a
  verdict on the argument (an expired credential, a 5xx) and no
  key matched the other two forms.

#### get\_by\_access\_key

```python
@classmethod
def get_by_access_key(cls, access_key: str, **kwargs: Any) -> "APIKey"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L648)

Find an API key by its value.

**Arguments**:

- `access_key` - The full access key (at least 8 characters).
- `**kwargs` - Additional arguments passed to ``list()``.
  

**Returns**:

- `APIKey` - The matching APIKey instance.
  

**Raises**:

- `ValidationError` - If ``access_key`` is too short.
- `ResourceError` - If no key matches, or if the account returns masked
  keys and more than one of them is consistent with this value.

#### get\_usage

```python
def get_usage(model: Optional[Any] = None) -> List[APIKeyUsageLimit]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L747)

Get usage statistics for this API key.

**Arguments**:

- `model` - Optional model to filter usage by (string path/ID or Model object)
  

**Returns**:

  List of usage limit objects

#### get\_usage\_limits

```python
@classmethod
def get_usage_limits(cls,
                     model: Optional[Any] = None,
                     **kwargs) -> List[APIKeyUsageLimit]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L768)

Get usage limits for the current API key (the one used for authentication).

**Arguments**:

- `model` - Optional model to filter usage by (string path/ID or Model object)
- `**kwargs` - Additional arguments (unused, for API consistency)
  

**Returns**:

  List of usage limit objects

#### set\_token\_per\_day

```python
def set_token_per_day(value: int, model: Optional[Any] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L796)

Set token per day limit.

#### set\_token\_per\_minute

```python
def set_token_per_minute(value: int, model: Optional[Any] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L800)

Set token per minute limit.

#### set\_request\_per\_day

```python
def set_request_per_day(value: int, model: Optional[Any] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L804)

Set request per day limit.

#### set\_request\_per\_minute

```python
def set_request_per_minute(value: int, model: Optional[Any] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L808)

Set request per minute limit.

#### create

```python
@classmethod
def create(cls,
           name: str,
           budget: float,
           global_limits: Optional[APIKeyLimitsInput] = None,
           asset_limits: Optional[List[APIKeyLimitsInput]] = None,
           expires_at: Optional[Union[datetime, str]] = None,
           **kwargs) -> "APIKey"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L817)

Create a new API key with specified limits and budget.

**Arguments**:

- `name` - Name for the API key
- `budget` - Budget limit
- `global_limits` - Global rate limits. A dict on the user-facing field
  names (see `APIKeyLimitsDict`) or an `APIKeyLimits`.
- `asset_limits` - Optional per-asset rate limits, in the same two forms
- `expires_at` - Optional expiration datetime
- `**kwargs` - Additional arguments passed to save()
  

**Returns**:

  The created APIKey instance

