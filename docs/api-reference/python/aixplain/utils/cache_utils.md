---
sidebar_label: cache_utils
title: aixplain.utils.cache_utils
---

#### get\_cache\_expiry

```python
def get_cache_expiry() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/cache_utils.py#L17)

Get the cache expiration duration in seconds.

Retrieves the cache expiration duration from the CACHE_EXPIRY_TIME
environment variable. If not set, falls back to the default CACHE_DURATION.

**Returns**:

- `int` - The cache expiration duration in seconds.

#### save\_to\_cache

```python
def save_to_cache(cache_file: str, data: dict, lock_file: str) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/cache_utils.py#L29)

Save data to a cache file with thread-safe file locking.

This function saves the provided data to a JSON cache file along with a
timestamp. It uses file locking to ensure thread safety during writing.

**Arguments**:

- `cache_file` _str_ - Path to the cache file where data will be saved.
- `data` _dict_ - The data to be cached. Must be JSON-serializable.
- `lock_file` _str_ - Path to the lock file used for thread safety.
  

**Notes**:

  - Creates the cache directory if it doesn&#x27;t exist
  - Logs an error if saving fails but doesn&#x27;t raise an exception
  - The data is saved with a timestamp for expiration checking

#### load\_from\_cache

```python
def load_from_cache(cache_file: str, lock_file: str) -> dict
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/cache_utils.py#L59)

Load data from a cache file with expiration checking.

This function loads data from a JSON cache file if it exists and hasn&#x27;t
expired. It uses file locking to ensure thread safety during reading.

**Arguments**:

- `cache_file` _str_ - Path to the cache file to load data from.
- `lock_file` _str_ - Path to the lock file used for thread safety.
  

**Returns**:

- `dict` - The cached data if the cache exists and hasn&#x27;t expired,
  None otherwise.
  

**Notes**:

  - Returns None if the cache file doesn&#x27;t exist
  - Returns None if the cached data has expired based on CACHE_EXPIRY_TIME
  - Uses thread-safe file locking for reading

