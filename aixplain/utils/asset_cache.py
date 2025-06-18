import os
import logging
import json
import time
from typing import Dict, Optional
from dataclasses import dataclass
from filelock import FileLock

from aixplain.utils import config
from typing import TypeVar, Generic, Type
from typing import List

logger = logging.getLogger(__name__)


T = TypeVar("T")

# Constants
CACHE_FOLDER = ".cache"
CACHE_DURATION = 86400


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
            expiry = int(os.getenv("CACHE_EXPIRY_TIME", CACHE_DURATION))
        except Exception as e:
            logger.warning(
                f"Failed to parse CACHE_EXPIRY_TIME: {e}, "
                f"fallback to default value {CACHE_DURATION}"
            )
            # remove the CACHE_EXPIRY_TIME from the environment variables
            del os.environ["CACHE_EXPIRY_TIME"]
            expiry = CACHE_DURATION

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
                    expiry = cache_data["expiry"]
                    raw_data = cache_data["data"]
                    parsed_data = {
                        k: self.cls.from_dict(v) for k, v in raw_data.items()
                    }

                    self.store = Store(data=parsed_data, expiry=expiry)

                    if self.store.expiry < time.time():
                        logger.warning(f"Cache expired for {self.cls.__name__}")
                        self.invalidate()

                except Exception as e:
                    self.invalidate()
                    logger.warning(f"Failed to load cache data: {e}")

                if self.store.expiry < time.time():
                    logger.warning(
                        f"Cache expired, invalidating cache for {self.cls.__name__}"
                    )
                    self.invalidate()
                    return

    def save(self):

        os.makedirs(CACHE_FOLDER, exist_ok=True)

        with FileLock(self.lock_file):
            with open(self.cache_file, "w") as f:
                data_dict = {}
                for asset_id, asset in self.store.data.items():
                    try:
                        data_dict[asset_id] = serialize(asset)
                    except Exception as e:
                        logger.error(f"Error serializing {asset_id}: {e}")
                serializable_store = {
                    "expiry": self.store.expiry,
                    "data": data_dict,
                }

                json.dump(serializable_store, f, indent=4)

    def get(self, asset_id: str) -> Optional[T]:
        return self.store.data.get(asset_id)

    def add(self, asset: T):
        self.store.data[asset.id] = asset.__dict__
        self.save()

    def add_list(self, assets: List[T]):
        self.store.data = {asset.id: asset for asset in assets}
        self.save()

    def get_all(self) -> List[T]:
        return list(self.store.data.values())

    def has_valid_cache(self) -> bool:
        return self.store.expiry >= time.time() and bool(self.store.data)
    
def serialize(obj):
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (list, tuple, set)):
        return [serialize(o) for o in obj]
    elif isinstance(obj, dict):
        return {str(k): serialize(v) for k, v in obj.items()}
    elif hasattr(obj, "to_dict"):
        return serialize(obj.to_dict())
    elif hasattr(obj, "__dict__"):
        return serialize(vars(obj))
    else:
        return str(obj)

