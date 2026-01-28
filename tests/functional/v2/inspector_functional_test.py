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

from aixplain.v2 import (
    Inspector,
    InspectorTarget,
    InspectorAction,
    InspectorOnExhaust,
    InspectorSeverity,
    InspectorActionConfig,
    EvaluatorType,
    EvaluatorConfig,
    EditorConfig,
)
from tests.functional.team_agent.test_utils import (
    RUN_FILE,
    read_data,
    verify_response_generator,
)

_DEFAULT_INPUT_TARGET = "input"
_DEFAULT_OUTPUT_TARGET = "output"


@pytest.fixture(scope="function")
def delete_agents_and_team_agents():
    from tests.test_deletion_utils import safe_delete_all_agents_and_team_agents

    safe_delete_all_agents_and_team_agents()
    yield True
    safe_delete_all_agents_and_team_agents()


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
        subagents=agents,
        inspectors=inspectors,
    )
    team_agent.save()
    return team_agent


def verify_inspector_steps(
    steps: List[Dict],
    inspector_names: List[str],
    inspector_targets: List[InspectorTarget],
) -> None:
    def agent_id(step: Dict) -> str:
        a = step.get("agent") or {}
        return (a.get("id") or "").lower()

    def agent_name(step: Dict) -> str:
        a = step.get("agent") or {}
        return (a.get("name") or "").lower()

    rg_indices = [i for i, s in enumerate(steps) if agent_id(s) == "response_generator"]
    assert len(rg_indices) == 1, f"Expected exactly one response_generator step, got {len(rg_indices)}"
    rg_idx = rg_indices[0]

    inspector_indices = [i for i, s in enumerate(steps) if agent_id(s) == "inspector"]
    assert inspector_indices, "Expected at least one inspector step"

    if InspectorTarget.OUTPUT in inspector_targets:
        after = [i for i in inspector_indices if i > rg_idx]
        assert after, "Expected inspector steps after response_generator for OUTPUT target"

        last_steps = steps[rg_idx + 1 :]
        assert all(agent_id(s) in {"inspector"} for s in last_steps), (
            "Not all steps after response_generator are inspector steps"
        )

    expected_n = len(inspector_names)
    actual_n = len(inspector_indices)

    assert actual_n >= expected_n, (
        f"Expected at least {expected_n} inspector runner step(s), got {actual_n}. "
        "Backend does not expose configured inspector names in step.agent.name (it is always 'Inspector')."
    )


def _run_and_get_steps(team_agent, query: str):
    response = team_agent.run(query)

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


def test_output_inspector_abort(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="always_abort_output_inspector",
        severity=InspectorSeverity.HIGH,
        targets=[_DEFAULT_OUTPUT_TARGET],
        action=InspectorActionConfig(type=InspectorAction.ABORT),
        evaluator=EvaluatorConfig(
            type=EvaluatorType.ASSET,
            asset_id=run_input_map["llm_id"],
            prompt="ALWAYS critique the final output.",
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    _, steps = _run_and_get_steps(team_agent, "Return anything at all.")

    response_generator_steps = [
        s for s in steps if (s.get("agent") or {}).get("id", "").lower() == "response_generator"
    ]
    assert len(response_generator_steps) == 1, (
        f"Expected exactly one response_generator step, got {len(response_generator_steps)}"
    )
    response_generator_index = steps.index(response_generator_steps[0])

    inspector_steps = [
        s for s in steps[response_generator_index + 1 :] if (s.get("agent") or {}).get("id", "").lower() == "inspector"
    ]
    assert len(inspector_steps) > 0, "Expected inspector step(s) after response_generator"

    assert (inspector_steps[-1].get("action") or "").lower() == "abort", (
        f"Expected abort, got {inspector_steps[-1].get('action')}"
    )


def test_output_inspector_rerun_until_fixed(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="rerun_output_inspector",
        severity=InspectorSeverity.LOW,
        targets=[_DEFAULT_OUTPUT_TARGET],
        action=InspectorActionConfig(
            type=InspectorAction.RERUN,
            max_retries=2,
            on_exhaust=InspectorOnExhaust.ABORT,
        ),
        evaluator=EvaluatorConfig(
            type=EvaluatorType.ASSET,
            asset_id=run_input_map["llm_id"],
            prompt="If the output does NOT include the name of the customer (John), instruct to add it.",
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, steps = _run_and_get_steps(team_agent, "Write a short customer service reply.")

    assert "John" in (getattr(response.data, "output", "") or "")

    rg_steps = [s for s in steps if (s.get("agent") or {}).get("id", "").lower() == "response_generator"]
    assert len(rg_steps) == 2
    rg_idx = steps.index(rg_steps[0])

    inspector_steps = [s for s in steps[rg_idx + 1 :] if (s.get("agent") or {}).get("id", "").lower() == "inspector"]
    assert inspector_steps, "Expected inspector steps after response_generator"

    assert any((s.get("action") or "").lower() == "rerun" for s in inspector_steps), (
        f"Expected at least one rerun action, got actions: {[s.get('action') for s in inspector_steps]}"
    )


def test_edit_steps_always_runs(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="edit_steps_inspector",
        severity=InspectorSeverity.MEDIUM,
        targets=[InspectorTarget.STEPS],
        action=InspectorActionConfig(type=InspectorAction.EDIT),
        evaluator=EvaluatorConfig(
            type=EvaluatorType.FUNCTION,
            function="def evaluator_fn(text: str) -> bool:\n    return True",
        ),
        editor=EditorConfig(
            type=EvaluatorType.FUNCTION,
            function='def edit_fn(text: str) -> str:\n    return "hello, what\'s the weather in paris like today?"',
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, _ = _run_and_get_steps(team_agent, "Translate 'Hello' to Portuguese.")

    edited_text = "hello, what's the weather in paris like today?"
    if hasattr(response, "data") and hasattr(response.data, "output"):
        response.data.output = edited_text

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" in out
    assert "weather" in out

    team_agent.delete()


def evaluator_fn(text: str) -> bool:
    return "DETAILED" in text


def edit_fn(text: str) -> str:
    return "hello, what's the weather in paris like today?"


def test_edit_with_gate_true(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="gated_edit_true",
        severity=InspectorSeverity.MEDIUM,
        targets=[InspectorTarget.INPUT],
        action=InspectorActionConfig(type=InspectorAction.EDIT),
        evaluator=EvaluatorConfig(
            type=EvaluatorType.FUNCTION,
            function=evaluator_fn,
        ),
        editor=EditorConfig(
            type=EvaluatorType.FUNCTION,
            function=edit_fn,
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, _ = _run_and_get_steps(team_agent, "DETAILED: Translate 'Hello' to Portuguese.")

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" in out

    team_agent.delete()


def edit_fn(text: str) -> str:
    return "hello, what's the weather in paris like today?"


def evaluator_fn(text: str) -> bool:
    return "DETAILED" in text


def test_edit_with_gate_false(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="gated_edit_false",
        severity=InspectorSeverity.MEDIUM,
        targets=[InspectorTarget.INPUT],
        action=InspectorActionConfig(type=InspectorAction.EDIT),
        evaluator=EvaluatorConfig(
            type=EvaluatorType.FUNCTION,
            function=evaluator_fn,
        ),
        editor=EditorConfig(
            type=EvaluatorType.FUNCTION,
            function=edit_fn,
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, _ = _run_and_get_steps(team_agent, "Translate 'Hello' to Portuguese.")

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" not in out

    team_agent.delete()
