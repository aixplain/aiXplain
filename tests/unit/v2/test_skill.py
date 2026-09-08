"""Unit tests for Skill content updates.

Covers the fix for "Skill Update on Agent Not Persisting": Skill.save() must
re-parse file_path and re-upload edited content on every call (not just at
construction), and the file-tree upload must update an existing node in place
(PUT) instead of colliding on name (POST). Also covers the new public
Skill.list_files()/Skill.update() surface built on top of that fix.
"""

import os
from unittest.mock import Mock, call

import pytest

from aixplain import Aixplain
from aixplain.v2.exceptions import ResourceError, ValidationError
from aixplain.v2.resource import BaseResource


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def _save_applying_kwargs(self, *args, **kwargs):
    """Stand in for BaseResource.save, keeping its attribute-shortcut behaviour.

    The real base save assigns every kwarg it recognises before building the
    payload; a no-op stub would hide whether Skill.save cooperates with that.
    """
    for key, value in kwargs.items():
        if hasattr(self, key):
            setattr(self, key, value)
    return self


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

        # The SKILL.md branch also writes the asset itself (see
        # TestUpdatePersistsMetadata), so assert on the file-node call only.
        assert aix.client.request.call_args_list[0] == call(
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


class TestSaveRefreshesFrontmatterMetadata:
    """A re-parse must adopt an edited frontmatter, not just an edited body.

    ``_load_from_path`` assigned with ``or`` precedence, so once ``description``
    was truthy the second save kept the stale value — and the frontmatter
    description is the routing signal an agent sees and what ``as_tool()``
    embeds, so the re-upload fixed the body and left routing on the old text.
    """

    def _staged(self, aix, skill_dir, monkeypatch):
        skill = aix.Skill(file_path=str(skill_dir))
        skill.id = "skill-1"
        monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)
        skill._tree_index = Mock(return_value={"SKILL.md": "file-id"})
        skill._upload = Mock(return_value="https://upload.example/SKILL.md")
        aix.client.request = Mock(return_value={"id": "file-id"})
        return skill

    def test_second_save_picks_up_an_edited_description(self, aix, tmp_path, monkeypatch):
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: s\ndescription: v1 desc\n---\n\nv1 body\n", encoding="utf-8"
        )
        skill = self._staged(aix, skill_dir, monkeypatch)
        skill.save()
        assert skill.description == "v1 desc"

        (skill_dir / "SKILL.md").write_text(
            "---\nname: s\ndescription: v2 desc\n---\n\nv2 body\n", encoding="utf-8"
        )
        skill.save()

        assert skill.description == "v2 desc", "an edited frontmatter description must reach the asset"
        assert skill.instructions.strip() == "v2 body"

    def test_second_save_picks_up_an_edited_name(self, aix, tmp_path, monkeypatch):
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: old-name\ndescription: d\n---\n\nb\n", encoding="utf-8")
        skill = self._staged(aix, skill_dir, monkeypatch)
        skill.save()
        assert skill.name == "old-name"

        (skill_dir / "SKILL.md").write_text("---\nname: new-name\ndescription: d\n---\n\nb\n", encoding="utf-8")
        skill.save()

        assert skill.name == "new-name"

    def test_a_developer_override_still_wins_over_the_file(self, aix, tmp_path, monkeypatch):
        """The file wins over its own earlier parse — never over an explicit assignment."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: s\ndescription: v1 desc\n---\n\nb\n", encoding="utf-8")
        skill = self._staged(aix, skill_dir, monkeypatch)
        skill.save()

        skill.description = "set by hand"
        (skill_dir / "SKILL.md").write_text("---\nname: s\ndescription: v2 desc\n---\n\nb\n", encoding="utf-8")
        skill.save()

        assert skill.description == "set by hand"

    def test_an_explicit_constructor_description_wins_over_frontmatter(self, aix, tmp_path):
        """The documented construction-time precedence must not regress."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: s\ndescription: from file\n---\n\nb\n", encoding="utf-8")

        skill = aix.Skill(file_path=str(skill_dir), description="explicit")

        assert skill.description == "explicit"


