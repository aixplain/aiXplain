"""Tests for the unified v2 File resource."""

from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, call, patch
import zipfile

import pytest

from aixplain import Aixplain
from aixplain.v2 import File, FileType, Page, Privacy, Resource
from aixplain.v2.exceptions import APIError, FileUploadError, ResourceError, ValidationError


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated SDK client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def _asset(identifier: str, name: str, file_type: str = "file", **kwargs):
    """Build a minimal File asset response."""
    return {"id": identifier, "name": name, "fileType": file_type, **kwargs}


def test_public_exports_and_compatibility_alias(aix):
    """Expose File publicly and retain Resource as one implementation."""
    assert File is Resource
    assert aix.File.context is aix
    assert issubclass(aix.Resource, File)


def test_constructor_infers_local_file_and_directory(tmp_path, aix):
    """Infer names, extensions, and structural types from local sources."""
    local_file = tmp_path / "report.pdf"
    local_file.write_bytes(b"pdf")
    directory = tmp_path / "reference"
    directory.mkdir()

    document = aix.File(local_file)
    folder = aix.File(directory)

    assert document.name == "report.pdf"
    assert document.extension == ".pdf"
    assert document.file_type == FileType.FILE
    assert folder.name == "reference"
    assert folder.is_dir


def test_constructor_infers_decoded_url_name(aix):
    """Ignore URL query parameters and decode the path basename."""
    document = aix.File("https://files.test/my%20report.pdf?token=secret")
    assert document.name == "my report.pdf"


@pytest.mark.parametrize("source", ["", "ftp://files.test/report.pdf"])
def test_constructor_rejects_invalid_source(aix, source):
    """Reject missing paths and unsupported URL schemes."""
    with pytest.raises(ValidationError):
        aix.File(source)


def test_save_local_file_promotes_upload_to_asset(tmp_path, aix):
    """Upload first, then create a permanent root File asset."""
    local_file = tmp_path / "data.csv"
    local_file.write_text("a,b\n1,2\n")
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            {"uploadUrl": "https://upload.test", "downloadUrl": "s3://bucket/temp/data.csv"},
            _asset("file-1", "data.csv"),
        ]
    )
    upload_response = Mock(ok=True)

    with patch("aixplain.v2.file.requests.put", return_value=upload_response) as upload:
        document = aix.File(local_file).save()

    assert document.id == "file-1"
    assert document.is_temp is False
    assert upload.call_args.kwargs["timeout"] == aix.client.timeout
    assert aix.client.post.call_args_list[0] == call(
        "sdk/file/upload/temp-url",
        json={"contentType": "text/csv", "originalName": "data.csv"},
    )
    assert aix.client.post.call_args_list[1] == call(
        "sdk/file-asset",
        json={
            "name": "data.csv",
            "fileType": "file",
            "url": "s3://bucket/temp/data.csv",
            "description": "",
            "tags": [],
            "privacy": "Private",
            "whitelist": [],
        },
    )


def test_save_local_file_sends_description_tags_and_privacy(tmp_path, aix):
    """Metadata set before save() must reach the backend, not just structural fields."""
    local_file = tmp_path / "report.pdf"
    local_file.write_bytes(b"pdf")
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            {"uploadUrl": "https://upload.test", "downloadUrl": "s3://bucket/temp/report.pdf"},
            _asset("file-1", "report.pdf"),
        ]
    )

    document = aix.File(local_file, description="Quarterly report", tags=["finance", "q3"])
    document.privacy = Privacy.PUBLIC
    with patch("aixplain.v2.file.requests.put", return_value=Mock(ok=True)):
        document.save()

    assert aix.client.post.call_args_list[1] == call(
        "sdk/file-asset",
        json={
            "name": "report.pdf",
            "fileType": "file",
            "url": "s3://bucket/temp/report.pdf",
            "description": "Quarterly report",
            "tags": ["finance", "q3"],
            "privacy": "Public",
            "whitelist": [],
        },
    )


def test_save_rejects_upload_over_quota_without_uploading(tmp_path, aix):
    """Ask the backend's quota check before streaming bytes, and stop if it says no."""
    local_file = tmp_path / "huge.bin"
    local_file.write_bytes(b"x" * 10)
    aix.client.get = Mock(return_value={"allowed": False, "reason": "file_too_large", "remainingSize": 0})
    aix.client.post = Mock()

    with patch("aixplain.v2.file.requests.put") as upload:
        with pytest.raises(FileUploadError, match="file_too_large"):
            aix.File(local_file).save()

    upload.assert_not_called()
    aix.client.post.assert_not_called()


