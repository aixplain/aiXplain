"""Tests for the asset cache's credential, permission and cost behaviour (BUG-940).

The cache mechanism itself was already covered; what was not covered was
*what* the cache writes, *where*, with *which* permissions, and what it costs
per call. Each test here pins one of those.
"""

import contextlib
import copy
import json
import os
import pickle
import stat
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone

import pytest

from pathlib import Path

from aixplain.enums import AssetStatus, Function
from aixplain.modules.model import Model
from aixplain.modules.model.model_parameters import ModelParameters
from aixplain.utils.asset_cache import (
    AssetCache,
    Store,
    atomic_write_private,
    default_cache_folder,
    purge_legacy_cwd_cache,
    serialize,
    serialize_asset,
)

SENTINEL_KEY = "SUPERSECRET_SENTINEL_0123456789abcdef"
POSIX_ONLY = pytest.mark.skipif(os.name == "nt", reason="POSIX file modes are not meaningful on Windows")


@pytest.fixture
def cache_folder(tmp_path, monkeypatch):
    """Point the cache at an isolated directory and drop shared instances.

    Yields the directory the cache actually uses -- the override gets its own
    ``aixplain`` subdirectory, so that the only directories the SDK tightens
    permissions on are ones it created itself.
    """
    monkeypatch.setenv("AIXPLAIN_CACHE_FOLDER", str(tmp_path / "cacheroot"))
    monkeypatch.delenv("CACHE_EXPIRY_TIME", raising=False)
    monkeypatch.delenv("CACHE_MAX_ENTRIES", raising=False)
    # Keep every test out of any real ``./.cache`` in the working directory.
    monkeypatch.chdir(tmp_path)
    AssetCache.reset_shared()
    yield Path(default_cache_folder())
    AssetCache.reset_shared()


def make_model(model_id="m-1", api_key=SENTINEL_KEY, **kwargs):
    """Build a Model carrying a recognisable credential."""
    kwargs.setdefault("name", f"model {model_id}")
    kwargs.setdefault("function", Function.TEXT_GENERATION)
    return Model(id=model_id, api_key=api_key, **kwargs)


# ----------------------------------------------------------------------
# 1. The credential must never be persisted
# ----------------------------------------------------------------------


def test_saved_cache_never_contains_the_api_key(cache_folder):
    """The account credential must not appear in the cache file."""
    cache = AssetCache(Model)
    cache.add(make_model())

    raw = open(cache.cache_file, encoding="utf-8").read()
    assert SENTINEL_KEY not in raw
    assert "api_key" not in raw


def test_serialize_asset_drops_the_api_key():
    """The persisted projection of a Model excludes api_key."""
    payload = serialize_asset(make_model())

    assert "api_key" not in payload
    assert payload["id"] == "m-1"


@pytest.mark.parametrize(
    "field",
    ["api_key", "token", "password", "secret", "access_token", "refresh_token", "client_secret", "authorization"],
)
def test_serialize_is_faithful_and_does_not_drop_nested_keys(field):
    """``serialize`` converts; it does not decide what may be persisted.

    It used to drop credential-shaped keys at every depth, which silently
    deleted user-defined parameters that happened to share those names. What
    may be persisted is decided from the asset's own attribute names, in
    :func:`serialize_asset`.
    """
    payload = serialize({"outer": {"inner": [{field: "a-parameter-value", "keep": 1}]}})

    assert payload == {"outer": {"inner": [{field: "a-parameter-value", "keep": 1}]}}


def test_serialize_asset_drops_credentials_on_arbitrary_objects():
    """A cached object that is not a Model still has its credential scrubbed."""

    class Holder:
        def __init__(self):
            self.api_key = SENTINEL_KEY
            self.name = "holder"

    assert serialize_asset(Holder()) == {"name": "holder"}


def test_environment_fields_are_not_persisted(cache_folder):
    """Backend URLs describe the session, not the asset, so they are not cached."""
    payload = serialize_asset(make_model())

    assert "url" not in payload
    assert "backend_url" not in payload


def test_cached_model_authenticates_with_the_live_credential(cache_folder):
    """A model rebuilt from cache uses the configured key, not one from disk."""
    cache = AssetCache(Model)
    cache.add(make_model())

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("aixplain.utils.config.TEAM_API_KEY", "ROTATED_KEY")
        AssetCache.reset_shared()
        reloaded = AssetCache(Model).get("m-1")

    assert reloaded.api_key == "ROTATED_KEY"


