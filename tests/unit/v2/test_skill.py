"""Unit tests for Skill content updates.

Covers the fix for "Skill Update on Agent Not Persisting": Skill.save() must
re-parse file_path and re-upload edited content on every call (not just at
construction), and the file-tree upload must update an existing node in place
(PUT) instead of colliding on name (POST). Also covers the new public
Skill.list_files()/Skill.update() surface built on top of that fix.
"""

import os
from unittest.mock import Mock

import pytest

from aixplain import Aixplain
from aixplain.v2.exceptions import ValidationError
from aixplain.v2.resource import BaseResource


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def _write_skill_md(dir_path: str, body: str, name: str = "s") -> None:
    with open(os.path.join(dir_path, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(f"---\nname: {name}\ndescription: test skill\n---\n\n{body}\n")


class TestListFiles:
    """Skill.list_files() wraps the backend tree with no endpoints exposed."""

    def test_returns_sorted_paths_from_tree(self, aix):
        skill = aix.Skill(id="skill-1", name="s")
        skill._tree_index = Mock(
            return_value={"resources/notes.txt": "f2", "SKILL.md": "f1", "resources": "d1"}
        )

        assert skill.list_files() == ["SKILL.md", "resources", "resources/notes.txt"]


class TestUpdate:
    """Skill.update(path, name) — the granular single-file/folder update API."""

    def test_updates_existing_file_in_place(self, aix, tmp_path):
        """A node already at `name` must be PUT, never re-created via POST."""
        skill = aix.Skill(id="skill-1", name="s")
        skill._tree_index = Mock(return_value={"SKILL.md": "existing-file-id"})
        skill._upload = Mock(return_value="https://upload.example/SKILL.md")
        aix.client.request = Mock(return_value={"id": "existing-file-id"})

        new_md = tmp_path / "SKILL.md"
        new_md.write_text("new content", encoding="utf-8")

        skill.update(str(new_md))

        aix.client.request.assert_called_once_with(
            "put",
            "sdk/skill/skill-1/file/existing-file-id",
            json={
                "name": "SKILL.md",
                "url": "https://upload.example/SKILL.md",
                "description": "",
                "parentId": None,
            },
        )

    def test_creates_new_file_and_missing_parent_folder(self, aix, tmp_path):
        """A genuinely new nested file must POST-create it, creating any missing folder first."""
        skill = aix.Skill(id="skill-1", name="s")
        skill._tree_index = Mock(return_value={})
        skill._upload = Mock(return_value="https://upload.example/notes.txt")
        aix.client.request = Mock(side_effect=[{"id": "folder-id"}, {"id": "file-id"}])

        note = tmp_path / "notes.txt"
        note.write_text("hello", encoding="utf-8")

        skill.update(str(note), "resources/notes.txt")

        calls = aix.client.request.call_args_list
        assert len(calls) == 2
        assert calls[0].args == ("post", "sdk/skill/skill-1/folder")
        assert calls[0].kwargs["json"] == {"name": "resources", "description": "", "parentId": None}
        assert calls[1].args == ("post", "sdk/skill/skill-1/file")
        assert calls[1].kwargs["json"] == {
            "name": "notes.txt",
            "url": "https://upload.example/notes.txt",
            "description": "",
            "parentId": "folder-id",
        }

    def test_defaults_name_to_local_basename(self, aix, tmp_path):
        """Omitting `name` targets the local file's own basename."""
        skill = aix.Skill(id="skill-1", name="s")
        skill._tree_index = Mock(return_value={})
        skill._upload = Mock(return_value="https://upload.example/helper.py")
        aix.client.request = Mock(return_value={"id": "file-id"})

        helper = tmp_path / "helper.py"
        helper.write_text("print(1)", encoding="utf-8")

        skill.update(str(helper))

        aix.client.request.assert_called_once_with(
            "post",
            "sdk/skill/skill-1/file",
            json={"name": "helper.py", "url": "https://upload.example/helper.py", "description": "", "parentId": None},
        )

    def test_raises_for_missing_local_path(self, aix):
        skill = aix.Skill(id="skill-1", name="s")

        with pytest.raises(ValueError, match="Path not found"):
            skill.update("/no/such/path/on/disk")

    def test_requires_the_skill_to_already_be_saved(self, aix, tmp_path):
        """update() targets an existing backend skill; an unsaved Skill has nothing to update."""
        skill = aix.Skill(name="not saved yet")
        target = tmp_path / "SKILL.md"
        target.write_text("content", encoding="utf-8")

        with pytest.raises(ValidationError):
            skill.update(str(target))


class TestSaveReupload:
    """Regression tests for 'Skill Update on Agent Not Persisting'.

    Before the fix, save() only ever parsed file_path inside __post_init__
    (construction time), so editing SKILL.md and calling save() again on an
    already-saved Skill silently skipped both the re-parse and the re-upload.
    """

    def test_second_save_on_a_folder_reparses_and_reuploads_edited_content(self, aix, tmp_path, monkeypatch):
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        _write_skill_md(str(skill_dir), "v1 body")

        skill = aix.Skill(id="skill-1", name="s")
        skill.file_path = str(skill_dir)

        monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)
        skill._tree_index = Mock(return_value={"SKILL.md": "file-id"})
        skill._upload = Mock(return_value="https://upload.example/SKILL.md")
        aix.client.request = Mock(return_value={"id": "file-id"})

        skill.save()
        assert skill.instructions.strip() == "v1 body"
        assert aix.client.request.call_count == 1

        _write_skill_md(str(skill_dir), "v2 body")  # edit on disk, same path
        skill.save()

        assert skill.instructions.strip() == "v2 body", "save() must re-parse file_path from disk on every call"
        assert aix.client.request.call_count == 2, "save() must re-upload the edited content, not silently skip it"

    def test_second_save_on_a_single_md_file_reparses_and_reuploads_edited_content(self, aix, tmp_path, monkeypatch):
        skill_md = tmp_path / "calculator.md"
        skill_md.write_text("---\nname: calc\ndescription: d\n---\n\nv1 body\n", encoding="utf-8")

        skill = aix.Skill(id="skill-1", name="s")
        skill.file_path = str(skill_md)

        monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)
        skill._tree_index = Mock(return_value={"SKILL.md": "file-id"})
        skill._upload = Mock(return_value="https://upload.example/calculator.md")
        aix.client.request = Mock(return_value={"id": "file-id"})

        skill.save()
        assert skill.instructions.strip() == "v1 body"

        skill_md.write_text("---\nname: calc\ndescription: d\n---\n\nv2 body\n", encoding="utf-8")
        skill.save()

        assert skill.instructions.strip() == "v2 body"
        assert aix.client.request.call_count == 2
