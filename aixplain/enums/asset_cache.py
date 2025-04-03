import os
import logging
import json
import time
from enum import Enum
from urllib.parse import urljoin
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from filelock import FileLock

from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.enums.privacy import Privacy
# Constants
CACHE_FOLDER = ".cache"
DEFAULT_CACHE_EXPIRY = 86400

@dataclass
class Asset:
    id: str
    name: str = ""
    description: str = ""
    api_key: str = config.TEAM_API_KEY
    supplier: str = "aiXplain"
    version: str = "1.0"
    status: str = "onboarded"
    created_at: str = ""

class AssetType(Enum):
    MODELS = "models"
    PIPELINES = "pipelines"
    AGENTS = "agents"

def get_cache_expiry():
    return int(os.getenv("CACHE_EXPIRY_TIME", DEFAULT_CACHE_EXPIRY))

def _serialize(obj):
    if isinstance(obj, (Privacy)):
        return str(obj)  # or obj.to_dict() if you have it
    if isinstance(obj, Enum):
        return obj.value
    return obj.__dict__ if hasattr(obj, "__dict__") else str(obj)

class AssetCache:
    """
    A modular caching system to handle different asset types (Models, Pipelines, Agents).
    """

    @staticmethod
    def save_to_cache(cache_file, data, lock_file):
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with FileLock(lock_file):
            with open(cache_file, "w") as f:
                json.dump({"timestamp": time.time(), "data": data}, f,default=_serialize)

    @staticmethod
    def load_from_cache(cache_file, lock_file):
        if os.path.exists(cache_file):
            with FileLock(lock_file):
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    if time.time() - cache_data["timestamp"] < get_cache_expiry():
                        return cache_data["data"]
                    else:
                        try:
                            os.remove(cache_file)
                            if os.path.exists(lock_file):
                                os.remove(lock_file)
                        except Exception as e:
                            logging.warning(f"Failed to remove expired cache or lock file: {e}")
        return None

    @staticmethod
    def fetch_assets_from_backend(asset_type_str: str) -> Optional[Dict]:
        """
        Fetch assets data from the backend API.
        """
        api_key = config.TEAM_API_KEY
        backend_url = config.BACKEND_URL
        url = urljoin(backend_url, f"sdk/{asset_type_str}")
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}

        try:
            response = _request_with_retry("get", url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to fetch {asset_type_str} from API: {e}")
            return None

    def __init__(self, asset_type: AssetType | str, cache_filename: Optional[str] = None):
        if isinstance(asset_type, str):
            asset_type = AssetType(asset_type.lower())
        self.asset_type = asset_type

        filename = cache_filename if cache_filename else self.asset_type.value
        self.cache_file = f"{CACHE_FOLDER}/{filename}.json"
        self.lock_file = f"{self.cache_file}.lock"
        os.makedirs(CACHE_FOLDER, exist_ok=True)

        # Load assets immediately during initialization
        self.assets_enum, self.assets_data = self._initialize_assets()


    def load_assets(self) -> Tuple[Enum, Dict]:
        """
        Load assets from cache or fetch from backend if not cached.
        """
        cached_data = self.load_from_cache(self.cache_file, self.lock_file)
        if cached_data:
            return self.parse_assets(cached_data)

        assets_data = self.fetch_assets_from_backend(self.asset_type.value)
        if not assets_data or "items" not in assets_data:
            return Enum(self.asset_type.name, {}), {}

        onboarded_assets = [
            asset for asset in assets_data["items"] 
            if asset.get("status", "").lower() == "onboarded"
        ]

        self.save_to_cache(self.cache_file, {"items": onboarded_assets}, self.lock_file)

        return self.parse_assets({"items": onboarded_assets})

    def parse_assets(self, assets_data: Dict) -> Tuple[Enum, Dict]:
        """
        Convert asset data into an Enum and dictionary format for easy use.
        """
        if not assets_data["items"]:
            logging.warning(f"No onboarded {self.asset_type.value} found.")
            return Enum(self.asset_type.name, {}), {}

        assets_enum = Enum(
            self.asset_type.name,
            {a["id"].upper().replace("-", "_"): a["id"] for a in assets_data["items"]},
            type=str,
        )

        assets_details = {
            asset["id"]: Asset(
                id=asset["id"],
                name=asset.get("name", ""),
                description=asset.get("description", ""),
                api_key=asset.get("api_key", config.TEAM_API_KEY),
                supplier=asset.get("supplier", "aiXplain"),
                version=asset.get("version", "1.0"),
                status=asset.get("status", "onboarded"),
                created_at=asset.get("created_at", "")
            )
            for asset in assets_data["items"]
        }

        return assets_enum, assets_details
    
    def _initialize_assets(self) -> Tuple[Enum, Dict]:
        cached_data = self.load_from_cache(self.cache_file, self.lock_file)
        if cached_data:
            return self.parse_assets(cached_data)

        assets_data = self.fetch_assets_from_backend(self.asset_type.value)
        if not assets_data or "items" not in assets_data:
            return Enum(self.asset_type.name, {}), {}

        onboarded_assets = [
            asset for asset in assets_data["items"] 
            if asset.get("status", "").lower() == "onboarded"
        ]
        self.save_to_cache(self.cache_file, {"items": onboarded_assets}, self.lock_file)
        return self.parse_assets({"items": onboarded_assets})
