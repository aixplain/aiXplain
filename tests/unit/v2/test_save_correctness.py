"""Unit tests for save() correctness invariants (BUG-1093).

Covers two failure modes that damaged the user's resources:

* ``save()`` on a deleted resource took the create branch and POSTed a
  duplicate, because ``save()`` was the only mutating path that never called
  ``_ensure_valid_state()``.
* ``_create()`` hydrated the POST response *before* recording the returned id,
  so a deserialization failure orphaned a resource that already existed
  remotely — and the obvious retry created a second one.
"""

from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import MagicMock

import pytest
from dataclasses_json import config, dataclass_json

from aixplain.v2.agent import Agent
from aixplain.v2.enums import AssetStatus
from aixplain.v2.exceptions import AixplainV2Error, ResourceError
from aixplain.v2.resource import (
    BaseResource,
    DeleteResourceMixin,
    GetResourceMixin,
)
from aixplain.v2.tool import Tool


def _reject(value):
    """Decoder standing in for an SDK that is behind the backend."""
    raise ValueError(f"unmodelled value {value!r}")


@dataclass_json
@dataclass
class Thing(BaseResource, DeleteResourceMixin, GetResourceMixin):
    """Minimal resource whose ``kind`` decoder rejects unmodelled values."""

    kind: Optional[str] = field(default=None, metadata=config(decoder=_reject))


Thing.RESOURCE_PATH = "v2/things"


def _thing(**kwargs) -> Thing:
    """Return a Thing bound to a mock context."""
    thing = Thing(**kwargs)
    thing.context = MagicMock()
    return thing


def _methods(context) -> list:
    """Return the HTTP methods requested through *context*'s client."""
    return [call.args[0] for call in context.client.request.call_args_list if call.args]


# =============================================================================
# Finding 1 — save() after delete() must not create a duplicate
# =============================================================================


def test_save_after_delete_raises_and_issues_no_request():
    """A deleted resource must never fall through to the create branch."""
    thing = _thing(id="ID1", name="thing")
    thing._update_saved_state()
    thing.mark_as_deleted()
    thing.context.client.request.reset_mock()

    with pytest.raises(AixplainV2Error, match="deleted"):
        thing.save()

    assert thing.context.client.request.call_args_list == []
    assert thing.id is None


def test_save_on_never_saved_resource_still_creates():
    """The guard is conditional: a fresh resource must still be created."""
    thing = _thing(name="thing")
    thing.context.client.request.return_value = {"id": "NEW-ID", "name": "thing"}

    thing.save()

    assert _methods(thing.context) == ["post"]
    assert thing.id == "NEW-ID"


def test_save_after_delete_is_not_one_shot():
    """Repeated saves on a deleted resource keep raising."""
    thing = _thing(id="ID1", name="thing")
    thing._update_saved_state()
    thing.mark_as_deleted()

    for _ in range(2):
        with pytest.raises(AixplainV2Error, match="deleted"):
            thing.save()

    assert _methods(thing.context) == []


def test_clone_of_deleted_resource_can_be_saved():
    """clone() produces a new resource, so the deleted flag must not carry over."""
    thing = _thing(id="ID1", name="thing")
    thing._update_saved_state()
    thing.mark_as_deleted()

    cloned = thing.clone(name="revived")
    cloned.context = MagicMock()
    cloned.context.client.request.return_value = {"id": "NEW-ID", "name": "revived"}

    assert cloned.is_deleted is False
    cloned.save()

    assert _methods(cloned.context) == ["post"]
    assert cloned.id == "NEW-ID"


def test_agent_save_after_delete_does_not_touch_subcomponents_or_status():
    """Agent.save() guards before saving children and before the status flip."""
    child = Tool(name="child tool", code="def main():\n    return 1\n")
    child.context = MagicMock()
    agent = Agent(name="agent", tools=[child])
    agent.context = MagicMock()
    agent.id = "AGENT-1"
    agent._update_saved_state()
    agent.status = AssetStatus.ONBOARDED
    agent.mark_as_deleted()
    agent.status = AssetStatus.DELETED

    with pytest.raises(AixplainV2Error, match="deleted"):
        agent.save(save_subcomponents=True)

    assert agent.status == AssetStatus.DELETED
    assert child.id is None
    assert agent.context.client.request.call_args_list == []
    assert child.context.client.request.call_args_list == []


