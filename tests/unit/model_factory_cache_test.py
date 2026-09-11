"""Tests for ModelFactory.get's use of the shared asset cache (BUG-940).

These exercise the getter rather than the cache: the cache-key form, what the
cold path does to entries it did not fetch, and what happens when the bulk
listing is unhealthy. All requests are mocked, and any real HTTP is an error.
"""

import contextlib
import json
import sys
import time
from unittest.mock import patch

import pytest
import requests

from aixplain.modules.model import Model
from aixplain.utils.asset_cache import AssetCache

SLUG_ID = "aixplain/openai/gpt-4o-mini/openai"


def model_payload(model_id):
    """A minimal backend model response."""
    return {
        "id": model_id,
        "name": f"model {model_id}",
        "description": "",
        "supplier": {"id": 1, "name": "aixplain", "code": "aixplain"},
        "version": {"id": "1.0"},
        "function": {"id": "text-generation"},
        "pricing": {"price": 0},
        "status": "onboarded",
        "params": [],
    }


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload, self.status_code = payload, status_code

    def json(self):
        return json.loads(json.dumps(self._payload))


class FakeBackend:
    """Serves the model endpoints and records every URL requested.

    ``canonical_ids`` mimics a backend that answers a request by slug with the
    model's own id, which is what makes the cache-key form observable.
    """

    def __init__(self, listing=(), paginate_error=None):
        self.listing = list(listing)
        self.paginate_error = paginate_error
        self.calls = []

    def __call__(self, method, url, *args, **kwargs):
        self.calls.append(url)
        if "paginate" in url:
            if self.paginate_error:
                raise self.paginate_error
            return FakeResponse({"items": [model_payload(i) for i in self.listing], "total": len(self.listing)})
        if "?ids=" in url:
            wanted = url.split("?ids=")[1].split("&")[0].split(",")
            return FakeResponse({"items": [model_payload(i) for i in wanted], "total": len(wanted)})
        if "sdk/models/" in url:
            requested = url.rstrip("/").split("sdk/models/")[1].split("?")[0]
            # The backend answers with the canonical, unescaped id.
            return FakeResponse(model_payload(requested.replace("%2F", "/")))
        raise AssertionError(f"unexpected URL: {url}")

    @property
    def paginate_calls(self):
        return [u for u in self.calls if "paginate" in u]

    @property
    def direct_calls(self):
        # "sdk/models/paginate" also starts with "sdk/models/", so exclude it.
        return [u for u in self.calls if "sdk/models/" in u and "paginate" not in u]


@contextlib.contextmanager
def mocked_backend(backend):
    """Patch every imported reference to ``_request_with_retry``.

    Call sites do ``from aixplain.utils.request_utils import
    _request_with_retry``, so each module holds its own reference and patching
    only the source module lets real HTTP through.
    """
    targets = {"aixplain.utils.request_utils"}
    for name, module in list(sys.modules.items()):
        if name.startswith("aixplain") and hasattr(module, "_request_with_retry"):
            targets.add(name)

    def no_network(*args, **kwargs):
        raise AssertionError(f"real HTTP escaped the mock: {args[:2]}")

    with contextlib.ExitStack() as stack:
        for name in targets:
            stack.enter_context(patch(f"{name}._request_with_retry", side_effect=backend))
        stack.enter_context(patch.object(requests.Session, "request", no_network))
        stack.enter_context(patch.object(requests, "request", no_network))
        yield backend


@pytest.fixture
def factory(tmp_path, monkeypatch):
    """Isolate the cache and hand back ModelFactory."""
    monkeypatch.setenv("AIXPLAIN_CACHE_FOLDER", str(tmp_path / "cache"))
    monkeypatch.chdir(tmp_path)
    # config reads the environment at import time, so set the attribute.
    monkeypatch.setattr("aixplain.utils.config.TEAM_API_KEY", "SENTINEL_KEY")
    AssetCache.reset_shared()

    from aixplain.factories import ModelFactory

    yield ModelFactory
    AssetCache.reset_shared()