# ----------------------------------------------------------------------
# 2. Permissions and atomicity
# ----------------------------------------------------------------------


@POSIX_ONLY
def test_cache_file_is_owner_only_and_directory_is_0700(cache_folder):
    """The cache file is 0600 inside a 0700 directory."""
    cache = AssetCache(Model)
    cache.add(make_model())

    assert stat.S_IMODE(os.stat(cache.cache_file).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(cache.cache_folder).st_mode) == 0o700


@POSIX_ONLY
def test_permissions_are_repaired_for_a_directory_left_by_an_older_version(cache_folder):
    """A pre-existing world-readable cache directory is tightened on save."""
    os.makedirs(cache_folder, exist_ok=True)
    os.chmod(cache_folder, 0o755)

    cache = AssetCache(Model)
    cache.add(make_model())

    assert stat.S_IMODE(os.stat(cache.cache_folder).st_mode) == 0o700


@POSIX_ONLY
def test_cache_file_is_never_world_readable_at_any_point(cache_folder):
    """No window exists in which the file is readable by others.

    The write goes to a private temporary file and is renamed into place, so
    every intermediate file observed in the directory is also 0600.
    """
    cache = AssetCache(Model)
    observed = []

    real_replace = os.replace

    def spy(src, dst):
        # Inspect every data-bearing file present in the cache directory
        # mid-write. The filelock lock file is excluded: it is always empty --
        # it carries an advisory lock, not cache content -- and the enclosing
        # 0700 directory already keeps other users out of it.
        folder = os.path.dirname(src) or "."
        for name in os.listdir(folder):
            path = os.path.join(folder, name)
            if os.path.isfile(path) and not name.endswith(".lock"):
                observed.append(stat.S_IMODE(os.stat(path).st_mode))
        return real_replace(src, dst)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("aixplain.utils.asset_cache.os.replace", spy)
        cache.add(make_model())

    assert observed, "expected to observe the temporary file mid-write"
    assert all(mode & 0o077 == 0 for mode in observed), f"group/other bits set: {[oct(m) for m in observed]}"


