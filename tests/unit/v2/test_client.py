"""Unit tests for the v2 HTTP client layer.

This module tests the foundational HTTP client that all API calls go through.
Covers: initialization, headers, retry logic, request handling, and error parsing.
"""

import pytest
from unittest.mock import Mock, patch
import requests
from requests.adapters import HTTPAdapter

from aixplain.v2.client import (
    AixplainClient,
    create_retry_session,
    DEFAULT_RETRY_TOTAL,
    DEFAULT_TIMEOUT_CONNECT,
    DEFAULT_TIMEOUT_READ,
    DEFAULT_RETRY_BACKOFF_FACTOR,
    DEFAULT_RETRY_STATUS_FORCELIST,
    RETRY_ALLOWED_METHODS,
)
from aixplain.v2.exceptions import APIError


class TestRetrySessionConstants:
    """Tests for retry configuration default constants."""

    def test_default_retry_total_value(self):
        """DEFAULT_RETRY_TOTAL should be a reasonable positive integer."""
        assert DEFAULT_RETRY_TOTAL == 5

    def test_default_backoff_factor_value(self):
        """DEFAULT_RETRY_BACKOFF_FACTOR should be a small positive float."""
        assert DEFAULT_RETRY_BACKOFF_FACTOR == 0.1

    def test_default_status_forcelist_contains_server_errors(self):
        """DEFAULT_RETRY_STATUS_FORCELIST should contain 5xx server errors."""
        assert 500 in DEFAULT_RETRY_STATUS_FORCELIST
        assert 502 in DEFAULT_RETRY_STATUS_FORCELIST
        assert 503 in DEFAULT_RETRY_STATUS_FORCELIST
        assert 504 in DEFAULT_RETRY_STATUS_FORCELIST


class TestCreateRetrySession:
    """Tests for the retry session factory."""

    def test_returns_requests_session(self):
        """Should return a requests.Session instance."""
        session = create_retry_session()

        assert isinstance(session, requests.Session)

    def test_mounts_https_adapter(self):
        """Should mount an HTTPAdapter for HTTPS."""
        session = create_retry_session()

        adapter = session.get_adapter("https://example.com")
        assert isinstance(adapter, HTTPAdapter)

    def test_mounts_http_adapter(self):
        """Should mount an HTTPAdapter for HTTP."""
        session = create_retry_session()

        adapter = session.get_adapter("http://example.com")
        assert isinstance(adapter, HTTPAdapter)

    def test_https_adapter_has_retry_strategy(self):
        """HTTPS adapter should have max_retries configured."""
        session = create_retry_session()

        adapter = session.get_adapter("https://example.com")
        # max_retries is the Retry object attached to the adapter
        assert adapter.max_retries is not None
        assert adapter.max_retries.total == DEFAULT_RETRY_TOTAL

    def test_custom_retry_total_applied(self):
        """Custom retry total should be set on the adapter's Retry object."""
        session = create_retry_session(total=10)

        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 10

    def test_custom_backoff_factor_applied(self):
        """Custom backoff factor should be set on the adapter's Retry object."""
        session = create_retry_session(backoff_factor=0.5)

        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.backoff_factor == 0.5

    def test_custom_status_forcelist_applied(self):
        """Custom status forcelist should be set on the adapter's Retry object."""
        custom_list = [500, 503]
        session = create_retry_session(status_forcelist=custom_list)

        adapter = session.get_adapter("https://example.com")
        assert set(adapter.max_retries.status_forcelist) == set(custom_list)

    @pytest.mark.parametrize("url", ["https://example.com", "http://example.com"])
    def test_post_is_never_retried(self, url):
        """POST must not be retried at the transport layer (BUG-1090).

        urllib3 retries on read/connect errors too, so a POST here means a slow
        ``/execute`` gets re-submitted — and re-billed — below the SDK.
        """
        session = create_retry_session()

        adapter = session.get_adapter(url)
        assert "GET" in adapter.max_retries.allowed_methods
        assert "POST" not in adapter.max_retries.allowed_methods
        assert adapter.max_retries.allowed_methods == RETRY_ALLOWED_METHODS

    def test_server_error_retry_is_method_scoped(self):
        """``status_forcelist`` alone does not decide a retry -- the method does.

        Asserting ``allowed_methods`` only pins configuration; this pins the
        urllib3 semantics we depend on, so a future urllib3 that stopped
        consulting ``allowed_methods`` for status retries would fail here.
        """
        session = create_retry_session()
        retry = session.get_adapter("https://example.com").max_retries

        assert retry.is_retry("GET", 503) is True
        assert retry.is_retry("POST", 503) is False


