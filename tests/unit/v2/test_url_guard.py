"""Unit tests for the v2 trusted-URL policy (BUG-937).

The team API key is workspace-wide, and poll URLs are chosen by response bodies.
These tests pin the rule that decides which URLs may carry that credential:
origin normalization, the allowlist, and credential stripping across redirects.
"""

import pytest
import requests
from unittest.mock import Mock, patch

from aixplain.v2.client import (
    AUTH_HEADER_NAMES,
    AixplainClient,
    TRUSTED_HOSTS_ENV_VAR,
    _AixplainSession,
    build_trusted_origins,
    normalize_origin,
)
from aixplain.v2.exceptions import UntrustedURLError


class _RecordingAdapter(requests.adapters.HTTPAdapter):
    """Transport adapter that answers from a canned map and records what it was sent.

    Used instead of a live server so redirect handling can be exercised end to end
    while still asserting on the exact headers each hop received.
    """

    def __init__(self, responses):
        """Store the ``url -> (status_code, location)`` map."""
        super().__init__()
        self.responses = dict(responses)
        self.sent = []

    def send(self, request, **kwargs):
        """Record the prepared request and return the canned response."""
        self.sent.append(request)
        status_code, location = self.responses[request.url]
        response = requests.Response()
        response.status_code = status_code
        response.url = request.url
        response.request = request
        response.raw = None
        response._content = b"{}"
        if location:
            response.headers["Location"] = location
        return response


class TestNormalizeOrigin:
    """Tests for URL -> (scheme, host, port) normalization."""

    def test_https_default_port_is_explicit(self):
        """An https URL without a port should normalize to port 443."""
        assert normalize_origin("https://platform-api.aixplain.com/x") == (
            "https",
            "platform-api.aixplain.com",
            443,
        )

    def test_explicit_default_port_matches_implicit(self):
        """https://host and https://host:443 should be the same origin."""
        assert normalize_origin("https://host.example.com:443/x") == normalize_origin("https://host.example.com/x")

    def test_http_default_port_is_80(self):
        """An http URL without a port should normalize to port 80."""
        assert normalize_origin("http://localhost/x") == ("http", "localhost", 80)

    def test_host_is_lowercased(self):
        """Host comparison should be case-insensitive."""
        assert normalize_origin("https://Platform-API.AIXPLAIN.com/x") == normalize_origin(
            "https://platform-api.aixplain.com/x"
        )

    def test_userinfo_is_rejected(self):
        """A trusted-looking userinfo prefix must not disguise the real host."""
        assert normalize_origin("https://platform-api.aixplain.com@evil.example.com/x") is None

    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "gopher://evil.example.com/x",
            "ftp://evil.example.com/x",
            "/sdk/runs/abc",
            "",
            "not a url",
        ],
    )
    def test_non_http_or_hostless_urls_are_rejected(self, url):
        """Anything that is not an http(s) URL with a host has no origin."""
        assert normalize_origin(url) is None

    def test_malformed_port_is_rejected(self):
        """A non-numeric port should not raise, just fail to normalize."""
        assert normalize_origin("https://host.example.com:notaport/x") is None

    def test_explicit_zero_port_is_not_the_default_port(self):
        """``:0`` is its own origin, not a spelling of ``:443``."""
        assert normalize_origin("https://host.example.com:0/x") == ("https", "host.example.com", 0)
        assert normalize_origin("https://host.example.com:0/x") != normalize_origin("https://host.example.com/x")


class TestBuildTrustedOrigins:
    """Tests for assembling the allowlist."""

    def test_includes_aixplain_defaults(self):
        """The aiXplain production endpoints are always trusted."""
        origins = build_trusted_origins([])

        assert ("https", "platform-api.aixplain.com", 443) in origins
        assert ("https", "models.aixplain.com", 443) in origins

    def test_includes_configured_urls(self):
        """Configured endpoints join the allowlist."""
        origins = build_trusted_origins(["https://dev-platform-api.aixplain.com/api/v1"])

        assert ("https", "dev-platform-api.aixplain.com", 443) in origins

    def test_bare_host_is_treated_as_https(self):
        """A bare host entry defaults to https, never http."""
        origins = build_trusted_origins(["my-onprem.example.com"])

        assert ("https", "my-onprem.example.com", 443) in origins
        assert ("http", "my-onprem.example.com", 80) not in origins

    def test_env_var_extends_the_set(self, monkeypatch):
        """AIXPLAIN_TRUSTED_HOSTS lets operators add hosts without a code change."""
        monkeypatch.setenv(TRUSTED_HOSTS_ENV_VAR, "my-onprem.example.com, https://other.example.com:8443")
        origins = build_trusted_origins([])

        assert ("https", "my-onprem.example.com", 443) in origins
        assert ("https", "other.example.com", 8443) in origins

    def test_unparseable_env_entries_are_ignored(self, monkeypatch):
        """A bad env entry must not poison the whole allowlist."""
        monkeypatch.setenv(TRUSTED_HOSTS_ENV_VAR, "file:///etc/passwd,,good.example.com")
        origins = build_trusted_origins([])

        assert ("https", "good.example.com", 443) in origins
        assert all(scheme in ("http", "https") for scheme, _, _ in origins)