class TestSaveWithReassignedFilePath:
    """``save(file_path=...)`` must upload the path it was just handed.

    The base ``save()`` applies attribute shortcuts *after* ``Skill.save`` runs,
    so re-parsing ``self.file_path`` first staged the previous bundle and
    published the wrong content under the new path.
    """

    def test_kwarg_file_path_is_staged_before_the_upload(self, aix, tmp_path, monkeypatch):
        v1 = tmp_path / "v1"
        v1.mkdir()
        (v1 / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\n\nv1 body\n", encoding="utf-8")
        v2 = tmp_path / "v2"
        v2.mkdir()
        (v2 / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\n\nv2 body\n", encoding="utf-8")

        skill = aix.Skill(file_path=str(v1))
        skill.id = "skill-1"
        monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)
        skill._tree_index = Mock(return_value={"SKILL.md": "file-id"})
        uploaded = []
        skill._upload = Mock(side_effect=lambda path: uploaded.append(path) or "https://upload.example/x")
        aix.client.request = Mock(return_value={"id": "file-id"})

        skill.save(file_path=str(v2))

        assert len(uploaded) == 1
        with open(uploaded[0], encoding="utf-8") as handle:
            assert "v2 body" in handle.read(), "save(file_path=...) must upload the new bundle"
        assert skill.instructions.strip() == "v2 body"

    def test_kwarg_file_path_on_a_fetched_skill_uploads_the_bundle(self, aix, tmp_path, monkeypatch):
        """A Skill.get() handle has file_path=None; assigning one via save() must still upload."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\n\nbody\n", encoding="utf-8")

        skill = aix.Skill(id="skill-1", name="s")
        monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)
        skill._tree_index = Mock(return_value={"SKILL.md": "file-id"})
        skill._upload = Mock(return_value="https://upload.example/SKILL.md")
        aix.client.request = Mock(return_value={"id": "file-id"})

        skill.save(file_path=str(skill_dir))

        assert skill._upload.call_count == 1, "a newly assigned file_path must be uploaded, not skipped"


class TestMetadataOnlySaveWithoutTheAuthoringPath:
    """An already-saved skill stays editable once its authoring folder is gone.

    Re-parsing unconditionally made every ``save()`` touch disk, so a
    metadata-only update (``save(description=...)``) raised ``ValueError`` after
    a temp authoring folder was cleaned up or the object moved machines.
    """

    def test_metadata_save_warns_and_skips_the_upload(self, aix, tmp_path, monkeypatch):
        skill_dir = tmp_path / "gone"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\n\nbody\n", encoding="utf-8")

        skill = aix.Skill(file_path=str(skill_dir))
        skill.id = "skill-1"
        monkeypatch.setattr(BaseResource, "save", _save_applying_kwargs)
        skill._upload = Mock()
        skill._tree_index = Mock(return_value={})

        (skill_dir / "SKILL.md").unlink()
        skill_dir.rmdir()

        with pytest.warns(UserWarning, match="Skill path not found"):
            skill.save(description="new desc")

        assert skill.description == "new desc"
        skill._upload.assert_not_called()

    def test_an_unsaved_skill_still_rejects_a_missing_path(self, aix):
        """With no id there is no backend bundle to fall back on — this must stay an error."""
        with pytest.raises(ValueError, match="Skill path not found"):
            aix.Skill(file_path="/no/such/skill/folder")

    def test_constructing_a_saved_skill_over_a_missing_path_does_not_raise(self, aix):
        """aix.Skill(id=..., file_path=...) must not fail construction on a stale path."""
        with pytest.warns(UserWarning, match="Skill path not found"):
            skill = aix.Skill(id="skill-1", name="s", file_path="/no/such/skill/folder")

        assert skill.id == "skill-1"


class TestDeletedSaveRaisesOneExceptionType:
    """The deleted-save guard must run before ``save()`` touches the disk (BUG-1093)."""

    def test_deleted_skill_with_a_live_path_raises_resource_error(self, aix, tmp_path):
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\n\nb\n", encoding="utf-8")
        skill = aix.Skill(file_path=str(skill_dir))
        skill.id = "skill-1"
        skill.mark_as_deleted()

        with pytest.raises(ResourceError, match="deleted"):
            skill.save()

    def test_deleted_skill_with_a_missing_path_raises_resource_error_too(self, aix):
        """The path check must not pre-empt the guard with a ValueError."""
        skill = aix.Skill(id="skill-1", name="s")
        skill.file_path = "/no/such/skill/folder"
        skill.mark_as_deleted()

        with pytest.raises(ResourceError, match="deleted"):
            skill.save()


class TestUpdatePersistsMetadata:
    """``update("SKILL.md")`` must write the parsed description to the asset.

    It mutated ``self.description`` and never saved it, so the backend kept
    advertising the old routing signal while this object silently disagreed —
    and ``refresh()`` only copies ``status``/``updated_at``, so nothing
    reconciled it.
    """

    def test_new_description_is_written_to_the_asset(self, aix, tmp_path):
        skill = aix.Skill(id="skill-1", name="s", description="old desc")
        skill._tree_index = Mock(return_value={"SKILL.md": "file-id"})
        skill._upload = Mock(return_value="https://upload.example/SKILL.md")
        aix.client.request = Mock(return_value={"id": "file-id"})

        new_md = tmp_path / "SKILL.md"
        new_md.write_text("---\nname: s\ndescription: new desc\n---\n\nnew body\n", encoding="utf-8")

        skill.update(str(new_md))

        assert skill.description == "new desc"
        asset_puts = [
            c for c in aix.client.request.call_args_list if c.args == ("put", "sdk/skill/skill-1")
        ]
        assert len(asset_puts) == 1, "the parsed description must reach the asset, not just the file node"
        assert asset_puts[0].kwargs["json"]["description"] == "new desc"

    def test_a_non_skill_md_update_leaves_the_asset_alone(self, aix, tmp_path):
        """Pushing a script must not rewrite the asset's metadata."""
        skill = aix.Skill(id="skill-1", name="s", description="old desc")
        skill._tree_index = Mock(return_value={})
        skill._upload = Mock(return_value="https://upload.example/helper.py")
        aix.client.request = Mock(return_value={"id": "file-id"})

        helper = tmp_path / "helper.py"
        helper.write_text("print(1)", encoding="utf-8")

        skill.update(str(helper))

        assert [c for c in aix.client.request.call_args_list if c.args == ("put", "sdk/skill/skill-1")] == []
        assert skill.description == "old desc"

    def test_a_later_save_adopts_the_authoring_folder_description(self, aix, tmp_path, monkeypatch):
        """update()'s description came from a file, so it must not shadow file_path's."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: s\ndescription: folder desc\n---\n\nb\n", encoding="utf-8")
        skill = aix.Skill(file_path=str(skill_dir))
        skill.id = "skill-1"
        skill._tree_index = Mock(return_value={"SKILL.md": "file-id"})
        skill._upload = Mock(return_value="https://upload.example/SKILL.md")
        aix.client.request = Mock(return_value={"id": "file-id"})

        pushed = tmp_path / "SKILL.md"
        pushed.write_text("---\nname: s\ndescription: pushed desc\n---\n\nb\n", encoding="utf-8")
        skill.update(str(pushed))
        assert skill.description == "pushed desc"

        monkeypatch.setattr(BaseResource, "save", lambda self, *a, **k: self)
        skill.save()

        assert skill.description == "folder desc"