def test_a_failed_serialization_leaves_the_previous_cache_intact(cache_folder):
    """Serialization happens before the file is touched, so nothing truncates."""
    cache = AssetCache(Model)
    cache.add(make_model("m-1"))
    good = open(cache.cache_file, encoding="utf-8").read()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("aixplain.utils.asset_cache.json.dumps", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
        cache.add(make_model("m-2"))

    assert open(cache.cache_file, encoding="utf-8").read() == good


def test_atomic_write_private_replaces_content_wholesale(tmp_path):
    """atomic_write_private overwrites without leaving temporary files behind."""
    target = tmp_path / "out.json"
    atomic_write_private(str(target), '{"a": 1}')
    atomic_write_private(str(target), '{"b": 2}')

    assert json.loads(target.read_text()) == {"b": 2}
    assert [p.name for p in tmp_path.iterdir()] == ["out.json"]


# ----------------------------------------------------------------------
# 3. Location
# ----------------------------------------------------------------------


def test_cache_folder_is_not_the_working_directory(monkeypatch, tmp_path):
    """The default cache location is the per-user cache dir, never $CWD."""
    monkeypatch.delenv("AIXPLAIN_CACHE_FOLDER", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    monkeypatch.chdir(tmp_path)

    folder = default_cache_folder()

    assert folder == str(tmp_path / "xdg" / "aixplain")
    assert os.path.relpath(folder, tmp_path) != "."
    assert ".cache" not in os.path.relpath(folder, tmp_path).split(os.sep)[:1]


def test_cache_folder_falls_back_to_home_when_xdg_is_unset(monkeypatch, tmp_path):
    """Without XDG_CACHE_HOME the cache lands in ~/.cache/aixplain."""
    monkeypatch.delenv("AIXPLAIN_CACHE_FOLDER", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    monkeypatch.setattr("os.path.expanduser", lambda p: p.replace("~", str(tmp_path)))
    monkeypatch.setattr("aixplain.utils.asset_cache.sys.platform", "linux")

    assert default_cache_folder() == str(tmp_path / ".cache" / "aixplain")


def test_nothing_is_written_into_the_working_directory(cache_folder, tmp_path, monkeypatch):
    """Using the cache leaves the working directory untouched."""
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)

    AssetCache(Model).add(make_model())

    assert list(work.iterdir()) == []


# ----------------------------------------------------------------------
# 4. Constructing a cache must not write
# ----------------------------------------------------------------------


def test_constructing_a_cache_writes_nothing(cache_folder):
    """A cache only touches disk once something is added.

    This is what lets ``ModelFactory.get(..., use_cache=False)`` avoid writing.
    """
    cache = AssetCache(Model)

    assert not os.path.exists(cache.cache_file)


# ----------------------------------------------------------------------
# 5. Locking
# ----------------------------------------------------------------------


def test_invalidate_leaves_the_lock_file_in_place(cache_folder):
    """invalidate() must not unlink the lock it may be running under.

    Unlinking it drops mutual exclusion: another process recreates the path and
    takes flock on a different inode, so both enter the critical section.
    """
    cache = AssetCache(Model)
    cache.add(make_model())
    assert os.path.exists(cache.lock_file)

    cache.invalidate()

    assert not os.path.exists(cache.cache_file), "the data file should be removed"
    assert os.path.exists(cache.lock_file), "the lock file must survive invalidate()"


def test_expiry_does_not_delete_the_lock_file(cache_folder, monkeypatch):
    """Loading an expired cache keeps the lock file."""
    cache = AssetCache(Model)
    cache.add(make_model())
    lock = cache.lock_file

    cache.store.expiry = time.time() - 10
    cache.save()
    AssetCache.reset_shared()
    reloaded = AssetCache(Model)

    assert reloaded.get("m-1") is None, "an expired cache must not serve entries"
    assert os.path.exists(lock)


CONCURRENT_WORKER = textwrap.dedent(
    """
    import os, sys, time
    from filelock import FileLock
    from aixplain.utils.asset_cache import AssetCache
    from aixplain.modules.model import Model

    tag, log = sys.argv[1], sys.argv[2]
    cache = AssetCache(Model)
    for _ in range(12):
        with FileLock(cache.lock_file):
            with open(log, "a") as f:
                f.write(tag + " IN\\n")
            cache.invalidate()
            time.sleep(0.01)
            with open(log, "a") as f:
                f.write(tag + " OUT\\n")
        time.sleep(0.001)
    """
)


@POSIX_ONLY
def test_two_processes_cannot_both_enter_the_critical_section(tmp_path):
    """Mutual exclusion holds across processes even when invalidate() runs inside it."""
    worker = tmp_path / "worker.py"
    worker.write_text(CONCURRENT_WORKER)
    log = tmp_path / "trace.log"

    env = dict(
        os.environ,
        AIXPLAIN_CACHE_FOLDER=str(tmp_path / "cache"),
        CACHE_EXPIRY_TIME="1",
        TEAM_API_KEY=SENTINEL_KEY,
        PYTHONPATH=os.pathsep.join(sys.path),
    )
    procs = [
        subprocess.Popen([sys.executable, str(worker), tag, str(log)], env=env, stderr=subprocess.PIPE)
        for tag in ("A", "B")
    ]
    for proc in procs:
        _, err = proc.communicate(timeout=120)
        assert proc.returncode == 0, err.decode()

    events = [line.split() for line in log.read_text().split("\n") if line.strip()]
    overlaps, holder = 0, None
    for _tag, event in events:
        if event == "IN":
            if holder is not None:
                overlaps += 1
            holder = _tag
        else:
            holder = None

    assert events, "workers produced no trace"
    assert overlaps == 0, f"{overlaps} of {len(events) // 2} critical sections overlapped"


# ----------------------------------------------------------------------
# 6. Cost per call
# ----------------------------------------------------------------------


def test_shared_returns_one_instance_per_asset_class(cache_folder):
    """The shared cache is memoized, so a lookup does not reload the file."""
    assert AssetCache.shared(Model) is AssetCache.shared(Model)


def test_shared_instance_is_not_reloaded_per_call(cache_folder):
    """Repeated shared() calls do not re-read the cache file."""
    AssetCache.shared(Model).add(make_model())
    reads = []

    real_open = open

    def counting_open(path, *a, **k):
        if str(path).endswith("model.json"):
            reads.append(path)
        return real_open(path, *a, **k)

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(__builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__, "open", counting_open)
        for _ in range(10):
            AssetCache.shared(Model).get("m-1")

    assert reads == [], "a cache hit must not read the cache file"


def test_a_cache_hit_does_not_rewrite_the_file(cache_folder):
    """Reads are free: nothing is serialized or written on a hit."""
    cache = AssetCache(Model)
    cache.add(make_model())
    before = os.stat(cache.cache_file).st_mtime_ns

    for _ in range(20):
        cache.get("m-1")

    assert os.stat(cache.cache_file).st_mtime_ns == before


def test_serialization_does_not_expand_enum_members(cache_folder):
    """An Enum serializes to its value, not to its class dictionary.

    Recursing into ``Enum.__objclass__`` pulled in every other member of the
    enum, which is what made a single cached Model ~21 KB.
    """
    payload = serialize_asset(make_model(supplier="aiXplain"))
    encoded = json.dumps(payload)

    assert "__objclass__" not in encoded
    assert "_value_" not in encoded
    assert len(encoded) < 4096, f"entry unexpectedly large: {len(encoded)} bytes"


def test_add_list_writes_once_for_the_whole_batch(cache_folder):
    """Bulk insertion is a single save, not one per asset."""
    cache = AssetCache(Model)
    saves = []

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "aixplain.utils.asset_cache.atomic_write_private",
            lambda path, blob: saves.append(path) or atomic_write_private(path, blob),
        )
        cache.add_list([make_model(f"m-{i}") for i in range(25)])

    assert len(saves) == 1
    assert len(cache.get_all()) == 25


# ----------------------------------------------------------------------
# 7. Size cap and eviction
# ----------------------------------------------------------------------


def test_cache_evicts_least_recently_used_entries_past_the_cap(cache_folder, monkeypatch):
    """The cache is bounded, and drops the least recently used entry first."""
    monkeypatch.setenv("CACHE_MAX_ENTRIES", "3")
    cache = AssetCache(Model)

    for i in range(3):
        cache.add(make_model(f"m-{i}"), save=False)
    cache.get("m-0")  # m-1 is now the least recently used
    cache.add(make_model("m-3"))

    assert sorted(m.id for m in cache.get_all()) == ["m-0", "m-2", "m-3"]
    assert cache.get("m-1") is None


def test_loading_respects_the_size_cap(cache_folder, monkeypatch):
    """A file larger than the cap is truncated to the cap on load."""
    cache = AssetCache(Model)
    cache.add_list([make_model(f"m-{i}") for i in range(10)])

    monkeypatch.setenv("CACHE_MAX_ENTRIES", "4")
    AssetCache.reset_shared()

    assert len(AssetCache(Model).get_all()) == 4


# ----------------------------------------------------------------------
# 8. Robustness
# ----------------------------------------------------------------------


def test_expiry_is_checked_before_entries_are_deserialized(cache_folder, monkeypatch):
    """An expired cache costs a read, not a full rebuild of every entry."""
    cache = AssetCache(Model)
    cache.add_list([make_model(f"m-{i}") for i in range(20)])
    cache.store.expiry = time.time() - 10
    cache.save()

    calls = []
    AssetCache.reset_shared()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Model, "from_dict", classmethod(lambda cls, d: calls.append(d)))
        reloaded = AssetCache(Model)

    assert calls == [], "expired entries must not be deserialized"
    assert reloaded.get_all() == []


