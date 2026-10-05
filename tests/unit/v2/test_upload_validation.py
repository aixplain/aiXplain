"""Unit tests for ``validate_file_for_upload``, the upload pre-flight check.

It reads only the local file, so it is tested here rather than in the
functional suite. Oversized files are sparse: ``truncate`` sets the size
the validator reads without writing the bytes.
"""

import pytest

from aixplain.v2.exceptions import FileUploadError
from aixplain.v2.upload_utils import FileValidator, validate_file_for_upload

MB = 1024 * 1024


def _sized_file(path, size_bytes):
    with open(path, "wb") as handle:
        handle.truncate(size_bytes)
    return str(path)


def test_valid_file_reports_its_type_and_size(tmp_path):
    path = tmp_path / "ok.txt"
    path.write_bytes(b"a" * 2048)

    info = validate_file_for_upload(str(path))

    assert info["valid"] is True
    assert info["file_type"] == "other"
    assert info["file_size_mb"] == pytest.approx(2048 / MB, abs=0.001)
    assert info["max_size_mb"] == FileValidator.SIZE_LIMITS["other"] / MB


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(FileUploadError, match="not found"):
        validate_file_for_upload(str(tmp_path / "nope.txt"))


def test_wav_is_classified_as_audio_with_a_50_mb_limit(tmp_path):
    info = validate_file_for_upload(_sized_file(tmp_path / "clip.wav", 1024))

    assert info["mime_type"] == "audio/wav"
    assert info["file_type"] == "audio"
    assert info["max_size_mb"] == 50


def test_audio_over_50_mb_is_rejected(tmp_path):
    path = _sized_file(tmp_path / "big.wav", 51 * MB)

    with pytest.raises(FileUploadError, match='of type "audio" exceeds 50.0 MB'):
        validate_file_for_upload(path)
