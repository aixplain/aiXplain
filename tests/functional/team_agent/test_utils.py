"""
Shared test utilities for team agent tests.
"""

import json
from copy import copy
from typing import Dict

from aixplain.factories import AgentFactory, TeamAgentFactory
from aixplain.enums.supplier import Supplier


RUN_FILE = "tests/functional/team_agent/data/team_agent_test_end2end.json"


def delete_agent_by_name(name: str, max_retries: int = 3):
    """Delete an agent with the given name if it exists, with retries."""
    import time

    for attempt in range(max_retries):
        try:
            agent = AgentFactory.get(name=name)
            agent.delete()
            time.sleep(2)  # Wait for backend to process delete
        except Exception:
            return  # Agent doesn't exist or was deleted successfully


def delete_team_agent_by_name(name: str, max_retries: int = 3):
    """Delete a team agent with the given name if it exists, with retries."""
    import time

    for attempt in range(max_retries):
        try:
            team_agent = TeamAgentFactory.get(name=name)
            team_agent.delete()
            time.sleep(2)  # Wait for backend to process delete
        except Exception:
            return  # Team agent doesn't exist or was deleted successfully


def read_data(data_path):
    return json.load(open(data_path, "r"))


def create_agents_from_input_map(run_input_map, deploy=True):
    """Helper function to create agents from input map"""
    # First delete any existing team agent (so agents are no longer in use)
    if "team_agent_name" in run_input_map:
        delete_team_agent_by_name(run_input_map["team_agent_name"])

    agents = []
    for agent_config in run_input_map["agents"]:
        # Clean up any existing agent with the same name
        delete_agent_by_name(agent_config["agent_name"])

        tools = []
        if "model_tools" in agent_config:
            for tool in agent_config["model_tools"]:
                tool_ = copy(tool)
                for supplier in Supplier:
                    if tool["supplier"] is not None and tool["supplier"].lower() in [
                        supplier.value["code"].lower(),
                        supplier.value["name"].lower(),
                    ]:
                        tool_["supplier"] = supplier
                        break
                tools.append(AgentFactory.create_model_tool(**tool_))
        if "pipeline_tools" in agent_config:
            for tool in agent_config["pipeline_tools"]:
                tools.append(
                    AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"])
                )

        agent = AgentFactory.create(
            name=agent_config["agent_name"],
            description=agent_config["agent_name"],
            instructions=agent_config["agent_name"],
            llm_id=agent_config["llm_id"],
            tools=tools,
        )
        if deploy:
            agent.deploy()
        agents.append(agent)

    return agents


def create_team_agent(factory, agents, run_input_map, use_mentalist=True):
    """Helper function to create a team agent"""
    # Clean up any existing team agent with the same name
    delete_team_agent_by_name(run_input_map["team_agent_name"])

    team_agent = factory.create(
        name=run_input_map["team_agent_name"],
        agents=agents,
        description=run_input_map["team_agent_name"],
        llm_id=run_input_map["llm_id"],
        use_mentalist=use_mentalist,
    )

    return team_agent


def verify_response_generator(steps: Dict) -> None:
    """Helper function to verify response generator step"""
    response_generator_steps = [step for step in steps if "response_generator" in step.get("agent", "").lower()]
    assert len(response_generator_steps) == 1, (
        f"Expected exactly one response_generator step, found {len(response_generator_steps)}"
    )
