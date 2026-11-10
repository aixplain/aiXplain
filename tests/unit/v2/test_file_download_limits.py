"""File downloads are bounded (BUG-1452).

* ``File(source=url).save()`` refuses a body over ``MAX_URL_SOURCE_BYTES``
  without writing more than the cap to disk, refuses an over-size
  ``Content-Length`` before downloading, and checks the quota from
  ``Content-Length`` before the body is fetched.
* A folder ZIP whose entry count or uncompressed total exceeds the caps is not
  extracted.
"""

import os
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from aixplain import Aixplain, File, FileUploadError, ResourceError
from aixplain.utils.url_safety import FETCH_TIMEOUT_CONNECT, FETCH_TIMEOUT_READ


@pytest.fixture
def aix() -> Aixplain:
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def _stream_response(chunks, headers=None):
    response = MagicMock()
    response.headers = headers or {}
    response.iter_content.return_value = chunks
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


_REAL_NAMED_TEMPORARY_FILE = tempfile.NamedTemporaryFile


class _SizeRecordingTempFile:
    """Patch target for ``tempfile.NamedTemporaryFile`` that remembers the path."""

    def __init__(self, directory):
        self.directory = directory
        self.paths = []
        self.max_size = 0

    def __call__(self, *args, **kwargs):
        kwargs["dir"] = self.directory
        handle = _REAL_NAMED_TEMPORARY_FILE(*args, **kwargs)
        self.paths.append(handle.name)
        original_write = handle.write

        def write(data):
            written = original_write(data)
            handle.flush()
            self.max_size = max(self.max_size, os.path.getsize(handle.name))
            return written

        handle.write = write
        return handle


def test_url_source_over_the_cap_is_refused_without_writing_past_it(aix, tmp_path, monkeypatch):
    monkeypatch.setattr(File, "MAX_URL_SOURCE_BYTES", 10)
    response = _stream_response([b"x" * 6, b"y" * 6, b"z" * 6])
    recorder = _SizeRecordingTempFile(tmp_path)
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock()

    with (
        patch("aixplain.v2.file.safe_get", return_value=response),
        patch("aixplain.v2.file.tempfile.NamedTemporaryFile", side_effect=recorder),
        pytest.raises(FileUploadError, match="limit"),
    ):
        aix.File("https://files.test/huge.bin").save()

    assert recorder.max_size <= 10
    assert all(not Path(path).exists() for path in recorder.paths)
    aix.client.post.assert_not_called()


def test_oversize_content_length_is_refused_before_downloading(aix, monkeypatch):
    monkeypatch.setattr(File, "MAX_URL_SOURCE_BYTES", 10)
    response = _stream_response([b"x" * 5], headers={"Content-Length": "11"})
    aix.client.get = Mock(return_value={"allowed": True})

    with (
        patch("aixplain.v2.file.safe_get", return_value=response),
        patch("aixplain.v2.file.tempfile.NamedTemporaryFile") as temp,
        pytest.raises(FileUploadError, match="11 bytes"),
    ):
        aix.File("https://files.test/huge.bin").save()

    temp.assert_not_called()
    response.iter_content.assert_not_called()
    aix.client.get.assert_not_called()


def test_quota_is_checked_from_content_length_before_downloading(aix):
    response = _stream_response([b"x" * 5], headers={"Content-Length": "5000"})
    aix.client.get = Mock(return_value={"allowed": False, "reason": "quota exceeded"})

    with (
        patch("aixplain.v2.file.safe_get", return_value=response),
        patch("aixplain.v2.file.tempfile.NamedTemporaryFile") as temp,
        pytest.raises(FileUploadError, match="not allowed"),
    ):
        aix.File("https://files.test/report.pdf").save()

    temp.assert_not_called()
    assert aix.client.get.call_args.kwargs["params"] == {"size": 5000}


def test_url_source_uses_the_fetch_timeout_not_the_api_timeout(aix):
    response = _stream_response([b"hello"])
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            {"uploadUrl": "https://bucket.s3.amazonaws.com/u", "downloadUrl": "s3://bucket/x"},
            {"id": "file-1", "name": "report.pdf", "fileType": "file"},
        ]
    )

    with (
        patch("aixplain.v2.file.safe_get", return_value=response) as fetch,
        patch("aixplain.v2.file.requests.put", return_value=Mock(ok=True)),
    ):
        aix.File("https://files.test/report.pdf").save()

    timeout = fetch.call_args.kwargs.get("timeout")
    assert timeout in (None, (FETCH_TIMEOUT_CONNECT, FETCH_TIMEOUT_READ))


def _zip_bytes(entries):
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in entries:
            bundle.writestr(name, data)
    return archive.getvalue()


def _folder(aix, payload):
    response = Mock()
    response.iter_content.return_value = [payload]
    aix.client.request_stream = Mock(return_value=response)
    return aix.File(id="root", name="reference", fileType="folder")


def test_zip_over_the_uncompressed_cap_is_not_extracted(aix, tmp_path, monkeypatch):
    monkeypatch.setattr(File, "MAX_ARCHIVE_BYTES", 1024)
    folder = _folder(aix, _zip_bytes([("a.txt", b"0" * 800), ("b.txt", b"0" * 800)]))
    target = tmp_path / "reference"

    with pytest.raises(ResourceError, match="limit"):
        folder.download(target)

    assert list(target.iterdir()) == []


def test_zip_with_too_many_entries_is_not_extracted(aix, tmp_path, monkeypatch):
    monkeypatch.setattr(File, "MAX_ARCHIVE_ENTRIES", 3)
    folder = _folder(aix, _zip_bytes([(f"f{i}.txt", b"x") for i in range(4)]))
    target = tmp_path / "reference"

    with pytest.raises(ResourceError, match="entries"):
        folder.download(target)

    assert list(target.iterdir()) == []


def test_zip_lying_about_its_size_is_still_capped_during_extraction(aix, tmp_path, monkeypatch):
    """The central directory can understate sizes; the copy loop enforces the cap too."""
    from aixplain.v2 import file as file_module

    monkeypatch.setattr(File, "MAX_ARCHIVE_BYTES", 1024)
    destinations = []
    payload = _zip_bytes([("a.txt", b"0" * 2048)])
    with zipfile.ZipFile(BytesIO(payload)) as bundle:
        for member in bundle.infolist():
            destinations.append((member, tmp_path / member.filename))
        with pytest.raises(ResourceError, match="limit"):
            file_module._extract_bounded(bundle, destinations, 1024)
    assert (tmp_path / "a.txt").stat().st_size <= 1024


def test_compressed_archive_over_the_cap_is_refused_while_downloading(aix, tmp_path, monkeypatch):
    monkeypatch.setattr(File, "MAX_ARCHIVE_BYTES", 10)
    response = Mock()
    response.iter_content.return_value = [b"x" * 6, b"x" * 6]
    aix.client.request_stream = Mock(return_value=response)
    folder = aix.File(id="root", name="reference", fileType="folder")

    with pytest.raises(ResourceError, match="limit"):
        folder.download(tmp_path / "reference")


def test_normal_zip_still_extracts(aix, tmp_path):
    folder = _folder(aix, _zip_bytes([("docs/a.txt", b"hello"), ("empty/", b"")]))

    result = Path(folder.download(tmp_path / "reference"))

    assert (result / "docs" / "a.txt").read_text() == "hello"
    assert (result / "empty").is_dir()
