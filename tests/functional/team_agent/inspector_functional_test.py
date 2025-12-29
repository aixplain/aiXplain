"""
Functional tests for team agents with inspectors.

WARNING: This feature is currently in private beta.
"""

from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

import pytest

from aixplain import aixplain_v2 as v2
from aixplain.factories import AgentFactory, TeamAgentFactory
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.team_agent import InspectorTarget
from aixplain.modules.team_agent.inspector import (
    Inspector,
    InspectorActionConfig,
    InspectorActionType,
    InspectorOnExhaust,
    InspectorSeverity,
)

from tests.functional.team_agent.test_utils import (
    RUN_FILE,
    read_data,
    create_agents_from_input_map,
    create_team_agent,
    verify_response_generator,
)

# ---- minimal config points ----
_DEFAULT_STEP_TARGET = "Agent1_agent"    
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


def verify_inspector_steps(steps: Dict, inspector_names: List[str], inspector_targets: List[InspectorTarget]) -> None:
    """Helper function to verify inspector steps"""
    inspector_counts = {}
    for inspector_name in inspector_names:
        inspector_steps = [step for step in steps if inspector_name.lower() in step.get("agent", "").lower()]
        inspector_counts[inspector_name] = len(inspector_steps)

    assert len(inspector_counts) == len(
        inspector_names
    ), f"Expected {len(inspector_names)} inspectors, found {len(inspector_counts)}"


    if len(inspector_counts) > 0:
        first_count = next(iter(inspector_counts.values()))
        for inspector, count in inspector_counts.items():
            assert count > 0, f"Inspector {inspector} has no steps"
            assert count == first_count, f"Inspector {inspector} has {count} steps, expected {first_count}"
            print(f"Inspector {inspector} has {count} steps")

    if InspectorTarget.OUTPUT in inspector_targets:
        response_generator_steps = [step for step in steps if "response_generator" in step.get("agent", "").lower()]
        assert len(response_generator_steps) == 1, "Expected exactly one response_generator step"
        response_generator_index = steps.index(response_generator_steps[0])

        inspector_steps_after = [
            step
            for step in steps[response_generator_index + 1 :]
            if any(inspector_name.lower() in step.get("agent", "").lower() for inspector_name in inspector_names)
        ]
        assert (
            len(inspector_steps_after) > 0
        ), "No inspector steps found after response generator step"

        last_steps = steps[response_generator_index + 1 :]
        assert all(
            any(inspector_name.lower() in step.get("agent", "").lower() for inspector_name in inspector_names)
            for step in last_steps
        ), "Not all steps after response generator are inspector steps"


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_warn_inspector(
    run_input_map, delete_agents_and_team_agents, TeamAgentFactory
):
    """Test team agent with CONTINUE inspector (warn-like: does not stop execution)"""

    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    inspector = Inspector(
        name="warn_inspector",
        description="Provides feedback but continues.",
        severity=InspectorSeverity.LOW,  # allows CONTINUE/RERUN
        targets=[_DEFAULT_STEP_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.CONTINUE,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Inspect ONLY the step output. If wrong, provide a critique. Otherwise output nothing.",
        ),
    )

    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.STEPS],
    )
    query = "What is the translation of 'Hello' to Portuguese?"

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    response = team_agent.run(data=query)

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["warn_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

        inspector_steps = [
            step for step in steps if "warn_inspector" in step.get("agent", "").lower()
        ]
        assert len(inspector_steps) > 0, "Inspector should run at least once"

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_adaptive_inspector(
    run_input_map, delete_agents_and_team_agents, TeamAgentFactory
):
    """Test team agent with rerun inspector (adaptive-like behavior happens in backend)"""


    agents = create_agents_from_input_map(run_input_map)

    inspector = Inspector(
        name="adaptive_inspector",
        description="Requests rerun when issues detected.",
        severity=InspectorSeverity.MEDIUM,  # allows RERUN/EDIT
        targets=[_DEFAULT_STEP_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.RERUN,
            max_retries=2,
            on_exhaust=InspectorOnExhaust.CONTINUE,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Always provide a critique to force at least one rerun.",
        ),

    )

    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.STEPS],
    )

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    response = team_agent.run(data="What is the translation of 'Hello' to Portuguese?")

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["adaptive_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

        inspector_steps = [
            step for step in steps if "adaptive_inspector" in step.get("agent", "").lower()
        ]
        assert len(inspector_steps) > 0, "Adaptive inspector should run"


    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_team_agent_with_abort_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with abort inspector that stops execution on critique"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    inspector = Inspector(
        name="abort_inspector",
        description="Always abort for test coverage.",
        severity=InspectorSeverity.HIGH,  # allows ABORT/EDIT
        targets=[_DEFAULT_STEP_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.ABORT,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Always provide a critique that forces abort.",
        ),
    )

    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.STEPS],
    )

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    response = team_agent.run(data="What is the translation of 'Hello' to Portuguese?")

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["abort_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

        inspector_steps = [
            step for step in steps if "abort_inspector" in step.get("agent", "").lower()
        ]
        assert len(inspector_steps) >= 1, "Abort inspector should run"


    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_team_agent_with_output_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with output inspector that runs after response generator"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    inspector = Inspector(
        name="output_inspector",
        description="Inspect output after response_generator.",
        severity=InspectorSeverity.LOW,  # allows CONTINUE/RERUN
        targets=[_DEFAULT_OUTPUT_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.CONTINUE,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Inspect ONLY the final output. If invalid, provide critique; else output nothing.",
        ),
    )

    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.OUTPUT],
    )

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    response = team_agent.run(data="What is the translation of 'Hello' to Portuguese?")

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["output_inspector"], [InspectorTarget.OUTPUT])
        verify_response_generator(steps)

        output_inspector_steps = [
            step for step in steps if "output_inspector" in step.get("agent", "").lower()
        ]
        assert len(output_inspector_steps) > 0, "There should be an output inspector step"


    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_team_agent_with_multiple_inspector_targets(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with inspectors targeting both steps and output"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    steps_inspector = Inspector(
        name="steps_inspector",
        description="Inspect steps.",
        severity=InspectorSeverity.LOW,
        targets=[_DEFAULT_STEP_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.CONTINUE,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Inspect ONLY the step output. Provide critique if invalid; else output nothing.",
        ),
    )
    output_inspector = Inspector(
        name="output_inspector",
        description="Inspect output.",
        severity=InspectorSeverity.LOW,
        targets=[_DEFAULT_OUTPUT_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.CONTINUE,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Inspect ONLY the final output. Provide critique if invalid; else output nothing.",
        ),
    )

    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[steps_inspector, output_inspector],
        inspector_targets=[InspectorTarget.STEPS, InspectorTarget.OUTPUT],
    )

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    response = team_agent.run(data="What is the translation of 'Hello' to Portuguese?")

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(
            steps,
            ["steps_inspector", "output_inspector"],
            [InspectorTarget.STEPS, InspectorTarget.OUTPUT],
        )
        verify_response_generator(steps)

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_team_agent_with_steps_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with steps inspector"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    inspector = Inspector(
        name="steps_inspector",
        description="Inspect steps.",
        severity=InspectorSeverity.LOW,
        targets=[_DEFAULT_STEP_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.CONTINUE,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Inspect ONLY the step output. Provide critique if invalid; else output nothing.",
        ),
    )

    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.STEPS],
    )

    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)

    response = team_agent.run(data="What is the translation of 'Hello' to Portuguese?")
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["steps_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

        inspector_steps = [step for step in steps if "steps_inspector" in step.get("agent", "").lower()]
        assert len(inspector_steps) > 0, "Steps inspector should run at least once"

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])

def test_team_agent_with_input_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with input inspector"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    inspector = Inspector(
        name="input_inspector",
        description="Inspect input.",
        severity=InspectorSeverity.LOW,
        targets=[_DEFAULT_INPUT_TARGET],
        action=InspectorActionConfig(
            action_type=InspectorActionType.CONTINUE,
            evaluator=run_input_map["llm_id"],
            evaluator_prompt="Inspect ONLY the query. Provide critique if invalid; else output nothing.",
        ),
    )

    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[inspector],
        inspector_targets=[InspectorTarget.INPUT],
    )

    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)

    response = team_agent.run(data="What is the translation of 'Hello' to Portuguese?")
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["input_inspector"], [InspectorTarget.INPUT])
        verify_response_generator(steps)

    team_agent.delete()

    