class TestTransportRetryBehaviour:
    """End-to-end urllib3 behaviour for the BUG-1090 acceptance criteria.

    These drive the real ``Retry`` machinery with the wire faulted out, because
    the defect was urllib3 silently re-sending a POST *below* the SDK -- a
    behaviour no assertion about ``allowed_methods`` can prove on its own.
    """

    @staticmethod
    def _timeout_session(**kwargs):
        """Session whose every wire attempt raises ReadTimeoutError, plus a counter."""
        from urllib3.exceptions import ReadTimeoutError

        session = create_retry_session(**kwargs)
        attempts = []

        def fail(self, conn, method, url, **_):
            attempts.append((method, url))
            raise ReadTimeoutError(self, url, "read timed out")

        return session, attempts, patch("urllib3.connectionpool.HTTPSConnectionPool._make_request", fail)

    def test_read_timeout_on_post_sends_exactly_one_request(self):
        """A read timeout on ``/execute`` must produce exactly one submission.

        A slow model exceeding DEFAULT_TIMEOUT_READ used to be retried by
        urllib3, turning one billable run into up to ``total + 1`` (BUG-1090).
        """
        session, attempts, patcher = self._timeout_session()

        with patcher:
            with pytest.raises(requests.exceptions.RequestException):
                session.post("https://example.com/execute", json={"q": "hi"})

        assert len(attempts) == 1, attempts

    def test_read_timeout_on_get_is_still_retried(self):
        """Control case: GET keeps its retries, so the count above is meaningful.

        Without this, a harness that never reached the retry machinery at all
        would make the POST assertion vacuously pass.
        """
        session, attempts, patcher = self._timeout_session(total=2, backoff_factor=0)

        with patcher:
            with pytest.raises(requests.exceptions.RequestException):
                session.get("https://example.com/results/123")

        assert len(attempts) == 3, attempts

    def test_connect_error_on_post_is_still_retried(self):
        """Documents the limit of the ``allowed_methods`` guarantee.

        urllib3 deliberately skips the method check for connect errors, and that
        is safe: no connection means no request bytes and therefore no
        submission to bill. Pinned so nobody reads
        ``RETRY_ALLOWED_METHODS = {"GET"}`` as "urllib3 never re-sends a POST"
        and builds a stronger assumption on top of it.
        """
        from urllib3.exceptions import NewConnectionError

        session = create_retry_session(total=2, backoff_factor=0)
        attempts = []

        def fail(self, conn, method, url, **_):
            attempts.append(method)
            raise NewConnectionError(self.pool or self, "connection refused")

        with patch("urllib3.connectionpool.HTTPSConnectionPool._make_request", fail):
            with pytest.raises(requests.exceptions.RequestException):
                session.post("https://example.com/execute", json={"q": "hi"})

        assert len(attempts) == 3, attempts


