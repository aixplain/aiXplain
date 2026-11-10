"""RLM URL contexts are size-capped before they are loaded into memory (BUG-1452)."""

import io

import pytest
import requests
from urllib3.response import HTTPResponse

from aixplain.utils import url_safety
from aixplain.utils.url_safety import UnsafeURLError
from aixplain.v2 import rlm
from aixplain.v2.rlm import RLM


def _response(body: bytes, headers=None) -> requests.Response:
    headers = headers or {}
    response = requests.Response()
    response.status_code = 200
    response.headers.update(headers)
    response.raw = HTTPResponse(body=io.BytesIO(body), headers=headers, status=200, preload_content=False)
    response.url = "https://example.com/context.txt"
    return response


@pytest.fixture
def fake_get(monkeypatch):
    """Serve one scripted response and skip DNS (the SSRF check has its own tests)."""
    calls = []

    def _install(response):
        def get(url, **kwargs):
            calls.append(kwargs)
            return response

        monkeypatch.setattr(url_safety, "validate_fetch_url", lambda url: url)
        monkeypatch.setattr(url_safety.requests, "get", get)
        return calls

    return _install


def test_oversize_url_context_is_refused(fake_get, monkeypatch):
    monkeypatch.setattr(rlm, "MAX_URL_CONTEXT_BYTES", 1024)
    fake_get(_response(b"x" * 4096))
    with pytest.raises(UnsafeURLError):
        RLM._resolve_url_context("https://example.com/context.txt")


def test_oversize_declared_length_is_refused(fake_get, monkeypatch):
    monkeypatch.setattr(rlm, "MAX_URL_CONTEXT_BYTES", 1024)
    fake_get(_response(b"x" * 10, {"Content-Length": "4096"}))
    with pytest.raises(UnsafeURLError):
        RLM._resolve_url_context("https://example.com/context.txt")


def test_url_context_within_the_cap_is_loaded(fake_get):
    calls = fake_get(_response(b"hello world"))
    assert RLM._resolve_url_context("https://example.com/context.txt") == "hello world"
    assert calls and calls[0]["stream"] is True


def test_json_url_context_within_the_cap_is_parsed(fake_get):
    fake_get(_response(b'{"a": 1}', {"Content-Type": "application/json"}))
    assert RLM._resolve_url_context("https://example.com/context.json") == {"a": 1}


def test_default_cap_is_bounded():
    assert 0 < rlm.MAX_URL_CONTEXT_BYTES <= 100 * 1024 * 1024
