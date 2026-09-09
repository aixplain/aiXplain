"""Asset cache utility module for aiXplain SDK.

This module provides a generic caching system for aiXplain assets (Models, Pipelines,
Agents, etc.) with file-based persistence, automatic serialization, expiration,
and thread-safe operations.

Security notes (BUG-940):
    * The cache lives under the per-user cache directory (``$XDG_CACHE_HOME`` /
      ``~/.cache/aixplain``), never the current working directory. A cache in
      ``$CWD`` leaks into shared CI workspaces and Docker image layers.
    * Cached entries are built from an explicit field allowlist and are additionally
      scrubbed of credential-shaped keys, so the account API key is never written
      to disk. :meth:`AssetCache.get` returns objects whose credential is taken from
      the live configuration instead.
    * Files are written atomically through a private temporary file
      (``0600``) inside a ``0700`` directory, so there is no window in which a
      world-readable or partially written cache file exists.
"""

import copy
import json
import logging
import os
import sys
import tempfile
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar

from filelock import FileLock

logging.getLogger("filelock").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


T = TypeVar("T")

# Constants
CACHE_DURATION = 86400
#: Upper bound on entries kept in a single cache file. Evicted least-recently-used
#: first, so a long-lived process cannot grow the file without limit.
CACHE_MAX_ENTRIES = 1000

#: Permissions for the cache directory and the cache files inside it. The cache
#: holds account-scoped metadata, so it is owner-only.
_DIR_MODE = 0o700
_FILE_MODE = 0o600

#: Keys that must never reach the cache file, at any nesting depth. This is a
#: backstop behind the per-class field allowlist, not a replacement for it.
SENSITIVE_FIELDS = frozenset(
    {
        "api_key",
        "apikey",
        "team_api_key",
        "aixplain_api_key",
        "access_token",
        "refresh_token",
        "token",
        "password",
        "secret",
        "client_secret",
        "authorization",
    }
)

#: Attributes that describe the current environment rather than the asset. Caching
#: them would pin a stale backend URL into a later session.
_ENVIRONMENT_FIELDS = frozenset({"url", "backend_url"})


