import os
import json
import time
import logging
from filelock import FileLock

CACHE_FOLDER = ".cache"
CACHE_FILE = f"{CACHE_FOLDER}/cache.json"
LOCK_FILE = f"{CACHE_FILE}.lock"
CACHE_DURATION = 86400


def get_cache_expiry() -> int:
    """Get the cache expiration duration in seconds.

    Retrieves the cache expiration duration from the CACHE_EXPIRY_TIME
    environment variable. If not set, falls back to the default CACHE_DURATION.

    Returns:
        int: The cache expiration duration in seconds.
    """
    return int(os.getenv("CACHE_EXPIRY_TIME", CACHE_DURATION))


def save_to_cache(cache_file: str, data: dict, lock_file: str) -> None:
    """Save data to a cache file with thread-safe file locking.

    This function saves the provided data to a JSON cache file along with a
    timestamp. It uses file locking to ensure thread safety during writing.

    Args:
        cache_file (str): Path to the cache file where data will be saved.
        data (dict): The data to be cached. Must be JSON-serializable.
        lock_file (str): Path to the lock file used for thread safety.

    Note:
        - Creates the cache directory if it doesn't exist
        - Logs an error if saving fails but doesn't raise an exception
        - The data is saved with a timestamp for expiration checking
    """
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with FileLock(lock_file):
            with open(cache_file, "w") as f:
                json.dump({"timestamp": time.time(), "data": data}, f)
    except Exception as e:
        logging.error(f"Failed to save cache to {cache_file}: {e}")


def load_from_cache(cache_file: str, lock_file: str) -> dict:
    """Load data from a cache file with expiration checking.

    This function loads data from a JSON cache file if it exists and hasn't
    expired. It uses file locking to ensure thread safety during reading.

    Args:
        cache_file (str): Path to the cache file to load data from.
        lock_file (str): Path to the lock file used for thread safety.

    Returns:
        dict: The cached data if the cache exists and hasn't expired,
            None otherwise.

    Note:
        - Returns None if the cache file doesn't exist
        - Returns None if the cached data has expired based on CACHE_EXPIRY_TIME
        - Uses thread-safe file locking for reading
    """
    if os.path.exists(cache_file):
        with FileLock(lock_file):
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                if time.time() - cache_data["timestamp"] < int(get_cache_expiry()):
                    return cache_data["data"]
                else:
                    return None
    return None
