"""Streaming and retry coverage for the presigned S3 upload (BUG-949).

``S3Uploader.upload_file`` used to read the whole file into memory before the
PUT, and the upload session excluded ``PUT`` from its retryable methods, so the
largest request the SDK makes got zero transport-level retries.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain import FileUploadError
from aixplain.v2.upload_utils import RequestManager, S3Uploader

PRESIGNED = "https://bucket.s3.amazonaws.com/uploads/x.csv?sig=abc"


def _response(status_code=200):
    response = Mock()
    response.status_code = status_code
    return response


@pytest.fixture
def sample_file(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_bytes(b"a,b\n" + b"1,2\n" * 1000)
    return path


class TestStreamingPut:
    def test_put_body_is_a_file_object_not_bytes(self, sample_file):
        seen = {}

        def fake_request(method, url, **kwargs):
            data = kwargs["data"]
            seen["is_stream"] = hasattr(data, "read") and not isinstance(data, (bytes, bytearray))
            seen["body"] = data.read()
            return _response()

        with patch.object(RequestManager, "request_with_retry", side_effect=fake_request):
            S3Uploader.upload_file(str(sample_file), PRESIGNED, "text/csv")

        assert seen["is_stream"]
        assert seen["body"] == sample_file.read_bytes()

    def test_file_handle_is_closed_after_upload(self, sample_file):
        captured = {}

        def fake_request(method, url, **kwargs):
            captured["fh"] = kwargs["data"]
            return _response()

        with patch.object(RequestManager, "request_with_retry", side_effect=fake_request):
            S3Uploader.upload_file(str(sample_file), PRESIGNED, "text/csv")

        assert captured["fh"].closed

    def test_file_handle_is_closed_when_the_put_raises(self, sample_file):
        captured = {}

        def fake_request(method, url, **kwargs):
            captured["fh"] = kwargs["data"]
            raise ConnectionError("boom")

        with patch.object(RequestManager, "request_with_retry", side_effect=fake_request):
            with pytest.raises(FileUploadError):
                S3Uploader.upload_file(str(sample_file), PRESIGNED, "text/csv")

        assert captured["fh"].closed

    def test_non_200_still_raises(self, sample_file):
        with patch.object(RequestManager, "request_with_retry", return_value=_response(500)):
            with pytest.raises(FileUploadError):
                S3Uploader.upload_file(str(sample_file), PRESIGNED, "text/csv")


class TestUploadSessionRetriesPut:
    def test_put_is_retried_on_5xx(self):
        retry = RequestManager.create_session().get_adapter("https://bucket.s3.amazonaws.com").max_retries
        assert retry.is_retry("PUT", 503)

    def test_post_is_never_retried_on_5xx(self):
        """The presigned-URL POST shares this session and must not be re-sent (BUG-1090)."""
        retry = RequestManager.create_session().get_adapter("https://api.example.com").max_retries
        assert not retry.is_retry("POST", 503)

    def test_global_retry_policy_is_unchanged(self):
        """Only the upload session gains PUT; the shared client stays GET-only."""
        from aixplain.v2.client import RETRY_ALLOWED_METHODS

        assert RETRY_ALLOWED_METHODS == frozenset({"GET"})
