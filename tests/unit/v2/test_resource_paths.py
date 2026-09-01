"""Effect-based guards on the backend paths v2 resources talk to.

These tests exist because renaming ``RESOURCE_PATH`` on ``Model``, ``Tool``,
``Integration`` or ``Skill`` used to break *no* test (ENG-3431): every test for
those resources mocks at a layer above URL construction, so an SDK pointed at
the wrong endpoint would have shipped green.

They are deliberately **effect-based**: each test drives the real code path and
asserts on the path string the client actually received. Asserting the constant
itself (``assert Model.RESOURCE_PATH == "v2/models"``) would kill the same
mutants while proving nothing -- such a test moves in lockstep with the bug.
"""

import os

import pytest
from unittest.mock import Mock

from aixplain.v2.integration import Integration
from aixplain.v2.model import Model
from aixplain.v2.skill import Skill
from aixplain.v2.tool import Tool

# (class, documented backend path). Kept as literals on purpose: this table is
# the specification, not a mirror of the constant under test.
RESOURCES = [
    (Model, "v2/models"),
    (Tool, "v2/tools"),
    (Integration, "v2/integrations"),
    (Skill, "sdk/skill"),
]
RESOURCE_IDS = [cls.__name__ for cls, _ in RESOURCES]

RESOURCE_ID = "abc123"


def _bind(monkeypatch, cls):
    """Bind *cls* to a mock context and return that context.

    ``monkeypatch`` restores the class attribute afterwards, so the real
    resource classes are left untouched for the rest of the session.
    """
    context = Mock(client=Mock(), backend_url="https://platform-api.aixplain.com", api_key="test_key")
    monkeypatch.setattr(cls, "context", context, raising=False)
    return context


def _bind_instance(monkeypatch, cls, payload):
    """Build a saved instance of *cls* bound to a mock context."""
    context = _bind(monkeypatch, cls)
    instance = cls.from_dict(payload)
    instance.context = context
    return context, instance


@pytest.mark.parametrize("cls, expected_path", RESOURCES, ids=RESOURCE_IDS)
def test_get_uses_resource_path(monkeypatch, cls, expected_path):
    """``get(id)`` must issue its GET against ``<RESOURCE_PATH>/<id>``."""
    context = _bind(monkeypatch, cls)
    context.client.get.return_value = {"id": RESOURCE_ID, "name": "fixture"}

    cls.get(RESOURCE_ID)

    context.client.get.assert_called_once()
    assert context.client.get.call_args[0][0] == f"{expected_path}/{RESOURCE_ID}"


@pytest.mark.parametrize("cls, expected_path", RESOURCES, ids=RESOURCE_IDS)
def test_search_uses_resource_path(monkeypatch, cls, expected_path):
    """``search()`` must paginate against ``<RESOURCE_PATH>/paginate``."""
    context = _bind(monkeypatch, cls)
    context.client.request.return_value = {"results": [], "total": 0, "pageTotal": 0}

    cls.search()

    context.client.request.assert_called_once()
    method, path = context.client.request.call_args[0][:2]
    assert method == "post"
    assert path == f"{expected_path}/paginate"


@pytest.mark.parametrize(
    "cls, expected_path",
    [(Model, "v2/models"), (Integration, "v2/integrations"), (Skill, "sdk/skill")],
    ids=["Model", "Integration", "Skill"],
)
def test_create_posts_to_resource_path(monkeypatch, cls, expected_path):
    """Creating an unsaved resource must POST to the collection root.

    ``Tool`` is absent by design: a saved tool's metadata update goes to
    ``sdk/utilities/<id>``, which is covered by ``test_tool.py``.
    """
    context = _bind(monkeypatch, cls)
    context.client.request.return_value = {"id": "new-id", "name": "fixture"}
    instance = cls(name="fixture")
    instance.context = context

    instance.save()

    method, path = context.client.request.call_args[0][:2]
    assert method == "post"
    assert path == expected_path


@pytest.mark.parametrize(
    "cls, expected_path",
    [(Tool, "v2/tools"), (Skill, "sdk/skill")],
    ids=["Tool", "Skill"],
)
def test_delete_uses_resource_path(monkeypatch, cls, expected_path):
    """``delete()`` must DELETE ``<RESOURCE_PATH>/<id>``.

    Only the two resources that mix in ``DeleteResourceMixin`` are listed;
    ``Model`` and ``Integration`` expose no ``delete()``.
    """
    context, instance = _bind_instance(monkeypatch, cls, {"id": RESOURCE_ID, "name": "fixture"})

    instance.delete()

    method, path = context.client.request_raw.call_args[0][:2]
    assert method == "delete"
    assert path == f"{expected_path}/{RESOURCE_ID}"


def test_skill_download_composes_resource_path(monkeypatch, tmp_path):
    """Skill sub-resources hang off RESOURCE_PATH and must move with it."""
    context, skill = _bind_instance(monkeypatch, Skill, {"id": RESOURCE_ID, "name": "fixture"})
    context.client.request_raw.return_value = Mock(content=b"bundle")
    target = tmp_path / "bundle.zip"

    skill.download(str(target))

    method, path = context.client.request_raw.call_args[0][:2]
    assert method == "get"
    assert path == f"sdk/skill/{RESOURCE_ID}/download"


def test_skill_file_upload_composes_resource_path(monkeypatch, tmp_path):
    """The internal file-tree upload must target ``sdk/skill/<id>/file``."""
    context, skill = _bind_instance(monkeypatch, Skill, {"id": RESOURCE_ID, "name": "fixture"})
    monkeypatch.setattr(Skill, "_upload", lambda self, path: "https://uploaded/SKILL.md")
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# fixture")

    skill._upload_file_as_skill(str(skill_md))

    method, path = context.client.request.call_args[0][:2]
    assert method == "post"
    assert path == f"sdk/skill/{RESOURCE_ID}/file"


def test_skill_folder_upload_composes_resource_path(monkeypatch, tmp_path):
    """Folder nodes are created under ``sdk/skill/<id>/folder``."""
    context, skill = _bind_instance(monkeypatch, Skill, {"id": RESOURCE_ID, "name": "fixture"})
    monkeypatch.setattr(Skill, "_upload", lambda self, path: "https://uploaded/file")
    context.client.request.return_value = {"id": "folder-1"}
    (tmp_path / "SKILL.md").write_text("# fixture")
    nested = tmp_path / "references"
    os.makedirs(str(nested))
    (nested / "notes.md").write_text("notes")

    skill._upload_folder(str(tmp_path))

    paths = [call[0][1] for call in context.client.request.call_args_list]
    assert f"sdk/skill/{RESOURCE_ID}/folder" in paths
    assert f"sdk/skill/{RESOURCE_ID}/file" in paths
