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
    DEFAULT_RETRY_BACKOFF_FACTOR,
    DEFAULT_RETRY_STATUS_FORCELIST,
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

    def test_allowed_methods_include_get_and_post(self):
        """Retry should be allowed for GET and POST methods."""
        session = create_retry_session()

        adapter = session.get_adapter("https://example.com")
        assert "GET" in adapter.max_retries.allowed_methods
        assert "POST" in adapter.max_retries.allowed_methods


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

    def test_team_api_key_sets_x_api_key_header(self):
        """team_api_key should set x-api-key header."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="my_team_key",
        )
        assert client.session.headers.get("x-api-key") == "my_team_key"

    def test_aixplain_api_key_sets_x_aixplain_key_header(self):
        """aixplain_api_key should set x-aixplain-key header."""
        client = AixplainClient(
            base_url="https://test.com",
            aixplain_api_key="my_aixplain_key",
        )
        assert client.session.headers.get("x-aixplain-key") == "my_aixplain_key"

    def test_content_type_header_set(self):
        """Client should set Content-Type: application/json."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="key",
        )
        assert client.session.headers.get("Content-Type") == "application/json"

    def test_team_key_does_not_set_aixplain_header(self):
        """team_api_key should not set x-aixplain-key header."""
        client = AixplainClient(
            base_url="https://test.com",
            team_api_key="my_team_key",
        )
        assert client.session.headers.get("x-aixplain-key") is None

    def test_aixplain_key_does_not_set_team_header(self):
        """aixplain_api_key should not set x-api-key header."""
        client = AixplainClient(
            base_url="https://test.com",
            aixplain_api_key="my_aixplain_key",
        )
        assert client.session.headers.get("x-api-key") is None


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

    def test_request_with_absolute_url(self):
        """Absolute URL should be used directly, not joined with base_url."""
        client = AixplainClient(
            base_url="https://api.example.com",
            team_api_key="key",
        )

        mock_response = Mock()
        mock_response.ok = True

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.request_raw("GET", "https://other.example.com/resource")

            call_args = mock_request.call_args
            assert call_args[1]["url"] == "https://other.example.com/resource"

    def test_request_with_http_absolute_url(self):
        """HTTP absolute URLs should also be used directly."""
        client = AixplainClient(
            base_url="https://api.example.com",
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
