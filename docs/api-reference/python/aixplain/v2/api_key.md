---
sidebar_label: api_key
title: aixplain.v2.api_key
---

API Key management module for aiXplain v2 API.

This module provides classes for managing API keys and their rate limits
using the V2 SDK foundation with proper mixin usage.

### TokenType Objects

```python
class TokenType(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L30)

Token type for rate limiting.

### APIKeyLimits Objects

```python
@dataclass_json

@dataclass
class APIKeyLimits()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L40)

Rate limits configuration for an API key.

Uses dataclass_json field mappings to handle API field names:
- tpm -&gt; token_per_minute
- tpd -&gt; token_per_day
- rpm -&gt; request_per_minute
- rpd -&gt; request_per_day
- assetId -&gt; model_id
- tokenType -&gt; token_type

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L66)

Handle string token_type conversion.

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L71)

Validate rate limit values are non-negative.

### APIKeyUsageLimit Objects

```python
@dataclass_json

@dataclass
class APIKeyUsageLimit()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L85)

Usage statistics for an API key.

Uses dataclass_json field mappings to handle API field names.
All fields are Optional since the API may return null values.

### APIKeySearchParams Objects

```python
class APIKeySearchParams(BaseSearchParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L99)

Search parameters for API keys (not used - endpoint returns all keys).

### APIKeyGetParams Objects

```python
class APIKeyGetParams(BaseGetParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L105)

Get parameters for API keys.

### APIKeyDeleteParams Objects

```python
class APIKeyDeleteParams(BaseDeleteParams)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L111)

Delete parameters for API keys.

### APIKey Objects

```python
@dataclass_json

@dataclass(repr=False)
class APIKey(BaseResource, SearchResourceMixin[APIKeySearchParams, "APIKey"],
             GetResourceMixin[APIKeyGetParams, "APIKey"],
             DeleteResourceMixin[APIKeyDeleteParams, DeleteResult])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L119)

An API key for accessing aiXplain services.

Inherits from V2 foundation:
- BaseResource: provides save() with _create/_update, clone(), _action()
- SearchResourceMixin: provides search() for listing with pagination
- GetResourceMixin: provides get() class method
- DeleteResourceMixin: provides delete() instance method

Configuration for non-paginated list endpoint:
- PAGINATE_PATH = &quot;&quot;: Direct GET to RESOURCE_PATH (no /paginate suffix)
- PAGINATE_METHOD = &quot;get&quot;: Use GET instead of POST
- Override _populate_filters: Return empty dict (no pagination params)
- Override _build_page: Fix page_total for non-paginated response

#### PAGINATE\_PATH

No /paginate suffix - direct GET to RESOURCE_PATH

#### PAGINATE\_METHOD

GET request instead of POST

#### \_\_post\_init\_\_

```python
def __post_init__() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L163)

Validate limits after initialization.

#### \_\_repr\_\_

```python
def __repr__() -> str
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L170)

Return string representation.

#### build\_save\_payload

```python
def build_save_payload(**kwargs: Any) -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L178)

Build the payload for save operations.

Override because:
1. Nested limits need manual serialization to API format
2. Default to_dict() excludes global_limits and asset_limits

#### list

```python
@classmethod
def list(cls, **kwargs) -> List["APIKey"]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L242)

List all API keys.

Convenience wrapper around search() that returns the results list directly.

#### get\_by\_access\_key

```python
@classmethod
def get_by_access_key(cls, access_key: str, **kwargs) -> "APIKey"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L251)

Find an API key by matching first/last 4 chars of access key.

**Arguments**:

- `access_key` - The full access key to match against (must be at least 8 chars)
- `**kwargs` - Additional arguments passed to list()
  

**Returns**:

  The matching APIKey instance
  

**Raises**:

- `ValidationError` - If access_key is too short
- `ResourceError` - If no matching key is found

#### get\_usage

```python
def get_usage(model_id: Optional[str] = None) -> List[APIKeyUsageLimit]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L279)

Get usage statistics for this API key.

**Arguments**:

- `model_id` - Optional model ID to filter usage by
  

**Returns**:

  List of usage limit objects

#### get\_usage\_limits

```python
@classmethod
def get_usage_limits(cls,
                     model_id: Optional[str] = None,
                     **kwargs) -> List[APIKeyUsageLimit]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L299)

Get usage limits for the current API key (the one used for authentication).

**Arguments**:

- `model_id` - Optional model ID to filter usage by
- `**kwargs` - Additional arguments (unused, for API consistency)
  

**Returns**:

  List of usage limit objects

#### set\_token\_per\_day

```python
def set_token_per_day(value: int, model_id: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L326)

Set token per day limit.

#### set\_token\_per\_minute

```python
def set_token_per_minute(value: int, model_id: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L330)

Set token per minute limit.

#### set\_request\_per\_day

```python
def set_request_per_day(value: int, model_id: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L334)

Set request per day limit.

#### set\_request\_per\_minute

```python
def set_request_per_minute(value: int, model_id: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L338)

Set request per minute limit.

#### create

```python
@classmethod
def create(cls,
           name: str,
           budget: float,
           global_limits: Union[Dict, APIKeyLimits],
           asset_limits: Optional[List[Union[Dict, APIKeyLimits]]] = None,
           expires_at: Optional[Union[datetime, str]] = None,
           **kwargs) -> "APIKey"
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/v2/api_key.py#L347)

Create a new API key with specified limits and budget.

**Arguments**:

- `name` - Name for the API key
- `budget` - Budget limit
- `global_limits` - Global rate limits (dict or APIKeyLimits)
- `asset_limits` - Optional per-asset rate limits
- `expires_at` - Optional expiration datetime
- `**kwargs` - Additional arguments passed to save()
  

**Returns**:

  The created APIKey instance

