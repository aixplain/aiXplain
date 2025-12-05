---
sidebar_label: asset_cache
title: aixplain.utils.asset_cache
---

### Store Objects

```python
@dataclass
class Store(Generic[T])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L25)

A generic data store for cached assets with expiration time.

This class serves as a container for cached data and its expiration timestamp.
It is used internally by AssetCache to store the cached assets.

**Attributes**:

- `data` _Dict[str, T]_ - Dictionary mapping asset IDs to their cached instances.
- `expiry` _int_ - Unix timestamp when the cached data expires.

### AssetCache Objects

```python
class AssetCache(Generic[T])
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L40)

A modular caching system for aiXplain assets with file-based persistence.

This class provides a generic caching mechanism for different types of assets
(Models, Pipelines, Agents, etc.) with automatic serialization, expiration,
and thread-safe file persistence.

The cache uses JSON files for storage and implements file locking to ensure
thread safety. It also supports automatic cache invalidation based on
expiration time.

**Attributes**:

- `cls` _Type[T]_ - The class type of assets to be cached.
- `cache_file` _str_ - Path to the JSON file storing the cached data.
- `lock_file` _str_ - Path to the lock file for thread-safe operations.
- `store` _Store[T]_ - The in-memory store containing cached data and expiry.
  

**Notes**:

  The cached assets must be serializable to JSON and should implement
  either a to_dict() method or have a standard __dict__ attribute.

#### \_\_init\_\_

```python
def __init__(cls: Type[T], cache_filename: Optional[str] = None) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L62)

Initialize a new AssetCache instance.

**Arguments**:

- `cls` _Type[T]_ - The class type of assets to be cached. Must be
  serializable to JSON.
- `cache_filename` _Optional[str], optional_ - Base name for the cache file.
  If None, uses lowercase class name. Defaults to None.

#### compute\_expiry

```python
def compute_expiry() -> int
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L92)

Calculate the expiration timestamp for cached data.

Uses CACHE_EXPIRY_TIME environment variable if set, otherwise falls back
to the default CACHE_DURATION. The expiry is calculated as current time
plus the duration.

**Returns**:

- `int` - Unix timestamp when the cache will expire.
  

**Notes**:

  If CACHE_EXPIRY_TIME is invalid, it will be removed from environment
  variables and the default duration will be used.

#### invalidate

```python
def invalidate() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L116)

Clear the cache and remove cache files.

This method:
1. Resets the in-memory store with empty data and new expiry
2. Deletes the cache file if it exists
3. Deletes the lock file if it exists

#### load

```python
def load() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L134)

Load cached data from the cache file.

This method reads the cache file (if it exists) and loads the data into
the in-memory store. It performs the following:
1. Checks if cache file exists, if not, invalidates cache
2. Uses file locking to ensure thread-safe reading
3. Deserializes JSON data and converts to appropriate asset instances
4. Checks expiration time and invalidates if expired
5. Handles any errors by invalidating the cache

**Notes**:

  If any errors occur during loading (file not found, invalid JSON,
  deserialization errors), the cache will be invalidated.

#### save

```python
def save() -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L182)

Save the current cache state to the cache file.

This method serializes the current cache state to JSON and writes it
to the cache file. It performs the following:
1. Creates the cache directory if it doesn&#x27;t exist
2. Uses file locking to ensure thread-safe writing
3. Serializes each cached asset to a JSON-compatible format
4. Writes the serialized data and expiry time to the cache file

**Notes**:

  If serialization fails for any asset, that asset will be skipped
  and an error will be logged, but the save operation will continue
  for other assets.

#### get

```python
def get(asset_id: str) -> Optional[T]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L231)

Retrieve a cached asset by its ID.

**Arguments**:

- `asset_id` _str_ - The unique identifier of the asset to retrieve.
  

**Returns**:

- `Optional[T]` - The cached asset instance if found, None otherwise.

#### add

```python
def add(asset: T) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L247)

Add a single asset to the cache.

**Arguments**:

- `asset` _T_ - The asset instance to cache. Must have an &#x27;id&#x27; attribute
  and be serializable to JSON.
  

**Notes**:

  This method automatically saves the updated cache to disk after
  adding the asset.

#### add\_list

```python
def add_list(assets: List[T]) -> None
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L262)

Add multiple assets to the cache at once.

This method replaces all existing cached assets with the new list.

**Arguments**:

- `assets` _List[T]_ - List of asset instances to cache. Each asset must
  have an &#x27;id&#x27; attribute and be serializable to JSON.
  

**Notes**:

  This method automatically saves the updated cache to disk after
  adding the assets.

#### get\_all

```python
def get_all() -> List[T]
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L279)

Retrieve all cached assets.

**Returns**:

- `List[T]` - List of all cached asset instances. Returns an empty list
  if the cache is empty.

#### has\_valid\_cache

```python
def has_valid_cache() -> bool
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L288)

Check if the cache is valid and not expired.

**Returns**:

- `bool` - True if the cache has not expired and contains data,
  False otherwise.

#### serialize

```python
def serialize(obj: Any) -> Any
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/utils/asset_cache.py#L302)

Convert a Python object into a JSON-serializable format.

This function handles various Python types and converts them to formats
that can be serialized to JSON. It supports:
- Basic types (str, int, float, bool, None)
- Collections (list, tuple, set, dict)
- Objects with to_dict() method
- Objects with __dict__ attribute
- Other objects (converted to string)

**Arguments**:

- `obj` _Any_ - The Python object to serialize.
  

**Returns**:

- `Any` - A JSON-serializable version of the input object.

