"""Regression tests for the v2 Agent findings in BUG-1461.

Items covered: 3 (failed save keeps the local status), 4 (duplicate hydrates
tools), 5 (to_dict/from_dict round trip keeps budget, graph and strategy),
6 (``execution_params=None``), 11 (get-then-save keeps model-tool fields and
member inspectors) and 12 (a cleared persisted budget is sent as cleared).
"""

from unittest.mock import MagicMock, Mock

import pytest

from aixplain.v2 import AssetStatus
from aixplain.v2.agent import Agent
from aixplain.v2.exceptions import APIError, ResourceError
from aixplain.v2.graph import Graph, LLMNode, StaticGraphStrategy
from aixplain.v2.model import Model
from aixplain.v2.tool import Tool


def _ctx() -> Mock:
    return Mock(client=Mock(), backend_url="https://example.test", api_key="k")


def _bound(ctx):
    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


class _BoundModel(Model):
    """A Model subclass with a class-level context, like ``aix.Model``."""


class _BoundTool(Tool):
    """A Tool subclass with a class-level context, like ``aix.Tool``."""


def _hydrating_ctx() -> MagicMock:
    ctx = MagicMock()
    _BoundModel.context = ctx
    _BoundTool.context = ctx
    ctx.Model = _BoundModel
    ctx.Tool = _BoundTool
    return ctx


# ---------------------------------------------------------------------------
# Item 3: a failed save() leaves the local status unchanged
# ---------------------------------------------------------------------------


def test_failed_save_of_a_draft_keeps_it_draft_and_runnable():
    ctx = _ctx()
    agent = _bound(ctx).from_dict({"id": "agent-1", "name": "a", "description": "d", "status": "draft", "tools": []})
    agent._update_saved_state()
    ctx.client.request.side_effect = APIError("name already taken", status_code=400)

    with pytest.raises(ResourceError, match="name already taken"):
        agent.save()

    assert agent.status == AssetStatus.DRAFT
    assert not agent.is_modified
    # The next run must not blame an "onboarded" agent.
    assert agent.before_run(query="hi") is None


# ---------------------------------------------------------------------------
# Item 4: duplicate() returns hydrated tools
# ---------------------------------------------------------------------------


def test_duplicate_hydrates_tools_into_tool_objects():
    ctx = _hydrating_ctx()
    agent = Agent.from_dict({"id": "orig", "name": "a", "description": "d", "status": "onboarded", "tools": []})
    agent.context = ctx
    agent._update_saved_state()
    ctx.client.request.return_value = {
        "id": "dup-1",
        "name": "a (Copy)",
        "description": "d",
        "status": "draft",
        "tools": [{"type": "tool", "id": "tool-1", "name": "Search", "description": "s", "parameters": []}],
    }

    dup = agent.duplicate()

    assert isinstance(dup.tools[0], Tool)
    assert dup.tools[0].id == "tool-1"
    assert dup.status == AssetStatus.DRAFT
    assert not dup.is_modified


# ---------------------------------------------------------------------------
# Item 5: to_dict()/from_dict() round trip
# ---------------------------------------------------------------------------


def _graph() -> Graph:
    node = LLMNode(name="A", node_id="a", model="model")
    return Graph(entry_point=node, nodes=[node])


def test_round_trip_keeps_budget_graph_and_strategy():
    agent = Agent(
        name="a",
        description="d",
        budget={"max_cost": 5},
        graph=_graph(),
        graph_version="2",
        strategy=StaticGraphStrategy(max_iterations=8),
    )

    copy = Agent.from_dict(agent.to_dict())

    assert copy.budget.max_cost == 5
    assert isinstance(copy.graph, Graph)
    assert copy.graph.to_dict() == agent.graph.to_dict()
    assert copy.graph_version == "2"
    assert copy.strategy.max_iterations == 8
    assert copy.build_save_payload()["budget"] == {"maxCost": 5}


def test_budget_still_does_not_count_toward_is_modified():
    agent = Agent.from_dict({"id": "x", "name": "a", "description": "d", "status": "onboarded"})
    agent._update_saved_state()

    agent.budget.max_cost = 3

    assert not agent.is_modified


# ---------------------------------------------------------------------------
# Item 6: execution_params=None behaves like {}
# ---------------------------------------------------------------------------


def test_execution_params_none_behaves_like_omitted():
    agent = Agent(name="a", description="d")

    assert agent.build_run_payload(query="q", execution_params=None) == agent.build_run_payload(query="q")


# ---------------------------------------------------------------------------
# Item 11: get-then-save keeps stored model-tool fields and member inspectors
# ---------------------------------------------------------------------------


def test_hydrated_model_tool_keeps_stored_supplier_function_and_version():
    ctx = _hydrating_ctx()
    entry = {
        "type": "model",
        "id": "model-1",
        "name": "GPT",
        "description": "d",
        "supplier": "openai",
        "function": "text-generation",
        "version": "v1",
        "parameters": [],
    }
    agent = _bound(ctx).from_dict({"id": "x", "name": "a", "description": "d", "tools": [entry]})
    assert isinstance(agent.tools[0], Model)

    tool_payload = agent.build_save_payload()["tools"][0]

    assert tool_payload["supplier"] == "openai"
    assert tool_payload["function"] == "text-generation"
    assert tool_payload["version"] == "v1"


def test_team_member_dict_keeps_fetched_inspectors():
    inspector = {"name": "guard", "targets": ["output"]}
    agent = Agent.from_dict(
        {
            "id": "team",
            "name": "t",
            "description": "d",
            "agents": [{"id": "m1", "inspectors": [inspector]}, {"id": "m2"}],
        }
    )

    members = agent.build_save_payload()["agents"]

    assert members == [{"id": "m1", "inspectors": [inspector]}, {"id": "m2", "inspectors": []}]


# ---------------------------------------------------------------------------
# Item 12: clearing a persisted budget is sent as an explicit empty budget
# ---------------------------------------------------------------------------


def test_clearing_a_fetched_budget_sends_an_empty_budget():
    agent = Agent.from_dict({"id": "x", "name": "a", "description": "d", "budget": {"maxCost": 5}})
    assert agent.build_save_payload()["budget"] == {"maxCost": 5}

    agent.budget = None

    assert agent.build_save_payload()["budget"] == {}


def test_clearing_an_in_place_budget_after_a_save_sends_an_empty_budget():
    agent = Agent(name="a", description="d")
    agent.budget.max_cost = 5
    agent.build_save_payload()  # the save that persisted the cap

    agent.budget.max_cost = None

    assert agent.build_save_payload()["budget"] == {}


def test_agent_that_never_had_a_budget_sends_no_budget_key():
    agent = Agent(name="a", description="d")
    agent.budget = None

    assert "budget" not in agent.build_save_payload()
