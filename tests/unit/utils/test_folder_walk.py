"""Tests for the safe folder-upload walk (BUG-1452)."""

import logging
import os

import pytest

from aixplain.utils.folder_walk import walk_upload_tree

symlinks = pytest.mark.skipif(os.name == "nt", reason="symlinks need privileges on Windows")


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


def collect(root, **kwargs):
    paths = []
    for dirpath, _dirnames, filenames in walk_upload_tree(str(root), **kwargs):
        rel = os.path.relpath(dirpath, root)
        rel = "" if rel == "." else rel.replace(os.sep, "/")
        paths.extend(f"{rel}/{name}" if rel else name for name in filenames)
    return sorted(paths)


@symlinks
def test_default_walk_skips_dotfiles_vcs_caches_and_escaping_symlinks(tmp_path):
    root = build_tree(tmp_path)
    assert collect(root) == ["SKILL.md", "inner.md", "scripts/a.py"]


@symlinks
def test_include_readmits_hidden_paths_but_never_an_escaping_symlink(tmp_path):
    root = build_tree(tmp_path)
    paths = collect(root, include=[".well-known/*", ".env", "notes.md"])
    assert ".well-known/info.json" in paths
    assert ".env" in paths
    assert "notes.md" not in paths
    assert ".git/config" not in paths


@symlinks
def test_symlinked_directories_are_pruned_from_dirnames(tmp_path):
    root = build_tree(tmp_path)
    top = next(iter(walk_upload_tree(str(root))))
    assert top[1] == ["scripts"]


@symlinks
def test_skipped_paths_are_logged_once_by_name(tmp_path, caplog):
    root = build_tree(tmp_path)
    with caplog.at_level(logging.WARNING, logger="aixplain.utils.folder_walk"):
        collect(root)
    records = [r for r in caplog.records if r.name == "aixplain.utils.folder_walk"]
    assert len(records) == 1
    message = records[0].getMessage()
    for name in (".env", ".git/", "__pycache__/", "notes.md", "linked_dir/"):
        assert name in message
    assert "AIXPLAIN_API_KEY=x" not in message


def test_clean_folder_walks_like_os_walk_without_warning(tmp_path, caplog):
    root = tmp_path / "clean"
    (root / "b").mkdir(parents=True)
    (root / "z.txt").write_text("z")
    (root / "a.txt").write_text("a")
    (root / "b" / "c.txt").write_text("c")
    with caplog.at_level(logging.WARNING):
        assert collect(root) == ["a.txt", "b/c.txt", "z.txt"]
    assert not caplog.records


@symlinks
def test_symlink_to_a_hidden_file_inside_the_root_is_skipped(tmp_path):
    root = tmp_path / "skill"
    (root / ".git").mkdir(parents=True)
    (root / ".env").write_text("AIXPLAIN_API_KEY=x")
    (root / ".git" / "config").write_text("[core]")
    (root / "SKILL.md").write_text("s")
    (root / "notes.md").symlink_to(root / ".env")
    (root / "cfg.txt").symlink_to(root / ".git" / "config")
    assert collect(root) == ["SKILL.md"]
    assert collect(root, include=[".env"]) == [".env", "SKILL.md", "notes.md"]
