"""Tests for the unified v2 File resource."""

from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, call, patch
import zipfile

import pytest

from aixplain import Aixplain
from aixplain.v2 import File, FileType, Page, Privacy
from aixplain.v2.exceptions import APIError, FileUploadError, ResourceError, ValidationError


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated SDK client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def _asset(identifier: str, name: str, file_type: str = "file", **kwargs):
    """Build a minimal File asset response."""
    return {"id": identifier, "name": name, "fileType": file_type, **kwargs}


def test_public_exports_and_compatibility_alias(aix):
    """Expose File publicly and retain Resource as one implementation, deprecated consistently everywhere."""
    assert aix.File.context is aix

    # ``aix.Resource`` (the instance property), ``aixplain.v2.Resource`` (the
    # package-level re-export), and ``aixplain.v2.file.Resource`` (the module
    # attribute) must all resolve to the exact same File class, and all three
    # must warn — none silently, unlike before this fix.
    with pytest.warns(DeprecationWarning, match="Aixplain\\(\\).Resource"):
        instance_resource = aix.Resource
    with pytest.warns(DeprecationWarning, match="aixplain.v2.Resource"):
        import aixplain.v2 as v2_package

        package_resource = v2_package.Resource
    with pytest.warns(DeprecationWarning, match="aixplain.v2.file.Resource"):
        from aixplain.v2 import file as file_module

        module_resource = file_module.Resource

    assert instance_resource is aix.File
    assert package_resource is File
    assert module_resource is File
    assert issubclass(instance_resource, File)
    # Same class both ways -> isinstance agrees in both directions (no more split).
    document = aix.File(id="file-1", name="handbook.pdf", fileType="file")
    assert isinstance(document, aix.Resource)
    assert isinstance(document, aix.File)


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


def test_is_temp_is_not_a_constructor_parameter(tmp_path, aix):
    """is_temp has no real effect, so it must not be offered as a constructor kwarg."""
    local_file = tmp_path / "data.csv"
    local_file.write_text("a,b\n1,2\n")

    with pytest.raises(TypeError):
        aix.File(local_file, is_temp=False)

    assert aix.File(local_file).is_temp is True


def test_save_local_file_promotes_upload_to_asset(tmp_path, aix):
    """Upload first, then create a permanent root File asset."""
    local_file = tmp_path / "data.csv"
    local_file.write_text("a,b\n1,2\n")
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            {"uploadUrl": "https://bucket.s3.amazonaws.com/upload", "downloadUrl": "s3://bucket/temp/data.csv"},
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
            {"uploadUrl": "https://bucket.s3.amazonaws.com/upload", "downloadUrl": "s3://bucket/temp/report.pdf"},
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
            {"uploadUrl": "https://bucket.s3.amazonaws.com/one", "downloadUrl": "s3://one"},
            _asset("security", "security.pdf"),
            {"uploadUrl": "https://bucket.s3.amazonaws.com/two", "downloadUrl": "s3://two"},
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
    aix.client.request = Mock(return_value={"results": [_asset("1", "handbook.pdf")], "total": 12, "pageTotal": 1})

    page = aix.File.search(query="handbook", page_size=10, file_type=FileType.FILE)

    assert isinstance(page, Page)
    assert isinstance(page.results[0], aix.File)
    assert page.total == 12
    assert aix.client.request.call_args.args[:2] == ("post", "sdk/file-asset/paginate")
    assert aix.client.request.call_args.kwargs["json"]["q"] == "handbook"
    assert aix.client.request.call_args.kwargs["json"]["fileType"] == "file"


def test_search_rejects_unknown_filters(aix):
    """Reject a typo'd or unsupported filter instead of silently matching everything."""
    with pytest.raises(ValidationError, match="unsupported filter"):
        aix.File.search(does_not_exist="x")


def test_search_defaults_to_newest_created_first(aix):
    """No sort_by/sort_order means newest-created-first, same as before."""
    aix.client.request = Mock(return_value={"results": [], "total": 0, "pageTotal": 1})

    aix.File.search()

    assert aix.client.request.call_args.kwargs["json"]["sort"] == [{"field": "createdAt", "dir": -1}]


