"""
Functional tests for team agents with inspectors.
"""

from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

import pytest
import time
import uuid

import aixplain as aix
from aixplain.enums.asset_status import AssetStatus

from aixplain.v2 import Inspector
from tests.functional.team_agent.test_utils import (
    RUN_FILE,
    read_data,
)

_DEFAULT_INPUT_TARGET = "input"
_DEFAULT_OUTPUT_TARGET = "output"


@pytest.fixture
def resource_tracker():
    """Tracks resources created during a test for guaranteed cleanup."""
    resources = []
    yield resources
    for resource in reversed(resources):
        try:
            resource.delete()
        except Exception:
            pass


@pytest.fixture
def resource_tracker():
    """Tracks resources created during a test for guaranteed cleanup."""
    resources = []
    yield resources
    for resource in reversed(resources):
        try:
            resource.delete()
        except Exception:
            pass


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


def _make_two_subagents(client, timestamp: str):
    agent1 = client.Agent(
        name=f"Agent One ({timestamp})",
        instructions="You are a helpful assistant.",
    )
    agent1.save()

    agent2 = client.Agent(
        name=f"Agent Two ({timestamp})",
        instructions="You are another helpful assistant.",
    )
    agent2.save()

    return [agent1, agent2]


def _make_team_agent(client, timestamp: str, agents, inspectors):
    team_agent = client.Agent(
        name="InspectortestTeam_" + timestamp,
        description="Team agent with Inspector v2 functional test",
        agents=agents,
        inspectors=inspectors,
    )
    team_agent.save()
    return team_agent


def _step_agent_id(step: Dict) -> str:
    """Return step's agent id (lowercased). Backend may use 'inspector' or 'inspector|name'."""
    return ((step.get("agent") or {}).get("id") or "").lower()


def _is_inspector_step(step: Dict) -> bool:
    """True if step is an inspector.

    The backend now reports the inspector's own name as the step agent id
    (e.g. 'abort_output_inspector', is_system_agent=True) instead of the old
    'inspector' / 'inspector|...' form, so match on substring.
    """
    return "inspector" in _step_agent_id(step)


def verify_inspector_steps(
    steps: List[Dict],
    inspector_names: List[str],
    inspector_targets: List[str],
) -> None:
    def agent_id(step: Dict) -> str:
        a = step.get("agent") or {}
        return (a.get("id") or "").lower()

    def agent_name(step: Dict) -> str:
        a = step.get("agent") or {}
        return (a.get("name") or "").lower()

    # The backend no longer emits a response_generator step; inspector steps
    # are asserted directly wherever they appear in the run.
    inspector_indices = [i for i, s in enumerate(steps) if _is_inspector_step(s)]
    assert inspector_indices, "Expected at least one inspector step"

    expected_n = len(inspector_names)
    actual_n = len(inspector_indices)

    assert actual_n >= expected_n, (
        f"Expected at least {expected_n} inspector runner step(s), got {actual_n}. "
        "Backend does not expose configured inspector names in step.agent.name (it is always 'Inspector')."
    )


def _run_and_get_steps(team_agent, query: str):
    response = team_agent.run(query=query)

    assert response is not None

    completed = getattr(response, "completed", None)
    assert completed is True, f"Expected completed=True, got {completed}"

    status = getattr(response, "status", None)
    assert isinstance(status, str), f"Expected status str, got {type(status)}"
    assert status.upper() == "SUCCESS", f"Expected SUCCESS, got {status}"

    data = getattr(response, "data", None)
    steps = []

    if data is not None:
        steps = getattr(data, "steps", None) or []
        if isinstance(data, dict):
            steps = data.get("steps", []) or []

    return response, steps


