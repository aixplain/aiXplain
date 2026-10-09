"""Functional tests for File assets and the upload utilities.

Covers the two halves of the File surface that had no functional twin: the
``upload_file`` helper, and the ``aix.File`` resource's own save/get/delete
round-trip. ``File`` is also what the deprecated ``aix.Resource`` alias points
at. The offline checks (``validate_file_for_upload`` and constructor
validation) are unit-tested in ``tests/unit/v2/``.

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

import pytest
import requests

from aixplain.v2.exceptions import APIError
from aixplain.v2.upload_utils import upload_file

MB = 1024 * 1024


def _write(path, size_bytes):
    with open(path, "wb") as handle:
        handle.write(b"a" * size_bytes)
    return str(path)


class TestUploadFileHelper:
    def test_upload_small_file_returns_s3_reference(self, client, tmp_path):
        path = _write(tmp_path / "small.txt", 1024)

        reference = upload_file(path, api_key=client.api_key, backend_url=client.backend_url)

        assert reference.startswith("s3://"), reference

    def test_upload_multi_megabyte_file_returns_s3_reference(self, client, tmp_path):
        path = _write(tmp_path / "large.txt", 6 * MB)

        reference = upload_file(path, api_key=client.api_key, backend_url=client.backend_url)

        assert reference.startswith("s3://"), reference


class TestFileResource:
    def test_save_get_download_delete_round_trip(self, client, tmp_path, resource_tracker):
        source = _write(tmp_path / "asset.txt", 4096)
        file = client.File(source=source)
        file.save()
        resource_tracker.append(file)
        assert file.id

        fetched = client.File.get(file.id)
        assert fetched.id == file.id
        assert fetched.name == file.name

        destination = tmp_path / "downloaded.txt"
        fetched.download(str(destination))
        assert destination.read_bytes() == b"a" * 4096

        deleted_id = file.id
        file.delete()
        resource_tracker.mark_cleaned(file)
        with pytest.raises(APIError):
            client.File.get(deleted_id)

    def test_upload_put_uses_the_client_timeout(self, client, tmp_path, resource_tracker, monkeypatch):
        """The presigned PUT of the file body is sent with the client's configured timeout."""
        source = _write(tmp_path / "timeout.txt", 1024)
        real_put = requests.put
        put_timeouts = []

        def spy_put(*args, **kwargs):
            put_timeouts.append(kwargs.get("timeout"))
            return real_put(*args, **kwargs)

        monkeypatch.setattr("aixplain.v2.file.requests.put", spy_put)
        original = client.client.timeout
        client.client.timeout = (10, 60)
        try:
            file = client.File(source=source)
            file.save()
            resource_tracker.append(file)
        finally:
            client.client.timeout = original

        assert file.id
        assert put_timeouts == [(10, 60)]
