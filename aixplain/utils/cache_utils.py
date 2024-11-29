import os
import json
import time
import logging
from ..utils.config import CACHE_DURATION


def save_to_cache(cache_file, data):
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
    except Exception as e:
        logging.error(f"Failed to save cache to {cache_file}: {e}")


def load_from_cache(cache_file):
    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
            if time.time() - cache_data["timestamp"] < CACHE_DURATION:
                return cache_data["data"]
            else:
                return None
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