def test_search_accepts_sort_by_and_sort_order(aix):
    """sort_by/sort_order — inherited from BaseSearchParams like every other resource — must actually work."""
    aix.client.request = Mock(return_value={"results": [], "total": 0, "pageTotal": 1})

    aix.File.search(sort_by=aix.SortBy.NAME, sort_order=aix.SortOrder.ASC)

    assert aix.client.request.call_args.kwargs["json"]["sort"] == [{"field": "name", "dir": 1}]


def test_search_accepts_ownership(aix):
    """Ownership — inherited from BaseSearchParams — must actually reach the backend, not be rejected."""
    aix.client.request = Mock(return_value={"results": [], "total": 0, "pageTotal": 1})

    aix.File.search(ownership=aix.OwnershipType.PRIVATE)

    assert aix.client.request.call_args.kwargs["json"]["ownership"] == "PRIVATE"


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


def test_download_defaults_destination_to_name(tmp_path, aix, monkeypatch):
    """Downloading without a destination writes to ./{name} in the current directory."""
    response = Mock()
    response.iter_content.return_value = [b"data"]
    aix.client.request_stream = Mock(return_value=response)
    document = aix.File(id="file-1", name="handbook.pdf", fileType="file")
    monkeypatch.chdir(tmp_path)

    result = document.download()

    assert result == "handbook.pdf"
    assert (tmp_path / "handbook.pdf").read_bytes() == b"data"


def test_download_sanitizes_a_traversal_name_before_using_it_as_a_path(tmp_path, aix, monkeypatch):
    """A hostile/unexpected backend name must not write outside the target directory."""
    response = Mock()
    response.iter_content.return_value = [b"data"]
    aix.client.request_stream = Mock(return_value=response)
    document = aix.File(id="file-1", name="../../etc/passwd", fileType="file")
    monkeypatch.chdir(tmp_path)

    result = document.download()

    assert result == "passwd"
    assert (tmp_path / "passwd").read_bytes() == b"data"
    assert not (tmp_path.parent.parent / "etc" / "passwd").exists()


def test_delete_calls_the_backend_and_marks_deleted(aix):
    """File.delete() DELETEs the asset and marks the instance deleted."""
    document = aix.File(id="file-1", name="handbook.pdf", fileType="file")
    aix.client.request_raw = Mock(return_value=Mock())

    result = document.delete()

    aix.client.request_raw.assert_called_once_with("delete", "sdk/file-asset/file-1")
    assert document.is_deleted is True
    assert result.deleted_id == "file-1"


def test_delete_rejects_a_child_file_node(aix):
    """A child from folder.children has no standalone delete endpoint; delete the folder instead."""
    aix.client.get = Mock(
        side_effect=[
            _asset("root", "reference", "folder", children=[]),
            [_asset("doc", "handbook.pdf", parentId="root")],
        ]
    )
    folder = aix.File.get("root")
    child = folder.children[0]

    # delete() runs through the ``with_hooks`` operation wrapper, which wraps
    # a non-ResourceError into a ResourceError — the message still carries the
    # original explanation.
    with pytest.raises(ResourceError, match="child under folder"):
        child.delete()


def test_get_signed_url_addresses_a_root_file_by_its_own_id_twice(aix):
    """File-asset responses carry no stable url; fetch a short-lived one on demand."""
    document = aix.File(id="file-1", name="handbook.pdf", fileType="file")
    aix.client.get = Mock(return_value={"url": "https://signed.example.com/handbook.pdf?sig=abc"})

    url = document.get_signed_url()

    aix.client.get.assert_called_once_with("sdk/file-asset/file-1/file/file-1/url")
    assert url == "https://signed.example.com/handbook.pdf?sig=abc"


def test_get_signed_url_passes_expires_in(aix):
    """An explicit expiry is forwarded as a query param."""
    document = aix.File(id="file-1", name="handbook.pdf", fileType="file")
    aix.client.get = Mock(return_value={"url": "https://signed.example.com/handbook.pdf"})

    document.get_signed_url(expires_in=120)

    aix.client.get.assert_called_once_with("sdk/file-asset/file-1/file/file-1/url", params={"expiresIn": 120})