def test_one_unreadable_entry_does_not_discard_the_whole_cache(cache_folder):
    """A single corrupt entry is skipped; the rest of the cache survives."""
    cache = AssetCache(Model)
    cache.add_list([make_model("good-1"), make_model("good-2")])

    payload = json.load(open(cache.cache_file, encoding="utf-8"))
    payload["data"]["broken"] = {"id": "broken", "function": "not-a-real-function"}
    open(cache.cache_file, "w", encoding="utf-8").write(json.dumps(payload))

    AssetCache.reset_shared()
    reloaded = AssetCache(Model)

    assert sorted(m.id for m in reloaded.get_all()) == ["good-1", "good-2"]


def test_malformed_cache_file_is_tolerated(cache_folder):
    """Invalid JSON yields an empty cache rather than an exception."""
    os.makedirs(cache_folder, exist_ok=True)
    open(os.path.join(cache_folder, "model.json"), "w").write("{not json")

    assert AssetCache(Model).get_all() == []


def test_get_returns_a_copy_so_callers_cannot_corrupt_the_cache(cache_folder):
    """Mutating a returned model must not change what the cache holds."""
    cache = AssetCache(Model)
    cache.add(make_model())

    cache.get("m-1").name = "mutated"

    assert cache.get("m-1").name != "mutated"