class TestClientTrustedURLs:
    """Tests for AixplainClient.ensure_trusted_url and is_trusted_url."""

    @pytest.fixture
    def client(self):
        """A client configured exactly the way ``Aixplain.init_client`` configures it."""
        return AixplainClient(
            base_url="https://platform-api.aixplain.com",
            team_api_key="team-key",
            trusted_urls=["https://models.aixplain.com/api/v2/execute"],
        )

    def test_relative_path_resolves_against_base_url(self, client):
        """A relative path is joined with base_url and trusted."""
        assert client.ensure_trusted_url("sdk/runs/abc") == "https://platform-api.aixplain.com/sdk/runs/abc"

    def test_trusted_absolute_url_passes_through(self, client):
        """An absolute URL on a trusted origin is returned unchanged."""
        url = "https://models.aixplain.com/api/v1/data/abc"

        assert client.ensure_trusted_url(url) == url

    @pytest.mark.parametrize(
        "url",
        [
            # The two URLs the bug report reproduced against the old regex.
            "http://evil.example.com/sdk/runs/abc",
            "http://169.254.169.254/api/v1/data/abc",
            # Cloud metadata over https, and the AWS IMDSv2 hostname.
            "https://169.254.169.254/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
            # RFC-1918 and loopback.
            "http://10.0.0.5/sdk/runs/abc",
            "http://192.168.1.10/sdk/runs/abc",
            "http://172.16.0.1/sdk/runs/abc",
            "http://127.0.0.1/sdk/runs/abc",
            "https://localhost/sdk/runs/abc",
            "http://[::1]/sdk/runs/abc",
            # Public host, plausible-looking path.
            "https://evil.example.com/sdk/runs/abc",
            # Trusted host as userinfo on a foreign host.
            "https://platform-api.aixplain.com@evil.example.com/sdk/runs/abc",
            # Trusted name as a subdomain label of an attacker domain.
            "https://platform-api.aixplain.com.evil.example.com/sdk/runs/abc",
            # Non-http schemes.
            "file:///etc/passwd",
        ],
    )
    def test_untrusted_urls_raise(self, client, url):
        """Every URL outside the allowlist must raise before a request is built."""
        with pytest.raises(UntrustedURLError):
            client.ensure_trusted_url(url)

    def test_http_downgrade_of_a_trusted_host_is_rejected(self, client):
        """Scheme is part of the origin: plain http to a trusted host is not trusted."""
        with pytest.raises(UntrustedURLError):
            client.ensure_trusted_url("http://platform-api.aixplain.com/sdk/runs/abc")

    def test_zero_port_on_a_trusted_host_is_rejected(self, client):
        """``:0`` must not inherit the trust of the scheme's default port."""
        with pytest.raises(UntrustedURLError):
            client.ensure_trusted_url("https://platform-api.aixplain.com:0/sdk/runs/abc")

    def test_protocol_relative_path_is_rejected(self, client):
        """``//evil.example.com/x`` only becomes foreign after urljoin, so validate the resolved URL."""
        with pytest.raises(UntrustedURLError):
            client.ensure_trusted_url("//evil.example.com/sdk/runs/abc")

    def test_error_message_names_the_url_and_the_escape_hatch(self, client):
        """The error should be actionable without reading the source."""
        with pytest.raises(UntrustedURLError) as exc_info:
            client.ensure_trusted_url("http://evil.example.com/sdk/runs/abc")

        message = str(exc_info.value)
        assert "evil.example.com" in message
        assert TRUSTED_HOSTS_ENV_VAR in message

    def test_explicitly_configured_localhost_is_trusted(self):
        """Local development against an http backend stays possible."""
        client = AixplainClient(base_url="http://localhost:8000", team_api_key="key")

        assert client.is_trusted_url("http://localhost:8000/sdk/runs/abc")

    def test_other_port_on_a_configured_host_is_not_trusted(self):
        """Port is part of the origin."""
        client = AixplainClient(base_url="http://localhost:8000", team_api_key="key")

        assert not client.is_trusted_url("http://localhost:9999/sdk/runs/abc")

    def test_env_var_hosts_are_trusted_by_the_client(self, monkeypatch):
        """On-prem deployments can extend the set without a code change."""
        monkeypatch.setenv(TRUSTED_HOSTS_ENV_VAR, "my-onprem.example.com")
        client = AixplainClient(base_url="https://platform-api.aixplain.com", team_api_key="key")

        assert client.is_trusted_url("https://my-onprem.example.com/sdk/runs/abc")


