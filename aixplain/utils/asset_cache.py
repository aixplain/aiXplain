import os
import logging
import json
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass
from filelock import FileLock

from aixplain.utils import config
from typing import TypeVar, Generic, Type
from typing import List

logger = logging.getLogger(__name__)


T = TypeVar("T")

# Constants
CACHE_FOLDER = ".cache"
CACHE_DURATION = 86400


@dataclass
class Store(Generic[T]):
    """A generic data store for cached assets with expiration time.

    This class serves as a container for cached data and its expiration timestamp.
    It is used internally by AssetCache to store the cached assets.

    Attributes:
        data (Dict[str, T]): Dictionary mapping asset IDs to their cached instances.
        expiry (int): Unix timestamp when the cached data expires.
    """
    data: Dict[str, T]
    expiry: int


class AssetCache(Generic[T]):
    """A modular caching system for aiXplain assets with file-based persistence.

    This class provides a generic caching mechanism for different types of assets
    (Models, Pipelines, Agents, etc.) with automatic serialization, expiration,
    and thread-safe file persistence.

    The cache uses JSON files for storage and implements file locking to ensure
    thread safety. It also supports automatic cache invalidation based on
    expiration time.

    Attributes:
        cls (Type[T]): The class type of assets to be cached.
        cache_file (str): Path to the JSON file storing the cached data.
        lock_file (str): Path to the lock file for thread-safe operations.
        store (Store[T]): The in-memory store containing cached data and expiry.

    Note:
        The cached assets must be serializable to JSON and should implement
        either a to_dict() method or have a standard __dict__ attribute.
    """

    def __init__(
        self,
        cls: Type[T],
        cache_filename: Optional[str] = None,
    ) -> None:
        """Initialize a new AssetCache instance.

        Args:
            cls (Type[T]): The class type of assets to be cached. Must be
                serializable to JSON.
            cache_filename (Optional[str], optional): Base name for the cache file.
                If None, uses lowercase class name. Defaults to None.
        """
        self.cls = cls
        if cache_filename is None:
            cache_filename = self.cls.__name__.lower()

        # create cache file and lock file name
        self.cache_file = os.path.join(CACHE_FOLDER, f"{cache_filename}.json")
        self.lock_file = os.path.join(CACHE_FOLDER, f"{cache_filename}.lock")
        self.store = Store(data={}, expiry=self.compute_expiry())
        self.load()

        if not os.path.exists(self.cache_file):
            self.save()

    def compute_expiry(self) -> int:
        """Calculate the expiration timestamp for cached data.

        Uses CACHE_EXPIRY_TIME environment variable if set, otherwise falls back
        to the default CACHE_DURATION. The expiry is calculated as current time
        plus the duration.

        Returns:
            int: Unix timestamp when the cache will expire.

        Note:
            If CACHE_EXPIRY_TIME is invalid, it will be removed from environment
            variables and the default duration will be used.
        """
        try:
            expiry = int(os.getenv("CACHE_EXPIRY_TIME", CACHE_DURATION))
        except Exception as e:
            logger.warning(
                f"Failed to parse CACHE_EXPIRY_TIME: {e}, "
                f"fallback to default value {CACHE_DURATION}"
            )
            # remove the CACHE_EXPIRY_TIME from the environment variables
            del os.environ["CACHE_EXPIRY_TIME"]
            expiry = CACHE_DURATION

        return time.time() + int(expiry)

    def invalidate(self) -> None:
        """Clear the cache and remove cache files.

        This method:
        1. Resets the in-memory store with empty data and new expiry
        2. Deletes the cache file if it exists
        3. Deletes the lock file if it exists
        """
        self.store = Store(data={}, expiry=self.compute_expiry())
        # delete cache file and lock file
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)

    def load(self) -> None:
        """Load cached data from the cache file.

        This method reads the cache file (if it exists) and loads the data into
        the in-memory store. It performs the following:
        1. Checks if cache file exists, if not, invalidates cache
        2. Uses file locking to ensure thread-safe reading
        3. Deserializes JSON data and converts to appropriate asset instances
        4. Checks expiration time and invalidates if expired
        5. Handles any errors by invalidating the cache

        Note:
            If any errors occur during loading (file not found, invalid JSON,
            deserialization errors), the cache will be invalidated.
        """
        if not os.path.exists(self.cache_file):
            self.invalidate()
            return

        with FileLock(self.lock_file):
            with open(self.cache_file, "r") as f:
                try:
                    cache_data = json.load(f)
                    expiry = cache_data["expiry"]
                    raw_data = cache_data["data"]
                    parsed_data = {
                        k: self.cls.from_dict(v) for k, v in raw_data.items()
                    }

                    self.store = Store(data=parsed_data, expiry=expiry)

                    if self.store.expiry < time.time():
                        logger.warning(f"Cache expired for {self.cls.__name__}")
                        self.invalidate()

                except Exception as e:
                    self.invalidate()
                    logger.warning(f"Failed to load cache data: {e}")

                if self.store.expiry < time.time():
                    logger.warning(
                        f"Cache expired, invalidating cache for {self.cls.__name__}"
                    )
                    self.invalidate()
                    return

    def save(self) -> None:
        """Save the current cache state to the cache file.

        This method serializes the current cache state to JSON and writes it
        to the cache file. It performs the following:
        1. Creates the cache directory if it doesn't exist
        2. Uses file locking to ensure thread-safe writing
        3. Serializes each cached asset to a JSON-compatible format
        4. Writes the serialized data and expiry time to the cache file

        Note:
            If serialization fails for any asset, that asset will be skipped
            and an error will be logged, but the save operation will continue
            for other assets.
        """

        os.makedirs(CACHE_FOLDER, exist_ok=True)

        with FileLock(self.lock_file):
            with open(self.cache_file, "w") as f:
                data_dict = {}
                for asset_id, asset in self.store.data.items():
                    try:
                        data_dict[asset_id] = serialize(asset)
                    except Exception as e:
                        logger.error(f"Error serializing {asset_id}: {e}")
                serializable_store = {
                    "expiry": self.store.expiry,
                    "data": data_dict,
                }

                json.dump(serializable_store, f, indent=4)

    def get(self, asset_id: str) -> Optional[T]:
        """Retrieve a cached asset by its ID.

        Args:
            asset_id (str): The unique identifier of the asset to retrieve.

        Returns:
            Optional[T]: The cached asset instance if found, None otherwise.
        """
        return self.store.data.get(asset_id)

    def add(self, asset: T) -> None:
        """Add a single asset to the cache.

        Args:
            asset (T): The asset instance to cache. Must have an 'id' attribute
                and be serializable to JSON.

        Note:
            This method automatically saves the updated cache to disk after
            adding the asset.
        """
        self.store.data[asset.id] = asset.__dict__
        self.save()

    def add_list(self, assets: List[T]) -> None:
        """Add multiple assets to the cache at once.

        This method replaces all existing cached assets with the new list.

        Args:
            assets (List[T]): List of asset instances to cache. Each asset must
                have an 'id' attribute and be serializable to JSON.

        Note:
            This method automatically saves the updated cache to disk after
            adding the assets.
        """
        self.store.data = {asset.id: asset for asset in assets}
        self.save()

    def get_all(self) -> List[T]:
        """Retrieve all cached assets.

        Returns:
            List[T]: List of all cached asset instances. Returns an empty list
                if the cache is empty.
        """
        return list(self.store.data.values())

    def has_valid_cache(self) -> bool:
        """Check if the cache is valid and not expired.

        Returns:
            bool: True if the cache has not expired and contains data,
                False otherwise.
        """
        return self.store.expiry >= time.time() and bool(self.store.data)
    
def serialize(obj: Any) -> Any:
    """Convert a Python object into a JSON-serializable format.

    This function handles various Python types and converts them to formats
    that can be serialized to JSON. It supports:
    - Basic types (str, int, float, bool, None)
    - Collections (list, tuple, set, dict)
    - Objects with to_dict() method
    - Objects with __dict__ attribute
    - Other objects (converted to string)

    Args:
        obj (Any): The Python object to serialize.

    Returns:
        Any: A JSON-serializable version of the input object.
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (list, tuple, set)):
        return [serialize(o) for o in obj]
    elif isinstance(obj, dict):
        return {str(k): serialize(v) for k, v in obj.items()}
    elif hasattr(obj, "to_dict"):
        return serialize(obj.to_dict())
    elif hasattr(obj, "__dict__"):
        return serialize(vars(obj))
    else:
        return str(obj)

