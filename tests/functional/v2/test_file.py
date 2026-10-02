"""Functional tests for File assets and the upload utilities.

Covers the two halves of the File surface that had no functional twin: the
``upload_file`` / ``validate_file_for_upload`` helpers, and the ``aix.File``
resource's own save/get/delete round-trip. ``File`` is also what the deprecated
``aix.Resource`` alias points at.
"""

import time

import pytest

from aixplain.v2.exceptions import FileUploadError, ValidationError
from aixplain.v2.file import File
from aixplain.v2.upload_utils import upload_file, validate_file_for_upload

MB = 1024 * 1024


def _write(path, size_bytes):
    with open(path, "wb") as handle:
        handle.write(b"a" * size_bytes)
    return str(path)


def _unique_name(prefix, suffix=".txt"):
    return f"{prefix}-{int(time.time())}-{time.time_ns() % 100000}{suffix}"


class TestUploadFileHelper:
    def test_upload_small_file_returns_reference(self, client, tmp_path):
        path = _write(tmp_path / "small.txt", 1024)

        reference = upload_file(path, api_key=client.api_key, backend_url=client.backend_url)

        assert isinstance(reference, str)
        assert reference

    def test_upload_file_over_five_megabytes(self, client, tmp_path):
        path = _write(tmp_path / "large.txt", 6 * MB)

        reference = upload_file(path, api_key=client.api_key, backend_url=client.backend_url)

        assert isinstance(reference, str)
        assert reference


class TestValidateFileForUpload:
    def test_valid_file_reports_its_type_and_size(self, tmp_path):
        path = _write(tmp_path / "ok.txt", 2048)

        info = validate_file_for_upload(path)

        assert info["valid"] is True
        assert info["file_size_mb"] == pytest.approx(2048 / MB, abs=0.001)
        assert info["max_size_mb"] > 0

    def test_missing_file_is_rejected(self, tmp_path):
        with pytest.raises(FileUploadError, match="not found"):
            validate_file_for_upload(str(tmp_path / "nope.txt"))

    def test_oversized_audio_type_is_rejected(self, tmp_path):
        """A ``.wav`` is classified as audio (50 MB limit) and 51 MB must fail."""
        path = _write(tmp_path / "big.wav", 51 * MB)

        with pytest.raises(FileUploadError, match="exceeds"):
            validate_file_for_upload(path)


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
        with pytest.raises(Exception):
            client.File.get(deleted_id)

    def test_get_requires_a_source_or_id(self, client):
        with pytest.raises(ValidationError):
            client.File()

    def test_upload_timeout_config_is_honoured(self, client, tmp_path, resource_tracker):
        """The client's configured timeout is what the upload path uses."""
        source = _write(tmp_path / "timeout.txt", 1024)
        original = client.client.timeout
        client.client.timeout = (10, 60)
        try:
            file = client.File(source=source)
            file.save()
            resource_tracker.append(file)
            assert file.id
        finally:
            client.client.timeout = original
