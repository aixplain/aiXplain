"""Unit tests for the v2 Skill asset: path handling, SKILL.md parsing, download."""

import os
from unittest.mock import Mock

import pytest

from aixplain.v2.skill import Skill, _parse_skill_md


SKILL_MD = """---
name: pdf-filler
description: Fill PDF forms.
requires:
  - aws/textract
---
# Instructions

Fill the form.
"""


def _make_skill_folder(tmp_path, content=SKILL_MD, folder_name="my-skill"):
    folder = tmp_path / folder_name
    folder.mkdir()
    (folder / "SKILL.md").write_text(content, encoding="utf-8")
    return folder


# --------------------------------------------------------------------- #
# Path handling
# --------------------------------------------------------------------- #
class TestSkillPathHandling:
    def test_tilde_is_expanded(self, tmp_path, monkeypatch):
        folder = _make_skill_folder(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))
        skill = Skill(file_path="~/my-skill")
        assert skill.name == "pdf-filler"
        assert skill._local_path == str(folder)

    def test_missing_path_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Skill path not found"):
            Skill(file_path=str(tmp_path / "does-not-exist"))

    def test_folder_without_skill_md_raises(self, tmp_path):
        folder = tmp_path / "empty-skill"
        folder.mkdir()
        with pytest.raises(ValueError, match="must contain a SKILL.md"):
            Skill(file_path=str(folder))

    def test_single_file_must_be_markdown(self, tmp_path):
        txt = tmp_path / "skill.txt"
        txt.write_text("not markdown", encoding="utf-8")
        with pytest.raises(ValueError, match=r"Markdown \(\.md\) file"):
            Skill(file_path=str(txt))

    def test_single_md_file_accepted(self, tmp_path):
        md = tmp_path / "calculator.md"
        md.write_text(SKILL_MD, encoding="utf-8")
        skill = Skill(file_path=str(md))
        assert skill.name == "pdf-filler"
        assert skill._local_is_file is True

    def test_single_md_file_case_insensitive_extension(self, tmp_path):
        md = tmp_path / "calculator.MD"
        md.write_text("# just a body\n", encoding="utf-8")
        skill = Skill(file_path=str(md))
        assert skill.name == "calculator"
        assert skill._local_is_file is True


# --------------------------------------------------------------------- #
# SKILL.md frontmatter parsing
# --------------------------------------------------------------------- #
class TestParseSkillMd:
    def test_valid_frontmatter(self):
        name, description, requires, body = _parse_skill_md(SKILL_MD)
        assert name == "pdf-filler"
        assert description == "Fill PDF forms."
        assert requires == ["aws/textract"]
        assert body.startswith("# Instructions")

    def test_malformed_yaml_raises_value_error(self, tmp_path):
        bad = "---\nname: [unclosed\n---\nbody\n"
        with pytest.raises(ValueError, match="Invalid SKILL.md frontmatter"):
            _parse_skill_md(bad)
        # Same behavior through the authoring path.
        folder = _make_skill_folder(tmp_path, content=bad, folder_name="bad-skill")
        with pytest.raises(ValueError, match="Invalid SKILL.md frontmatter"):
            Skill(file_path=str(folder))

    def test_scalar_frontmatter_falls_back_to_path_name(self, tmp_path):
        scalar = "---\njust a string\n---\n# Body\n"
        name, description, requires, body = _parse_skill_md(scalar)
        assert name is None
        assert description is None
        assert requires == []
        assert body.startswith("# Body")
        # Through the authoring path, name falls back to the folder name.
        folder = _make_skill_folder(tmp_path, content=scalar, folder_name="scalar-skill")
        skill = Skill(file_path=str(folder))
        assert skill.name == "scalar-skill"

    def test_list_frontmatter_falls_back_to_path_name(self, tmp_path):
        listy = "---\n- a\n- b\n---\n# Body\n"
        name, _, requires, _ = _parse_skill_md(listy)
        assert name is None
        assert requires == []
        folder = _make_skill_folder(tmp_path, content=listy, folder_name="list-skill")
        assert Skill(file_path=str(folder)).name == "list-skill"

    def test_no_frontmatter(self):
        name, description, requires, body = _parse_skill_md("# Only body\n")
        assert name is None and description is None and requires == []
        assert body == "# Only body\n"


# --------------------------------------------------------------------- #
# download()
# --------------------------------------------------------------------- #
def _make_saved_skill(name):
    skill = Skill(id="skill-123", name=name)
    skill.context = Mock()
    skill.context.client.request_raw = Mock(return_value=Mock(content=b"zip-bytes"))
    return skill


class TestSkillDownload:
    def test_default_path_sanitizes_slashed_name(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        skill = _make_saved_skill("ws/skill")
        written = skill.download()
        assert written == "./ws-skill.zip"
        assert (tmp_path / "ws-skill.zip").read_bytes() == b"zip-bytes"

    def test_default_path_uses_plain_name(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        skill = _make_saved_skill("plain-skill")
        assert skill.download() == "./plain-skill.zip"

    def test_missing_name_requires_explicit_path(self):
        skill = _make_saved_skill(None)
        with pytest.raises(ValueError, match="file_path"):
            skill.download()

    def test_explicit_path_bypasses_name(self, tmp_path):
        skill = _make_saved_skill(None)
        target = tmp_path / "bundle.zip"
        assert skill.download(file_path=str(target)) == str(target)
        assert target.read_bytes() == b"zip-bytes"
