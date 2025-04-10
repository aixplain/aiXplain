import os
import logging
import json
import time
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from filelock import FileLock

from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin
from typing import TypeVar, Generic, Type
from typing import List

logger = logging.getLogger(__name__)


T = TypeVar("T")

# Constants
CACHE_FOLDER = ".cache"
DEFAULT_CACHE_EXPIRY = 86400

@dataclass
class Model:
    id: str
    name: str = ""
    description: str = ""
    api_key: str = config.TEAM_API_KEY
    supplier: str = "aiXplain"
    version: str = "1.0"
    status: str = "onboarded"
    created_at: str = ""

    @classmethod
    def from_dict(cls, data: Dict) -> "Model":
        return cls(**data)

@dataclass
class Store(Generic[T]):
    data: Dict[str, T]
    expiry: int

class AssetCache(Generic[T]):
    """
    A modular caching system to handle different asset types (Models, Pipelines, Agents).
    """

    def __init__(
        self,
        cls: Type[T],
        cache_filename: Optional[str] = None,
    ):
        self.cls = cls
        if cache_filename is None:
            cache_filename = self.cls.__name__.lower()

        # create cache file and lock file name
        self.cache_file = os.path.join(CACHE_FOLDER, f"{cache_filename}.json")
        self.lock_file = os.path.join(CACHE_FOLDER, f"{cache_filename}.lock")
        self.store = Store(data={}, expiry=self.compute_expiry())
        self.load()

        if not os.path.exists(self.cache_file):
            self.save()

    def compute_expiry(self):
        try:
            expiry = int(os.getenv("CACHE_EXPIRY_TIME", DEFAULT_CACHE_EXPIRY))
        except Exception as e:
            logger.warning(
                f"Failed to parse CACHE_EXPIRY_TIME: {e}, "
                f"fallback to default value {DEFAULT_CACHE_EXPIRY}"
            )
            # remove the CACHE_EXPIRY_TIME from the environment variables
            del os.environ["CACHE_EXPIRY_TIME"]
            expiry = DEFAULT_CACHE_EXPIRY

        return time.time() + int(expiry)

    def invalidate(self):
        self.store = Store(data={}, expiry=self.compute_expiry())
        # delete cache file and lock file
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)

    def load(self):
        if not os.path.exists(self.cache_file):
            self.invalidate()
            return

        with FileLock(self.lock_file):
            with open(self.cache_file, "r") as f:
                try:
                    cache_data = json.load(f)
                except Exception as e:
                    # data is corrupted, invalidate the cache
                    self.invalidate()
                    logging.warning(f"Failed to parse cache file: {e}")
                    return

                try:
                    expiry = cache_data["expiry"]
                    raw_data = cache_data["data"]
                    parsed_data = {
                        k: self.cls(
                            id=v.get("id", ""),
                            name=v.get("name", ""),
                            description=v.get("description", ""),
                            api_key=v.get("api_key", config.TEAM_API_KEY),
                            supplier=v.get("supplier", "aiXplain"),
                            version=v.get("version", "1.0"),
                            status=v.get("status", "onboarded"),
                            created_at=v.get("created_at", ""),
                        ) for k, v in raw_data.items()
                    }


                    self.store = Store(data=parsed_data, expiry=expiry)
                except Exception as e:
                    self.invalidate()
                    logging.warning(f"Failed to load cache data: {e}")


                if self.store.expiry < time.time():
                    logger.warning(
                        f"Cache expired, invalidating cache for {self.cls.__name__}"
                    )
                    # cache expired, invalidate the cache
                    self.invalidate()
                    return

    def save(self):
        os.makedirs(CACHE_FOLDER, exist_ok=True)

        with FileLock(self.lock_file):
            with open(self.cache_file, "w") as f:
                # serialize the data manually
                serializable_store = {
                    "expiry": self.compute_expiry(),
                    "data": {
                        asset_id: {
                            "id": model.id,
                            "name": model.name,
                            "description": model.description,
                            "api_key": model.api_key,
                            "supplier": model.supplier,
                            "version": model.version,
                            "created_at": model.created_at.isoformat() if hasattr(model.created_at, "isoformat") else model.created_at,
                        }
                        for asset_id, model in self.store.data.items()
                    },
                }
                json.dump(serializable_store, f)


    def get(self, asset_id: str) -> Optional[T]:
        return self.store.data.get(asset_id)

    def add(self, asset: T):
        self.store.data[asset.id] = asset
        self.save()

    def add_model_list(self, models: List[T]):
        self.store.data = {model.id: model for model in models}
        self.save()

    def get_all_models(self) -> List[T]:
        return list(self.store.data.values())

    def has_valid_cache(self) -> bool:
        return self.store.expiry >= time.time()