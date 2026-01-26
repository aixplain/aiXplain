---
sidebar_label: api_key
title: aixplain.modules.api_key
---

### APIKeyLimits Objects

```python
class APIKeyLimits()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L9)

Rate limits configuration for an API key.

This class defines the rate limits that can be applied either globally
to an API key or specifically to a model.

**Attributes**:

- `token_per_minute` _int_ - Maximum number of tokens allowed per minute.
- `token_per_day` _int_ - Maximum number of tokens allowed per day.
- `request_per_minute` _int_ - Maximum number of requests allowed per minute.
- `request_per_day` _int_ - Maximum number of requests allowed per day.
- `model` _Optional[Model]_ - The model these limits apply to, if any.

#### \_\_init\_\_

```python
def __init__(token_per_minute: int,
             token_per_day: int,
             request_per_minute: int,
             request_per_day: int,
             model: Optional[Union[Text, Model]] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L23)

Initialize an APIKeyLimits instance.

**Arguments**:

- `token_per_minute` _int_ - Maximum number of tokens per minute.
- `token_per_day` _int_ - Maximum number of tokens per day.
- `request_per_minute` _int_ - Maximum number of requests per minute.
- `request_per_day` _int_ - Maximum number of requests per day.
- `model` _Optional[Union[Text, Model]], optional_ - The model to apply
  limits to. Can be a model ID or Model instance. Defaults to None.

### APIKeyUsageLimit Objects

```python
class APIKeyUsageLimit()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L52)

#### \_\_init\_\_

```python
def __init__(daily_request_count: int,
             daily_request_limit: int,
             daily_token_count: int,
             daily_token_limit: int,
             model: Optional[Union[Text, Model]] = None)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L53)

Get the usage limits of an API key globally (model equals to None) or for a specific model.

**Arguments**:

- `daily_request_count` _int_ - number of requests made
- `daily_request_limit` _int_ - limit of requests
- `daily_token_count` _int_ - number of tokens used
- `daily_token_limit` _int_ - limit of tokens
- `model` _Optional[Union[Text, Model]], optional_ - Model which the limits apply. Defaults to None.

### APIKey Objects

```python
class APIKey()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L80)

An API key for accessing aiXplain services.

This class represents an API key with its associated limits, budget,
and access controls. It can have both global rate limits and
model-specific rate limits.

**Attributes**:

- `id` _int_ - The ID of this API key.
- `name` _Text_ - A descriptive name for the API key.
- `budget` _Optional[float]_ - Maximum spending limit, if any.
- `global_limits` _Optional[APIKeyLimits]_ - Rate limits applied globally.
- `asset_limits` _List[APIKeyLimits]_ - Rate limits for specific models.
- `expires_at` _Optional[datetime]_ - Expiration date and time.
- `access_key` _Optional[Text]_ - The actual API key value.
- `is_admin` _bool_ - Whether this is an admin API key.

#### \_\_init\_\_

```python
def __init__(name: Text,
             expires_at: Optional[Union[datetime, Text]] = None,
             budget: Optional[float] = None,
             asset_limits: List[APIKeyLimits] = [],
             global_limits: Optional[Union[Dict, APIKeyLimits]] = None,
             id: int = "",
             access_key: Optional[Text] = None,
             is_admin: bool = False)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L98)

Initialize an APIKey instance.

**Arguments**:

- `name` _Text_ - A descriptive name for the API key.
- `expires_at` _Optional[Union[datetime, Text]], optional_ - When the key
  expires. Can be a datetime or ISO format string. Defaults to None.
- `budget` _Optional[float], optional_ - Maximum spending limit.
  Defaults to None.
- `asset_limits` _List[APIKeyLimits], optional_ - Rate limits for specific
  models. Defaults to empty list.
- `global_limits` _Optional[Union[Dict, APIKeyLimits]], optional_ - Global
  rate limits. Can be a dict with tpm/tpd/rpm/rpd keys or an
  APIKeyLimits instance. Defaults to None.
- `id` _int, optional_ - Unique identifier. Defaults to empty string.
- `access_key` _Optional[Text], optional_ - The actual API key value.
  Defaults to None.
- `is_admin` _bool, optional_ - Whether this is an admin key.
  Defaults to False.


**Notes**:

  The global_limits dict format should have these keys:
  - tpm: tokens per minute
  - tpd: tokens per day
  - rpm: requests per minute
  - rpd: requests per day

#### validate

```python
def validate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L161)

Validate the APIKey configuration.

This method checks that all rate limits are non-negative and that
referenced models exist and are valid.

**Raises**:

- `AssertionError` - If any of these conditions are not met:
  - Budget is negative
  - Global rate limits are negative
  - Asset-specific rate limits are negative
- `Exception` - If a referenced model ID is not a valid aiXplain model.


**Notes**:

  - For asset limits, both the model reference and limits are checked
  - Models can be specified by ID or Model instance
  - Model IDs are resolved to Model instances during validation

#### to\_dict

```python
def to_dict() -> Dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L201)