def default_cache_folder() -> str:
    """Return the directory holding aiXplain cache files.

    Resolution order:
        1. ``$AIXPLAIN_CACHE_FOLDER/aixplain``, when the variable is set.
        2. ``%LOCALAPPDATA%\\aixplain\\cache`` on Windows.
        3. ``$XDG_CACHE_HOME/aixplain``, when ``XDG_CACHE_HOME`` is set.
        4. ``~/.cache/aixplain``.

    Returns:
        str: Absolute path to the cache directory. The directory is not created.

    Note:
        The current working directory is deliberately never used: a cache in
        ``$CWD`` is readable by anything sharing the checkout (CI runners,
        Docker build contexts, co-tenant processes).

        Every branch ends in a directory belonging to the SDK, including the
        override, which gets its own ``aixplain`` subdirectory. That matters
        because :func:`ensure_cache_folder` restricts this directory to its
        owner on every save: pointed straight at ``$HOME``, ``.`` or a shared
        volume, it would strip the group and other bits off a directory the
        user never meant to hand over (BUG-940).
    """
    override = os.getenv("AIXPLAIN_CACHE_FOLDER")
    if override:
        return os.path.join(os.path.abspath(os.path.expanduser(override)), "aixplain")

    if sys.platform == "win32":
        root = os.getenv("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(root, "aixplain", "cache")

    xdg = os.getenv("XDG_CACHE_HOME")
    if xdg:
        return os.path.join(xdg, "aixplain")

    return os.path.join(os.path.expanduser("~"), ".cache", "aixplain")


#: Where releases before this fix wrote the cache: relative to the working
#: directory, world-readable, credential included.
LEGACY_CACHE_FOLDER = ".cache"


def purge_legacy_cwd_cache(cache_filename: str) -> bool:
    """Delete a pre-fix cache file left in the working directory.

    Moving the cache out of ``$CWD`` stops new leaks but does nothing about the
    cleartext credential an earlier release already wrote there, which would
    otherwise sit in the checkout indefinitely. Removing it is part of the fix.

    Args:
        cache_filename (str): Base name of the cache file, e.g. ``"model"``.

    Returns:
        bool: True if a legacy cache file was removed.

    Note:
        Deliberately narrow. It removes only ``.cache/<cache_filename>.json``,
        only after confirming the contents are this cache's own structure, and
        it leaves the ``.cache`` directory itself in place -- other tools use
        that name, and none of their files are ours to delete.
    """
    legacy = os.path.join(LEGACY_CACHE_FOLDER, f"{cache_filename}.json")
    if not os.path.isfile(legacy):
        return False

    try:
        with open(legacy, "r", encoding="utf-8") as f:
            content = json.load(f)
        if not (isinstance(content, dict) and "expiry" in content and "data" in content):
            logger.debug(f"Leaving {legacy} alone: not an aiXplain asset cache")
            return False
    except Exception as e:
        logger.debug(f"Leaving {legacy} alone: could not be read as an asset cache ({e})")
        return False

    try:
        os.remove(legacy)
        logger.warning(
            f"Removed legacy cache {legacy}, which earlier versions wrote to the working "
            "directory with the account API key in cleartext. If it was committed or copied "
            "into an image, rotate the key."
        )
    except OSError as e:
        logger.warning(f"Could not remove legacy cache {legacy}: {e}")
        return False

    legacy_lock = os.path.join(LEGACY_CACHE_FOLDER, f"{cache_filename}.lock")
    if os.path.isfile(legacy_lock):
        try:
            os.remove(legacy_lock)
        except OSError:
            pass
    return True


def ensure_cache_folder(folder: str) -> None:
    """Create ``folder`` and restrict it to its owner.

    Args:
        folder (str): Directory to create.

    Note:
        The mode is applied with an explicit ``chmod`` because ``makedirs``
        masks its ``mode`` through the process umask, and because the directory
        may already exist with looser permissions from an earlier SDK version.
    """
    os.makedirs(folder, exist_ok=True)
    try:
        os.chmod(folder, _DIR_MODE)
    except OSError as e:
        # Windows and some network/overlay filesystems ignore POSIX modes.
        logger.debug(f"Could not set permissions on {folder}: {e}")


def atomic_write_private(path: str, blob: str) -> None:
    """Write ``blob`` to ``path`` atomically, readable only by its owner.

    The content goes to a private temporary file in the destination directory
    and is then moved into place with :func:`os.replace`. Consequently readers
    never see a truncated file, and the file is never world-readable -- not even
    for the instant between ``open`` and ``chmod`` that a plain write would leave
    (BUG-940).

    Args:
        path (str): Destination file path.
        blob (str): Content to write.
    """
    folder = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=folder, prefix=".tmp-", suffix=".json")
    try:
        # mkstemp already creates the file 0600; make it explicit so the
        # guarantee does not rest on the platform's mkstemp semantics.
        #
        # os.fchmod is Unix-only, and an absent attribute raises AttributeError
        # rather than OSError -- which would escape this handler and abort the
        # whole write, so every cache save failed on Windows.
        try:
            if hasattr(os, "fchmod"):
                os.fchmod(fd, _FILE_MODE)
            else:
                os.chmod(tmp_path, _FILE_MODE)
        except (OSError, AttributeError, NotImplementedError) as e:
            # Windows honours only the read-only bit, and some network and
            # overlay filesystems ignore modes entirely. Not fatal: the
            # enclosing directory is already owner-only. AttributeError is
            # caught as well as guarded for, so tightening permissions can
            # never be what stops the cache from being written.
            logger.debug(f"Could not set permissions on {tmp_path}: {e}")

        with os.fdopen(fd, "w", encoding="utf-8") as f:
            fd = -1  # ownership transferred to the file object
            f.write(blob)
            f.flush()
            os.fsync(f.fileno())

        # Rename preserves the temporary file's 0600 mode, so the published file
        # is never world-readable.
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if fd >= 0:
            os.close(fd)
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _isolate(asset: Any, asset_id: str = "") -> Any:
    """Return a copy of ``asset`` sharing no mutable state with the original.

    The cache is a process-wide singleton, so an entry and the object a caller
    holds must never be the same object, and must not share mutable attributes
    (``model_params``, ``additional_info``, ...). Otherwise one consumer's
    in-place edit silently rewrites what every later consumer reads.

    Args:
        asset (Any): The asset to copy.
        asset_id (str, optional): Identifier, for log context only.

    Returns:
        Any: A deep copy, or a shallow copy if the asset cannot be deep-copied.

    Note:
        The shallow fallback is logged at warning, not debug: it does *not*
        deliver isolation, and a silent fallback here is exactly what hid the
        aliasing this function exists to prevent (BUG-940).
    """
    try:
        return copy.deepcopy(asset)
    except Exception as e:
        logger.warning(
            f"Could not deep-copy cached asset {asset_id or type(asset).__name__} ({e}); "
            "falling back to a shallow copy, which leaves mutable attributes shared"
        )
        return copy.copy(asset)


