"""Effect-based guards on the headers the v2 file-upload path sends.

``AixplainClient.__init__`` header building is covered by ``test_client.py``,
but ``aixplain/v2/upload_utils.py`` builds its own headers outside the client
and nothing asserted on them: renaming ``Authorization`` there killed no test
(ENG-3431). These tests drive ``FileUploader.upload()`` and assert on the
header dicts the HTTP layer actually received.
"""

import pytest
from unittest.mock import Mock, patch

from aixplain.v2.upload_utils import FileUploader

API_KEY = "test-team-key"
PRESIGNED_URL = "https://test-bucket.s3.amazonaws.com/upload?signature=xyz"


@pytest.fixture
def upload_file_path(tmp_path):
    """A small on-disk file that passes validation and MIME detection."""
    path = tmp_path / "sample.csv"
    path.write_text("col_a,col_b\n1,2\n")
    return str(path)


@pytest.fixture
def captured_requests():
    """Patch the retrying request layer and record every call made through it."""
    presigned_response = Mock(
        status_code=200,
        **{
            "json.return_value": {
                "key": "data/sample.csv",
                "uploadUrl": PRESIGNED_URL,
                "downloadUrl": "https://download/sample.csv",
            },
            "raise_for_status.return_value": None,
        },
    )
    s3_response = Mock(status_code=200)

    with patch(
        "aixplain.v2.upload_utils.RequestManager.request_with_retry",
        side_effect=[presigned_response, s3_response],
    ) as mock_request:
        yield mock_request


def _call_for(mock_request, method):
    """Return the single recorded call made with *method*."""
    calls = [call for call in mock_request.call_args_list if call[0][0] == method]
    assert len(calls) == 1, f"expected exactly one {method!r} request, got {len(calls)}"
    return calls[0]


def test_presigned_url_request_sends_authorization_token(captured_requests, upload_file_path):
    """The pre-signed URL request must authenticate with `Authorization: token <key>`."""
    FileUploader(backend_url="https://platform-api.aixplain.com", api_key=API_KEY).upload(upload_file_path)

    headers = _call_for(captured_requests, "post")[1]["headers"]
    assert headers["Authorization"] == f"token {API_KEY}"


def test_s3_upload_sends_content_type_and_no_credential(captured_requests, upload_file_path):
    """The S3 PUT carries the content type -- and must not leak the API key.

    The pre-signed URL already encodes the grant; forwarding the team key to a
    third-party host would widen its exposure for no benefit.
    """
    FileUploader(backend_url="https://platform-api.aixplain.com", api_key=API_KEY).upload(upload_file_path)

    put_call = _call_for(captured_requests, "put")
    headers = put_call[1]["headers"]
    assert put_call[0][1] == PRESIGNED_URL
    assert headers["Content-Type"] == "text/csv"
    assert "Authorization" not in headers
    assert API_KEY not in str(headers)


def test_temp_upload_targets_temp_url_endpoint(captured_requests, upload_file_path):
    """A temporary upload negotiates against `sdk/file/upload/temp-url`."""
    uploader = FileUploader(backend_url="https://platform-api.aixplain.com", api_key=API_KEY)
    uploader.upload(upload_file_path, is_temp=True)

    assert _call_for(captured_requests, "post")[0][1] == "https://platform-api.aixplain.com/sdk/file/upload/temp-url"


def test_permanent_upload_targets_upload_url_endpoint(captured_requests, upload_file_path):
    """A permanent upload negotiates against `sdk/file/upload-url`."""
    FileUploader(backend_url="https://platform-api.aixplain.com", api_key=API_KEY).upload(
        upload_file_path, is_temp=False, tags=["unit-test"]
    )

    post_call = _call_for(captured_requests, "post")
    assert post_call[0][1] == "https://platform-api.aixplain.com/sdk/file/upload-url"
    assert post_call[1]["headers"]["Authorization"] == f"token {API_KEY}"
