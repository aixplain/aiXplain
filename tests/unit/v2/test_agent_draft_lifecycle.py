"""Unit tests for the v2 Agent draft/onboard lifecycle (ENG-3688).

The functional twin lives in ``tests/functional/v2/test_agent_lifecycle.py``.
These tests pin the state machine offline:

* ``before_save`` maps ``as_draft`` to DRAFT / ONBOARDED;
* a modified ONBOARDED agent refuses to run until explicitly saved, while a
  modified DRAFT one is implicitly saved as a draft;
* an unsaved child is rejected by ``save()`` unless ``save_subcomponents=True``.
"""

from unittest.mock import Mock

import pytest

from aixplain.v2 import AssetStatus
from aixplain.v2.agent import Agent


def _ctx() -> Mock:
    """A mock client context, enough for save()/before_run() to run offline."""
    return Mock(client=Mock(), backend_url="https://example.test", api_key="k")


def _bound(ctx: Mock):
    """An Agent subclass bound to *ctx* without constructing a real client."""

    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


def _created_response(status: str) -> dict:
    return {"id": "agent-1", "name": "a", "description": "d", "status": status, "tools": []}


# ---------------------------------------------------------------------------
# before_save: as_draft drives the status transition
# ---------------------------------------------------------------------------


def test_before_save_as_draft_sets_draft_status():
    """``as_draft=True`` maps to DRAFT."""
    agent = Agent(name="a", description="d")
    agent.before_save(as_draft=True)
    assert agent.status == AssetStatus.DRAFT


def test_before_save_defaults_to_onboarded():
    """An omitted ``as_draft`` onboards."""
    agent = Agent(name="a", description="d")
    agent.before_save()
    assert agent.status == AssetStatus.ONBOARDED


def test_save_as_draft_sends_draft_status():
    """The create payload carries ``status: draft``."""
    ctx = _ctx()
    ctx.client.request.return_value = _created_response("draft")
    agent = _bound(ctx)(name="a", description="d")

    agent.save(as_draft=True)

    assert ctx.client.request.call_args.kwargs["json"]["status"] == "draft"
    assert agent.status == AssetStatus.DRAFT


def test_save_default_sends_onboarded_status():
    """The create payload carries ``status: onboarded`` by default."""
    ctx = _ctx()
    ctx.client.request.return_value = _created_response("onboarded")
    agent = _bound(ctx)(name="a", description="d")

    agent.save()

    assert ctx.client.request.call_args.kwargs["json"]["status"] == "onboarded"
    assert agent.status == AssetStatus.ONBOARDED


def test_before_save_json_requires_expected_output():
    """JSON output without a schema is rejected at save time."""
    agent = Agent(name="a", description="d", output_format="json")

    with pytest.raises(ValueError, match="requires expected_output"):
        agent.before_save()


# ---------------------------------------------------------------------------
# before_run: modified onboarded refuses; modified draft auto-saves
# ---------------------------------------------------------------------------


def _persisted_agent(ctx: Mock, status: str):
    agent = _bound(ctx).from_dict({"id": "agent-1", "name": "a", "description": "d", "status": status, "tools": []})
    agent._update_saved_state()
    return agent


def test_modified_onboarded_agent_refuses_to_run_until_saved():
    """A dirty onboarded agent raises instead of silently dropping edits."""
    agent = _persisted_agent(_ctx(), "onboarded")
    agent.instructions = "changed"

    with pytest.raises(ValueError, match="onboarded and cannot be modified"):
        agent.before_run(query="hi")


def test_unmodified_onboarded_agent_runs_without_saving():
    """A clean onboarded agent runs without an implicit save."""
    agent = _persisted_agent(_ctx(), "onboarded")
    assert agent.before_run(query="hi") is None


def test_modified_draft_agent_is_implicitly_saved_as_draft():
    """A dirty draft is PUT with its edits and ``status: draft`` before running."""
    ctx = _ctx()
    ctx.client.request.return_value = _created_response("draft")
    agent = _persisted_agent(ctx, "draft")
    agent.instructions = "changed"

    agent.before_run(query="hi")

    ctx.client.request.assert_called_once()
    method, path = ctx.client.request.call_args.args
    payload = ctx.client.request.call_args.kwargs["json"]
    assert method == "put"
    assert path.endswith("/agent-1")
    assert payload["status"] == AssetStatus.DRAFT
    assert payload["instructions"] == "changed"
    assert not agent.is_modified


def test_unmodified_draft_agent_is_not_saved_on_run():
    """A clean draft is not re-saved on every run."""
    agent = _persisted_agent(_ctx(), "draft")
    agent.save = Mock(return_value=agent)

    agent.before_run(query="hi")

    agent.save.assert_not_called()


# ---------------------------------------------------------------------------
# save(): unsaved subcomponents
# ---------------------------------------------------------------------------


def test_save_rejects_unsaved_subagent():
    """A plain save refuses a subagent with no id."""
    ctx = _ctx()
    Bound = _bound(ctx)
    sub = Bound(name="sub", description="d")
    parent = Bound(name="parent", description="d", agents=[sub])

    with pytest.raises(ValueError, match="must be saved before saving"):
        parent.save()


def test_save_subcomponents_persists_unsaved_subagent():
    """``save_subcomponents=True`` saves the subagent first."""
    ctx = _ctx()
    ctx.client.request.return_value = {
        "id": "parent-1",
        "name": "parent",
        "description": "d",
        "status": "onboarded",
        "tools": [],
        "agents": [],
    }
    Bound = _bound(ctx)
    sub = Bound(name="sub", description="d")
    sub.save = Mock(side_effect=lambda **kwargs: setattr(sub, "id", "sub-1") or sub)
    parent = Bound(name="parent", description="d", agents=[sub])

    parent.save(save_subcomponents=True)

    sub.save.assert_called_once_with(save_subcomponents=True)