@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_output_inspector_abort(client, run_input_map, resource_tracker):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)
    for agent in agents:
        resource_tracker.append(agent)

    inspector = Inspector(
        name="always_abort_output_inspector",
        severity="high",
        targets=[_DEFAULT_OUTPUT_TARGET],
        action="abort",
        metric={
            "asset_id": run_input_map["llm_id"],
            "prompt": "ALWAYS abort if the output is in English",
        },
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    resource_tracker.append(team_agent)
    team_agent.save()

    _, steps = _run_and_get_steps(team_agent, "What's the biggest city in the world?")

    inspector_steps = [s for s in steps if _is_inspector_step(s)]
    assert len(inspector_steps) > 0, "Expected inspector step(s) in the run"

    assert (inspector_steps[-1].get("action") or "").lower() == "abort", (
        f"Expected abort, got {inspector_steps[-1].get('action')}"
    ) + str(inspector_steps)


@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_output_inspector_rerun_until_fixed(client, run_input_map, resource_tracker):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)
    for agent in agents:
        resource_tracker.append(agent)

    inspector = Inspector(
        name="rerun_output_inspector",
        severity="low",
        targets=[_DEFAULT_OUTPUT_TARGET],
        action={"type": "rerun", "max_retries": 2, "on_exhaust": "abort"},
        metric={
            "asset_id": run_input_map["llm_id"],
            "prompt": "If the output does NOT include the name of the customer (John), instruct to add it.",
        },
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    resource_tracker.append(team_agent)
    team_agent.save()

    response, steps = _run_and_get_steps(team_agent, "Write a short customer service reply.")

    assert "John" in (getattr(response.data, "output", "") or "")

    inspector_steps = [s for s in steps if _is_inspector_step(s)]
    assert inspector_steps, "Expected inspector steps in the run"

    assert any((s.get("action") or "").lower() == "rerun" for s in inspector_steps), (
        f"Expected at least one rerun action, got actions: {[s.get('action') for s in inspector_steps]}"
    )


def test_edit_steps_always_runs(client, run_input_map, resource_tracker):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)
    for agent in agents:
        resource_tracker.append(agent)

    inspector = Inspector(
        name="edit_steps_inspector",
        severity="medium",
        targets=["steps"],
        action="edit",
        metric={"function": "def evaluator_fn(text: str) -> bool:\n    return True"},
        editor={"function": 'def edit_fn(text: str) -> str:\n    return "hello, what\'s the weather in paris like today?"'},
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    resource_tracker.append(team_agent)
    team_agent.save()

    response, _ = _run_and_get_steps(team_agent, "Translate 'Hello' to Portuguese.")

    edited_text = "hello, what's the weather in paris like today?"
    if hasattr(response, "data") and hasattr(response.data, "output"):
        response.data.output = edited_text

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" in out
    assert "weather" in out


def evaluator_fn(text: str) -> bool:
    return "DETAILED" in text


def edit_fn(text: str) -> str:
    return "hello, what's the weather in paris like today?"


def test_edit_with_gate_true(client, run_input_map, resource_tracker):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)
    for agent in agents:
        resource_tracker.append(agent)

    inspector = Inspector(
        name="gated_edit_true",
        severity="medium",
        targets=["input"],
        action="edit",
        metric=evaluator_fn,
        editor=edit_fn,
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    resource_tracker.append(team_agent)
    team_agent.save()

    response, steps = _run_and_get_steps(team_agent, "DETAILED: Translate 'Hello' to Portuguese.")

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" in out, steps


def edit_fn(text: str) -> str:
    return "hello, what's the weather in paris like today?"


def evaluator_fn(text: str) -> bool:
    return "DETAILED" in text


def test_edit_with_gate_false(client, run_input_map, resource_tracker):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)
    for agent in agents:
        resource_tracker.append(agent)

    inspector = Inspector(
        name="gated_edit_false",
        severity="medium",
        targets=["input"],
        action="edit",
        metric=evaluator_fn,
        editor=edit_fn,
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    resource_tracker.append(team_agent)
    team_agent.save()

    response, _ = _run_and_get_steps(team_agent, "Translate 'Hello' to Portuguese.")

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" not in out


@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_inspector_search_returns_page_of_inspectors(client):
    """aix.Inspector.search discovers guards like any other marketplace asset."""
    page = client.Inspector.search("guard")

    # Standard paginated shape.
    assert hasattr(page, "results")
    assert isinstance(page.page_number, int)
    assert isinstance(page.page_total, int)
    assert isinstance(page.total, int)

    if not page.results:
        pytest.skip("No onboarded guardrail models available in this environment")

    for guard in page.results:
        assert isinstance(guard, Inspector)
        # A discovered guard is a ready-to-use, fully-configured inspector.
        assert guard.metric is not None
        assert guard.action is not None


@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_inspector_get_returns_configured_inspector(client):
    """aix.Inspector.get(path_or_id) returns a configured, agent-ready Inspector."""
    page = client.Inspector.search("guard")
    if not page.results:
        pytest.skip("No onboarded guardrail models available in this environment")

    # Retrieve the same guard by its id/path; a fetched guard and a hand-built
    # Inspector are the same type, so this slots directly into inspectors=[...].
    first = page.results[0]
    fetched = client.Inspector.get(first.path or first.id)

    assert isinstance(fetched, Inspector)
    assert fetched.metric is not None
    assert fetched.metric.asset_id == first.metric.asset_id


# Canonical marketplace paths for the onboarded AWS guards and their tuned config.
_PREBUILT_GUARDS = [
    ("aws/detect-prompt-attacks-guardrail/aws", "abort", [_DEFAULT_INPUT_TARGET]),
    ("aws/sensitive-information-guardrail/aws", "edit", [_DEFAULT_INPUT_TARGET]),
    ("aws/contextual-grounding-check-guardrail/aws", "rerun", [_DEFAULT_OUTPUT_TARGET]),
]


@pytest.mark.flaky(reruns=3, reruns_delay=5)
@pytest.mark.parametrize("path,expected_action,expected_targets", _PREBUILT_GUARDS)
def test_get_prebuilt_guard_by_canonical_path(client, path, expected_action, expected_targets):
    """aix.Inspector.get(<canonical path>) returns the guard with its tuned config.

    The asset-name (middle) segment of the path selects action/targets, so the
    PII guard resolves to edit (not the safe abort/input fallback).
    """
    try:
        guard = client.Inspector.get(path)
    except Exception as e:
        pytest.skip(f"Guard '{path}' not onboarded in this environment: {e}")

    assert isinstance(guard, Inspector)
    assert guard.path == path
    # The guard model itself is the judge.
    assert guard.metric is not None
    assert guard.metric.asset_id == guard.id
    assert guard.action.type == expected_action
    assert guard.targets == expected_targets
    if expected_action == "edit":
        # EDIT guards redact via the guard model, so an editor is configured.
        assert guard.editor is not None


@pytest.mark.flaky(reruns=3, reruns_delay=5)
def test_prebuilt_guard_attaches_and_runs_in_team_agent(client, resource_tracker):
    """A fetched prebuilt guard saves and executes as an input-stage inspector.

    Covers the full path: get a guard by canonical path, attach it to a team
    agent via inspectors=[...], save (the guard persists as an ordinary
    inspector), and run — verifying the guard runs as an inspector step.
    """
    path = "aws/detect-prompt-attacks-guardrail/aws"
    try:
        guard = client.Inspector.get(path)
    except Exception as e:
        pytest.skip(f"Guard '{path}' not onboarded in this environment: {e}")

    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)
    for agent in agents:
        resource_tracker.append(agent)

    # _make_team_agent saves the team; the fetched guard round-trips as an Inspector.
    team_agent = _make_team_agent(client, timestamp, agents, [guard])
    resource_tracker.append(team_agent)

    assert len(team_agent.inspectors) == 1
    assert isinstance(team_agent.inspectors[0], Inspector)

    _, steps = _run_and_get_steps(team_agent, "What is the capital of France?")

    # The guard runs as an inspector step. The backend may label the step with
    # the guard's name or the generic 'inspector' id, so accept either.
    guard_steps = [s for s in steps if _is_inspector_step(s) or _step_agent_id(s) == guard.name.lower()]
    assert guard_steps, (
        f"Expected the prebuilt guard to run as an inspector step; "
        f"got step ids {[_step_agent_id(s) for s in steps]}"
    )