def test_add_stores_the_asset_not_its_dict(cache_folder):
    """In-process readers get the object back, with its concrete type."""
    cache = AssetCache(Model)
    cache.add(make_model())

    assert isinstance(cache.get("m-1"), Model)
    assert isinstance(cache.get_all()[0], Model)


def test_contains_does_not_require_a_copy(cache_folder):
    """Membership can be tested without rebuilding the entry."""
    cache = AssetCache(Model)
    cache.add(make_model())

    assert "m-1" in cache
    assert "absent" not in cache


def test_status_and_datetime_round_trip_through_the_cache(cache_folder):
    """Fields the cache claims to keep survive a reload."""
    created = datetime(2024, 5, 6, 7, 8, 9, tzinfo=timezone.utc)
    cache = AssetCache(Model)
    cache.add(make_model(status=AssetStatus.DRAFT, created_at=created))

    AssetCache.reset_shared()
    reloaded = AssetCache(Model).get("m-1")

    assert reloaded.status == AssetStatus.DRAFT
    assert reloaded.created_at == created


def test_store_accepts_a_plain_dict_for_backwards_compatibility():
    """Store keeps its published shape."""
    store = Store(data={"a": 1}, expiry=123)

    assert store.data == {"a": 1}
    assert store.expiry == 123


def test_a_concurrent_add_by_another_process_is_not_lost(cache_folder):
    """An incremental add merges with the file instead of overwriting it.

    Two instances that both loaded an empty cache used to race, and whichever
    saved last erased the other's entry.
    """
    first = AssetCache(Model)
    second = AssetCache(Model)

    first.add(make_model("from-first"))
    second.add(make_model("from-second"))

    AssetCache.reset_shared()
    on_disk = sorted(json.load(open(second.cache_file, encoding="utf-8"))["data"])
    assert on_disk == ["from-first", "from-second"]


def test_add_list_replaces_rather_than_merging(cache_folder):
    """add_list defines the whole cache, so stale entries do not survive it."""
    cache = AssetCache(Model)
    cache.add(make_model("stale"))

    AssetCache(Model).add_list([make_model("fresh")])

    on_disk = sorted(json.load(open(cache.cache_file, encoding="utf-8"))["data"])
    assert on_disk == ["fresh"]


def test_merge_does_not_resurrect_an_expired_cache(cache_folder, monkeypatch):
    """Entries from an expired file on disk are dropped, not merged in."""
    stale = AssetCache(Model)
    stale.add(make_model("stale"))
    stale.store.expiry = time.time() - 10
    stale.save(merge=False)

    AssetCache.reset_shared()
    fresh = AssetCache(Model)
    fresh.add(make_model("fresh"))

    on_disk = sorted(json.load(open(fresh.cache_file, encoding="utf-8"))["data"])
    assert on_disk == ["fresh"]


def test_in_place_mutation_of_a_returned_model_does_not_corrupt_the_cache(cache_folder):
    """A caller mutating a mutable attribute in place must not affect the cache.

    The shared instance hands the same entry to every caller, so the copy has
    to be deep -- ``Model.add_additional_info_for_benchmark`` mutates
    ``additional_info`` in place.
    """
    cache = AssetCache(Model)
    cache.add(make_model(displayName="original"))

    borrowed = cache.get("m-1")
    borrowed.additional_info["displayName"] = "mutated"

    assert cache.get("m-1").additional_info["displayName"] == "original"


def test_two_callers_receive_independent_objects(cache_folder):
    """Concurrent consumers of one cached entry cannot see each other's edits."""
    cache = AssetCache(Model)
    cache.add(make_model())

    first, second = cache.get("m-1"), cache.get("m-1")
    first.api_key = "KEY_A"
    second.api_key = "KEY_B"

    assert (first.api_key, second.api_key) == ("KEY_A", "KEY_B")
    assert first is not second


