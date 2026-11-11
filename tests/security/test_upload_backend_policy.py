"""``upload_file()`` / ``FileUploader`` apply the config-URL policy (BUG-1451).

These public helpers resolve the backend URL themselves (argument or
``BACKEND_URL``) and send ``Authorization: token <key>`` to it. They now run
``validate_config_url`` on that URL, so an ``http://`` backend is refused
before any request carries the key, and a foreign https host gets the same
WARNING ``Aixplain()`` emits.
"""

import logging
from unittest.mock import Mock, patch

import pytest
import requests

from aixplain import FileUploader, upload_file
from aixplain.utils import url_safety
from aixplain.utils.url_safety import INSECURE_OPT_IN_ENV_VAR, UnsafeURLError

CANARY_KEY = "CANARY-UPLOAD-KEY-1451"
PRESIGNED_URL = "https://test-bucket.s3.amazonaws.com/upload?signature=xyz"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("BACKEND_URL", raising=False)
    monkeypatch.delenv(INSECURE_OPT_IN_ENV_VAR, raising=False)
    monkeypatch.setenv("TEAM_API_KEY", CANARY_KEY)
    url_safety._WARNED_CONFIG_HOSTS.clear()
    yield
    url_safety._WARNED_CONFIG_HOSTS.clear()


@pytest.fixture
def sample_file(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("a,b\n1,2\n")
    return str(path)


@pytest.fixture
def wire():
    """Record every request at both HTTP layers the upload path could use."""
    presigned = Mock(
        status_code=200,
        **{
            "json.return_value": {"key": "data/sample.csv", "uploadUrl": PRESIGNED_URL, "downloadUrl": "https://d/x"},
            "raise_for_status.return_value": None,
        },
    )
    with (
        patch(
            "aixplain.v2.upload_utils.RequestManager.request_with_retry",
            side_effect=[presigned, Mock(status_code=200)],
        ) as retry_layer,
        patch.object(requests.Session, "request", side_effect=AssertionError("unexpected network call")) as session,
    ):
        yield retry_layer, session


def _assert_nothing_sent(wire):
    retry_layer, session = wire
    assert retry_layer.call_count == 0
    assert session.call_count == 0


def test_upload_file_refuses_http_backend_from_env(monkeypatch, sample_file, wire):
    monkeypatch.setenv("BACKEND_URL", "http://collector.invalid/")
    with pytest.raises(UnsafeURLError):
        upload_file(sample_file)
    _assert_nothing_sent(wire)


def test_file_uploader_refuses_http_backend_from_env(monkeypatch, sample_file, wire):
    monkeypatch.setenv("BACKEND_URL", "http://collector.invalid/")
    with pytest.raises(UnsafeURLError):
        FileUploader().upload(sample_file)
    _assert_nothing_sent(wire)


@pytest.mark.parametrize(
    "backend_url",
    ["http://collector.invalid/", "https://user:pw@collector.invalid/", "ftp://collector.invalid/"],
)
def test_explicit_unsafe_backend_url_is_refused(backend_url, sample_file, wire):
    with pytest.raises(UnsafeURLError):
        upload_file(sample_file, backend_url=backend_url)
    with pytest.raises(UnsafeURLError):
        FileUploader(backend_url=backend_url)
    _assert_nothing_sent(wire)


def test_foreign_https_backend_warns_like_aixplain(monkeypatch, sample_file, wire, caplog):
    monkeypatch.setenv("BACKEND_URL", "https://not-aixplain.test")
    with caplog.at_level(logging.WARNING, logger="aixplain.utils.url_safety"):
        uploader = FileUploader()
    assert uploader.backend_url == "https://not-aixplain.test"
    warnings = [r for r in caplog.records if r.name == "aixplain.utils.url_safety"]
    assert len(warnings) == 1
    assert "not-aixplain.test" in warnings[0].getMessage()


def test_default_backend_is_used_silently(sample_file, wire, caplog):
    with caplog.at_level(logging.WARNING, logger="aixplain.utils.url_safety"):
        upload_file(sample_file)
    retry_layer, _ = wire
    method, url = retry_layer.call_args_list[0][0][:2]
    assert method == "post"
    assert url.startswith("https://platform-api.aixplain.com/")
    assert not [r for r in caplog.records if r.name == "aixplain.utils.url_safety"]


def test_http_localhost_is_allowed_with_insecure_opt_in(monkeypatch):
    monkeypatch.setenv(INSECURE_OPT_IN_ENV_VAR, "1")
    assert FileUploader(backend_url="http://localhost:8000").backend_url == "http://localhost:8000"
