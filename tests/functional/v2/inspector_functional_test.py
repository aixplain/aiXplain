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

from aixplain.modules.team_agent import InspectorTarget
from aixplain.modules.team_agent.inspector import (
    InspectorActionConfig,
    Inspectoraction_type,
    InspectorOnExhaust,
    InspectorSeverity,
)
from aixplain.v2.inspector import Inspector
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
        agents=agents,
        inspectors=inspectors,
    )
    team_agent.save()
    return team_agent


def verify_inspector_steps(
    steps: List[Dict],
    inspector_names: List[str],
    inspector_targets: List[InspectorTarget],
) -> None:
    inspector_counts = {}
    for inspector_name in inspector_names:
        inspector_steps = [
            step for step in steps
            if inspector_name.lower() in step.get("agent", "").lower()
        ]
        inspector_counts[inspector_name] = len(inspector_steps)

    assert len(inspector_counts) == len(inspector_names), (
        f"Expected {len(inspector_names)} inspectors, found {len(inspector_counts)}"
    )

    if len(inspector_counts) > 0:
        first_count = next(iter(inspector_counts.values()))
        for inspector, count in inspector_counts.items():
            assert count > 0, f"Inspector {inspector} has no steps"
            assert count == first_count, (
                f"Inspector {inspector} has {count} steps, expected {first_count}"
            )

    if InspectorTarget.OUTPUT in inspector_targets:
        response_generator_steps = [
            step for step in steps
            if "response_generator" in step.get("agent", "").lower()
        ]
        assert len(response_generator_steps) == 1, "Expected exactly one response_generator step"
        response_generator_index = steps.index(response_generator_steps[0])

        inspector_steps_after = [
            step
            for step in steps[response_generator_index + 1 :]
            if any(inspector_name.lower() in step.get("agent", "").lower()
                   for inspector_name in inspector_names)
        ]
        assert len(inspector_steps_after) > 0, "No inspector steps found after response generator step"

        last_steps = steps[response_generator_index + 1 :]
        assert all(
            any(inspector_name.lower() in step.get("agent", "").lower() for inspector_name in inspector_names)
            for step in last_steps
        ), "Not all steps after response generator are inspector steps"

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
        steps = getattr(data, "intermediate_steps", None) or []
        if isinstance(data, dict):
            steps = data.get("intermediate_steps", []) or []

    return response, steps



def test_output_inspector_abort(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="always_abort_output_inspector",
        severity=InspectorSeverity.HIGH,
        targets=[_DEFAULT_OUTPUT_TARGET],
        action=InspectorActionConfig(
            actionType=Inspectoraction_type.ABORT,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="ALWAYS critique the final output.",
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    _, steps = _run_and_get_steps(
        team_agent,
        "Return anything at all."
    )

    verify_inspector_steps(
        steps,
        ["always_abort_output_inspector"],
        [InspectorTarget.OUTPUT],
    )

    inspector_steps = [
        s for s in steps if "always_abort_output_inspector" in s.get("agent", "").lower()
    ]
    assert inspector_steps[-1].get("action") == "abort"

    team_agent.delete()


def test_output_inspector_rerun_until_fixed(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="rerun_output_inspector",
        severity=InspectorSeverity.LOW,
        targets=[_DEFAULT_OUTPUT_TARGET],
        action=InspectorActionConfig(
            actionType=Inspectoraction_type.RERUN,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt=(
                "If the output does NOT include the name of the customer (John), instruct to add it."
            ),
            maxRetries=2,
            onExhaust=InspectorOnExhaust.ABORT,
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, steps = _run_and_get_steps(
        team_agent,
        "Write a short customer service reply."
    )

    assert "John" in (getattr(response.data, "output", "") or "")

    inspector_steps = [
        s for s in steps if "rerun_output_inspector" in s.get("agent", "").lower()
    ]
    assert any(s.get("action") == "rerun" for s in inspector_steps)

    team_agent.delete()

def test_edit_steps_always_runs(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="edit_steps_inspector",
        severity=InspectorSeverity.MEDIUM,
        targets=[InspectorTarget.STEPS],
        action=InspectorActionConfig(
            actionType=Inspectoraction_type.EDIT,
            edit_fn=(
                "def edit_fn(text: str) -> str:\n"
                "    return \"hello, what's the weather in paris like today?\""
            ),
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, _ = _run_and_get_steps(
        team_agent,
        "Translate 'Hello' to Portuguese."
    )

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
        action=InspectorActionConfig(
            actionType=Inspectoraction_type.EDIT,
            edit_evaluator_fn=evaluator_fn,
            edit_fn=edit_fn,
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, _ = _run_and_get_steps(
        team_agent,
        "DETAILED: Translate 'Hello' to Portuguese."
    )

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" in out

    team_agent.delete()


def edit_fn(text: str) -> str:
    return "hello, what's the weather in paris like today?"

def gate_fn(text: str) -> bool:
    return "DETAILED" in text
def test_edit_with_gate_false(client, run_input_map, delete_agents_and_team_agents):
    timestamp = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
    agents = _make_two_subagents(client, timestamp)

    inspector = Inspector(
        name="gated_edit_false",
        severity=InspectorSeverity.MEDIUM,
        targets=[InspectorTarget.INPUT],
        action=InspectorActionConfig(
            actionType=Inspectoraction_type.EDIT,
            edit_evaluator_fn=edit_fn,
            edit_fn=gate_fn,
        ),
    )

    team_agent = _make_team_agent(client, timestamp, agents, [inspector])
    team_agent.save()

    response, _ = _run_and_get_steps(
        team_agent,
        "Translate 'Hello' to Portuguese."
    )

    out = (getattr(response.data, "output", "") or "").lower()
    assert "paris" not in out

    team_agent.delete()
