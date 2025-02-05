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
from aixplain.enums import Supplier

PIPELINE_CACHE_FILE = f"{CACHE_FOLDER}/pipelines.json"
LOCK_FILE = f"{PIPELINE_CACHE_FILE}.lock"


def load_pipelines(cache_expiry: Optional[int] = None):
    """
    Load pipelines from cache or fetch from backend if not cached.
    Only pipelines with status "onboarded" should be cached.

    Args:
        cache_expiry (int, optional): Expiry time in seconds. Default is user-configurable.
    """
    if cache_expiry is None:
        cache_expiry = 86400

    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL

    cached_data = load_from_cache(PIPELINE_CACHE_FILE, LOCK_FILE)
    if cached_data is not None:
        return parse_pipelines(cached_data)

    url = urljoin(backend_url, "sdk/pipelines")
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    response = _request_with_retry("get", url, headers=headers)
    if not 200 <= response.status_code < 300:
        raise Exception(f"Pipelines could not be loaded, API key '{api_key}' might be invalid.")

    pipelines_data = response.json()

    onboarded_pipelines = [pipeline for pipeline in pipelines_data["items"] if pipeline["status"].lower() == "onboarded"]

    save_to_cache(PIPELINE_CACHE_FILE, {"items": onboarded_pipelines}, LOCK_FILE)

    return parse_pipelines({"items": onboarded_pipelines})


def parse_pipelines(pipelines_data):
    """
    Convert pipeline data into an Enum and dictionary format for easy use.

    Returns:
        - pipelines_enum: Enum with pipeline IDs.
        - pipelines_details: Dictionary containing all pipeline parameters.
    """
    if not pipelines_data["items"]:
        logging.warning("No onboarded pipelines found.")
        return Enum("Pipeline", {}), {}

    pipelines_enum = Enum("Pipeline", {p["id"].upper().replace("-", "_"): p["id"] for p in pipelines_data["items"]}, type=str)

    pipelines_details = {
        pipeline["id"]: {
            "id": pipeline["id"],
            "name": pipeline.get("name", ""),
            "description": pipeline.get("description", ""),
            "api_key": pipeline.get("api_key", config.TEAM_API_KEY),
            "supplier": pipeline.get("supplier", "aiXplain"),
            "version": pipeline.get("version", "1.0"),
            "status": pipeline.get("status", "onboarded"),
            "created_at": pipeline.get("created_at"),
            "architecture": pipeline.get("architecture", {}),
            **pipeline,
        }
        for pipeline in pipelines_data["items"]
    }

    return pipelines_enum, pipelines_details


Pipeline, PipelineDetails = load_pipelines()