def test_a_slug_id_hits_the_cache_on_the_second_get(factory):
    """A repeated lookup by slug must not re-issue the request.

    The getter percent-escaped the id before the cache lookup while writes
    keyed on the raw id, so ids containing "/" -- documented model paths such
    as "openai/gpt-4o-mini/openai" -- never hit the cache. Every call refetched
    and rewrote the file under the exclusive lock.
    """
    backend = FakeBackend()
    with mocked_backend(backend):
        first = factory.get(SLUG_ID, use_cache=True)
        after_first = len(backend.direct_calls)
        second = factory.get(SLUG_ID, use_cache=True)

    assert first.id == SLUG_ID and second.id == SLUG_ID
    assert len(backend.direct_calls) == after_first, "the second get must be served from cache"
    assert SLUG_ID in AssetCache.shared(Model), "the entry must be keyed on the unescaped id"


def test_a_slug_id_is_still_escaped_in_the_request_url(factory):
    """Moving the escaping must not send raw slashes as path segments."""
    backend = FakeBackend()
    with mocked_backend(backend):
        factory.get(SLUG_ID, use_cache=False)

    assert backend.direct_calls, "expected a direct fetch"
    assert "%2F" in backend.direct_calls[0]
    assert f"sdk/models/{SLUG_ID}" not in backend.direct_calls[0]


def test_an_expired_store_does_not_clobber_a_populated_cache_file(factory):
    """A long-lived process whose store expired must not wipe the file.

    Expiry only cleared memory, so the next lookup took the cold path, replaced
    the cache with the ~20 models on the first listing page (``add_list``), and
    discarded everything other processes had written since. Reloading on expiry
    and adding additively both have to hold for this to be safe.
    """
    cache = AssetCache.shared(Model)
    cache.add_many([Model(id=f"prior-{i}", api_key="SENTINEL_KEY") for i in range(50)])
    assert len(json.load(open(cache.cache_file, encoding="utf-8"))["data"]) == 50

    # The in-process copy goes stale while the file stays fresh.
    cache.store.expiry = time.time() - 1

    backend = FakeBackend(listing=["page-a", "page-b"])
    with mocked_backend(backend):
        factory.get("prior-7", use_cache=True)

    on_disk = json.load(open(cache.cache_file, encoding="utf-8"))["data"]
    assert "prior-7" in on_disk, "entries this process did not fetch must survive"
    assert len(on_disk) >= 50, f"cache shrank to {len(on_disk)} entries"


def test_a_failing_listing_is_not_retried_on_every_call(factory):
    """When the bulk listing is unhealthy, the direct fetch is still cached.

    The fallback stopped caching, so with use_cache=True and a failing paginate
    every lookup re-issued the failing POST -- with retries -- before its direct
    GET. A 10-tool agent paid that on every build.
    """
    backend = FakeBackend(paginate_error=RuntimeError("paginate 503"))
    with mocked_backend(backend):
        for _ in range(3):
            factory.get("m-9", use_cache=True)

    assert len(backend.paginate_calls) == 1, f"paginate attempted {len(backend.paginate_calls)} times"
    assert len(backend.direct_calls) == 1, f"direct fetch repeated {len(backend.direct_calls)} times"
    assert "m-9" in AssetCache.shared(Model)


def test_use_cache_false_still_writes_nothing_when_the_cache_is_unhealthy(factory):
    """The new fallback caching must not leak into the opt-out path."""
    backend = FakeBackend(paginate_error=RuntimeError("paginate 503"))
    with mocked_backend(backend):
        factory.get("m-9")

    assert not AssetCache.shared(Model).has_valid_cache()
    assert "m-9" not in AssetCache.shared(Model)


def test_an_explicit_api_key_is_not_served_from_another_callers_entry(factory):
    """A cache hit carries the key the current call is authorized with."""
    backend = FakeBackend()
    with mocked_backend(backend):
        factory.get("m-1", use_cache=True)
        other = factory.get("m-1", api_key="OTHER_KEY", use_cache=True)
        mine = factory.get("m-1", use_cache=True)

    assert other.api_key == "OTHER_KEY"
    assert mine.api_key == "SENTINEL_KEY"
