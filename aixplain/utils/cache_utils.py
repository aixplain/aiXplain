import os
import json
import time
import logging
from ..utils.config import CACHE_DURATION


def save_to_cache(cache_file, data):
    def ensure_json_serializable(data):
        if isinstance(data, dict):
            return {k: ensure_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, set):
            return list(data)
        else:
            return data

    data = ensure_json_serializable(data)
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump({"timestamp": time.time(), "data": data}, f)
        logging.info(f"Cache successfully saved to {cache_file}.")
    except Exception as e:
        logging.error(f"Failed to save cache to {cache_file}: {e}")


def load_from_cache(cache_file):
    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
            if time.time() - cache_data["timestamp"] < CACHE_DURATION:
                logging.info(f"Loaded valid cache from {cache_file}.")
                return cache_data["data"]
            else:
                logging.info(f"Cache expired for {cache_file}.")
                return None
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
