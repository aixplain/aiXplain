import os
import json
import time
import logging
from datetime import datetime
from enum import Enum
from urllib.parse import urljoin
from typing import Dict, Optional, Union, Text
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.cache_utils import save_to_cache, load_from_cache, CACHE_FOLDER
from aixplain.enums import Supplier, Function

CACHE_FILE = f"{CACHE_FOLDER}/models.json"
LOCK_FILE = f"{CACHE_FILE}.lock" 

def load_models(cache_expiry: Optional[int] = None):
    """
    Load models from cache or fetch from backend if not cached.
    Only models with status "onboarded" should be cached.

    Args:
        cache_expiry (int, optional): Expiry time in seconds. Default is user-configurable.
    """

    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL

    cached_data = load_from_cache(CACHE_FILE, LOCK_FILE)

    if cached_data is not None:

        return parse_models(cached_data)

    url = urljoin(backend_url, "sdk/models")
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    response = _request_with_retry("get", url, headers=headers)
    if not 200 <= response.status_code < 300:
        raise Exception(f"Models could not be loaded, API key '{api_key}' might be invalid.")

    models_data = response.json()

    onboarded_models = [model for model in models_data["items"] if model["status"].lower() == "onboarded"]
    save_to_cache(CACHE_FILE, {"items": onboarded_models}, LOCK_FILE)

    return parse_models({"items": onboarded_models})

def parse_models(models_data):
    """
    Convert model data into an Enum and dictionary format for easy use.

    Returns:
        - models_enum: Enum with model IDs.
        - models_details: Dictionary containing all model parameters.
    """

    if not models_data["items"]: 
        logging.warning("No onboarded models found.")
        return Enum("Model", {}), {}
    models_enum = Enum("Model", {m["id"].upper().replace("-", "_"): m["id"] for m in models_data["items"]}, type=str)

    models_details = {
        model["id"]: {
            "id": model["id"],
            "name": model.get("name", ""),
            "description": model.get("description", ""),
            "api_key": model.get("api_key", config.TEAM_API_KEY),
            "supplier": model.get("supplier", "aiXplain"),
            "version": model.get("version"),
            "function": model.get("function"),
            "is_subscribed": model.get("is_subscribed", False),
            "cost": model.get("cost"),
            "created_at": model.get("created_at"),
            "input_params": model.get("input_params"),
            "output_params": model.get("output_params"),
            "model_params": model.get("model_params"),
            **model,  
        }
        for model in models_data["items"]
    }

    return models_enum, models_details


Model, ModelDetails = load_models()
