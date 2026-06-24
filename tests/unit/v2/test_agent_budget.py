"""Unit tests for agent budget serialization.

A run-time ``budget`` rides inside ``executionParams`` as a nested camelCase
``budget`` object; a persisted ``budget`` lives at the top level of the create
payload. ``Budget`` is the single source of truth for the iteration cap, so the
deprecated ``max_iterations`` surfaces fold into it and the standalone
``maxIterations`` key is no longer emitted. These tests cover:
- A ``Budget`` instance, a snake_case dict, and a camelCase dict all yield the
  same camelCase payload.
- Partial budgets emit no null keys; ``warnAtPercent`` is never emitted.
- Omitting ``budget`` produces no ``budget`` key (backward compatible).
- Persisted budget serialization in the create payload.
- The deprecated persisted/run-time ``max_iterations`` fold into ``budget`` with
  a ``DeprecationWarning``; Budget wins on conflict.
- No standalone ``maxIterations`` survives in either emitted payload.
"""

import warnings
from unittest.mock import MagicMock

import pytest

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


def _build_agent(**kwargs):
    """Construct a V2 Agent (running __post_init__) with a mocked client context."""
    agent = Agent(name="test-agent", **kwargs)
    agent.context = MagicMock()
    return agent


class TestPersistedBudgetInCreatePayload:
    """build_save_payload persists ``budget`` and never emits standalone maxIterations."""

    def test_budget_instance_persisted(self):
        agent = _build_agent(budget=Budget(max_iterations=10, max_cost=0.50))
        payload = agent.build_save_payload()
        assert payload["budget"] == {"maxIterations": 10, "maxCost": 0.50}

    def test_budget_dict_snake_case_persisted(self):
        agent = _build_agent(budget={"max_iterations": 10})
        payload = agent.build_save_payload()
        assert payload["budget"] == {"maxIterations": 10}

    def test_budget_dict_camel_case_persisted(self):
        agent = _build_agent(budget={"maxIterations": 10})
        payload = agent.build_save_payload()
        assert payload["budget"] == {"maxIterations": 10}

    def test_no_budget_means_no_budget_key(self):
        agent = _build_agent()
        payload = agent.build_save_payload()
        assert "budget" not in payload

    def test_empty_budget_means_no_budget_key(self):
        agent = _build_agent(budget=Budget())
        payload = agent.build_save_payload()
        assert "budget" not in payload

    def test_no_standalone_max_iterations_when_unset(self):
        agent = _build_agent()
        payload = agent.build_save_payload()
        assert "maxIterations" not in payload

    def test_zero_iterations_preserved(self):
        agent = _build_agent(budget=Budget(max_iterations=0))
        payload = agent.build_save_payload()
        assert payload["budget"] == {"maxIterations": 0}