class TestAixplainClientInitialization:
    """Tests for client initialization."""

    def test_client_requires_api_key(self):
        """Client must have either aixplain_api_key or team_api_key."""
        with pytest.raises(
            ValueError,
            match="Either `aixplain_api_key` or `team_api_key` should be set",
        ):
            AixplainClient(base_url="https://test.com")

    def test_client_rejects_both_api_keys(self):
        """Client must not accept both API key types simultaneously."""
        with pytest.raises(
            ValueError,
            match="Either `aixplain_api_key` or `team_api_key` should be set",
        ):
            AixplainClient(
                base_url="https://test.com",
                aixplain_api_key="key1",
                team_api_key="key2",
            )

    def test_client_accepts_team_api_key(self):
        """Client should accept team_api_key."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="test_team_key",
        )
        assert client.team_api_key == "test_team_key"
        assert client.aixplain_api_key is None

    def test_client_accepts_aixplain_api_key(self):
        """Client should accept aixplain_api_key."""
        client = AixplainClient(
            base_url="https://test.com",
            aixplain_api_key="test_aixplain_key",
        )
        assert client.aixplain_api_key == "test_aixplain_key"
        assert client.team_api_key is None

    def test_client_stores_base_url(self):
        """Client should store the base URL."""
        client = AixplainClient(
            base_url="https://custom.example.com",
            team_api_key="key",
        )
        assert client.base_url == "https://custom.example.com"

    def test_client_creates_session_with_retry(self):
        """Client should create a session with retry configuration."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="key",
        )
        adapter = client.session.get_adapter("https://example.com")
        assert adapter.max_retries is not None

    def test_client_applies_custom_retry_total(self):
        """Custom retry_total should be applied to the session."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="key",
            retry_total=10,
        )
        adapter = client.session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 10

    def test_client_applies_custom_backoff_factor(self):
        """Custom retry_backoff_factor should be applied to the session."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="key",
            retry_backoff_factor=0.5,
        )
        adapter = client.session.get_adapter("https://example.com")
        assert adapter.max_retries.backoff_factor == 0.5

    def test_client_applies_custom_status_forcelist(self):
        """Custom retry_status_forcelist should be applied to the session."""
        custom_list = [500, 503]
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="key",
            retry_status_forcelist=custom_list,
        )
        adapter = client.session.get_adapter("https://example.com")
        assert set(adapter.max_retries.status_forcelist) == set(custom_list)


