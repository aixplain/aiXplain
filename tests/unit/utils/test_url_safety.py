"""Tests for the central URL trust policy (BUG-939).

Covers the three decisions in ``aixplain.utils.url_safety``: the configured
endpoint policy, the SSRF guard applied to caller/response URLs (including the
redirect re-check), and the presigned upload host allowlist.

No test opens a non-loopback socket: ``socket.getaddrinfo`` is patched so the
resolved-IP blocklist can be exercised deterministically and offline.
"""

import io
import logging
import socket

import pytest
import requests
from urllib3.response import HTTPResponse

from aixplain.utils import url_safety
from aixplain.utils.url_safety import (
    ALLOW_PRIVATE_FETCH_ENV_VAR,
    INSECURE_OPT_IN_ENV_VAR,
    UPLOAD_ALLOWLIST_ENV_VAR,
    UnsafeURLError,
    safe_get,
    validate_config_url,
    validate_fetch_url,
    validate_upload_url,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Run every test with the security opt-ins off and no remembered warnings."""
    for name in (INSECURE_OPT_IN_ENV_VAR, ALLOW_PRIVATE_FETCH_ENV_VAR, UPLOAD_ALLOWLIST_ENV_VAR):
        monkeypatch.delenv(name, raising=False)
    url_safety._WARNED_CONFIG_HOSTS.clear()
    yield
    url_safety._WARNED_CONFIG_HOSTS.clear()


@pytest.fixture
def resolver(monkeypatch):
    """Patch ``socket.getaddrinfo`` with a host -> addresses mapping.

    Returns a callable that installs the mapping; unknown hosts are treated as
    literal addresses, which is what ``getaddrinfo`` does for an IP host anyway.
    """

    def _install(mapping):
        def fake_getaddrinfo(host, port, *args, **kwargs):
            addresses = mapping.get(host)
            if addresses is None:
                try:
                    socket.inet_pton(socket.AF_INET6 if ":" in host else socket.AF_INET, host)
                except OSError:
                    raise socket.gaierror(8, "nodename nor servname provided")
                addresses = [host]
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, port)) for address in addresses]

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    return _install


# --------------------------------------------------------------------------
# validate_config_url
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://platform-api.aixplain.com",
        "https://dev-platform-api.aixplain.com",
        "https://test-platform-api.aixplain.com",
        "https://models.aixplain.com/api/v2/execute",
        "https://platform-api.aixplain.com/assets/pipeline/execution/run",
    ],
)
def test_real_backends_validate_silently(url, caplog):
    """Production, dev and test endpoints must pass with no warning at all."""
    with caplog.at_level(logging.WARNING, logger="aixplain.utils.url_safety"):
        assert validate_config_url(url, "BACKEND_URL") == url
    assert caplog.records == []


def test_http_config_url_is_rejected_without_opt_in():
    """Plain http would put the API key on the wire, so it fails closed."""
    with pytest.raises(UnsafeURLError) as excinfo:
        validate_config_url("http://platform-api.aixplain.com", "BACKEND_URL")
    assert INSECURE_OPT_IN_ENV_VAR in str(excinfo.value)


@pytest.mark.parametrize("url", ["http://platform-api.aixplain.com", "http://localhost:8000", "http://127.0.0.1:8000"])
def test_http_config_url_is_allowed_with_opt_in(url, monkeypatch):
    """The documented opt-in restores http, which is what local dev needs."""
    monkeypatch.setenv(INSECURE_OPT_IN_ENV_VAR, "1")
    assert validate_config_url(url, "BACKEND_URL") == url


@pytest.mark.parametrize(
    "url",
    [
        "ftp://platform-api.aixplain.com",
        "file:///etc/passwd",
        "https://",
        "https://user:pw@evil.example.com/",
        "not a url",
        "",
    ],
)
def test_structurally_invalid_config_urls_are_rejected(url):
    """Non-http(s) schemes, missing hosts and embedded credentials all fail."""
    with pytest.raises(UnsafeURLError):
        validate_config_url(url, "BACKEND_URL")


def test_foreign_host_warns_exactly_once(caplog):
    """A non-aiXplain host is allowed but warned about, and only once."""
    with caplog.at_level(logging.WARNING, logger="aixplain.utils.url_safety"):
        validate_config_url("https://evil.example.com", "BACKEND_URL")
        validate_config_url("https://evil.example.com/other/path", "BACKEND_URL")
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "evil.example.com" in warnings[0].getMessage()


def test_lookalike_host_is_not_treated_as_aixplain(caplog):
    """``evil-aixplain.com`` must not match the ``aixplain.com`` suffix."""
    with caplog.at_level(logging.WARNING, logger="aixplain.utils.url_safety"):
        validate_config_url("https://evil-aixplain.com", "BACKEND_URL")
    assert len(caplog.records) == 1


def test_loopback_under_opt_in_does_not_warn(caplog, monkeypatch):
    """A local-dev endpoint is obviously not aiXplain; warning about it is noise."""
    monkeypatch.setenv(INSECURE_OPT_IN_ENV_VAR, "1")
    with caplog.at_level(logging.WARNING, logger="aixplain.utils.url_safety"):
        validate_config_url("http://localhost:8000", "BACKEND_URL")
    assert caplog.records == []


# --------------------------------------------------------------------------
# validate_fetch_url
# --------------------------------------------------------------------------


@pytest.mark.parametrize("url", ["file:///etc/passwd", "gopher://x/1", "ftp://example.com/x", "ldap://x/"])
def test_non_http_schemes_are_rejected(url):
    """``validators.url()`` rejects some of these; the guard rejects all of them."""
    with pytest.raises(UnsafeURLError):
        validate_fetch_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8080/x",
        "http://10.0.0.1/",
        "http://172.16.0.1/",
        "http://192.168.1.1/",
        "http://0.0.0.0/",
        "http://[::1]/",
        "http://[fe80::1]/",
    ],
)
def test_private_and_metadata_literals_are_rejected(url, resolver):
    """Exactly the addresses ``validators.url()`` waves through (BUG-939)."""
    resolver({})
    with pytest.raises(UnsafeURLError):
        validate_fetch_url(url)


def test_metadata_hostname_is_rejected(resolver):
    """``metadata.google.internal`` is refused by name, before any resolution."""
    resolver({"metadata.google.internal": ["93.184.216.34"]})
    with pytest.raises(UnsafeURLError):
        validate_fetch_url("http://metadata.google.internal/computeMetadata/v1/")


def test_private_address_behind_a_public_name_is_rejected(resolver):
    """The check is on the resolved address, not on how public the name looks."""
    resolver({"internal.example.com": ["127.0.0.1"]})
    with pytest.raises(UnsafeURLError):
        validate_fetch_url("http://internal.example.com/x")


def test_ipv4_mapped_ipv6_loopback_is_rejected(resolver):
    """``::ffff:127.0.0.1`` is loopback and must be unwrapped before classifying."""
    resolver({"sneaky.example.com": ["::ffff:127.0.0.1"]})
    with pytest.raises(UnsafeURLError):
        validate_fetch_url("http://sneaky.example.com/x")


def test_any_private_answer_rejects_the_whole_host(resolver):
    """A host with one public and one private record cannot be trusted."""
    resolver({"split.example.com": ["93.184.216.34", "192.168.1.5"]})
    with pytest.raises(UnsafeURLError):
        validate_fetch_url("http://split.example.com/x")


def test_unresolvable_host_is_rejected(resolver):
    """A resolver failure must never read as a passed check."""
    resolver({})
    with pytest.raises(UnsafeURLError):
        validate_fetch_url("http://does-not-exist.example/x")


def test_public_host_is_accepted(resolver):
    """The ordinary case still works."""
    resolver({"example.com": ["93.184.216.34"]})
    assert validate_fetch_url("https://example.com/code.py") == "https://example.com/code.py"


def test_private_fetch_opt_in(resolver, monkeypatch):
    """On-prem deployments can re-enable private targets deliberately."""
    monkeypatch.setenv(ALLOW_PRIVATE_FETCH_ENV_VAR, "1")
    resolver({})
    assert validate_fetch_url("http://10.0.0.1/code.py") == "http://10.0.0.1/code.py"


# --------------------------------------------------------------------------
# safe_get
# --------------------------------------------------------------------------


class _RecordingAdapter(requests.adapters.BaseAdapter):
    """Adapter that records every request and replies from a scripted map."""

    def __init__(self, responses):
        """Store the ``url -> (status, headers, body)`` script."""
        super().__init__()
        self.responses = responses
        self.requests = []

    def send(self, request, **kwargs):
        """Record *request* and return the scripted response.

        The body is served through a real ``urllib3`` response so that
        ``iter_content`` -- the path ``safe_get`` uses to bound a download --
        is exercised rather than bypassed.
        """
        self.requests.append(request.url)
        status, headers, body = self.responses[request.url]
        response = requests.Response()
        response.status_code = status
        response.headers.update(headers)
        response.raw = HTTPResponse(
            body=io.BytesIO(body),
            headers=headers,
            status=status,
            preload_content=False,
        )
        response.url = request.url
        response.request = request
        return response

    def close(self):
        """No-op: nothing to release."""


def _session_with(responses):
    """Return a session whose http(s) traffic is served by a recording adapter."""
    adapter = _RecordingAdapter(responses)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session, adapter


def test_safe_get_returns_the_body(resolver):
    """The happy path behaves like ``requests.get``."""
    resolver({"example.com": ["93.184.216.34"]})
    session, _ = _session_with({"https://example.com/code.py": (200, {}, b"def main():\n    pass\n")})
    response = safe_get("https://example.com/code.py", session=session)
    assert response.text.startswith("def main()")


def test_safe_get_passes_a_timeout(resolver):
    """A caller-supplied URL must never be fetched without a bound."""
    resolver({"example.com": ["93.184.216.34"]})
    session, _ = _session_with({"https://example.com/x": (200, {}, b"ok")})
    captured = {}
    original = session.get

    def spy(url, **kwargs):
        captured.update(kwargs)
        return original(url, **kwargs)

    session.get = spy
    safe_get("https://example.com/x", session=session)
    assert captured["timeout"] is not None
    assert captured["allow_redirects"] is False


def test_safe_get_revalidates_redirect_targets(resolver):
    """A public host that redirects to the metadata endpoint is stopped there."""
    resolver({"example.com": ["93.184.216.34"]})
    session, adapter = _session_with(
        {"https://example.com/x": (302, {"Location": "http://169.254.169.254/latest/meta-data/"}, b"")}
    )
    with pytest.raises(UnsafeURLError):
        safe_get("https://example.com/x", session=session)
    # The redirect was never followed onto the wire.
    assert adapter.requests == ["https://example.com/x"]


def test_safe_get_follows_a_safe_redirect(resolver):
    """A redirect to another public host is followed, not blocked."""
    resolver({"example.com": ["93.184.216.34"], "cdn.example.com": ["93.184.216.35"]})
    session, adapter = _session_with(
        {
            "https://example.com/x": (302, {"Location": "https://cdn.example.com/y"}, b""),
            "https://cdn.example.com/y": (200, {}, b"payload"),
        }
    )
    assert safe_get("https://example.com/x", session=session).text == "payload"
    assert adapter.requests == ["https://example.com/x", "https://cdn.example.com/y"]


def test_safe_get_caps_redirects(resolver):
    """A redirect loop terminates instead of spinning."""
    resolver({"example.com": ["93.184.216.34"]})
    session, adapter = _session_with({"https://example.com/x": (302, {"Location": "https://example.com/x"}, b"")})
    with pytest.raises(UnsafeURLError):
        safe_get("https://example.com/x", session=session, max_redirects=2)
    assert len(adapter.requests) == 3


def test_safe_get_enforces_max_bytes(resolver):
    """A hostile endpoint cannot balloon the memory of the fetching process."""
    resolver({"example.com": ["93.184.216.34"]})
    session, _ = _session_with({"https://example.com/big": (200, {}, b"x" * 4096)})
    with pytest.raises(UnsafeURLError):
        safe_get("https://example.com/big", session=session, max_bytes=1024)


# --------------------------------------------------------------------------
# validate_upload_url
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://bucket.s3.amazonaws.com/key?X-Amz-Signature=abc",
        "https://s3.us-east-1.amazonaws.com/bucket/key",
        "https://uploads.aixplain.com/x",
        "https://aixplain.com/x",
    ],
)
def test_expected_upload_hosts_are_allowed(url):
    """The hosts the backend actually hands out keep working."""
    assert validate_upload_url(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example.com/x",
        "https://evil.com/?x=amazonaws.com",
        "https://notamazonaws.com/x",
        "http://bucket.s3.amazonaws.com/x",
        "ftp://bucket.s3.amazonaws.com/x",
    ],
)
def test_foreign_upload_hosts_are_rejected(url):
    """Anything else raises before a single byte is PUT."""
    with pytest.raises(UnsafeURLError):
        validate_upload_url(url)


def test_upload_allowlist_env_var_extends_the_defaults(monkeypatch):
    """A custom object store is supported without a fork."""
    monkeypatch.setenv(UPLOAD_ALLOWLIST_ENV_VAR, "storage.example.com, *.cdn.example.org")
    assert validate_upload_url("https://storage.example.com/x")
    assert validate_upload_url("https://a.cdn.example.org/x")
    with pytest.raises(UnsafeURLError):
        validate_upload_url("https://other.example.com/x")
