import json
import logging
import os
import time

from filelock import FileLock

from aixplain.utils.asset_cache import atomic_write_private, default_cache_folder, ensure_cache_folder

logging.getLogger("filelock").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

#: Cache location. Resolved under the per-user cache directory rather than the
#: current working directory, which would expose the contents to anything sharing
#: the checkout -- CI runners, Docker build contexts, co-tenant processes
#: (BUG-940).
CACHE_FOLDER = default_cache_folder()
CACHE_FILE = os.path.join(CACHE_FOLDER, "cache.json")
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
        - Creates the cache directory (owner-only) if it doesn't exist
        - Writes atomically through a private temporary file, so the file is
          never world-readable and never observed half-written
        - Logs an error if saving fails but doesn't raise an exception
        - The data is saved with a timestamp for expiration checking
    """
    logger.info(f"Attempting to save cache to {cache_file}")
    try:
        blob = json.dumps({"timestamp": time.time(), "data": data})
    except Exception as e:
        logger.error(f"Failed to serialize cache for {cache_file}: {e}")
        return

    try:
        folder = os.path.dirname(cache_file) or "."
        ensure_cache_folder(folder)
        logger.info(f"Cache directory created/verified: {folder}")

        with FileLock(lock_file):
            logger.info(f"Acquired file lock: {lock_file}")
            atomic_write_private(cache_file, blob)
            logger.info(f"Successfully saved cache to {cache_file}")
    except Exception as e:
        logger.error(f"Failed to save cache to {cache_file}: {e}")


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
    logger.info(f"Attempting to load cache from {cache_file}")

    if not os.path.exists(cache_file):
        logger.info(f"Cache file does not exist: {cache_file}")
        return None

    try:
        with FileLock(lock_file):
            logger.info(f"Acquired file lock for reading: {lock_file}")
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                cache_age = time.time() - cache_data["timestamp"]
                expiry_time = int(get_cache_expiry())

                logger.info(f"Cache age: {cache_age:.2f}s, expiry threshold: {expiry_time}s")

                if cache_age < expiry_time:
                    logger.info(f"Successfully loaded valid cache from {cache_file}")
                    return cache_data["data"]
                else:
                    logger.info(f"Cache expired (age: {cache_age:.2f}s > {expiry_time}s): {cache_file}")
                    return None
    except Exception as e:
        logger.error(f"Failed to load cache from {cache_file}: {e}")
        return None