class TestAixplainClientHeaders:
    """Tests for client header configuration."""

    def test_team_api_key_sent_per_request(self):
        """team_api_key should be injected per request, not pinned to the session.

        Session headers ride along with every absolute URL handed to the client,
        which is how the key used to reach body-supplied hosts (BUG-937).
        """
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="my_team_key",
        )
        assert client.session.headers.get("x-api-key") is None

        mock_response = Mock()
        mock_response.ok = True
        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("GET", "resource")

        assert mock_request.call_args[1]["headers"]["x-api-key"] == "my_team_key"

    def test_aixplain_api_key_sent_per_request(self):
        """aixplain_api_key should be injected per request, not pinned to the session."""
        client = AixplainClient(
            base_url="https://test.com",
            aixplain_api_key="my_aixplain_key",
        )
        assert client.session.headers.get("x-aixplain-key") is None

        mock_response = Mock()
        mock_response.ok = True
        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("GET", "resource")

        assert mock_request.call_args[1]["headers"]["x-aixplain-key"] == "my_aixplain_key"

    def test_content_type_header_set(self):
        """Client should set Content-Type: application/json."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="key",
        )
        assert client.session.headers.get("Content-Type") == "application/json"

    def test_team_key_does_not_set_aixplain_header(self):
        """team_api_key should not produce an x-aixplain-key header."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="my_team_key",
        )
        assert "x-aixplain-key" not in client._auth_headers()

    def test_aixplain_key_does_not_set_team_header(self):
        """aixplain_api_key should not produce an x-api-key header."""
        client = AixplainClient(
            base_url="https://test.com",
            aixplain_api_key="my_aixplain_key",
        )
        assert "x-api-key" not in client._auth_headers()

    def test_caller_headers_are_preserved_alongside_credentials(self):
        """Per-request headers should merge with, not replace, the credential."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="my_team_key",
        )

        mock_response = Mock()
        mock_response.ok = True
        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("POST", "resource", headers={"x-agent": "agent-1"})

        headers = mock_request.call_args[1]["headers"]
        assert headers["x-agent"] == "agent-1"
        assert headers["x-api-key"] == "my_team_key"


class TestAixplainClientRequestRaw:
    """Tests for the request_raw method."""

    def test_request_with_relative_path(self):
        """Relative path should be joined with base_url."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"result": "success"}

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("GET", "v2/models")

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["url"] == "https://api.example.com/v2/models"

    def test_request_with_trusted_absolute_url(self):
        """A trusted absolute URL should be used directly, not joined with base_url."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
            trusted_urls=["https://other.example.com"],
        )

        mock_response = Mock()
        mock_response.ok = True

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("GET", "https://other.example.com/resource")

            call_args = mock_request.call_args
            assert call_args[1]["url"] == "https://other.example.com/resource"

    def test_request_with_trusted_http_absolute_url(self):
        """An explicitly configured http endpoint should be used directly."""
        client = AixplainClient(
            base_url="http://local.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("GET", "http://local.example.com/test")

            call_args = mock_request.call_args
            assert call_args[1]["url"] == "http://local.example.com/test"

    def test_request_passes_method_correctly(self):
        """HTTP method should be passed to session.request."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("DELETE", "resource/123")

            call_args = mock_request.call_args
            assert call_args[1]["method"] == "DELETE"

    def test_request_passes_json_kwargs(self):
        """JSON payload should be passed to session.request."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("POST", "resource", json={"key": "value"})

            call_args = mock_request.call_args
            assert call_args[1]["json"] == {"key": "value"}

    def test_request_passes_timeout_kwargs(self):
        """Timeout should be passed to session.request."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("POST", "resource", timeout=30)

            call_args = mock_request.call_args
            assert call_args[1]["timeout"] == 30

    def test_request_returns_response_object(self):
        """Successful request should return the response object."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True
        mock_response.text = "response body"

        with patch.object(client.session, "request", return_value=mock_response):
            response = client.request_raw("GET", "resource")

            assert response is mock_response


class TestAixplainClientErrorHandling:
    """Tests for client error handling."""

    def test_non_ok_response_raises_api_error(self):
        """Failed request should raise APIError with correct status code."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.side_effect = Exception("Not JSON")

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client.request_raw("GET", "resource")

            assert exc_info.value.status_code == 400

    def test_error_extracts_message_from_json(self):
        """APIError message should be extracted from JSON 'message' field."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "message": "Resource not found",
            "error": "NOT_FOUND",
            "statusCode": 404,
        }

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client.request_raw("GET", "resource/123")

            # Message should come from the 'message' field
            assert exc_info.value.message == "Resource not found"
            assert exc_info.value.status_code == 404
            assert exc_info.value.error == "NOT_FOUND"

    def test_error_prefers_supplier_error_detail(self):
        """supplierError carries the actionable detail (e.g. 'Name already exists')
        and must win over the generic 'error' code (e.g. 'err.supplier_error')."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "completed": True,
            "error": "err.supplier_error",
            "supplierError": "Name already exists",
        }

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client.request_raw("GET", "resource")

            assert exc_info.value.message == "Name already exists"
            assert exc_info.value.error == "err.supplier_error"

    def test_error_falls_back_to_error_field(self):
        """When 'message' is absent, should use 'error' field."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "fallback text"
        mock_response.json.return_value = {
            "error": "Internal server error occurred",
            "statusCode": 500,
        }

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client.request_raw("GET", "resource")

            assert exc_info.value.message == "Internal server error occurred"

    def test_error_handles_non_json_response(self):
        """Non-JSON error response should use response.text as message."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 502
        mock_response.text = "Bad Gateway"
        mock_response.json.side_effect = ValueError("No JSON")

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client.request_raw("GET", "resource")

            assert exc_info.value.status_code == 502
            assert exc_info.value.message == "Bad Gateway"
            assert exc_info.value.error == "Bad Gateway"

    def test_error_stores_full_response_data(self):
        """APIError should store the full JSON response in response_data."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        error_response = {
            "message": "Validation failed",
            "errors": [{"field": "name", "message": "required"}],
            "statusCode": 422,
        }
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 422
        mock_response.json.return_value = error_response

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client.request_raw("POST", "resource")

            assert exc_info.value.response_data == error_response

    def test_error_uses_status_code_from_json_over_response(self):
        """statusCode from JSON should be used over response.status_code."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500  # Response status
        mock_response.json.return_value = {
            "message": "Error",
            "statusCode": 422,  # JSON statusCode takes precedence
        }

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(APIError) as exc_info:
                client.request_raw("POST", "resource")

            assert exc_info.value.status_code == 422