def test_save_directory_preserves_parent_relationships_and_empty_folders(tmp_path, aix):
    """Create folders deterministically and place files under their actual parents."""
    root = tmp_path / "reference"
    (root / "empty").mkdir(parents=True)
    (root / "policies" / "regional").mkdir(parents=True)
    (root / "policies" / "security.pdf").write_bytes(b"pdf")
    (root / "policies" / "regional" / "eu.txt").write_text("eu")
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            _asset("root", "reference", "folder"),
            _asset("empty-id", "empty", "folder"),
            _asset("policies-id", "policies", "folder"),
            _asset("regional-id", "regional", "folder"),
            {"uploadUrl": "https://upload.test/one", "downloadUrl": "s3://one"},
            _asset("security", "security.pdf"),
            {"uploadUrl": "https://upload.test/two", "downloadUrl": "s3://two"},
            _asset("eu", "eu.txt"),
        ]
    )

    with patch("aixplain.v2.file.requests.put", return_value=Mock(ok=True)):
        folder = aix.File(root).save()

    assert folder.id == "root"
    folder_calls = [item for item in aix.client.post.call_args_list if item.args[0].endswith("/folder")]
    assert [item.kwargs["json"] for item in folder_calls] == [
        {"name": "empty", "description": ""},
        {"name": "policies", "description": ""},
        {"name": "regional", "description": "", "parentId": "policies-id"},
    ]
    file_calls = [item for item in aix.client.post.call_args_list if item.args[0].endswith("/file")]
    assert file_calls[0].kwargs["json"]["parentId"] == "policies-id"
    assert file_calls[1].kwargs["json"]["parentId"] == "regional-id"


def test_get_rebuilds_recursive_tree(aix):
    """Rebuild nested Files from a breadth-first parentId response."""
    aix.client.get = Mock(
        side_effect=[
            _asset("root", "reference", "folder", children=[]),
            [
                _asset("policy", "policies", "folder", parentId="root"),
                _asset("doc", "handbook.pdf", parentId="root"),
                _asset("security", "security.pdf", parentId="policy"),
            ],
        ]
    )

    folder = aix.File.get("team/reference")

    assert folder.is_dir
    assert [child.name for child in folder.children] == ["policies", "handbook.pdf"]
    assert folder.children[0].children[0].name == "security.pdf"
    assert all(isinstance(child, aix.File) for child in folder.children)


def test_get_retains_immediate_children_when_recursive_endpoint_is_forbidden(aix):
    """Gracefully support environments that do not expose recursive children."""
    aix.client.get = Mock(
        side_effect=[
            _asset(
                "root",
                "reference",
                "folder",
                children=[_asset("doc", "handbook.pdf")],
            ),
            APIError("Forbidden", status_code=403),
        ]
    )

    folder = aix.File.get("root")

    assert [child.name for child in folder.children] == ["handbook.pdf"]
    assert isinstance(folder.children[0], aix.File)


def test_search_returns_standard_page(aix):
    """Map query and pagination to the File paginate API."""
    aix.client.post = Mock(return_value={"results": [_asset("1", "handbook.pdf")], "total": 12, "pageTotal": 1})

    page = aix.File.search(query="handbook", page_size=10, file_type=FileType.FILE)

    assert isinstance(page, Page)
    assert isinstance(page.results[0], aix.File)
    assert page.total == 12
    assert aix.client.post.call_args.kwargs["json"]["q"] == "handbook"
    assert aix.client.post.call_args.kwargs["json"]["fileType"] == "file"


def test_folder_download_extracts_one_zip_safely(tmp_path, aix):
    """Use one request and preserve the archived directory tree."""
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("policies/security.txt", "safe")
        bundle.writestr("empty/", "")
    response = Mock()
    response.iter_content.return_value = [archive.getvalue()]
    aix.client.request_stream = Mock(return_value=response)
    folder = aix.File(id="root", name="reference", fileType="folder")

    result = Path(folder.download(tmp_path / "reference"))

    assert (result / "policies" / "security.txt").read_text() == "safe"
    assert (result / "empty").is_dir()
    aix.client.request_stream.assert_called_once()


def test_folder_download_rejects_zip_traversal(tmp_path, aix):
    """Reject archive members outside the requested destination."""
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../../outside.txt", "unsafe")
    response = Mock()
    response.iter_content.return_value = [archive.getvalue()]
    aix.client.request_stream = Mock(return_value=response)
    folder = aix.File(id="root", name="reference", fileType="folder")

    with pytest.raises(ResourceError, match="Unsafe ZIP entry"):
        folder.download(tmp_path / "reference")
    assert not (tmp_path.parent / "outside.txt").exists()