def test_a_shared_instance_stops_serving_entries_once_expired(cache_folder, monkeypatch):
    """Expiry is enforced on read, not only when the file is loaded.

    The shared instance is built once per process, so a lookup no longer runs
    load(); without a read-time check an expired entry would be served forever.
    """
    monkeypatch.setenv("CACHE_EXPIRY_TIME", "3600")
    cache = AssetCache.shared(Model)
    cache.add(make_model())
    assert cache.get("m-1") is not None

    # Expire both the store and the file, which is what elapsed time does.
    cache.store.expiry = time.time() - 1
    cache.save(merge=False)
    cache.store.expiry = time.time() - 1

    assert cache.get("m-1") is None
    assert "m-1" not in cache
    assert not cache.has_valid_cache()


# ======================================================================
# Regression tests for the review of 515a133a. Each fails on that commit.
# ======================================================================


class _FchmodAbsent:
    """Context manager removing ``os.fchmod``, as on Windows."""

    def __enter__(self):
        self._saved = os.fchmod
        del os.fchmod

    def __exit__(self, *exc):
        os.fchmod = self._saved


def _raise(exc):
    def _boom(*args, **kwargs):
        raise exc

    return _boom


@pytest.mark.parametrize(
    "label, context",
    [
        ("absent", _FchmodAbsent()),
        ("raises AttributeError", None),  # filled in below; patch needs the module
        ("raises OSError", None),
    ],
)
def test_write_succeeds_when_fchmod_is_unavailable(tmp_path, label, context, monkeypatch):
    """Tightening permissions must never be what prevents the write (BUG-940).

    ``os.fchmod`` is Unix-only, and a missing attribute raises ``AttributeError``
    -- not ``OSError``. That escaped the handler, aborted the write and left
    ``save()`` logging a failure, so every cache write failed on Windows while
    the base branch's plain ``open()`` worked there. CI is Linux-only, so
    nothing caught it.
    """
    if label == "raises AttributeError":
        monkeypatch.setattr(os, "fchmod", _raise(AttributeError("no fchmod")))
        context = contextlib.nullcontext()
    elif label == "raises OSError":
        monkeypatch.setattr(os, "fchmod", _raise(OSError("unsupported")))
        context = contextlib.nullcontext()

    target = tmp_path / "out.json"
    with context:
        atomic_write_private(str(target), '{"a": 1}')

    assert json.loads(target.read_text()) == {"a": 1}
    assert [p.name for p in tmp_path.iterdir()] == ["out.json"], "no temporary file may be left behind"


@POSIX_ONLY
def test_permissions_still_applied_through_the_chmod_fallback(tmp_path):
    """With no ``os.fchmod``, the path-based fallback still yields 0600."""
    target = tmp_path / "out.json"
    with _FchmodAbsent():
        atomic_write_private(str(target), "{}")

    assert stat.S_IMODE(target.stat().st_mode) == 0o600


def test_a_model_carrying_parameters_can_be_deep_copied():
    """``deepcopy`` of a Model with ``model_params`` must not raise.

    ``BaseParameters.__getattr__`` read ``self.parameters``, which misses on the
    attribute-less instance ``copy`` builds before restoring state, re-entering
    ``__getattr__`` until ``RecursionError``. ``get()`` then silently fell back
    to a shallow copy.
    """
    original = make_model(model_params={"temperature": {"required": False}})

    duplicate = copy.deepcopy(original)

    assert duplicate.model_params is not original.model_params
    assert duplicate.id == original.id


def test_base_parameters_survives_pickling():
    """The same defect broke pickling, e.g. across a process pool."""
    params = ModelParameters({"temperature": {"required": False}})

    assert "temperature" in pickle.loads(pickle.dumps(params)).parameters


def test_undefined_parameter_still_raises_attribute_error():
    """The __getattr__ fix must not weaken the error it reports."""
    params = ModelParameters({"temperature": {"required": False}})

    with pytest.raises(AttributeError, match="Parameter 'nope' is not defined"):
        params.nope


def test_isolation_holds_for_a_model_carrying_parameters(cache_folder):
    """Isolation must hold for the models that actually reach the cache.

    The earlier isolation test used a Model without ``model_params``, the one
    shape whose ``deepcopy`` succeeded, so it proved nothing about the case
    that matters.
    """
    cache = AssetCache(Model)
    cache.add(make_model(displayName="original", model_params={"temperature": {"required": False}}))

    borrowed = cache.get("m-1")
    borrowed.additional_info["displayName"] = "mutated"
    borrowed.model_params.temperature = 0.99

    fresh = cache.get("m-1")
    assert fresh.additional_info["displayName"] == "original"
    assert fresh.model_params.parameters["temperature"].value is None