class TestClientRefusesUntrustedRequests:
    """The guard must fire before any socket is opened."""

    @pytest.fixture
    def client(self):
        """Client pointed at the production platform API."""
        return AixplainClient(base_url="https://platform-api.aixplain.com", team_api_key="team-key")

    @pytest.mark.parametrize("method_name", ["request_raw", "request_stream"])
    def test_untrusted_url_never_reaches_the_transport(self, client, method_name):
        """Both the plain and the streaming path refuse without sending."""
        adapter = Mock()

        with patch.object(client.session, "get_adapter", return_value=adapter):
            with patch.object(client.session, "request") as mock_request:
                with pytest.raises(UntrustedURLError):
                    getattr(client, method_name)("GET", "http://169.254.169.254/api/v1/data/abc")

        mock_request.assert_not_called()
        adapter.send.assert_not_called()

    def test_get_refuses_untrusted_url(self, client):
        """The convenience wrappers inherit the guard."""
        with patch.object(client.session, "request") as mock_request:
            with pytest.raises(UntrustedURLError):
                client.get("http://evil.example.com/sdk/runs/abc")

        mock_request.assert_not_called()

    def test_credential_never_lands_on_the_session(self, client):
        """A stray absolute URL must not be able to inherit the key from session defaults."""
        for name in AUTH_HEADER_NAMES:
            assert name not in client.session.headers

    def test_streaming_path_still_sends_the_credential(self, client):
        """Moving the key off the session must not leave the SSE path unauthenticated."""
        mock_response = Mock()
        mock_response.ok = True

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_stream("POST", "sdk/agents/abc/run")

        assert mock_request.call_args[1]["headers"]["x-api-key"] == "team-key"

    def test_error_is_importable_from_the_package_root(self):
        """Callers need a public name to catch, not a private module path."""
        import aixplain.v2 as v2

        assert v2.UntrustedURLError is UntrustedURLError


class TestRedirectCredentialStripping:
    """A cross-host 302 must not deliver the credential to the target."""

    @pytest.fixture
    def client(self):
        """Client trusting both aiXplain production endpoints."""
        return AixplainClient(
            base_url="https://platform-api.aixplain.com",
            team_api_key="team-key",
            trusted_urls=["https://models.aixplain.com/api/v2/execute"],
        )

    def test_session_is_redirect_aware(self, client):
        """The client must use the credential-stripping session subclass."""
        assert isinstance(client.session, _AixplainSession)

    def test_allowlist_survives_a_deepcopy_of_the_session(self, client):
        """``BaseResource.clone`` deepcopies resources; a copied session must keep the rule.

        ``requests.Session`` only pickles the names in ``__attrs__``, so without
        carrying ``trusted_origins`` a copy would lose the allowlist entirely and
        ``rebuild_auth`` would raise AttributeError instead of deciding.
        """
        import copy

        copied = copy.deepcopy(client.session)

        assert copied.trusted_origins == client.session.trusted_origins
        assert "x-api-key" not in self._redirect(copied, "https://evil.example.com/x")
        assert self._redirect(copied, "https://models.aixplain.com/x")["x-api-key"] == "team-key"

    def test_a_session_restored_without_init_fails_closed(self):
        """No allowlist attribute must mean "trust nothing", not a crash."""
        bare = _AixplainSession.__new__(_AixplainSession)

        assert bare.trusted_origins == frozenset()

    def _redirect(self, session, location):
        """Run ``rebuild_auth`` the way ``Session.resolve_redirects`` would."""
        prepared = requests.Request(
            method="GET",
            url=location,
            headers={"x-api-key": "team-key", "x-aixplain-key": "other-key", "Accept": "application/json"},
        ).prepare()
        response = Mock(spec=requests.Response)
        response.request = requests.Request(method="GET", url="https://platform-api.aixplain.com/x").prepare()
        session.rebuild_auth(prepared, response)
        return prepared.headers

    def test_credentials_dropped_on_foreign_redirect(self, client):
        """The acceptance criterion: no x-api-key reaches the redirect target."""
        headers = self._redirect(client.session, "https://evil.example.com/x")

        assert "x-api-key" not in headers
        assert "x-aixplain-key" not in headers
        assert headers["Accept"] == "application/json"

    def test_credentials_dropped_on_scheme_downgrade(self, client):
        """A downgrade to http on the same host drops the key too."""
        headers = self._redirect(client.session, "http://platform-api.aixplain.com/x")

        assert "x-api-key" not in headers

    def test_credentials_retained_between_trusted_hosts(self, client):
        """A legitimate platform-api -> models redirect keeps working."""
        headers = self._redirect(client.session, "https://models.aixplain.com/x")

        assert headers["x-api-key"] == "team-key"

    def test_end_to_end_redirect_history_carries_no_credential(self, client):
        """Full requests round trip through the real redirect machinery.

        Exercises ``Session.send`` -> ``resolve_redirects`` -> ``rebuild_auth``
        rather than calling the hook directly, so it would catch the header
        surviving by some path other than the one under test.
        """
        adapter = _RecordingAdapter({"https://evil.example.com/x": (200, None)})
        adapter.responses["https://platform-api.aixplain.com/sdk/runs/abc"] = (302, "https://evil.example.com/x")
        client.session.mount("https://", adapter)

        client.get("sdk/runs/abc")

        first, second = adapter.sent
        assert first.headers["x-api-key"] == "team-key"
        assert "x-api-key" not in second.headers
        assert second.url == "https://evil.example.com/x"
