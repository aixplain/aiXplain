"""Tests for persistent File references on v2 Agents."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from aixplain import Aixplain


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def test_agent_accepts_saved_files_and_folders(aix):
    """Serialize saved files and folders as persistent definition references."""
    document = aix.File(id="file-id", name="handbook.pdf", fileType="file")
    folder = aix.File(id="folder-id", name="reference", fileType="folder", description="Reference tree")

    agent = aix.Agent(name="doc-agent", instructions="Use the references.", files=[document, folder])
    payload = agent.build_save_payload()

    assert payload["files"] == [
        {"id": "file-id", "name": "handbook.pdf"},
        {"id": "folder-id", "name": "reference", "description": "Reference tree"},
    ]
    assert agent.files == ["file-id", "folder-id"]


def test_agent_accepts_file_ids_and_backend_dicts(aix):
    """Accept compact ids and File dictionaries returned by Platform."""
    agent = aix.Agent(
        name="doc-agent",
        files=[
            "file-id",
            {"id": "folder-id", "name": "reference", "fileType": "folder", "updatedAt": "2026-08-14"},
        ],
    )

    assert agent.build_save_payload()["files"] == [
        {"id": "file-id"},
        {"id": "folder-id", "name": "reference"},
    ]


def test_agent_rejects_unsaved_file(aix, tmp_path: Path):
    """Do not silently upload or reinterpret an unsaved persistent File."""
    path = tmp_path / "notes.txt"
    path.write_text("notes")
    agent = aix.Agent(name="doc-agent", files=[aix.File(path)])

    with pytest.raises(ValueError, match="file 'notes.txt'.*saved before saving"):
        agent.save()


def test_save_subcomponents_can_save_file_before_agent(aix, tmp_path: Path):
    """Explicit recursive saving persists the File before the Agent reference."""
    path = tmp_path / "notes.txt"
    path.write_text("notes")
    document = aix.File(path)
    document.save = Mock(side_effect=lambda: setattr(document, "id", "file-id") or document)
    aix.client.request = Mock(return_value={"id": "agent-id", "name": "doc-agent", "files": []})
    agent = aix.Agent(name="doc-agent", files=[document])

    agent.save(save_subcomponents=True)

    document.save.assert_called_once_with()
    request_payload = aix.client.request.call_args.kwargs["json"]
    assert request_payload["files"] == [{"id": "file-id", "name": "notes.txt"}]


def test_agent_get_round_trips_file_references(aix):
    """Hydrate Platform File descriptors and preserve them on a later save."""
    aix.client.get = Mock(
        return_value={
            "id": "agent-id",
            "name": "doc-agent",
            "files": [
                {
                    "id": "folder-id",
                    "name": "reference",
                    "description": "Reference tree",
                    "fileType": "folder",
                    "updatedAt": "2026-08-14T00:00:00Z",
                }
            ],
        }
    )

    agent = aix.Agent.get("agent-id")

    assert agent.files == ["folder-id"]
    assert agent.build_save_payload()["files"] == [
        {"id": "folder-id", "name": "reference", "description": "Reference tree"}
    ]


def test_mutating_fetched_agent_files_changes_next_save_payload(aix):
    """Honor list replacement and append operations after construction."""
    first = aix.File(id="first-id", name="first.txt")
    second = aix.File(id="second-id", name="second.txt")
    agent = aix.Agent(id="agent-id", name="doc-agent", files=[first])

    agent.files.append(second)

    assert agent.build_save_payload()["files"] == [
        {"id": "first-id", "name": "first.txt"},
        {"id": "second-id", "name": "second.txt"},
    ]


def test_deleting_an_unsaved_file_keeps_the_right_one(aix, tmp_path: Path):
    """Removing one unsaved file must not attach a different unsaved file instead."""
    first_path = tmp_path / "first.txt"
    first_path.write_text("first")
    second_path = tmp_path / "second.txt"
    second_path.write_text("second")
    first = aix.File(first_path)
    second = aix.File(second_path)
    agent = aix.Agent(name="doc-agent", files=[first, second])

    del agent.files[0]
    agent._sync_file_references()

    assert agent._original_files == [second]


def test_inserting_an_id_does_not_orphan_an_unsaved_file(aix, tmp_path: Path):
    """A raw id inserted ahead of an unsaved File must not push it out as a bare None."""
    path = tmp_path / "notes.txt"
    path.write_text("notes")
    document = aix.File(path)
    agent = aix.Agent(name="doc-agent", files=[document])

    agent.files.insert(0, "saved-id")

    with pytest.raises(ValueError, match="file 'notes.txt'.*saved before saving"):
        agent.save()


def test_clearing_all_files_sends_an_empty_list(aix):
    """Detaching every file must send files=[] so the backend actually clears it."""
    document = aix.File(id="file-id", name="handbook.pdf")
    agent = aix.Agent(name="doc-agent", files=[document])

    agent.files = []

    assert agent.build_save_payload()["files"] == []


def test_agent_never_configured_with_files_omits_the_key(aix):
    """An agent that never touched files must not start sending files=[]."""
    agent = aix.Agent(name="plain-agent", instructions="hi")

    assert "files" not in agent.build_save_payload()


def test_persistent_files_do_not_enter_run_attachments(aix):
    """Keep definition files separate from per-run attachment payloads."""
    agent = aix.Agent(id="agent-id", name="doc-agent", files=["persistent-file-id"])

    payload = agent.build_run_payload(query="Use the handbook")

    assert "files" not in payload
    assert "attachments" not in payload