def test_add_does_not_keep_the_callers_object(cache_folder):
    """``add()`` stores a copy, so the caller never holds the cached entry.

    ``ModelFactory.get`` returns the object it just added. On a shared instance
    that handed every later reader an object the first caller was still free to
    mutate -- ``build_llm`` assigns a temperature to it -- so a second agent
    with the same llmId silently inherited the first agent's settings.
    """
    mine = make_model(model_params={"temperature": {"required": False}})
    cache = AssetCache(Model)
    cache.add(mine)

    assert cache.store.data["m-1"] is not mine

    mine.temperature = 0.9  # what build_llm does to the object it was handed
    mine.additional_info["leaked"] = True

    assert getattr(cache.get("m-1"), "temperature", None) != 0.9
    assert "leaked" not in cache.get("m-1").additional_info


@pytest.mark.parametrize(
    "payload",
    [
        '{"expiry": null, "data": {}}',
        '{"expiry": 99999999999, "data": []}',
        '{"expiry": "soon", "data": {}}',
        '{"data": {}}',
        "[]",
        "{not json",
    ],
)
def test_a_malformed_cache_file_never_escapes_construction(cache_folder, payload):
    """A bad cache file must self-heal, not break every caller.

    ``load()`` runs from ``__init__``, and ``agent_factory`` calls
    ``AssetCache.shared(Model)`` outside its own try, so an exception here made
    every ``AgentFactory.get`` with tools fail until the file was deleted by
    hand.
    """
    os.makedirs(cache_folder, exist_ok=True)
    (cache_folder / "model.json").write_text(payload)

    cache = AssetCache.shared(Model)  # must not raise

    assert cache.get_all() == []
    assert not cache.has_valid_cache()


@pytest.mark.parametrize("name", ["url", "token", "password", "secret", "authorization", "backend_url", "api_key"])
def test_a_parameter_named_like_a_credential_is_still_persisted(cache_folder, name):
    """Parameter *names* are data and must survive the credential filter.

    Redacting by key name at every depth also stripped user-defined parameters,
    because ``input_params``/``output_params``/``model_params`` are keyed by
    parameter name. A fetch tool taking a ``url`` was cached without it; next
    process ``ModelTool.validate_parameters`` raised, ``build_tool_safe``
    swallowed it, and the tool disappeared for the whole TTL.
    """
    payload = serialize_asset(
        make_model(
            input_params={"text": {"required": True}, name: {"required": True}},
            model_params={name: {"required": True}},
        )
    )

    assert name in payload["input_params"], f"input parameter {name!r} was dropped"
    assert name in payload["model_params"], f"model parameter {name!r} was dropped"


def test_the_credential_attribute_is_still_excluded(cache_folder):
    """Narrowing redaction must not reintroduce the leak it replaced."""
    payload = serialize_asset(make_model(input_params={"url": {"required": True}}))
    raw = json.dumps(payload)

    assert "api_key" not in payload
    assert SENTINEL_KEY not in raw
    assert payload["input_params"]["url"] == {"required": True}


def test_credential_attributes_are_excluded_without_an_allowlist():
    """Assets with no ``__cache_fields__`` still lose their top-level secrets."""

    class Untyped:
        def __init__(self):
            self.id = "u-1"
            self.api_key = SENTINEL_KEY
            self.backend_url = "https://internal"
            self.params = {"url": "https://example.com"}

    payload = serialize_asset(Untyped())

    assert "api_key" not in payload and "backend_url" not in payload
    assert payload["params"] == {"url": "https://example.com"}, "nested data must be untouched"


def test_an_expired_store_picks_up_another_processes_refresh(cache_folder):
    """An expired store reloads the file instead of discarding it.

    Only clearing memory sent the next lookup down the cold path, which
    repopulates from one page of the account's models and then overwrote
    everything other processes had just written.
    """
    writer = AssetCache(Model)
    writer.add_list([make_model(f"m-{i}") for i in range(300)])

    reader = AssetCache(Model)
    assert len(reader.get_all()) == 300
    reader.store.expiry = time.time() - 1  # the reader's copy goes stale

    # The file is still fresh, so the reader must recover all of it.
    assert reader.get("m-7") is not None
    assert len(reader.get_all()) == 300