class TestAixplainClientRequest:
    """Tests for the request method (JSON wrapper)."""

    def test_request_returns_parsed_json(self):
        """Successful request should return parsed JSON dict."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        expected_data = {"id": "123", "name": "test"}
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = expected_data

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.request("GET", "resource/123")

            assert result == expected_data

    def test_request_calls_request_raw(self):
        """request() should delegate to request_raw()."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {}

        with patch.object(client, "request_raw", return_value=mock_response) as mock_raw:
            client.request("POST", "resource", json={"data": "value"})

            mock_raw.assert_called_once_with("POST", "resource", json={"data": "value"})


class TestAixplainClientGet:
    """Tests for the get method (GET shorthand)."""

    def test_get_calls_request_with_get_method(self):
        """get() should call request() with GET method."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        with patch.object(client, "request", return_value={}) as mock_request:
            client.get("resource/123")

            mock_request.assert_called_once_with("GET", "resource/123")

    def test_get_passes_kwargs_to_request(self):
        """get() should pass kwargs to request()."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        with patch.object(client, "request", return_value={}) as mock_request:
            client.get("resource", params={"filter": "active"})

            mock_request.assert_called_once_with("GET", "resource", params={"filter": "active"})

    def test_get_returns_json_response(self):
        """get() should return the JSON response from request()."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        expected_data = {"data": "value"}
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = expected_data

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.get("resource")

            assert result == expected_data


class TestDefaultTimeout:
    """Every request must carry a timeout: without one, a backend that accepts
    the connection and then goes quiet blocks the calling thread forever
    (observed in production: a LIST_INPUTS POST hung for 938s)."""

    def _client(self, **kwargs):
        return AixplainClient(base_url="https://api.example.com", team_api_key="key", **kwargs)

    def _ok_response(self):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {}
        return mock_response

    def test_default_timeout_applied_to_request_raw(self):
        client = self._client()

        with patch.object(client.session, "request", return_value=self._ok_response()) as mock_request:
            client.request_raw("GET", "v2/models")

        assert mock_request.call_args.kwargs["timeout"] == (DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ)

    def test_default_timeout_applied_to_request_stream(self):
        client = self._client()

        with patch.object(client.session, "request", return_value=self._ok_response()) as mock_request:
            client.request_stream("GET", "v2/models")

        assert mock_request.call_args.kwargs["timeout"] == (DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ)
        assert mock_request.call_args.kwargs["stream"] is True

    def test_per_call_timeout_wins(self):
        """A caller that knows its own bound keeps it."""
        client = self._client()

        with patch.object(client.session, "request", return_value=self._ok_response()) as mock_request:
            client.request_raw("GET", "v2/models", timeout=1.5)

        assert mock_request.call_args.kwargs["timeout"] == 1.5

    def test_constructor_timeout_overrides_default(self):
        client = self._client(timeout=(5.0, 60.0))

        with patch.object(client.session, "request", return_value=self._ok_response()) as mock_request:
            client.request_raw("GET", "v2/models")

        assert mock_request.call_args.kwargs["timeout"] == (5.0, 60.0)

    def test_env_overrides_are_honoured(self, monkeypatch):
        monkeypatch.setenv("AIXPLAIN_HTTP_CONNECT_TIMEOUT", "3")
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", "45.5")

        client = self._client()

        assert client.timeout == (3.0, 45.5)

    @pytest.mark.parametrize("bad", ["abc", "0", "-5", ""])
    def test_unusable_env_values_fall_back_to_defaults(self, bad, monkeypatch):
        """A typo in the knob must not silently remove the bound it configures."""
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", bad)

        client = self._client()

        assert client.timeout == (DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ)
