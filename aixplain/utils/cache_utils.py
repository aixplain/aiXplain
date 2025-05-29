import os
import json
import time
import logging
from filelock import FileLock

CACHE_FOLDER = ".cache"
CACHE_FILE = f"{CACHE_FOLDER}/cache.json"
LOCK_FILE = f"{CACHE_FILE}.lock"
CACHE_DURATION = 86400


def get_cache_expiry():
    return int(os.getenv("CACHE_EXPIRY_TIME", CACHE_DURATION))


def save_to_cache(cache_file, data, lock_file):
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with FileLock(lock_file):
            with open(cache_file, "w") as f:
                json.dump({"timestamp": time.time(), "data": data}, f)
    except Exception as e:
        logging.error(f"Failed to save cache to {cache_file}: {e}")


def load_from_cache(cache_file, lock_file):
    if os.path.exists(cache_file):
        with FileLock(lock_file):
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                if time.time() - cache_data["timestamp"] < int(get_cache_expiry()):
                    return cache_data["data"]
                else:
                    return None
    return None