def test_add_list_restarts_the_expiry(cache_folder):
    """Replacing the cache wholesale restarts its TTL.

    add_list inherited whatever expiry the store happened to hold, so
    repopulating an already-expired store wrote a file that was dead on
    arrival and could never be read back.
    """
    cache = AssetCache(Model)
    cache.store.expiry = time.time() - 10

    cache.add_list([make_model()])

    assert cache.has_valid_cache()
    assert json.load(open(cache.cache_file, encoding="utf-8"))["expiry"] > time.time()
    AssetCache.reset_shared()
    assert AssetCache(Model).get("m-1") is not None


def test_cache_keys_are_the_unescaped_id(cache_folder):
    """Store, lookup and membership must agree on one key form.

    Lookups percent-escaped the id while every write keyed on the raw id, so a
    slug id never hit the cache -- and prefetch's membership test used the raw
    form, so it also skipped warming ids the getter could never read.
    """
    slug = "aixplain/openai/gpt-4o-mini/openai"
    cache = AssetCache(Model)
    cache.add(make_model(slug))

    assert slug in cache
    assert cache.get(slug) is not None
    assert list(cache.store.data) == [slug], "the key must not be escaped"


def test_add_can_key_on_the_requested_id(cache_folder):
    """A slug request answered with a canonical id is still cached under the slug."""
    cache = AssetCache(Model)
    cache.add(make_model("canonical-123"), key="openai/gpt-4o")

    assert cache.get("openai/gpt-4o") is not None
    assert cache.get("openai/gpt-4o").id == "canonical-123"


def test_override_gets_its_own_subdirectory(monkeypatch, tmp_path):
    """The override is never used verbatim.

    ensure_cache_folder tightens the cache directory on every save, so pointing
    the override at $HOME or a shared volume would strip that directory's group
    and other bits -- and re-strip them after any manual fix.
    """
    shared = tmp_path / "shared_volume"
    shared.mkdir()
    monkeypatch.setenv("AIXPLAIN_CACHE_FOLDER", str(shared))

    folder = default_cache_folder()

    assert folder == str(shared / "aixplain")
    assert folder != str(shared)


@POSIX_ONLY
def test_a_user_directory_named_by_the_override_keeps_its_permissions(monkeypatch, tmp_path):
    """Only the SDK's own subdirectory is tightened, not the directory given."""
    shared = tmp_path / "shared_volume"
    shared.mkdir()
    os.chmod(shared, 0o755)
    monkeypatch.setenv("AIXPLAIN_CACHE_FOLDER", str(shared))
    AssetCache.reset_shared()

    AssetCache(Model).add(make_model())

    assert stat.S_IMODE(shared.stat().st_mode) == 0o755, "the user's directory must be left alone"
    assert stat.S_IMODE((shared / "aixplain").stat().st_mode) == 0o700


def test_legacy_cwd_cache_is_removed(cache_folder, tmp_path):
    """The credential an earlier release leaked into $CWD is cleaned up.

    Relocating the cache stops new leaks but leaves the old cleartext file in
    the checkout, where it stays readable indefinitely.
    """
    legacy_dir = tmp_path / ".cache"
    legacy_dir.mkdir()
    legacy = legacy_dir / "model.json"
    legacy.write_text(json.dumps({"expiry": time.time() + 999, "data": {"m-1": {"id": "m-1", "api_key": SENTINEL_KEY}}}))

    AssetCache.reset_shared()
    AssetCache(Model)

    assert not legacy.exists(), "the legacy cache file must be removed"
    assert legacy_dir.exists(), "the .cache directory itself belongs to other tools too"


@pytest.mark.parametrize(
    "content",
    ['{"unrelated": "tool"}', "not json at all", '{"expiry": 1}'],
)
def test_an_unrelated_cwd_cache_file_is_left_alone(cache_folder, tmp_path, content):
    """Cleanup touches only files that are recognisably this cache's own."""
    legacy_dir = tmp_path / ".cache"
    legacy_dir.mkdir()
    legacy = legacy_dir / "model.json"
    legacy.write_text(content)

    AssetCache.reset_shared()
    AssetCache(Model)

    assert legacy.read_text() == content, "a file we cannot identify as ours must be untouched"


def test_legacy_cleanup_reports_nothing_to_do(cache_folder, tmp_path):
    """With no legacy file the cleanup is a no-op."""
    assert purge_legacy_cwd_cache("model") is False
