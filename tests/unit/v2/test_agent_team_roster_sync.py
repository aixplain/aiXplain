"""Unit tests for BUG-1457: public edits to ``team.agents`` reach the save payload.

``__post_init__`` snapshots the roster into ``_original_agents`` and turns the
public ``agents`` list into ids. ``_sync_agent_references`` rebuilds that
snapshot from the public list before validation and save, so replace, remove,
clear and append edits are no longer silently dropped.
"""

from unittest.mock import Mock, patch

import pytest

from aixplain import Agent
from aixplain.v2.enums import AssetStatus


def _ctx():
    return Mock(client=Mock(), backend_url="https://platform-api.aixplain.com", api_key="test_key")


def _bound_agent(ctx):
    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


def _payload_ids(agent):
    return [entry["id"] for entry in agent.build_save_payload()["agents"]]


def _fetched_team(**extra):
    team = Agent.from_dict(
        {
            "id": "team_1",
            "name": "Team",
            "instructions": "lead",
            "status": "onboarded",
            "agents": [{"id": "A"}, {"id": "B"}],
            **extra,
        }
    )
    team._update_saved_state()
    return team


class TestPublicRosterEdits:
    def test_unchanged_roster(self):
        team = _fetched_team()
        assert team.agents == ["A", "B"]
        assert _payload_ids(team) == ["A", "B"]
        assert not team.is_modified

    def test_replace(self):
        team = _fetched_team()
        team.agents = ["C"]
        assert team.is_modified
        assert _payload_ids(team) == ["C"]

    def test_remove_in_place(self):
        team = _fetched_team()
        team.agents.remove("B")
        assert team.is_modified
        assert _payload_ids(team) == ["A"]

    def test_clear_sends_empty_list(self):
        team = _fetched_team()
        team.agents = []
        assert team.is_modified
        assert team.build_save_payload()["agents"] == []

    def test_clear_with_none(self):
        team = _fetched_team()
        team.agents = None
        assert team.build_save_payload()["agents"] == []

    @pytest.mark.parametrize("entry", ["C", {"id": "C"}, Agent(id="C", name="c")], ids=["id", "dict", "agent"])
    def test_append_any_reference_shape(self, entry):
        team = _fetched_team()
        team.agents.append(entry)
        assert _payload_ids(team) == ["A", "B", "C"]
        # The public list is normalised back to ids.
        assert team.agents == ["A", "B", "C"]
        assert team.is_modified


class TestRetainedObjects:
    def test_retained_agent_objects_are_kept(self):
        a = Agent(id="A", name="a")
        b = Agent(id="B", name="b")
        team = Agent(id="team_1", name="T", agents=[a, b])
        team.agents.remove("B")
        assert _payload_ids(team) == ["A"]
        assert team._original_agents == [a]
        assert team._original_agents[0] is a

    def test_unsaved_placeholder_resolves_after_save(self):
        child = Agent(name="child", instructions="x")
        team = Agent(name="T", instructions="lead", agents=[child])
        assert team.agents == [None]
        with pytest.raises(ValueError, match="must be saved"):
            team._validate_dependencies()

        child.id = "X"
        team._sync_agent_references()
        assert team._original_agents[0] is child
        assert _payload_ids(team) == ["X"]

    def test_unsaved_placeholder_with_mismatched_length_is_rejected(self):
        child = Agent(name="child", instructions="x")
        team = Agent(name="T", instructions="lead", agents=[child, "B"])
        team.agents.append("C")  # [None, "B", "C"]: the None slot can no longer be resolved by position
        with pytest.raises(ValueError, match="All agents must be saved"):
            team.build_save_payload()


class TestPlainAgent:
    def test_plain_agent_payload_agents_is_empty(self):
        agent = Agent(name="plain", instructions="y")
        # Same as to_dict() has always sent for a plain agent.
        assert agent.to_dict()["agents"] == []
        assert agent.build_save_payload()["agents"] == []
        assert agent._original_agents == []


class TestSaveRequests:
    def test_save_attribute_shortcut_sends_new_roster(self):
        ctx = _ctx()
        BoundAgent = _bound_agent(ctx)
        team = BoundAgent.from_dict(
            {"id": "team_1", "name": "Team", "instructions": "lead", "agents": [{"id": "A"}, {"id": "B"}]}
        )
        team._update_saved_state()
        team.save(agents=["C"])

        method, _path = ctx.client.request.call_args[0][:2]
        assert method == "put"
        assert ctx.client.request.call_args[1]["json"]["agents"] == [{"id": "C", "inspectors": []}]

    def test_create_then_edit_then_save(self):
        ctx = _ctx()
        BoundAgent = _bound_agent(ctx)
        a = BoundAgent(id="A", name="a")
        b = BoundAgent(id="B", name="b")
        team = BoundAgent(name="T", instructions="lead", agents=[a, b])
        ctx.client.request.return_value = {
            "id": "team_1",
            "name": "T",
            "instructions": "lead",
            "agents": [{"id": "A", "inspectors": []}, {"id": "B", "inspectors": []}],
        }
        team.save()
        assert ctx.client.request.call_args[1]["json"]["agents"] == [
            {"id": "A", "inspectors": []},
            {"id": "B", "inspectors": []},
        ]
        assert team.id == "team_1"

        team.agents.remove("B")
        team.save()
        method = ctx.client.request.call_args[0][0]
        assert method == "put"
        assert ctx.client.request.call_args[1]["json"]["agents"] == [{"id": "A", "inspectors": []}]
        assert team._original_agents[0] is a

    def test_draft_auto_save_on_run_sends_new_roster(self):
        ctx = _ctx()
        BoundAgent = _bound_agent(ctx)
        team = BoundAgent.from_dict(
            {"id": "team_1", "name": "Team", "instructions": "lead", "agents": [{"id": "A"}, {"id": "B"}]}
        )
        team.status = AssetStatus.DRAFT
        team._update_saved_state()
        team.agents = ["C"]

        with patch.object(BoundAgent, "save", wraps=team.save) as save:
            # Only the before_run guard matters here; stop before the HTTP run itself.
            team.before_run()
        save.assert_called_once_with(as_draft=True)
        put_payloads = [c[1]["json"] for c in ctx.client.request.call_args_list if c[0][0] == "put"]
        assert put_payloads and put_payloads[-1]["agents"] == [{"id": "C", "inspectors": []}]

    def test_create_response_without_agents_keeps_roster(self):
        ctx = _ctx()
        BoundAgent = _bound_agent(ctx)
        a = BoundAgent(id="A", name="a")
        b = BoundAgent(id="B", name="b")
        team = BoundAgent(name="T", instructions="lead", agents=[a, b])
        # The create response does not echo ``agents``.
        ctx.client.request.return_value = {"id": "team_1", "name": "T", "instructions": "lead"}
        team.save()

        assert team.agents == ["A", "B"]
        assert team._original_agents == [a, b]
        assert not team.is_modified
        assert _payload_ids(team) == ["A", "B"]
