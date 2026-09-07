"""Functional tests for v2 Skill content updates.

Covers the fix for "Skill Update on Agent Not Persisting": updating an
already-saved skill's content (via the granular update()) must actually reach
the backend, and an agent using that skill must reflect the change on its very
next run - even a freshly re-fetched agent, ruling out any session/caching
explanation for the original bug.
"""

import os
import tempfile
import time
import zipfile

import pytest


SIGNAL_TEMPLATE = """---
name: {name}
description: Use this skill whenever the user asks for "the current signal". Follow the instructions in this skill exactly.
---

When the user asks for "the current signal", respond with exactly the single word: {signal}
Do not add any explanation, punctuation, or extra text - output only the signal word.
"""


def _write_skill_md(path, name, signal):
    with open(path, "w", encoding="utf-8") as f:
        f.write(SIGNAL_TEMPLATE.format(name=name, signal=signal))


@pytest.fixture
def skill_dir(tmp_path):
    """A minimal single-file skill folder, authored fresh per test."""
    d = tmp_path / "skill"
    d.mkdir()
    _write_skill_md(str(d / "SKILL.md"), f"func-test-skill-{int(time.time())}", "SIGNAL-ALPHA")
    return str(d)


@pytest.fixture
def saved_skill(client, skill_dir):
    """Create and persist a skill for a test, deleting it afterward."""
    skill = client.Skill(file_path=skill_dir)
    skill.save()
    yield skill
    try:
        skill.delete()
    except Exception:
        pass


class TestSkillListFiles:
    def test_lists_the_authored_file(self, saved_skill):
        assert saved_skill.list_files() == ["SKILL.md"]


class TestSkillUpdate:
    """Skill.update() pushes a single changed file/folder to an existing skill."""

    def test_update_replaces_skill_md_in_place(self, saved_skill, tmp_path):
        """update() must change the backend's existing file node, not create a duplicate."""
        new_md = tmp_path / "SKILL.md"
        _write_skill_md(str(new_md), saved_skill.name, "SIGNAL-BETA")

        saved_skill.update(str(new_md))

        assert saved_skill.list_files() == ["SKILL.md"], "must not create a duplicate node"

        download_dir = tempfile.mkdtemp(prefix="skill-update-test-")
        zip_path = saved_skill.download(file_path=os.path.join(download_dir, "skill.zip"))
        with zipfile.ZipFile(zip_path) as zf:
            content = zf.read("SKILL.md").decode("utf-8")

        assert "SIGNAL-BETA" in content
        assert "SIGNAL-ALPHA" not in content

    def test_update_adds_a_new_nested_file(self, saved_skill, tmp_path):
        """update() can add a brand-new file at a nested path without disturbing existing ones."""
        note = tmp_path / "notes.txt"
        note.write_text("reference notes", encoding="utf-8")

        saved_skill.update(str(note), "resources/notes.txt")

        files = saved_skill.list_files()
        assert "resources/notes.txt" in files
        assert "SKILL.md" in files


class TestAgentReflectsSkillUpdate:
    """The core reported bug: an agent must use updated skill content immediately."""

    def test_agent_run_reflects_updated_skill_content(self, client, saved_skill):
        agent = client.Agent(
            name=f"Skill Update Test Agent {int(time.time())}",
            instructions=(
                "You are a helpful assistant. Always check your attached skills before "
                "answering, and follow a skill's instructions exactly whenever it applies."
            ),
            skills=[saved_skill],
        )
        agent.save(save_subcomponents=True)

        try:
            before = agent.run(query="What is the current signal?")
            assert "SIGNAL-ALPHA" in before.data.output

            new_md = os.path.join(tempfile.mkdtemp(prefix="skill-update-test-"), "SKILL.md")
            _write_skill_md(new_md, saved_skill.name, "SIGNAL-BETA")
            saved_skill.update(new_md)

            # Re-fetch the agent from the backend entirely - rules out any
            # client-side caching, matching the ticket's "even on a new session".
            fresh_agent = client.Agent.get(agent.id)
            after = fresh_agent.run(query="What is the current signal?")
            assert "SIGNAL-BETA" in after.data.output
        finally:
            try:
                agent.delete()
            except Exception:
                pass
