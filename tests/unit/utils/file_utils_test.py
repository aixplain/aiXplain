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

from unittest.mock import Mock, patch

import pytest

from aixplain.enums import License
from aixplain.utils.file_utils import upload_data


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