Convert the APIKey instance to a dictionary representation.

This method serializes the APIKey and its associated limits into a
format suitable for API requests or storage.

**Returns**:

- `Dict` - A dictionary containing:
  - id (int): The API key&#x27;s ID
  - name (Text): The API key&#x27;s name
  - budget (Optional[float]): The spending limit
  - assetsLimits (List[Dict]): Model-specific limits with:
  - tpm: tokens per minute
  - tpd: tokens per day
  - rpm: requests per minute
  - rpd: requests per day
  - assetId: model ID
  - expiresAt (Optional[Text]): ISO format expiration date
  - globalLimits (Optional[Dict]): Global limits with tpm/tpd/rpm/rpd


**Notes**:

  - Datetime objects are converted to ISO format strings
  - Model instances are referenced by their ID

#### delete

```python
def delete() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L256)

Delete this API key from the system.

This method permanently removes the API key from the aiXplain platform.
The operation cannot be undone.

**Raises**:

- `Exception` - If deletion fails, which can happen if:
  - The API key doesn&#x27;t exist
  - The user doesn&#x27;t have permission to delete it
  - The API request fails
  - The server returns a non-200 status code


**Notes**:

  - This operation is permanent and cannot be undone
  - Only the API key owner can delete it
  - Uses the team API key for authentication

#### get\_usage

```python
def get_usage(asset_id: Optional[Text] = None) -> APIKeyUsageLimit
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L286)

Get current usage statistics for this API key.

This method retrieves the current usage counts and limits for the API key,
either globally or for a specific model.

**Arguments**:

- `asset_id` _Optional[Text], optional_ - The model ID to get usage for.
  If None, returns usage for all models. Defaults to None.


**Returns**:

- `APIKeyUsageLimit` - A list of usage statistics objects containing:
  - daily_request_count: Number of requests made today
  - daily_request_limit: Maximum requests allowed per day
  - daily_token_count: Number of tokens used today
  - daily_token_limit: Maximum tokens allowed per day
  - model: The model ID these stats apply to (None for global)


**Raises**:

- `Exception` - If the request fails, which can happen if:
  - The API key doesn&#x27;t exist
  - The user doesn&#x27;t have permission to view usage
  - The API request fails
  - The server returns an error response


**Notes**:

  - Uses the team API key for authentication
  - Counts reset at the start of each day
  - Filtered by asset_id if provided

#### set\_token\_per\_day

```python
def set_token_per_day(token_per_day: int,
                      model: Optional[Union[Text, Model]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L377)

Set the daily token limit for this API key.

**Arguments**:

- `token_per_day` _int_ - Maximum number of tokens allowed per day.
- `model` _Optional[Union[Text, Model]], optional_ - The model to set
  limit for. If None, sets global limit. Defaults to None.


**Raises**:

- `Exception` - If the model isn&#x27;t configured in this API key&#x27;s
  asset_limits.


**Notes**:

  - Model can be specified by ID or Model instance
  - For global limits, model should be None
  - The new limit takes effect immediately

#### set\_token\_per\_minute

```python
def set_token_per_minute(token_per_minute: int,
                         model: Optional[Union[Text, Model]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L396)

Set the per-minute token limit for this API key.

**Arguments**:

- `token_per_minute` _int_ - Maximum number of tokens allowed per minute.
- `model` _Optional[Union[Text, Model]], optional_ - The model to set
  limit for. If None, sets global limit. Defaults to None.


**Raises**:

- `Exception` - If the model isn&#x27;t configured in this API key&#x27;s
  asset_limits.


**Notes**:

  - Model can be specified by ID or Model instance
  - For global limits, model should be None
  - The new limit takes effect immediately

#### set\_request\_per\_day

```python
def set_request_per_day(request_per_day: int,
                        model: Optional[Union[Text, Model]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L415)

Set the daily request limit for this API key.

**Arguments**:

- `request_per_day` _int_ - Maximum number of requests allowed per day.
- `model` _Optional[Union[Text, Model]], optional_ - The model to set
  limit for. If None, sets global limit. Defaults to None.


**Raises**:

- `Exception` - If the model isn&#x27;t configured in this API key&#x27;s
  asset_limits.


**Notes**:

  - Model can be specified by ID or Model instance
  - For global limits, model should be None
  - The new limit takes effect immediately

#### set\_request\_per\_minute

```python
def set_request_per_minute(request_per_minute: int,
                           model: Optional[Union[Text, Model]] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/api_key.py#L434)

Set the per-minute request limit for this API key.

**Arguments**:

- `request_per_minute` _int_ - Maximum number of requests allowed per minute.
- `model` _Optional[Union[Text, Model]], optional_ - The model to set
  limit for. If None, sets global limit. Defaults to None.


**Raises**:

- `Exception` - If the model isn&#x27;t configured in this API key&#x27;s
  asset_limits.


**Notes**:

  - Model can be specified by ID or Model instance
  - For global limits, model should be None
  - The new limit takes effect immediately
