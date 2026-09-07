"""Tests that the presigned ``uploadUrl`` host is validated before the PUT (BUG-939).

The URL comes straight out of a backend response. If the backend is compromised
-- or ``BACKEND_URL`` was redirected by an ambient ``.env`` -- every dataset,
database file, skill bundle and attachment would be PUT to the attacker while the
SDK reported success, because ``_build_s3_link_from_presigned_url`` infers the
bucket by regex and falls back to ``"aixplain-uploads"`` rather than raising.
"""

from unittest.mock import MagicMock, patch

import pytest

from aixplain.utils import file_utils
from aixplain.utils.url_safety import UnsafeURLError
from aixplain.v2.upload_utils import S3Uploader

FOREIGN_URL = "https://evil.example.com/upload"
GOOD_URL = "https://bucket.s3.amazonaws.com/key?X-Amz-Signature=abc"


def test_v2_uploader_refuses_a_foreign_host(tmp_path):
    """``S3Uploader.upload_file`` raises before opening or sending the file."""
    target = tmp_path / "data.csv"
    target.write_text("a,b\n1,2\n")

    with patch("aixplain.v2.upload_utils.RequestManager.request_with_retry") as request:
        with pytest.raises(UnsafeURLError):
            S3Uploader.upload_file(str(target), FOREIGN_URL, "text/csv")
    request.assert_not_called()


def test_v2_uploader_error_is_not_masked_as_a_generic_failure(tmp_path):
    """The refusal must survive the ``except Exception -> FileUploadError`` wrapper."""
    target = tmp_path / "data.csv"
    target.write_text("x")

    with patch("aixplain.v2.upload_utils.RequestManager.request_with_retry"):
        with pytest.raises(UnsafeURLError) as excinfo:
            S3Uploader.upload_file(str(target), FOREIGN_URL, "text/csv")
    assert "evil.example.com" in str(excinfo.value)


def test_v2_uploader_accepts_a_presigned_s3_url(tmp_path):
    """The ordinary S3 target still works end to end."""
    target = tmp_path / "data.csv"
    target.write_text("x")

    response = MagicMock(status_code=200)
    with patch("aixplain.v2.upload_utils.RequestManager.request_with_retry", return_value=response) as request:
        S3Uploader.upload_file(str(target), GOOD_URL, "text/csv")
    request.assert_called_once()


def test_upload_data_refuses_a_foreign_host_without_retrying(tmp_path):
    """``file_utils.upload_data`` raises immediately and issues no PUT.

    The generic handler in ``upload_data`` retries ``nattempts`` times and masks
    the cause; a refused host is not transient, so it must bypass that path.
    """
    target = tmp_path / "data.csv"
    target.write_text("a,b\n1,2\n")

    post_response = MagicMock()
    post_response.json.return_value = {"key": "some/key", "uploadUrl": FOREIGN_URL}

    with patch.object(file_utils, "_request_with_retry", return_value=post_response) as request:
        with pytest.raises(UnsafeURLError):
            file_utils.upload_data(file_name=str(target), nattempts=2)

    # Exactly one call: the POST that fetched the presigned URL. No PUT, and no
    # recursive retry of the whole upload.
    assert request.call_count == 1
    assert request.call_args[0][0] == "post"