def test_file_save_after_delete_raises():
    """File.save() bypasses BaseResource.save(), so it carries its own guard.

    File has no delete mixin today, so the deleted flag is set directly — the
    guard exists so File never regains the duplicate-on-save behaviour if one
    is added.
    """
    from aixplain.v2.file import File

    file = File(id="FILE-1", name="report.pdf")
    file.context = MagicMock()
    file._update_saved_state()
    file.id = None
    file._deleted = True
    file.context.client.request.reset_mock()

    with pytest.raises(AixplainV2Error, match="deleted"):
        file.save()

    assert file.context.client.request.call_args_list == []


# =============================================================================
# Finding 2 — a create whose response cannot be hydrated must keep the id
# =============================================================================


def test_create_hydration_failure_records_server_id():
    """The POST succeeded, so the id must land on self before hydration runs."""
    thing = _thing(name="thing")
    thing.context.client.request.return_value = {
        "id": "SERVER-ID-123",
        "name": "thing",
        "kind": "WEIRD_NEW_ENUM",
    }

    with pytest.raises(ResourceError) as excinfo:
        thing.save()

    assert thing.id == "SERVER-ID-123"
    message = str(excinfo.value)
    assert "SERVER-ID-123" in message
    assert "do NOT retry" in message


def test_create_hydration_failure_does_not_duplicate_on_second_save():
    """After the failure the resource is reachable, so a retry updates it."""
    thing = _thing(name="thing")
    thing.context.client.request.return_value = {
        "id": "SERVER-ID-123",
        "name": "thing",
        "kind": "WEIRD_NEW_ENUM",
    }
    with pytest.raises(ResourceError):
        thing.save()

    thing.context.client.request.reset_mock()
    thing.context.client.request.return_value = {"id": "SERVER-ID-123", "name": "thing"}
    thing.save()

    assert _methods(thing.context) == ["put"]
    assert thing.context.client.request.call_args_list[0].args[1] == "v2/things/SERVER-ID-123"


def test_api_key_create_reraises_hydration_failure():
    """ApiKey._create's 422 fallback must not swallow the hydration error."""
    from aixplain.v2.api_key import APIKey

    api_key = APIKey(name="key")
    api_key.context = MagicMock()
    api_key.context.client.request.return_value = {"id": "KEY-1", "globalLimits": "not-a-mapping"}

    with pytest.raises(ResourceError, match="do NOT retry"):
        api_key.save()

    assert api_key.id == "KEY-1"


def test_create_preserves_recorded_id_when_response_omits_id_field():
    """The copy loop must not overwrite the captured id with None."""

    @dataclass_json
    @dataclass
    class IdLosingThing(BaseResource):
        """Resource whose id decoder drops the value."""

        id: Optional[str] = field(default=None, metadata=config(decoder=lambda _: None))

    IdLosingThing.RESOURCE_PATH = "v2/things"
    thing = IdLosingThing(name="thing")
    thing.context = MagicMock()
    thing.context.client.request.return_value = {"id": "SERVER-ID-123", "name": "thing"}

    thing.save()

    assert thing.id == "SERVER-ID-123"


def test_create_hydration_failure_without_id_gives_actionable_message():
    """A response with no id cannot be re-fetched, so the hint must not claim it can."""
    thing = _thing(name="thing")
    thing.context.client.request.return_value = {"name": "thing", "kind": "WEIRD_NEW_ENUM"}

    with pytest.raises(ResourceError) as excinfo:
        thing.save()

    message = str(excinfo.value)
    assert thing.id is None
    assert "Thing.get(None)" not in message
    assert "check before retrying" in message