def _max_entries() -> int:
    """Return the configured maximum number of cached entries."""
    try:
        value = int(os.getenv("CACHE_MAX_ENTRIES", CACHE_MAX_ENTRIES))
    except (TypeError, ValueError):
        logger.warning(f"Invalid CACHE_MAX_ENTRIES, falling back to {CACHE_MAX_ENTRIES}")
        return CACHE_MAX_ENTRIES
    return value if value > 0 else CACHE_MAX_ENTRIES


@dataclass
class Store(Generic[T]):
    """A generic data store for cached assets with expiration time.

    This class serves as a container for cached data and its expiration timestamp.
    It is used internally by AssetCache to store the cached assets.

    Attributes:
        data (Dict[str, T]): Dictionary mapping asset IDs to their cached instances.
        expiry (int): Unix timestamp when the cached data expires.
    """

    data: Dict[str, T]
    expiry: int


class AssetCache(Generic[T]):
    """A modular caching system for aiXplain assets with file-based persistence.

    This class provides a generic caching mechanism for different types of assets
    (Models, Pipelines, Agents, etc.) with automatic serialization, expiration,
    and thread-safe file persistence.

    Instances are cheap to reuse and expensive to rebuild -- constructing one reads
    and deserializes the whole cache file -- so callers should obtain them through
    :meth:`shared` rather than instantiating per operation.

    Attributes:
        cls (Type[T]): The class type of assets to be cached.
        cache_folder (str): Directory holding the cache and lock files.
        cache_file (str): Path to the JSON file storing the cached data.
        lock_file (str): Path to the lock file for cross-process exclusion.
        store (Store[T]): The in-memory store containing cached data and expiry.

    Note:
        Cached assets are persisted through an explicit field allowlist
        (``__cache_fields__`` on the asset class, falling back to ``to_dict()``)
        and are rebuilt with ``cls.from_dict()``. Credential-shaped fields are
        never written.
    """

    def __init__(
        self,
        cls: Type[T],
        cache_filename: Optional[str] = None,
        cache_folder: Optional[str] = None,
    ) -> None:
        """Initialize a new AssetCache instance.

        Args:
            cls (Type[T]): The class type of assets to be cached. Must expose a
                ``from_dict`` classmethod.
            cache_filename (Optional[str], optional): Base name for the cache file.
                If None, uses lowercase class name. Defaults to None.
            cache_folder (Optional[str], optional): Directory for the cache file.
                Defaults to :func:`default_cache_folder`.

        Note:
            Constructing a cache never writes to disk; the file appears on the
            first :meth:`add`/:meth:`add_list`/:meth:`save`. This is what lets
            callers that opted out of caching avoid touching the filesystem.
        """
        self.cls = cls
        if cache_filename is None:
            cache_filename = self.cls.__name__.lower()

        self.cache_folder = cache_folder or default_cache_folder()
        self.cache_file = os.path.join(self.cache_folder, f"{cache_filename}.json")
        self.lock_file = os.path.join(self.cache_folder, f"{cache_filename}.lock")

        logger.info(f"Initializing AssetCache for {self.cls.__name__} with cache file: {self.cache_file}")

        # Guards ``store`` and ``_serialized`` against the SDK's own thread pools
        # (e.g. the agent tool-build pool), which share one instance.
        self._lock = threading.RLock()
        # asset_id -> already-serialized payload, so save() never re-walks an
        # object graph it has already converted.
        self._serialized: Dict[str, Any] = {}
        self.store = Store(data=OrderedDict(), expiry=self.compute_expiry())

        # Clean up after releases that cached into the working directory with
        # the credential in cleartext. Best effort, and never fatal.
        try:
            purge_legacy_cwd_cache(cache_filename)
        except Exception as e:  # pragma: no cover - defensive
            logger.debug(f"Legacy cache cleanup skipped: {e}")

        self.load()

    # ------------------------------------------------------------------
    # Shared instances
    # ------------------------------------------------------------------

    _instances: Dict[Tuple[Any, ...], "AssetCache"] = {}
    _instances_lock = threading.Lock()

    @classmethod
    def shared(
        cls,
        asset_cls: Type[T],
        cache_filename: Optional[str] = None,
        cache_folder: Optional[str] = None,
    ) -> "AssetCache":
        """Return a process-wide cache instance for ``asset_cls``.

        Building an ``AssetCache`` loads and deserializes the entire cache file, so
        constructing one per lookup makes every read O(cache size). Callers share a
        single instance instead.

        Args:
            asset_cls (Type[T]): The class type of assets to be cached.
            cache_filename (Optional[str], optional): Base name for the cache file.
            cache_folder (Optional[str], optional): Directory for the cache file.

        Returns:
            AssetCache: A shared instance, created on first use.
        """
        key = (asset_cls, cache_filename, cache_folder or default_cache_folder())
        with cls._instances_lock:
            instance = cls._instances.get(key)
            if instance is None:
                instance = cls(asset_cls, cache_filename, cache_folder)
                cls._instances[key] = instance
            return instance

    @classmethod
    def reset_shared(cls) -> None:
        """Drop all shared instances.

        Intended for tests and for callers that change ``AIXPLAIN_CACHE_FOLDER``
        at runtime.
        """
        with cls._instances_lock:
            cls._instances.clear()

    # ------------------------------------------------------------------
    # Expiry
    # ------------------------------------------------------------------

    def compute_expiry(self) -> int:
        """Calculate the expiration timestamp for cached data.

        Uses CACHE_EXPIRY_TIME environment variable if set, otherwise falls back
        to the default CACHE_DURATION. The expiry is calculated as current time
        plus the duration.

        Returns:
            int: Unix timestamp when the cache will expire.

        Note:
            If CACHE_EXPIRY_TIME is invalid, it will be removed from environment
            variables and the default duration will be used.
        """
        try:
            expiry = int(os.getenv("CACHE_EXPIRY_TIME", CACHE_DURATION))
        except Exception as e:
            logger.warning(f"Failed to parse CACHE_EXPIRY_TIME: {e}, fallback to default value {CACHE_DURATION}")
            # remove the CACHE_EXPIRY_TIME from the environment variables
            os.environ.pop("CACHE_EXPIRY_TIME", None)
            expiry = CACHE_DURATION

        return time.time() + int(expiry)

    def invalidate(self, delete_file: bool = True) -> None:
        """Clear the cache and, by default, remove the cache file.

        Args:
            delete_file (bool, optional): Whether to unlink the cache file as well
                as clearing memory. Defaults to True.

        Note:
            The lock file is deliberately left in place. Unlinking it while the
            lock is held drops mutual exclusion: a second process recreates the
            path and takes ``flock`` on a different inode, so both processes enter
            the critical section and one write is lost (BUG-940).
        """
        logger.info(f"Invalidating cache for {self.cls.__name__}")
        with self._lock:
            self.store = Store(data=OrderedDict(), expiry=self.compute_expiry())
            self._serialized = {}

        if delete_file and os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
                logger.info(f"Removed cache file: {self.cache_file}")
            except OSError as e:
                logger.warning(f"Could not remove cache file {self.cache_file}: {e}")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load cached data from the cache file.

        Reads the cache file (if present) and populates the in-memory store:

        1. Returns early when the file does not exist.
        2. Reads the file under the cross-process lock, then releases it.
        3. Checks expiry *before* deserializing, so an expired cache costs one
           read instead of a full rebuild of every entry.
        4. Rebuilds entries with ``cls.from_dict``, skipping individual
           unreadable entries rather than discarding the whole cache.

        Note:
            Any malformed file -- bad JSON, missing keys, a null expiry, a
            ``data`` that is not a mapping -- clears the in-memory store and
            leaves the file to be overwritten by the next save. Nothing here
            propagates: this runs from ``__init__``, so an exception would make
            every ``AssetCache(...)``/:meth:`shared` call fail until the user
            deleted the file by hand (BUG-940).
        """
        logger.info(f"Loading cache for {self.cls.__name__} from {self.cache_file}")

        if not os.path.exists(self.cache_file):
            logger.info(f"Cache file doesn't exist: {self.cache_file}")
            self.invalidate(delete_file=False)
            return

        try:
            # Hold the lock only for the read itself; deserialization happens
            # outside so a slow rebuild does not block other processes.
            with FileLock(self.lock_file):
                logger.info(f"Acquired file lock for loading: {self.lock_file}")
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

            expiry = cache_data["expiry"]
            raw_data = cache_data["data"]

            # Expiry is checked before any deserialization work.
            if not isinstance(expiry, (int, float)) or expiry < time.time():
                logger.warning(f"Cache expired or unusable for {self.cls.__name__} (expiry: {expiry!r})")
                self.invalidate(delete_file=False)
                return

            if not isinstance(raw_data, dict):
                raise TypeError(f"'data' must be a mapping, got {type(raw_data).__name__}")

            logger.info(f"Found {len(raw_data)} cached items for {self.cls.__name__}")

            parsed_data: "OrderedDict[str, T]" = OrderedDict()
            serialized: Dict[str, Any] = {}
            skipped = 0
            # Keep the most recently written entries when the file exceeds the cap.
            for key, value in list(raw_data.items())[-_max_entries() :]:
                try:
                    parsed_data[key] = self.cls.from_dict(value)
                    serialized[key] = value
                except Exception as e:
                    skipped += 1
                    logger.warning(f"Skipping unreadable cache entry {key} for {self.cls.__name__}: {e}")

            with self._lock:
                self.store = Store(data=parsed_data, expiry=expiry)
                self._serialized = serialized

            if skipped:
                logger.warning(f"Loaded {len(parsed_data)} cached items for {self.cls.__name__}, skipped {skipped}")
            else:
                logger.info(f"Successfully loaded {len(parsed_data)} cached items for {self.cls.__name__}")

        except Exception as e:
            logger.error(f"Failed to load cache data for {self.cls.__name__}: {e}")
            self.invalidate(delete_file=False)

    def save(self, merge: bool = True) -> None:
        """Persist the current cache state to the cache file.

        The payload is serialized to a string *before* the file is touched, then
        written to a private temporary file (``0600``) in the cache directory and
        moved into place with :func:`os.replace`. Consequently:

        * readers never observe a truncated or partially written cache;
        * the file is never world-readable, not even briefly;
        * a serialization failure leaves the previous cache intact.

        Note:
            Failures are logged, not raised -- a cache is best-effort.

        Args:
            merge (bool, optional): Fold in entries other processes added since
                this instance loaded, instead of overwriting them. Defaults to
                True. :meth:`add_list` passes False, since replacing the cache
                wholesale is exactly what it promises.
        """
        with self._lock:
            data = {
                asset_id: self._serialized[asset_id]
                for asset_id in self.store.data
                if asset_id in self._serialized
            }
            expiry = self.store.expiry

        logger.info(f"Saving cache for {self.cls.__name__} with {len(data)} items")

        try:
            ensure_cache_folder(self.cache_folder)
            with FileLock(self.lock_file):
                logger.info(f"Acquired file lock for saving: {self.lock_file}")
                # Read-modify-write, entirely inside the lock.
                merged, merged_expiry = self._merge_with_disk(data, expiry) if merge else (data, expiry)
                # Serialize fully before the file is touched, so a failure here
                # cannot leave a partial file behind.
                blob = json.dumps({"expiry": merged_expiry, "data": merged}, separators=(",", ":"))
                atomic_write_private(self.cache_file, blob)
            logger.info(f"Successfully saved cache for {self.cls.__name__} with {len(merged)} items")
        except Exception as e:
            logger.error(f"Failed to save cache for {self.cls.__name__}: {e}")

    def _merge_with_disk(self, data: Dict[str, Any], expiry: float) -> Tuple[Dict[str, Any], float]:
        """Fold entries added by other processes into ``data``.

        Overwriting the file outright drops every entry another process added
        since this one last loaded. Because this runs under the same lock as the
        write, the read-modify-write is atomic with respect to other SDK
        processes.

        Args:
            data (Dict[str, Any]): This instance's serialized entries.
            expiry (float): This instance's expiry timestamp.

        Returns:
            Tuple[Dict[str, Any], float]: Merged entries (this instance's
                winning on conflict) and the *earlier* of the two expiries.

        Note:
            The earlier expiry is kept deliberately. The merged set contains
            entries from both writers, and taking the later deadline would keep
            serving the older writer's entries past the point it declared them
            stale. Erring early only costs a refetch.
        """
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                on_disk = json.load(f)
            other, other_expiry = on_disk["data"], on_disk["expiry"]
        except (OSError, ValueError, KeyError, TypeError):
            # No readable cache on disk: nothing to merge.
            return data, expiry

        if other_expiry < time.time():
            # Their cache is stale; do not resurrect it.
            return data, expiry

        # Our entries go last so that trimming to the cap drops theirs first.
        merged = {key: value for key, value in other.items() if key not in data}
        merged.update(data)

        limit = _max_entries()
        if len(merged) > limit:
            merged = dict(list(merged.items())[-limit:])

        return merged, min(expiry, other_expiry)

    # ------------------------------------------------------------------
    # Reads and writes
    # ------------------------------------------------------------------

    def get(self, asset_id: str) -> Optional[T]:
        """Retrieve a cached asset by its ID.

        Args:
            asset_id (str): The unique identifier of the asset to retrieve.

        Returns:
            Optional[T]: A deep copy of the cached asset if present, None
                otherwise.

        Note:
            The copy is deep because the instance is shared process-wide. A
            shallow copy would still alias mutable attributes, letting a caller
            that mutates one in place (``additional_info``, say) corrupt what
            every later reader sees. The cost is a fixed ~45us per hit and does
            not grow with the cache.
        """
        with self._lock:
            self._expire_if_needed()
            result = self.store.data.get(asset_id)
            if result is None:
                logger.info(f"Cache miss for {self.cls.__name__} asset: {asset_id}")
                return None
            # Track recency for LRU eviction.
            self._ensure_ordered()
            self.store.data.move_to_end(asset_id)

        logger.info(f"Cache hit for {self.cls.__name__} asset: {asset_id}")
        return _isolate(result, asset_id)

    def _expire_if_needed(self) -> bool:
        """Refresh the store from disk once it has passed its expiry.

        The instance is memoized process-wide, so :meth:`load` -- which is where
        expiry used to be enforced -- no longer runs on every lookup. Without
        this check a long-lived process would keep serving entries forever.

        Expiry then *reloads* rather than only clearing memory. Another process
        has very likely refreshed the file in the meantime, and simply emptying
        the store sent the next lookup down the cold path, which repopulates
        from one page of the account's models and overwrote everything those
        other processes had just written (BUG-940).

        Must be called with ``self._lock`` held.

        Returns:
            bool: True when the store had expired and was refreshed.
        """
        if self.store.data and self.store.expiry < time.time():
            logger.info(f"Cache expired for {self.cls.__name__}; reloading {self.cache_file}")
            self.store = Store(data=OrderedDict(), expiry=self.compute_expiry())
            self._serialized = {}
            # Safe to re-enter: ``_lock`` is an RLock and ``load`` takes the
            # cross-process lock afresh, never nested inside another.
            self.load()
            return True
        return False

    def _ensure_ordered(self) -> None:
        """Normalize the store's mapping to an ``OrderedDict``.

        ``store`` is a public attribute, so a caller may assign a plain dict.
        LRU tracking needs ``move_to_end``/``popitem(last=False)``, which a
        plain dict does not provide.

        Must be called with ``self._lock`` held.
        """
        if not isinstance(self.store.data, OrderedDict):
            self.store.data = OrderedDict(self.store.data)

    def __contains__(self, asset_id: str) -> bool:
        """Return whether ``asset_id`` is cached, without copying the entry.

        Args:
            asset_id (str): The unique identifier to look for.

        Returns:
            bool: True if the asset is present in the cache.
        """
        with self._lock:
            self._expire_if_needed()
            return asset_id in self.store.data

    def add(self, asset: T, save: bool = True, key: Optional[str] = None) -> None:
        """Add a single asset to the cache.

        Args:
            asset (T): The asset instance to cache. Must have an ``id`` attribute.
            save (bool, optional): Whether to persist the cache afterwards.
                Defaults to True.
            key (Optional[str], optional): Cache key to store under. Defaults to
                ``asset.id``. Pass the identifier the caller looked the asset up
                by when that can differ from the asset's own id -- a request by
                slug may be answered with a canonical id, and the next lookup
                will use the slug again.

        Note:
            An isolated copy is stored, so the caller keeps sole ownership of
            the object it passed in. The persisted form is the allowlisted,
            credential-free projection produced by :func:`serialize_asset`.
        """
        logger.info(f"Adding {self.cls.__name__} asset to cache: {key or asset.id}")
        with self._lock:
            self._put(asset, key=key)
        if save:
            self.save()

    def add_many(self, assets: List[T], save: bool = True) -> None:
        """Add several assets to the cache, keeping existing entries.

        Args:
            assets (List[T]): Asset instances to cache.
            save (bool, optional): Whether to persist the cache afterwards.
                Defaults to True.

        Note:
            Unlike :meth:`add_list`, existing entries are preserved. One save
            covers the whole batch.
        """
        logger.info(f"Adding {len(assets)} {self.cls.__name__} assets to cache")
        with self._lock:
            for asset in assets:
                self._put(asset)
        if save:
            self.save()

    def add_list(self, assets: List[T], save: bool = True) -> None:
        """Replace all cached assets with the given list.

        Args:
            assets (List[T]): List of asset instances to cache. Each asset must
                have an ``id`` attribute.
            save (bool, optional): Whether to persist the cache afterwards.
                Defaults to True.
        """
        logger.info(f"Adding {len(assets)} {self.cls.__name__} assets to cache (replacing existing)")
        with self._lock:
            self.store.data = OrderedDict()
            self._serialized = {}
            # A full replacement restarts the TTL. Without this the new file
            # inherits whatever expiry the store happened to hold, which for an
            # already-expired store means writing a file that is dead on
            # arrival (BUG-940).
            self.store.expiry = self.compute_expiry()
            for asset in assets:
                self._put(asset)
        if save:
            # Replacing, not merging: this call defines the whole cache.
            self.save(merge=False)

    def _put(self, asset: T, key: Optional[str] = None) -> None:
        """Insert one asset and evict least-recently-used entries past the cap.

        Must be called with ``self._lock`` held.

        Args:
            asset (T): The asset instance to cache.
            key (Optional[str], optional): Cache key. Defaults to ``asset.id``.
        """
        self._ensure_ordered()
        asset_id = key or asset.id
        try:
            self._serialized[asset_id] = serialize_asset(asset)
        except Exception as e:
            # Keep it in memory; it just will not survive this process.
            logger.error(f"Error serializing {asset_id}: {e}")
            self._serialized.pop(asset_id, None)

        # Store an isolated copy. The instance is shared process-wide, so
        # keeping the caller's object would let whatever the caller does to it
        # next -- ``build_llm`` assigning a temperature, say -- rewrite the
        # entry every later reader sees (BUG-940).
        self.store.data[asset_id] = _isolate(asset, asset_id)
        self.store.data.move_to_end(asset_id)

        limit = _max_entries()
        while len(self.store.data) > limit:
            evicted, _ = self.store.data.popitem(last=False)
            self._serialized.pop(evicted, None)
            logger.info(f"Evicted {self.cls.__name__} cache entry {evicted} (cap {limit})")

    def get_all(self) -> List[T]:
        """Retrieve all cached assets.

        Returns:
            List[T]: List of all cached asset instances. Returns an empty list
                if the cache is empty.
        """
        with self._lock:
            return list(self.store.data.values())

    def has_valid_cache(self) -> bool:
        """Check if the cache is valid and not expired.

        Returns:
            bool: True if the cache has not expired and contains data,
                False otherwise.
        """
        with self._lock:
            self._expire_if_needed()
            is_valid = self.store.expiry >= time.time() and bool(self.store.data)
            count = len(self.store.data)
            expiry = self.store.expiry
        logger.info(
            f"Cache validity check for {self.cls.__name__}: {is_valid} "
            f"(expiry: {expiry}, current: {time.time()}, data count: {count})"
        )
        return is_valid


def serialize_asset(asset: Any) -> Any:
    """Project an asset onto its cacheable, credential-free fields.

    Fields are chosen from the asset class's ``__cache_fields__`` allowlist when
    present, falling back to ``to_dict()`` and finally to the instance
    ``__dict__``.

    Args:
        asset (Any): The asset to project.

    Returns:
        Any: A JSON-serializable dictionary safe to write to disk.

    Note:
        The allowlist is what keeps the account API key -- held as a plain
        instance attribute -- out of the cache file (BUG-940).

        Redaction is applied to this mapping's own keys and nowhere deeper,
        because these are *attribute* names while everything below is data. In
        particular ``input_params``, ``output_params``, ``model_params`` and
        ``additional_info["parameters"]`` are keyed by user-defined parameter
        name, so a tool that legitimately takes a ``url`` or ``token``
        parameter would otherwise have it silently dropped -- and then fail
        validation on the next process, which is worse than the leak this was
        meant to guard against. The credential is a single attribute; excluding
        it by name here is the whole job.
    """
    fields = getattr(type(asset), "__cache_fields__", None)
    if fields:
        raw = {name: getattr(asset, name, None) for name in fields if not _is_redacted(name)}
    elif hasattr(asset, "to_dict"):
        raw = {key: value for key, value in asset.to_dict().items() if not _is_redacted(key)}
    else:
        raw = {key: value for key, value in vars(asset).items() if not _is_redacted(key)}

    return serialize(raw)


def serialize(obj: Any) -> Any:
    """Convert a Python object into a JSON-serializable format.

    This function handles various Python types and converts them to formats
    that can be serialized to JSON. It supports:
    - Basic types (str, int, float, bool, None)
    - Enums (converted to their value)
    - Dates and datetimes (ISO 8601 strings)
    - Collections (list, tuple, set, dict)
    - Objects with to_dict() method
    - Objects with __dict__ attribute
    - Other objects (converted to string)

    Args:
        obj (Any): The Python object to serialize.

    Returns:
        Any: A JSON-serializable version of the input object.

    Note:
        This is a faithful conversion and drops nothing. Choosing what may be
        persisted belongs to :func:`serialize_asset`, which decides it from the
        asset's own attribute names. Filtering by key name during the recursion
        instead cannot tell an attribute from a parameter that merely shares its
        name (BUG-940).
    """
    # Enums first: a member is often also a str, and recursing into its
    # ``__dict__`` would drag in ``__objclass__`` -- i.e. every other member of
    # the enum, which is how a single Model used to serialize to ~20 KB.
    if isinstance(obj, Enum):
        return serialize(obj.value)
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
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


def _is_redacted(key: Any) -> bool:
    """Return True when ``key`` names a credential or environment field.

    Args:
        key (Any): Candidate mapping key or attribute name.

    Returns:
        bool: True if the key must not be persisted.
    """
    if not isinstance(key, str):
        return False
    normalized = key.strip().lower().lstrip("_").replace("-", "_")
    return normalized in SENSITIVE_FIELDS or normalized in _ENVIRONMENT_FIELDS
