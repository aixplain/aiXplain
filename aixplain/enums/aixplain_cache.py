import os
import json
import logging
from datetime import datetime
from enum import Enum
from urllib.parse import urljoin
from typing import Dict, Optional, Tuple, List
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.cache_utils import save_to_cache, load_from_cache, CACHE_FOLDER


class AixplainCache:
    """
    A modular caching system to handle different asset types (Models, Pipelines, Agents).
    This class reduces code repetition and allows easier maintenance.
    """

    def __init__(self, asset_type: str, cache_filename: str):
        """
        Initialize the cache for a given asset type.

        Args:
            asset_type (str): Type of the asset (e.g., "models", "pipelines", "agents").
            cache_filename (str): Filename for storing cached data.
        """
        self.asset_type = asset_type
        self.cache_file = f"{CACHE_FOLDER}/{cache_filename}.json"
        self.lock_file = f"{self.cache_file}.lock"
        os.makedirs(CACHE_FOLDER, exist_ok=True)  # Ensure cache folder exists

    def load_assets(self, cache_expiry: Optional[int] = 86400) -> Tuple[Enum, Dict]:
        """
        Load assets from cache or fetch from backend if not cached.

        Args:
            cache_expiry (int, optional): Expiry time in seconds. Default is 24 hours.

        Returns:
            Tuple[Enum, Dict]: (Enum of asset IDs, Dictionary with asset details)
        """
        cached_data = load_from_cache(self.cache_file, self.lock_file)
        if cached_data is not None:
            return self.parse_assets(cached_data)

        api_key = config.TEAM_API_KEY
        backend_url = config.BACKEND_URL
        url = urljoin(backend_url, f"sdk/{self.asset_type}")
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}

        try:
            response = _request_with_retry("get", url, headers=headers)
            response.raise_for_status()
            assets_data = response.json()
        except Exception as e:
            logging.error(f"Failed to fetch {self.asset_type} from API: {e}")
            return Enum(self.asset_type.capitalize(), {}), {} 

        if "items" not in assets_data:
            return Enum(self.asset_type.capitalize(), {}), {}

        onboarded_assets = [asset for asset in assets_data["items"] if asset.get("status", "").lower() == "onboarded"]

        save_to_cache(self.cache_file, {"items": onboarded_assets}, self.lock_file)

        return self.parse_assets({"items": onboarded_assets})

    def parse_assets(self, assets_data: Dict) -> Tuple[Enum, Dict]:
        """
        Convert asset data into an Enum and dictionary format for easy use.

        Args:
            assets_data (Dict): JSON response with asset list.

        Returns:
            - assets_enum: Enum with asset IDs.
            - assets_details: Dictionary containing all asset parameters.
        """
        if not assets_data["items"]:  # Handle case where no assets are onboarded
            logging.warning(f"No onboarded {self.asset_type} found.")
            return Enum(self.asset_type.capitalize(), {}), {}

        assets_enum = Enum(
            self.asset_type.capitalize(),
            {a["id"].upper().replace("-", "_"): a["id"] for a in assets_data["items"]},
            type=str,
        )

        assets_details = {
            asset["id"]: {
                "id": asset["id"],
                "name": asset.get("name", ""),
                "description": asset.get("description", ""),
                "api_key": asset.get("api_key", config.TEAM_API_KEY),
                "supplier": asset.get("supplier", "aiXplain"),
                "version": asset.get("version", "1.0"),
                "status": asset.get("status", "onboarded"),
                "created_at": asset.get("created_at", ""),
                **asset,  # Include any extra fields
            }
            for asset in assets_data["items"]
        }

        return assets_enum, assets_details


ModelCache = AixplainCache("models", "models")
Model, ModelDetails = ModelCache.load_assets()

PipelineCache = AixplainCache("pipelines", "pipelines")
Pipeline, PipelineDetails = PipelineCache.load_assets()

AgentCache = AixplainCache("agents", "agents")
Agent, AgentDetails = AgentCache.load_assets()
