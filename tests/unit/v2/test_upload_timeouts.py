"""Timeout coverage for the v2 upload path (BUG-938).

``RequestManager.request_with_retry`` is the single dispatch point for both
upload legs (the presigned-URL POST to the backend and the S3 PUT of the file
body).  Without a ``timeout`` ``requests`` waits forever, so a peer that
accepts the connection and then goes silent pins the calling thread with no
upper bound.
"""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from aixplain.v2.client import DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ
from aixplain.v2.exceptions import FileUploadError
from aixplain.v2.upload_utils import FileUploader, RequestManager

# ``blackhole_url`` comes from tests/unit/conftest.py.


def _ok_response():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"key": "uploads/x.csv", "uploadUrl": "https://s3.example.com/x"}
    return response


class TestRequestWithRetryTimeout:
    def test_default_timeout_is_applied(self):
        with patch("requests.Session.request", return_value=_ok_response()) as mock_request:
            RequestManager.request_with_retry("post", "https://api.example.com/x")

        assert mock_request.call_args.kwargs["timeout"] == (DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ)

    def test_explicit_timeout_wins(self):
        """A caller that knows its own bound keeps it."""
        with patch("requests.Session.request", return_value=_ok_response()) as mock_request:
            RequestManager.request_with_retry("post", "https://api.example.com/x", timeout=1.5)

        assert mock_request.call_args.kwargs["timeout"] == 1.5

    def test_env_override_is_honoured(self, monkeypatch):
        monkeypatch.setenv("AIXPLAIN_HTTP_CONNECT_TIMEOUT", "3")
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", "7")

        with patch("requests.Session.request", return_value=_ok_response()) as mock_request:
            RequestManager.request_with_retry("get", "https://api.example.com/x")

        assert mock_request.call_args.kwargs["timeout"] == (3.0, 7.0)

    @pytest.mark.parametrize("bad", ["abc", "0", "-5", ""])
    def test_unusable_env_values_fall_back_to_defaults(self, bad, monkeypatch):
        """A typo in the knob must not silently remove the bound it configures."""
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", bad)

        with patch("requests.Session.request", return_value=_ok_response()) as mock_request:
            RequestManager.request_with_retry("get", "https://api.example.com/x")

        assert mock_request.call_args.kwargs["timeout"] == (DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ)


class TestUploadLegsUseTheDispatcher:
    """Neither upload leg may bypass ``request_with_retry`` and its default."""

    def test_both_legs_go_through_request_with_retry(self, tmp_path):
        file_path = tmp_path / "sample.csv"
        file_path.write_text("a,b\n1,2\n")

        uploader = FileUploader(backend_url="https://api.example.com", api_key="key")

        with patch.object(RequestManager, "request_with_retry", return_value=_ok_response()) as mock_dispatch:
            uploader.upload(str(file_path))

        methods = [call.args[0] for call in mock_dispatch.call_args_list]
        assert methods == ["post", "put"]

    def test_dispatched_calls_carry_a_timeout(self, tmp_path):
        file_path = tmp_path / "sample.csv"
        file_path.write_text("a,b\n1,2\n")

        uploader = FileUploader(backend_url="https://api.example.com", api_key="key")

        with patch("requests.Session.request", return_value=_ok_response()) as mock_request:
            uploader.upload(str(file_path))

        assert mock_request.call_count == 2
        for call in mock_request.call_args_list:
            assert call.kwargs["timeout"] == (DEFAULT_TIMEOUT_CONNECT, DEFAULT_TIMEOUT_READ)


class TestBlackholeFailsFast:
    """The acceptance criterion: bounded failure instead of an infinite hang."""

    def test_put_leg_raises_timeout(self, blackhole_url, monkeypatch):
        monkeypatch.setenv("AIXPLAIN_HTTP_CONNECT_TIMEOUT", "1")
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", "1")

        started = time.monotonic()
        # PUT is outside the retry session's allowed_methods, so the read
        # timeout surfaces directly rather than as an exhausted-retry error.
        with pytest.raises(requests.exceptions.Timeout):
            RequestManager.request_with_retry("put", blackhole_url, data=b"payload")
        elapsed = time.monotonic() - started

        assert elapsed < 10, f"took {elapsed:.1f}s; the timeout is not bounding the read"

    def test_upload_wraps_the_timeout_in_file_upload_error(self, blackhole_url, tmp_path, monkeypatch):
        monkeypatch.setenv("AIXPLAIN_HTTP_CONNECT_TIMEOUT", "1")
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", "1")
        file_path = tmp_path / "sample.csv"
        file_path.write_text("a,b\n1,2\n")

        uploader = FileUploader(backend_url=blackhole_url, api_key="key")

        started = time.monotonic()
        # The presigned POST *is* retried, so this leg fails after a bounded
        # number of attempts (a urllib3 MaxRetryError surfacing as
        # ConnectionError) rather than on the first read timeout.
        with pytest.raises(FileUploadError):
            uploader.upload(str(file_path))
        elapsed = time.monotonic() - started

        assert elapsed < 60, f"took {elapsed:.1f}s; the retry budget is not bounded"


class TestUploadSessionReuse:
    """BUG-942 item 3: the upload path built a fresh Session per request.

    ``create_session()`` called ``create_retry_session()`` on every request, so
    each leg of every upload paid a TLS handshake and pooled nothing -- the same
    defect as v1's ``_request_with_retry``, reproduced in v2.
    """

    def test_create_session_returns_the_same_object(self):
        assert RequestManager.create_session() is RequestManager.create_session()

    def test_a_hundred_requests_build_one_session(self):
        RequestManager.create_session()  # warm the cache

        with patch("requests.Session.request", return_value=_ok_response()):
            with patch("aixplain.v2.client.create_retry_session") as factory:
                for index in range(100):
                    RequestManager.request_with_retry("get", f"https://api.example.com/{index}")

        factory.assert_not_called()

    def test_the_shared_session_is_pool_sized(self):
        """It must be a ``create_retry_session``, not a bare Session."""
        from aixplain.v2.client import DEFAULT_POOL_MAXSIZE, RETRY_ALLOWED_METHODS

        adapter = RequestManager.create_session().get_adapter("https://api.example.com")

        assert adapter._pool_maxsize == DEFAULT_POOL_MAXSIZE
        assert adapter.max_retries.allowed_methods == RETRY_ALLOWED_METHODS

    def test_concurrent_first_use_creates_exactly_one_session(self):
        """The double-checked lock must not race into two sessions."""
        import threading

        from aixplain.v2 import upload_utils

        upload_utils.RequestManager._session = None
        barrier = threading.Barrier(16)
        results = [None] * 16

        def create(index):
            barrier.wait()
            results[index] = RequestManager.create_session()

        threads = [threading.Thread(target=create, args=(i,)) for i in range(16)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len({id(session) for session in results}) == 1