class TestDeprecatedPersistedMaxIterations:
    """Agent(max_iterations=N) warns, folds into budget, and drops the standalone key."""

    def test_deprecation_warning_emitted(self):
        with pytest.warns(DeprecationWarning, match="max_iterations"):
            _build_agent(max_iterations=7)

    def test_folds_into_budget(self):
        with pytest.warns(DeprecationWarning):
            agent = _build_agent(max_iterations=7)
        assert agent.budget is not None
        assert agent.budget.max_iterations == 7

    def test_create_payload_has_budget_not_standalone(self):
        with pytest.warns(DeprecationWarning):
            agent = _build_agent(max_iterations=7)
        payload = agent.build_save_payload()
        assert payload["budget"] == {"maxIterations": 7}
        assert "maxIterations" not in payload

    def test_no_warning_when_unset(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            _build_agent()  # must not raise

    def test_conflict_budget_wins(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            agent = _build_agent(max_iterations=7, budget=Budget(max_iterations=99))
        categories = {w.category for w in caught}
        assert DeprecationWarning in categories
        assert UserWarning in categories
        assert agent.budget.max_iterations == 99
        payload = agent.build_save_payload()
        assert payload["budget"]["maxIterations"] == 99
        assert "maxIterations" not in payload


class TestDeprecatedRunTimeMaxIterations:
    """run-time execution_params['max_iterations'] folds into executionParams.budget."""

    def test_deprecation_warning_emitted(self):
        agent = _create_agent()
        with pytest.warns(DeprecationWarning, match="max_iterations"):
            agent.build_run_payload(query="q", execution_params={"max_iterations": 7})

    def test_folds_into_execution_budget(self):
        agent = _create_agent()
        with pytest.warns(DeprecationWarning):
            payload = agent.build_run_payload(
                query="q", execution_params={"max_iterations": 7}
            )
        assert payload["executionParams"]["budget"] == {"maxIterations": 7}
        assert "maxIterations" not in payload["executionParams"]

    def test_camel_case_exec_param_also_folds(self):
        agent = _create_agent()
        with pytest.warns(DeprecationWarning):
            payload = agent.build_run_payload(
                query="q", execution_params={"maxIterations": 7}
            )
        assert payload["executionParams"]["budget"] == {"maxIterations": 7}
        assert "maxIterations" not in payload["executionParams"]

    def test_no_standalone_max_iterations_by_default(self):
        agent = _create_agent()
        payload = agent.build_run_payload(query="q")
        assert "maxIterations" not in payload["executionParams"]
        assert "budget" not in payload["executionParams"]

    def test_conflict_budget_wins(self):
        agent = _create_agent()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            payload = agent.build_run_payload(
                query="q",
                execution_params={"max_iterations": 7},
                budget=Budget(max_iterations=99),
            )
        categories = {w.category for w in caught}
        assert DeprecationWarning in categories
        assert UserWarning in categories
        assert payload["executionParams"]["budget"]["maxIterations"] == 99
        assert "maxIterations" not in payload["executionParams"]

    def test_fold_combines_with_other_budget_fields(self):
        agent = _create_agent()
        with pytest.warns(DeprecationWarning):
            payload = agent.build_run_payload(
                query="q",
                execution_params={"max_iterations": 7},
                budget=Budget(max_cost=1.0),
            )
        assert payload["executionParams"]["budget"] == {
            "maxCost": 1.0,
            "maxIterations": 7,
        }


class TestFromDictLegacyMaxIterations:
    """Loading a backend agent with legacy ``maxIterations`` must NOT warn.

    ``Agent.from_dict`` (used by ``aix.Agent.get(id)``) deserializes backend
    agents that may still carry a legacy top-level ``maxIterations``. Loading an
    agent the caller never configured must be silent, but the explicit
    ``Agent(max_iterations=...)`` constructor must still warn.
    """

    def test_from_dict_with_max_iterations_emits_no_warning(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # any warning becomes an error
            agent = Agent.from_dict({"id": "a", "name": "t", "maxIterations": 5})
        assert agent.budget is not None
        assert agent.budget.max_iterations == 5
        assert agent.max_iterations is None

    def test_constructor_with_max_iterations_still_warns(self):
        with pytest.warns(DeprecationWarning, match="max_iterations"):
            Agent(name="t", max_iterations=5)

    def test_from_dict_folds_into_budget(self):
        agent = Agent.from_dict({"id": "a", "name": "t", "maxIterations": 5})
        assert agent.budget.max_iterations == 5

    def test_from_dict_budget_wins_silently_on_conflict(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            agent = Agent.from_dict(
                {
                    "id": "a",
                    "name": "t",
                    "maxIterations": 5,
                    "budget": {"maxIterations": 99, "maxCost": 1.0},
                }
            )
        assert agent.budget.max_iterations == 99
        assert agent.budget.max_cost == 1.0

    def test_from_dict_without_max_iterations_no_budget(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            agent = Agent.from_dict({"id": "a", "name": "t"})
        assert agent.budget is None

    def test_from_dict_does_not_mutate_caller_dict(self):
        data = {"id": "a", "name": "t", "maxIterations": 5}
        Agent.from_dict(data)
        assert data["maxIterations"] == 5  # original dict untouched
        assert "budget" not in data

    def test_from_dict_serializes_back_to_budget_only(self):
        agent = Agent.from_dict({"id": "a", "name": "t", "maxIterations": 5})
        agent.context = MagicMock()
        payload = agent.build_save_payload()
        assert payload["budget"] == {"maxIterations": 5}
        assert "maxIterations" not in payload

    def test_from_dict_preserves_nested_fields(self):
        agent = Agent.from_dict(
            {
                "id": "a",
                "name": "t",
                "maxIterations": 3,
                "tasks": [
                    {"name": "task1", "description": "desc", "expectedOutput": "o"}
                ],
            }
        )
        assert agent.budget.max_iterations == 3
        assert len(agent.tasks) == 1
        assert agent.tasks[0].name == "task1"


class TestRunPathWarningStacklevel:
    """Run-path deprecation/conflict warnings must point at the user's run() call.

    The warnings are emitted deep inside ``build_run_payload`` but the stacklevel
    is tuned so the displayed location is the caller's ``agent.run(...)`` line,
    not SDK internals.
    """

    @staticmethod
    def _runnable_agent():
        agent = Agent.from_dict({"id": "a1", "name": "t"})
        agent.context = MagicMock()
        agent.status = None
        fake_result = MagicMock()
        fake_result.url = None
        fake_result.completed = True
        agent.handle_run_response = lambda response, **kw: fake_result
        agent.before_run = lambda *a, **k: None
        agent.after_run = lambda result, *a, **k: None
        return agent

    def test_run_deprecation_warning_points_at_call_site(self):
        agent = self._runnable_agent()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            agent.run(query="hi", execution_params={"max_iterations": 7})
        dep = [w for w in caught if w.category is DeprecationWarning and "max_iterations" in str(w.message)]
        assert dep, "expected a run-path DeprecationWarning"
        # The warning must resolve to THIS test file (the user call site), not agent.py.
        assert dep[0].filename == __file__, dep[0].filename

    def test_run_conflict_warning_points_at_call_site(self):
        agent = self._runnable_agent()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            agent.run(
                query="hi",
                execution_params={"max_iterations": 7},
                budget=Budget(max_iterations=99),
            )
        conflict = [w for w in caught if w.category is UserWarning and "precedence" in str(w.message)]
        assert conflict, "expected a run-path conflict UserWarning"
        assert conflict[0].filename == __file__, conflict[0].filename
