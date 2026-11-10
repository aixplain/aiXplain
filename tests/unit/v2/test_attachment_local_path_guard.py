"""Plain-string attachments must not become arbitrary local-file reads (BUG-948).

``resolve_attachments`` backs both ``Session.add_message(attachments=...)`` and
``Agent.run(attachments=...)``. A plain string is often model- or user-authored
text, so one naming a dotfile or a system path is refused before any upload;
other plain-string local paths still upload but are deprecated. Network-free:
``FileUploader`` is always mocked.
"""

import os
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from aixplain import ResourceError
from aixplain.v2.session import STRICT_ATTACHMENTS_ENV_VAR, _is_hosted_url, resolve_attachments

SENSITIVE = [
    "/etc/passwd",
    "/proc/self/environ",
    "/sys/kernel/x",
    "/dev/null",
    "~/.aws/credentials",
    "./.env",
    ".env",
    "foo/../.ssh/id_rsa",
]


def _ctx():
    return Mock(backend_url="https://platform-api.aixplain.com", api_key="ctx-key")


@pytest.fixture(autouse=True)
def _not_strict(monkeypatch):
    monkeypatch.delenv(STRICT_ATTACHMENTS_ENV_VAR, raising=False)


@pytest.fixture
def uploader():
    with (
        patch("aixplain.v2.upload_utils.FileUploader") as MockUploader,
        patch("aixplain.v2.upload_utils.MimeTypeDetector") as MockDetector,
    ):
        MockUploader.return_value.upload.return_value = "https://cdn.example.com/x"
        MockDetector.detect_mime_type.return_value = "application/octet-stream"
        yield MockUploader


@pytest.mark.parametrize("url", ["HTTPS://cdn.example.com/a.wav", "Http://x/a.png", "S3://bucket/k", " https://x/y"])
def test_hosted_url_match_is_case_insensitive(url):
    assert _is_hosted_url(url)


def test_uppercase_url_is_attached_without_upload(uploader):
    out = resolve_attachments(_ctx(), ["HTTPS://cdn.example.com/a.wav"], None)
    assert out[0]["url"] == "HTTPS://cdn.example.com/a.wav"
    uploader.assert_not_called()


@pytest.mark.parametrize("value", SENSITIVE)
def test_sensitive_plain_string_is_refused_before_upload(uploader, value):
    with pytest.raises(ResourceError, match="Refusing to upload"):
        resolve_attachments(_ctx(), [value], None, error_label="agent 'a'")
    uploader.assert_not_called()
    uploader.return_value.upload.assert_not_called()


@pytest.mark.parametrize("value", ["/etc/passwd", "~/.aws/credentials"])
def test_sensitive_path_via_files_kwarg_is_refused(uploader, value):
    with pytest.warns(DeprecationWarning), pytest.raises(ResourceError, match="Refusing to upload"):
        resolve_attachments(_ctx(), None, [value])
    uploader.return_value.upload.assert_not_called()


def test_symlink_into_system_tree_is_refused(uploader, tmp_path):
    link = tmp_path / "innocent.txt"
    os.symlink("/etc/hosts", link)
    with pytest.raises(ResourceError, match="Refusing to upload"):
        resolve_attachments(_ctx(), [str(link)], None)
    uploader.return_value.upload.assert_not_called()


def test_benign_plain_string_uploads_with_deprecation_warning(uploader, tmp_path):
    path = tmp_path / "clip.wav"
    path.write_bytes(b"x")
    with pytest.warns(DeprecationWarning, match="plain string"):
        out = resolve_attachments(_ctx(), [str(path)], None)
    assert out[0]["url"] == "https://cdn.example.com/x"
    uploader.assert_called_once_with(backend_url="https://platform-api.aixplain.com", api_key="ctx-key")
    uploader.return_value.upload.assert_called_once_with(str(path), is_temp=True, return_download_link=True)


@pytest.mark.parametrize("entry_factory", [lambda p: Path(p), lambda p: {"path": p}])
def test_explicit_local_forms_upload_without_warning(uploader, tmp_path, entry_factory):
    path = tmp_path / "clip.wav"
    path.write_bytes(b"x")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        out = resolve_attachments(_ctx(), [entry_factory(str(path))], None)
    assert out[0]["url"] == "https://cdn.example.com/x"
    uploader.return_value.upload.assert_called_once()


def test_strict_mode_rejects_benign_plain_string(uploader, tmp_path, monkeypatch):
    monkeypatch.setenv(STRICT_ATTACHMENTS_ENV_VAR, "1")
    with pytest.raises(ResourceError, match=STRICT_ATTACHMENTS_ENV_VAR):
        resolve_attachments(_ctx(), [str(tmp_path / "clip.wav")], None)
    uploader.return_value.upload.assert_not_called()


def test_strict_mode_still_accepts_path_objects(uploader, tmp_path, monkeypatch):
    monkeypatch.setenv(STRICT_ATTACHMENTS_ENV_VAR, "1")
    resolve_attachments(_ctx(), [tmp_path / "clip.wav"], None)
    uploader.return_value.upload.assert_called_once()


def test_project_under_dot_directory_is_not_refused(uploader, tmp_path, monkeypatch):
    """Only dot components in the path as written count, not those in the CWD."""
    work = tmp_path / ".agents" / "proj"
    work.mkdir(parents=True)
    (work / "clip.wav").write_bytes(b"x")
    monkeypatch.chdir(work)
    with pytest.warns(DeprecationWarning):
        resolve_attachments(_ctx(), ["clip.wav"], None)
    uploader.return_value.upload.assert_called_once()


@pytest.mark.parametrize("value", ["/etc/passwd", "~/.aws/credentials", "/proc/self/environ"])
def test_agent_and_session_entry_points_refuse_sensitive_paths(uploader, value):
    from aixplain import Agent, Session

    ctx = _ctx()
    ctx.client = Mock()
    agent = Agent.from_dict({"id": "agent-1", "name": "A", "instructions": "x", "tools": [], "agents": []})
    agent.context = ctx
    with pytest.raises(ResourceError, match="Refusing to upload"):
        agent.build_run_payload(query="summarise", attachments=[value])

    session = Session.from_dict({"id": "s1", "agentId": "agent-1"})
    session.context = ctx
    with pytest.raises(ResourceError, match="Refusing to upload"):
        session.add_message(role="user", content="q", attachments=[value])

    uploader.return_value.upload.assert_not_called()
    ctx.client.request.assert_not_called()
