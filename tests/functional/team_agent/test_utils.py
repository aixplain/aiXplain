"""
Shared test utilities for team agent tests.
"""

import json
from copy import copy
from typing import Dict

from aixplain.factories import AgentFactory
from aixplain.enums.supplier import Supplier


RUN_FILE = "tests/functional/team_agent/data/team_agent_test_end2end.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


def create_agents_from_input_map(run_input_map, deploy=True):
    """Helper function to create agents from input map"""
    agents = []
    for agent in run_input_map["agents"]:
        tools = []
        if "model_tools" in agent:
            for tool in agent["model_tools"]:
                tool_ = copy(tool)
                for supplier in Supplier:
                    if tool["supplier"] is not None and tool["supplier"].lower() in [
                        supplier.value["code"].lower(),
                        supplier.value["name"].lower(),
                    ]:
                        tool_["supplier"] = supplier
                        break
                tools.append(AgentFactory.create_model_tool(**tool_))
        if "pipeline_tools" in agent:
            for tool in agent["pipeline_tools"]:
                tools.append(AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"]))

        agent = AgentFactory.create(
            name=agent["agent_name"],
            description=agent["agent_name"],
            instructions=agent["agent_name"],
            llm_id=agent["llm_id"],
            tools=tools,
        )
        if deploy:
            agent.deploy()
        agents.append(agent)

    return agents


def create_team_agent(factory, agents, run_input_map, use_mentalist=True):
    """Helper function to create a team agent"""

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
    assert (
        len(response_generator_steps) == 1
    ), f"Expected exactly one response_generator step, found {len(response_generator_steps)}"
