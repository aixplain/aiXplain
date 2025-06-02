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

        # Verify inspector steps are the last steps
        last_steps = steps[response_generator_index + 1 :]
        assert all(
            any(inspector_name.lower() in step.get("agent", "").lower() for inspector_name in inspector_names)
            for step in last_steps
        ), "Not all steps after response generator are inspector steps"


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_adaptive_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with adaptive inspector that runs multiple times"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    # Create inspector with adaptive policy
    inspector = Inspector(
        name="adaptive_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the steps are valid and provide feedback for improvement"},
        policy=InspectorPolicy.ADAPTIVE,
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
        print(*steps, sep="\n")
        verify_inspector_steps(steps, ["adaptive_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

        # Verify inspector runs multiple times
        inspector_steps = [step for step in steps if "adaptive_inspector" in step.get("agent", "").lower()]
        assert len(inspector_steps) > 1, "Adaptive inspector should run more than once"

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_abort_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with abort inspector that stops execution on critique"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    # Create inspector with abort policy
    inspector = Inspector(
        name="abort_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Always find issues and provide negative feedback"},
        policy=InspectorPolicy.ABORT,
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
    assert "I couldn't provide an answer because the inspector detected issues" in response["data"]["output"]

    # Check for inspector steps
    if "intermediate_steps" in response["data"]:
        steps = response["data"]["intermediate_steps"]
        verify_inspector_steps(steps, ["abort_inspector"], [InspectorTarget.STEPS])
        verify_response_generator(steps)

        # Verify response generator comes right after first inspector critique
        inspector_steps = [step for step in steps if "abort_inspector" in step.get("agent", "").lower()]
        assert len(inspector_steps) == 1, "Abort inspector should only run once"
        response_generator_index = steps.index(
            [step for step in steps if "response_generator" in step.get("agent", "").lower()][0]
        )
        assert (
            response_generator_index == steps.index(inspector_steps[0]) + 1
        ), "Response generator should come right after inspector critique"

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_output_inspector(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with output inspector that runs after response generator"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    # Create inspector
    inspector = Inspector(
        name="output_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the output is valid and provide feedback"},
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
        verify_inspector_steps(steps, ["output_inspector"], [InspectorTarget.OUTPUT])
        verify_response_generator(steps)

        # Verify critiques are in response data
        assert "critiques" in response["data"]
        assert response["data"]["critiques"], "No critiques found in response data"

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_with_multiple_inspector_targets(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    """Test team agent with inspectors targeting both steps and output"""
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map)

    # Create inspectors
    steps_inspector = Inspector(
        name="steps_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the steps are valid"},
        policy=InspectorPolicy.WARN,
    )
    output_inspector = Inspector(
        name="output_inspector",
        model_id=run_input_map["llm_id"],
        model_params={"prompt": "Check if the output is valid"},
        policy=InspectorPolicy.WARN,
    )

    # Create team agent with multiple inspectors
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
        verify_inspector_steps(steps, ["steps_inspector", "output_inspector"], [InspectorTarget.STEPS, InspectorTarget.OUTPUT])
        verify_response_generator(steps)

        # Verify critiques are in response data
        assert "critiques" in response["data"]
        assert response["data"]["critiques"], "No critiques found in response data"

    team_agent.delete()
