import os
import json
import time
import logging

CACHE_DURATION = 24 * 60 * 60


def save_to_cache(cache_file, data):
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
    except Exception as e:
        logging.error(f"Failed to save cache to {cache_file}: {e}")


def load_from_cache(cache_file):
    if os.path.exists(cache_file) is True:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
            if time.time() - cache_data["timestamp"] < CACHE_DURATION:
                logging.info(f"Loaded valid cache from {cache_file}.")
                return cache_data["data"]
            else:
                logging.info(f"Cache expired for {cache_file}.")
                return None
    return None
