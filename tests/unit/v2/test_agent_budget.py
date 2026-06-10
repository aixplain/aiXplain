"""Unit tests for per-run agent budget serialization.

A run-time-only ``budget`` rides inside ``executionParams`` as a nested
camelCase ``budget`` object. These tests cover the shared wire contract:
- A ``Budget`` instance, a snake_case dict, and a camelCase dict all yield the
  same camelCase payload.
- Partial budgets emit no null keys.
- Omitting ``budget`` produces no ``budget`` key (backward compatible).
- ``warnAtPercent`` is never emitted.
"""

from unittest.mock import MagicMock

from aixplain.v2.agent import Agent, Budget


def _create_agent():
    """Build a V2 Agent through ``from_dict`` with a mocked client context."""
    agent = Agent.from_dict({"id": "agent-123", "name": "test-agent"})
    agent.context = MagicMock()
    return agent


class TestBudgetSerialization:
    """Budget.to_dict() honours the camelCase wire contract."""

    def test_full_budget_to_dict(self):
        budget = Budget(max_cost=1.0, max_duration_seconds=300, max_iterations=50)
        assert budget.to_dict() == {
            "maxCost": 1.0,
            "maxDurationSeconds": 300,
            "maxIterations": 50,
        }

    def test_partial_budget_drops_none_keys(self):
        assert Budget(max_cost=2.0).to_dict() == {"maxCost": 2.0}

    def test_empty_budget_is_empty(self):
        assert Budget().to_dict() == {}

    def test_zero_values_are_preserved(self):
        # Falsy-but-valid values must survive; dropping uses ``is None``, not truthiness.
        assert Budget(max_cost=0.0, max_iterations=0).to_dict() == {
            "maxCost": 0.0,
            "maxIterations": 0,
        }


class TestBudgetInRunPayload:
    """build_run_payload threads budget into executionParams.budget."""

    def test_budget_instance(self):
        agent = _create_agent()
        payload = agent.build_run_payload(
            query="q",
            budget=Budget(max_cost=1.0, max_duration_seconds=300, max_iterations=50),
        )
        assert payload["executionParams"]["budget"] == {
            "maxCost": 1.0,
            "maxDurationSeconds": 300,
            "maxIterations": 50,
        }

    def test_budget_dict_snake_case(self):
        agent = _create_agent()
        payload = agent.build_run_payload(
            query="q",
            budget={"max_cost": 1.0, "max_duration_seconds": 300, "max_iterations": 50},
        )
        assert payload["executionParams"]["budget"] == {
            "maxCost": 1.0,
            "maxDurationSeconds": 300,
            "maxIterations": 50,
        }

    def test_budget_dict_camel_case(self):
        agent = _create_agent()
        payload = agent.build_run_payload(
            query="q",
            budget={"maxCost": 1.0, "maxDurationSeconds": 300, "maxIterations": 50},
        )
        assert payload["executionParams"]["budget"] == {
            "maxCost": 1.0,
            "maxDurationSeconds": 300,
            "maxIterations": 50,
        }

    def test_partial_budget_instance(self):
        agent = _create_agent()
        payload = agent.build_run_payload(query="q", budget=Budget(max_cost=2.0))
        assert payload["executionParams"]["budget"] == {"maxCost": 2.0}

    def test_partial_budget_dict(self):
        agent = _create_agent()
        payload = agent.build_run_payload(query="q", budget={"max_cost": 2.0})
        assert payload["executionParams"]["budget"] == {"maxCost": 2.0}

    def test_zero_value_budget_preserved_in_payload(self):
        # A zero cap is semantically distinct from "no cap" and must be sent.
        agent = _create_agent()
        payload = agent.build_run_payload(query="q", budget={"max_cost": 0.0})
        assert payload["executionParams"]["budget"] == {"maxCost": 0.0}

    def test_dict_with_none_value_drops_key(self):
        agent = _create_agent()
        payload = agent.build_run_payload(
            query="q", budget={"max_cost": 1.0, "max_iterations": None}
        )
        assert payload["executionParams"]["budget"] == {"maxCost": 1.0}

    def test_budget_does_not_leak_to_payload_top_level(self):
        agent = _create_agent()
        payload = agent.build_run_payload(query="q", budget=Budget(max_cost=1.0))
        assert "budget" not in payload

    def test_no_budget_means_no_budget_key(self):
        agent = _create_agent()
        payload = agent.build_run_payload(query="q")
        assert "budget" not in payload["executionParams"]

    def test_empty_budget_instance_means_no_budget_key(self):
        agent = _create_agent()
        payload = agent.build_run_payload(query="q", budget=Budget())
        assert "budget" not in payload["executionParams"]

    def test_empty_budget_dict_means_no_budget_key(self):
        agent = _create_agent()
        payload = agent.build_run_payload(query="q", budget={})
        assert "budget" not in payload["executionParams"]

    def test_warn_at_percent_never_emitted(self):
        agent = _create_agent()
        payload = agent.build_run_payload(
            query="q",
            budget=Budget(max_cost=1.0, max_duration_seconds=300, max_iterations=50),
        )
        budget = payload["executionParams"]["budget"]
        assert "warnAtPercent" not in budget
        assert "warn_at_percent" not in budget

    def test_no_budget_payload_unchanged(self):
        """A run without budget produces the same executionParams as before."""
        agent = _create_agent()
        with_budget = agent.build_run_payload(query="q", budget=Budget(max_cost=1.0))
        without_budget = agent.build_run_payload(query="q")

        ep_with = dict(with_budget["executionParams"])
        ep_with.pop("budget", None)
        assert ep_with == without_budget["executionParams"]
