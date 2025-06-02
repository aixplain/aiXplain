"""
Functional tests for team agents with inspectors.
"""

from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

import pytest

from aixplain import aixplain_v2 as v2
from aixplain.factories import AgentFactory, TeamAgentFactory
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.team_agent import InspectorTarget
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy

from tests.functional.team_agent.test_utils import (
    RUN_FILE,
    read_data,
    create_agents_from_input_map,
    create_team_agent,
    verify_response_generator,
)


@pytest.fixture(scope="function")
def delete_agents_and_team_agents():
    for team_agent in TeamAgentFactory.list()["results"]:
        team_agent.delete()
    for agent in AgentFactory.list()["results"]:
        agent.delete()

    yield True

    for team_agent in TeamAgentFactory.list()["results"]:
        team_agent.delete()
    for agent in AgentFactory.list()["results"]:
        agent.delete()


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


def verify_inspector_steps(steps: Dict, inspector_names: List[str], inspector_targets: List[InspectorTarget]) -> None:
    """Helper function to verify inspector steps"""
    # Count occurrences of each inspector
    inspector_counts = {}
    for inspector_name in inspector_names:
        inspector_steps = [step for step in steps if inspector_name.lower() in step.get("agent", "").lower()]
        inspector_counts[inspector_name] = len(inspector_steps)

    # Verify all inspectors are present and have the same number of steps
    assert len(inspector_counts) == len(
        inspector_names
    ), f"Expected {len(inspector_names)} inspectors, found {len(inspector_counts)}"

    if len(inspector_counts) > 0:
        first_count = next(iter(inspector_counts.values()))
        for inspector, count in inspector_counts.items():
            assert count > 0, f"Inspector {inspector} has no steps"
            assert count == first_count, f"Inspector {inspector} has {count} steps, expected {first_count}"
            print(f"Inspector {inspector} has {count} steps")

    # If OUTPUT is in inspector_targets, verify there are inspector steps after response generator
    if InspectorTarget.OUTPUT in inspector_targets:
        response_generator_steps = [step for step in steps if "response_generator" in step.get("agent", "").lower()]
        assert len(response_generator_steps) == 1, "Expected exactly one response_generator step"
        response_generator_index = steps.index(response_generator_steps[0])

        inspector_steps_after = [
            step
            for step in steps[response_generator_index + 1 :]
            if any(inspector_name.lower() in step.get("agent", "").lower() for inspector_name in inspector_names)
        ]
        assert len(inspector_steps_after) > 0, "No inspector steps found after response generator step"
        print(f"Found {len(inspector_steps_after)} inspector steps after response generator")


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_steps_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with one inspector targeting steps"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    # Create inspector
    inspector = Inspector(
        name="test_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the steps are valid"},
        policy=InspectorPolicy.WARN,
    )

    # Create team agent with steps inspector
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

    # deploy team agent
    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    # Run the team agent
    response = team_agent.run(data=run_input_map["query"])

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    # Check for inspector steps
    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["test_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_output_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with one inspector targeting output"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    # Create inspector
    inspector = Inspector(
        name="test_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the output is valid"},
        policy=InspectorPolicy.WARN,
    )

    # Create team agent with output inspector
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

    # deploy team agent
    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    # Run the team agent
    response = team_agent.run(data=run_input_map["query"])

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    # Check for inspector steps
    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["test_inspector"], [InspectorTarget.OUTPUT])
        verify_response_generator(steps)

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_multiple_inspectors(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with multiple inspectors targeting steps"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    # Create inspectors
    inspector1 = Inspector(
        name="test1_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the steps are valid"},
        policy=InspectorPolicy.WARN,
    )
    inspector2 = Inspector(
        name="test2_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the steps are valid"},
        policy=InspectorPolicy.WARN,
    )

    # Create team agent with multiple steps inspectors
    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
        inspectors=[inspector1, inspector2],
        inspector_targets=[InspectorTarget.STEPS],
    )

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    # deploy team agent
    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED

    # Run the team agent
    response = team_agent.run(data=run_input_map["query"])

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"

    # Check for inspector steps
    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["test1_inspector", "test2_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

    team_agent.delete()
