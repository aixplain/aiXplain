"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from aixplain.enums import License
from aixplain.utils.file_utils import (
    DEFAULT_DOWNLOAD_CONNECT_TIMEOUT,
    DEFAULT_DOWNLOAD_READ_TIMEOUT,
    download_data,
    upload_data,
)


@pytest.mark.parametrize(
    "presigned_url,expected_link",
    [
        pytest.param(
            "https://my-bucket.s3.us-east-1.amazonaws.com/upload/path?signature=test",
            "s3://my-bucket/uploads/test.csv",
            id="regional_virtual_hosted_url",
        ),
        pytest.param(
            "https://s3.us-east-1.amazonaws.com/my-bucket/upload/path?signature=test",
            "s3://my-bucket/uploads/test.csv",
            id="regional_path_style_url",
        ),
    ],
)
def test_upload_data_builds_s3_link_from_modern_presigned_url(tmp_path, presigned_url, expected_link):
    """Permanent uploads should support regional S3 presigned URL formats."""
    file_path = tmp_path / "test.csv"
    file_path.write_text("a,b\n1,2\n", encoding="utf-8")

    presigned_response = Mock()
    presigned_response.json.return_value = {
        "key": "uploads/test.csv",
        "uploadUrl": presigned_url,
        "downloadUrl": "https://download.example/test.csv",
    }
    upload_response = Mock(status_code=200)

    with patch("aixplain.utils.file_utils._request_with_retry", side_effect=[presigned_response, upload_response]):
        s3_link = upload_data(
            file_name=file_path,
            tags=["test"],
            license=License.MIT,
            is_temp=False,
            api_key="test-api-key",
        )

    assert s3_link == expected_link


# ``blackhole_url`` comes from tests/unit/conftest.py.


def _streaming_response():
    """A ``requests.get(..., stream=True)`` stand-in usable as a context manager."""
    response = MagicMock()
    response.__enter__.return_value = response
    response.iter_content.return_value = [b"chunk"]
    return response


class TestDownloadDataTimeout:
    """The streaming download must be bounded: without a timeout the thread
    hangs mid-``iter_content`` holding an open file handle (BUG-938)."""

    def test_default_timeout_is_applied(self, tmp_path):
        with patch("aixplain.utils.file_utils.requests.get", return_value=_streaming_response()) as mock_get:
            download_data("https://example.com/f.bin", local_filename=str(tmp_path / "f.bin"))

        assert mock_get.call_args.kwargs["timeout"] == (
            DEFAULT_DOWNLOAD_CONNECT_TIMEOUT,
            DEFAULT_DOWNLOAD_READ_TIMEOUT,
        )

    def test_explicit_timeout_wins(self, tmp_path):
        with patch("aixplain.utils.file_utils.requests.get", return_value=_streaming_response()) as mock_get:
            download_data("https://example.com/f.bin", local_filename=str(tmp_path / "f.bin"), timeout=2.5)

        assert mock_get.call_args.kwargs["timeout"] == 2.5

    def test_env_override_is_honoured(self, tmp_path, monkeypatch):
        monkeypatch.setenv("AIXPLAIN_HTTP_CONNECT_TIMEOUT", "4")
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", "9.5")

        with patch("aixplain.utils.file_utils.requests.get", return_value=_streaming_response()) as mock_get:
            download_data("https://example.com/f.bin", local_filename=str(tmp_path / "f.bin"))

        assert mock_get.call_args.kwargs["timeout"] == (4.0, 9.5)

    @pytest.mark.parametrize("bad", ["abc", "0", "-5", ""])
    def test_unusable_env_values_fall_back_to_defaults(self, bad, tmp_path, monkeypatch):
        """A typo in the knob must not silently remove the bound it configures."""
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", bad)

        with patch("aixplain.utils.file_utils.requests.get", return_value=_streaming_response()) as mock_get:
            download_data("https://example.com/f.bin", local_filename=str(tmp_path / "f.bin"))

        assert mock_get.call_args.kwargs["timeout"] == (
            DEFAULT_DOWNLOAD_CONNECT_TIMEOUT,
            DEFAULT_DOWNLOAD_READ_TIMEOUT,
        )

    def test_blackhole_fails_fast(self, blackhole_url, tmp_path, monkeypatch):
        monkeypatch.setenv("AIXPLAIN_HTTP_CONNECT_TIMEOUT", "1")
        monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", "1")

        started = time.monotonic()
        with pytest.raises(requests.exceptions.Timeout):
            download_data(blackhole_url, local_filename=str(tmp_path / "f.bin"))
        elapsed = time.monotonic() - started

        assert elapsed < 10, f"took {elapsed:.1f}s; the timeout is not bounding the read"
