"""Unit tests for v1 connection reuse in ``_request_with_retry`` (BUG-942 item 3).

``_request_with_retry`` used to build a fresh ``requests.Session`` inside the
per-request function, use it once and drop it (never ``close()``d), so every one
of the ~105 v1 call sites paid a full TLS handshake. A 5-minute v1 job polls ~44
times: ~44 handshakes where keep-alive needs one.

There is no socket here, so the offline proxy for "~1 TLS handshake, not ~100"
is "~1 ``Session``, not ~100" -- a session is what owns the connection pool.
"""

from unittest.mock import Mock, patch

import requests

from aixplain.utils import request_utils
from aixplain.utils.request_utils import _request_with_retry


class TestSessionReuse:
    """One session for the process, reused by every call."""

    def test_module_level_session_exists(self):
        assert isinstance(request_utils._SESSION, requests.Session)

    def test_a_hundred_calls_construct_no_new_session(self):
        """The acceptance criterion: ~1 pooled connection, not ~100."""
        with patch.object(request_utils._SESSION, "request", return_value=Mock()) as request:
            with patch("requests.Session") as session_ctor:
                for index in range(100):
                    _request_with_retry("get", f"https://example.com/poll/{index}")

        assert request.call_count == 100
        session_ctor.assert_not_called()

    def test_every_call_uses_the_same_session_object(self):
        # Session identity, observed through the public entry point.
        seen = []

        def capture(self, **kwargs):
            seen.append(id(self))
            return Mock()

        with patch.object(requests.Session, "request", capture):
            _request_with_retry("get", "https://example.com/a")
            _request_with_retry("get", "https://example.com/b")

        assert len(set(seen)) == 1


class TestRetryConfigPreserved:
    """The change is connection reuse only -- retry behaviour is untouched."""

    def test_https_adapter_carries_the_same_retry_config(self):
        adapter = request_utils._SESSION.get_adapter("https://example.com")

        assert adapter.max_retries.total == 5
        assert adapter.max_retries.backoff_factor == 0.1
        assert set(adapter.max_retries.status_forcelist) == {500, 502, 503, 504}

    def test_method_and_params_are_forwarded_unchanged(self):
        with patch.object(request_utils._SESSION, "request", return_value=Mock()) as request:
            _request_with_retry("post", "https://example.com/x", headers={"a": "b"}, data="payload")

        assert request.call_args.kwargs == {
            "method": "POST",
            "url": "https://example.com/x",
            "headers": {"a": "b"},
            "data": "payload",
        }

    def test_method_is_upper_cased(self):
        with patch.object(request_utils._SESSION, "request", return_value=Mock()) as request:
            _request_with_retry("get", "https://example.com/x")

        assert request.call_args.kwargs["method"] == "GET"

    def test_response_is_returned_unchanged(self):
        sentinel = Mock()

        with patch.object(request_utils._SESSION, "request", return_value=sentinel):
            assert _request_with_retry("get", "https://example.com/x") is sentinel