def test_get_signed_url_rejects_unsaved_file(aix):
    """An unsaved File has no id to address a signed url with."""
    document = aix.File(name="notes.txt")

    with pytest.raises(ValidationError, match="must be saved"):
        document.get_signed_url()


def test_get_signed_url_rejects_folder(aix):
    """A folder has no single signed url; download it as a zip instead."""
    folder = aix.File(id="folder-1", name="reference", fileType="folder")

    with pytest.raises(ValidationError, match="no single signed url"):
        folder.get_signed_url()


def test_get_signed_url_addresses_a_child_file_by_its_root_and_own_id(aix):
    """A child from folder.children must address its parent folder's asset id, not its own."""
    aix.client.get = Mock(
        side_effect=[
            _asset("root", "reference", "folder", children=[]),
            [_asset("doc", "handbook.pdf", parentId="root")],
            {"url": "https://signed.example.com/handbook.pdf"},
        ]
    )
    folder = aix.File.get("root")
    child = folder.children[0]

    url = child.get_signed_url()

    assert aix.client.get.call_args.args[0] == "sdk/file-asset/root/file/doc/url"
    assert url == "https://signed.example.com/handbook.pdf"


def test_save_directory_populates_children_without_a_follow_up_get(tmp_path, aix):
    """A saved folder's tree is available immediately, not only after File.get()."""
    root = tmp_path / "reference"
    (root / "policies").mkdir(parents=True)
    (root / "policies" / "security.pdf").write_bytes(b"pdf")
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            _asset("root", "reference", "folder"),
            _asset("policies-id", "policies", "folder"),
            {"uploadUrl": "https://bucket.s3.amazonaws.com/one", "downloadUrl": "s3://one"},
            _asset("security", "security.pdf"),
        ]
    )

    with patch("aixplain.v2.file.requests.put", return_value=Mock(ok=True)):
        folder = aix.File(root).save()

    assert [child.name for child in folder.children] == ["policies"]
    assert [child.name for child in folder.children[0].children] == ["security.pdf"]
    assert all(isinstance(child, aix.File) for child in folder.children)
    # Every node in the tree must know it lives under the root asset, not
    # under itself, so get_signed_url()/delete() address it correctly.
    assert folder.children[0]._root_id == "root"
    assert folder.children[0].children[0]._root_id == "root"


def test_save_directory_rolls_back_on_partial_failure(tmp_path, aix):
    """A failed upload mid-directory deletes the partially created root folder."""
    root = tmp_path / "reference"
    (root / "policies").mkdir(parents=True)
    (root / "policies" / "security.pdf").write_bytes(b"pdf")
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            _asset("root", "reference", "folder"),
            _asset("policies-id", "policies", "folder"),
            RuntimeError("network blip"),
        ]
    )
    # The rollback delete must use ``request_raw`` (an empty response body),
    # not ``request`` (which always calls ``.json()`` and would make a
    # successful rollback look like it failed).
    aix.client.request_raw = Mock(return_value=Mock())

    with pytest.raises(ResourceError, match="partial upload"):
        aix.File(root).save()

    aix.client.request_raw.assert_called_once_with("delete", "sdk/file-asset/root")


def test_save_directory_does_not_roll_back_on_a_hydration_only_failure(tmp_path, aix):
    """A local parsing error after a fully successful upload must not delete the folder."""
    root = tmp_path / "reference"
    root.mkdir()
    (root / "note.txt").write_text("hi")
    aix.client.get = Mock(return_value={"allowed": True})
    aix.client.post = Mock(
        side_effect=[
            _asset("root", "reference", "folder"),
            {"uploadUrl": "https://bucket.s3.amazonaws.com/one", "downloadUrl": "s3://one"},
            # An unrecognized fileType breaks hydration (``FileType(...)`` raises)
            # even though the upload itself fully succeeded.
            _asset("note", "note.txt", "not-a-real-type"),
        ]
    )
    aix.client.request = Mock()
    aix.client.request_raw = Mock()

    with patch("aixplain.v2.file.requests.put", return_value=Mock(ok=True)):
        with pytest.raises(ValueError):
            aix.File(root).save()

    aix.client.request.assert_not_called()
    aix.client.request_raw.assert_not_called()
