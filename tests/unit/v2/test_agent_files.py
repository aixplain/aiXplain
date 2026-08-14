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


def test_persistent_files_do_not_enter_run_attachments(aix):
    """Keep definition files separate from per-run attachment payloads."""
    agent = aix.Agent(id="agent-id", name="doc-agent", files=["persistent-file-id"])

    payload = agent.build_run_payload(query="Use the handbook")

    assert "files" not in payload
    assert "attachments" not in payload
