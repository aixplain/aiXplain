"""Folder uploads never publish dotfiles, VCS folders or outward symlinks (BUG-1452).

Covers the three walks the ticket names: ``Skill.save`` on a folder,
``Skill.update`` on a folder and ``File.save`` on a directory. Uploads are
mocked; only the set of relative paths handed to the uploader is asserted.
"""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from aixplain import Aixplain
from aixplain.v2.resource import BaseResource

pytestmark = pytest.mark.skipif(os.name == "nt", reason="symlinks need privileges on Windows")


def build_tree(tmp_path):
    """A skill-like folder with secrets, VCS/cache folders and symlinks mixed in."""
    outside = tmp_path / "outside.txt"
    outside.write_text("not part of the folder")
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()
    (outside_dir / "secret.txt").write_text("nope")

    root = tmp_path / "skill"
    (root / "scripts").mkdir(parents=True)
    (root / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\n")
    (root / "scripts" / "a.py").write_text("print(1)")
    (root / ".env").write_text("AIXPLAIN_API_KEY=x")
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("[core]")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "x.pyc").write_bytes(b"\0")
    (root / "node_modules" / "pkg").mkdir(parents=True)
    (root / "node_modules" / "pkg" / "index.js").write_text("")
    (root / ".well-known").mkdir()
    (root / ".well-known" / "info.json").write_text("{}")
    if os.name != "nt":
        (root / "notes.md").symlink_to(outside)
        (root / "inner.md").symlink_to(root / "scripts" / "a.py")
        (root / "linked_dir").symlink_to(outside_dir, target_is_directory=True)
    return root


SAFE = ["SKILL.md", "inner.md", "scripts/a.py"]


@pytest.fixture
def aix() -> Aixplain:
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def _skill_with_recording_upload(aix):
    skill = aix.Skill(id="skill-1", name="s")
    skill._tree_index = Mock(return_value={})
    skill._ensure_folder = Mock(side_effect=lambda rel, existing: f"folder:{rel}")
    uploaded = []
    skill._put_or_post_file = Mock(side_effect=lambda local, rel, parent, existing: uploaded.append(rel))
    return skill, uploaded


def test_skill_save_folder_skips_unsafe_entries(aix, tmp_path, monkeypatch):
    root = build_tree(tmp_path)
    skill, uploaded = _skill_with_recording_upload(aix)
    skill.file_path = str(root)
    monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)

    skill.save()

    assert sorted(uploaded) == SAFE


def test_skill_save_include_readmits_a_hidden_path(aix, tmp_path, monkeypatch):
    root = build_tree(tmp_path)
    skill, uploaded = _skill_with_recording_upload(aix)
    skill.file_path = str(root)
    monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)

    skill.save(include=[".well-known/*"])

    assert sorted(uploaded) == sorted(SAFE + [".well-known/info.json"])
    assert not hasattr(skill, "include")


def test_skill_update_folder_skips_unsafe_entries(aix, tmp_path):
    root = build_tree(tmp_path)
    skill, uploaded = _skill_with_recording_upload(aix)

    skill.update(str(root), "resources")

    assert sorted(uploaded) == [f"resources/{p}" for p in SAFE]


def test_skill_update_single_named_file_is_not_filtered(aix, tmp_path):
    """Naming a single file is an explicit choice, so it is uploaded as asked."""
    root = build_tree(tmp_path)
    skill, uploaded = _skill_with_recording_upload(aix)

    skill.update(str(root / ".env"), "config/.env")

    assert uploaded == ["config/.env"]


def test_file_save_directory_skips_unsafe_entries(aix, tmp_path):
    root = build_tree(tmp_path)
    folders = []
    uploaded = []

    def post(path, json):
        if path == "sdk/file-asset":
            return {"id": "root", "name": json["name"], "fileType": "folder"}
        return {"id": f"file:{json['name']}", "name": json["name"], "fileType": "file"}

    aix.client.post = Mock(side_effect=post)
    document = aix.File(root)
    document._create_child_folder = Mock(
        side_effect=lambda root_id, path, parent_id: (
            folders.append(path.relative_to(root).as_posix())
            or {"id": f"dir:{path.name}", "name": path.name, "fileType": "folder"}
        )
    )
    document._upload_local_file = Mock(
        side_effect=lambda local: uploaded.append(Path(local).relative_to(root).as_posix()) or "s3://x"
    )

    document.save()

    assert sorted(uploaded) == SAFE
    assert folders == ["scripts"]


def test_file_save_directory_include_readmits_a_hidden_path(aix, tmp_path):
    root = build_tree(tmp_path)
    uploaded = []
    aix.client.post = Mock(
        side_effect=lambda path, json: {"id": f"id:{json['name']}", "name": json["name"], "fileType": "file"}
    )
    document = aix.File(root)
    document._create_child_folder = Mock(
        side_effect=lambda root_id, path, parent_id: {"id": f"dir:{path.name}", "name": path.name, "fileType": "folder"}
    )
    document._upload_local_file = Mock(
        side_effect=lambda local: uploaded.append(Path(local).relative_to(root).as_posix()) or "s3://x"
    )

    document.save(include=[".well-known/*"])

    assert ".well-known/info.json" in uploaded
    assert ".env" not in uploaded
