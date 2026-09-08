"""Tests that the configured endpoint URLs are validated (BUG-939).

``BACKEND_URL``, ``MODELS_RUN_URL`` and ``PIPELINES_RUN_URL`` are read straight
from the environment and decide where the team API key is sent, so both entry
points that resolve them -- importing ``aixplain.utils.config`` and constructing
``Aixplain()`` -- have to apply the policy.

Importing the config module only *warns*: it is on the ``import aixplain`` path,
so raising there would break ``aixplain --help`` and unit test collection on a
machine with no valid environment (BUG-946). The refusal happens instead at the
v1 request choke point, before any socket is opened.
"""

import importlib
import socket

import pytest
import requests

from aixplain.utils import config, request_utils, url_safety
from aixplain.utils.url_safety import INSECURE_OPT_IN_ENV_VAR, UnsafeURLError
from aixplain.v2.core import Aixplain


@pytest.fixture(autouse=True)
def no_remembered_warnings():
    """Clear the once-per-host warning memo so each test sees a fresh state."""
    url_safety._WARNED_CONFIG_HOSTS.clear()
    yield
    url_safety._WARNED_CONFIG_HOSTS.clear()


@pytest.fixture
def reload_config(monkeypatch):
    """Reload ``aixplain.utils.config`` under a chosen ``BACKEND_URL``.

    Restores the module afterwards so the rest of the session is unaffected.
    """
    original = config.BACKEND_URL

    def _reload(backend_url):
        monkeypatch.setenv("BACKEND_URL", backend_url)
        return importlib.reload(config)

    yield _reload

    monkeypatch.setenv("BACKEND_URL", original)
    importlib.reload(config)


def test_import_warns_but_does_not_raise_on_http_backend_url(reload_config, caplog):
    """Importing the config module warns instead of breaking ``import aixplain``."""
    with caplog.at_level("WARNING", logger="aixplain.utils.config"):
        reloaded = reload_config("http://platform-api.aixplain.com")
    assert reloaded.BACKEND_URL == "http://platform-api.aixplain.com"
    assert any("BACKEND_URL must use https" in record.message for record in caplog.records)


def test_a_rejected_backend_url_still_blocks_the_first_request(reload_config, monkeypatch):
    """The deferred failure becomes a refusal before any socket is opened."""

    def explode(*args, **kwargs):
        raise AssertionError("an outbound request was attempted")

    monkeypatch.setattr(requests.Session, "request", explode)
    monkeypatch.setattr(socket, "create_connection", explode)

    reload_config("http://platform-api.aixplain.com")
    with pytest.raises(UnsafeURLError):
        request_utils._request_with_retry("get", "https://platform-api.aixplain.com/sdk/models")


def test_a_valid_backend_url_leaves_requests_alone(reload_config, monkeypatch):
    """The gate is inert once the configured endpoints satisfy the policy."""
    sent = []

    def record(self, method, url, **kwargs):
        sent.append((method, url))
        return "response"

    monkeypatch.setattr(requests.Session, "request", record)
    reload_config("https://platform-api.aixplain.com")
    assert request_utils._request_with_retry("get", "https://platform-api.aixplain.com/x") == "response"
    assert sent == [("GET", "https://platform-api.aixplain.com/x")]


def test_import_accepts_the_dev_backend(reload_config):
    """The dev host must keep working exactly as before."""
    reloaded = reload_config("https://dev-platform-api.aixplain.com")
    assert reloaded.BACKEND_URL == "https://dev-platform-api.aixplain.com"
    assert reloaded.ENV == "dev"


def test_import_accepts_the_test_backend(reload_config):
    """The test host must keep working exactly as before."""
    reloaded = reload_config("https://test-platform-api.aixplain.com")
    assert reloaded.ENV == "test"


def test_import_allows_http_with_the_opt_in(reload_config, monkeypatch):
    """A local backend is supported through the documented opt-in."""
    monkeypatch.setenv(INSECURE_OPT_IN_ENV_VAR, "1")
    reloaded = reload_config("http://localhost:8000")
    assert reloaded.BACKEND_URL == "http://localhost:8000"


def test_aixplain_rejects_an_http_pipeline_url(monkeypatch):
    """``PIPELINES_RUN_URL`` is read nowhere else, so ``Aixplain()`` is its check."""
    monkeypatch.delenv(INSECURE_OPT_IN_ENV_VAR, raising=False)
    with pytest.raises(UnsafeURLError):
        Aixplain(api_key="dummy", pipeline_url="http://evil.example.com/run")


def test_aixplain_rejects_a_non_http_model_url(monkeypatch):
    """A non-http(s) run URL is refused before a client is built."""
    monkeypatch.delenv(INSECURE_OPT_IN_ENV_VAR, raising=False)
    with pytest.raises(UnsafeURLError):
        Aixplain(api_key="dummy", model_url="file:///etc/passwd")


def test_aixplain_accepts_the_production_defaults():
    """The default configuration is unaffected."""
    instance = Aixplain(api_key="dummy")
    assert instance.backend_url.startswith("https://")
    assert instance.model_url.startswith("https://")
    assert instance.pipeline_url.startswith("https://")
