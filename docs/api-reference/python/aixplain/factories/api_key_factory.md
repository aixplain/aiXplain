---
sidebar_label: api_key_factory
title: aixplain.factories.api_key_factory
---

### APIKeyFactory Objects

```python
class APIKeyFactory()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/api_key_factory.py#L10)

Factory class for managing API keys in the aiXplain platform.

This class provides functionality for creating, retrieving, updating, and
monitoring API keys, including their usage limits and budgets.

**Attributes**:

- `backend_url` _str_ - Base URL for the aiXplain backend API.

#### get

```python
@classmethod
def get(cls, api_key: Text) -> APIKey
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/api_key_factory.py#L22)

Retrieve an API key by its value.

This method searches for an API key by matching the first and last 4
characters of the provided key.

**Arguments**:

- `api_key` _Text_ - The API key value to search for.
  

**Returns**:

- `APIKey` - The matching API key object.
  

**Raises**:

- `Exception` - If no matching API key is found.

#### list

```python
@classmethod
def list(cls) -> List[APIKey]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/api_key_factory.py#L43)

List all API keys accessible to the current user.

This method retrieves all API keys that the authenticated user has access to,
using the configured TEAM_API_KEY.

**Returns**:

- `List[APIKey]` - List of API key objects.
  

**Raises**:

- `Exception` - If the API request fails or returns an error, including cases
  where authentication fails or the service is unavailable.

#### create

```python
@classmethod
def create(cls, name: Text, budget: int, global_limits: Union[Dict,
                                                              APIKeyLimits],
           asset_limits: List[Union[Dict, APIKeyLimits]],
           expires_at: datetime) -> APIKey
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/api_key_factory.py#L85)

Create a new API key with specified limits and budget.

This method creates a new API key with configured usage limits, budget,
and expiration date.

**Arguments**:

- `name` _Text_ - Name or description for the API key.
- `budget` _int_ - Total budget allocated to this API key.
- `global_limits` _Union[Dict, APIKeyLimits]_ - Global usage limits for the key,
  either as a dictionary or APIKeyLimits object.
- `asset_limits` _List[Union[Dict, APIKeyLimits]]_ - List of per-asset usage
  limits, each either as a dictionary or APIKeyLimits object.
- `expires_at` _datetime_ - Expiration date and time for the API key.
  

**Returns**:

- `APIKey` - Created API key object with its access key and configuration.
  

**Raises**:

- `Exception` - If the API request fails or returns an error, including cases
  where validation fails or the service is unavailable.

#### update

```python
@classmethod
def update(cls, api_key: APIKey) -> APIKey
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/api_key_factory.py#L145)

Update an existing API key&#x27;s configuration.

This method updates an API key&#x27;s settings such as limits, budget, and
expiration date. The API key must be validated before update.

**Arguments**:

- `api_key` _APIKey_ - API key object with updated configuration.
  Must have a valid ID of an existing key.
  

**Returns**:

- `APIKey` - Updated API key object with new configuration.
  

**Raises**:

- `Exception` - If:
  - API key validation fails
  - API key ID is invalid
  - Update request fails
  - Service is unavailable

#### get\_usage\_limits

```python
@classmethod
def get_usage_limits(
        cls,
        api_key: Text = config.TEAM_API_KEY,
        asset_id: Optional[Text] = None) -> List[APIKeyUsageLimit]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/factories/api_key_factory.py#L194)

Retrieve current usage limits and counts for an API key.

This method fetches the current usage statistics and limits for an API key,
optionally filtered by a specific asset.

**Arguments**:

- `api_key` _Text, optional_ - API key to check usage for. Defaults to
  config.TEAM_API_KEY.
- `asset_id` _Optional[Text], optional_ - Filter usage limits for a specific
  asset. Defaults to None, showing all assets.
  

**Returns**:

- `List[APIKeyUsageLimit]` - List of usage limit objects containing:
  - daily_request_count: Current number of requests today
  - daily_request_limit: Maximum allowed requests per day
  - daily_token_count: Current number of tokens used today
  - daily_token_limit: Maximum allowed tokens per day
  - model: Asset ID if limit is asset-specific, None if global
  

**Raises**:

- `Exception` - If:
  - API key is invalid
  - User is not the key owner
  - Service is unavailable

