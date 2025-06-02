__author__ = "lucaspavanelli"

import logging
from typing import Dict, Text, List
from urllib.parse import urljoin

import aixplain.utils.config as config
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent, InspectorTarget
from aixplain.modules.team_agent.inspector import Inspector
from aixplain.factories.agent_factory import AgentFactory
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules.model.model_parameters import ModelParameters


GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_team_agent(payload: Dict, agents: List[Agent] = None, api_key: Text = config.TEAM_API_KEY) -> TeamAgent:
    """Instantiate a new team agent in the platform."""
    agents_dict = payload["agents"]
    payload_agents = agents
    if payload_agents is None:
        payload_agents = []
        for i, agent in enumerate(agents_dict):
            try:
                payload_agents.append(AgentFactory.get(agent["assetId"]))
            except Exception:
                logging.warning(
                    f"Agent {agent['assetId']} not found. Make sure it exists or you have access to it. "
                    "If you think this is an error, please contact the administrators."
                )
                continue

    # Ensure custom classes are instantiated: for compatibility with backend return format
    inspectors = [
        inspector if isinstance(inspector, Inspector) else Inspector(**inspector) for inspector in payload.get("inspectors", [])
    ]
    inspector_targets = [InspectorTarget(target.lower()) for target in payload.get("inspectorTargets", [])]

    # Get LLMs from tools if present
    supervisor_llm = None
    mentalist_llm = None

    # First check if we have direct LLM objects in the payload
    if "supervisor_llm" in payload:
        supervisor_llm = payload["supervisor_llm"]
    if "mentalist_llm" in payload:
        mentalist_llm = payload["mentalist_llm"]
    # Otherwise create from the parameters
    elif "tools" in payload:
        for tool in payload["tools"]:
            if tool["type"] == "llm":
                llm = ModelFactory.get(payload["llmId"], api_key=api_key)
                # Set parameters from the tool
                if "parameters" in tool:
                    # Apply all parameters directly to the LLM properties
                    for param in tool["parameters"]:
                        param_name = param["name"]
                        param_value = param["value"]
                        # Apply any parameter that exists as an attribute on the LLM
                        if hasattr(llm, param_name):
                            setattr(llm, param_name, param_value)

                    # Also set model_params for completeness
                    # Convert parameters list to dictionary format expected by ModelParameters
                    params_dict = {}
                    for param in tool["parameters"]:
                        params_dict[param["name"]] = {"required": False, "value": param["value"]}
                    # Create ModelParameters and set it on the LLM
                    llm.model_params = ModelParameters(params_dict)

                # Assign LLM based on description
                if tool["description"] == "supervisor":
                    supervisor_llm = llm
                elif tool["description"] == "mentalist":
                    mentalist_llm = llm

    team_agent = TeamAgent(
        id=payload.get("id", ""),
        name=payload.get("name", ""),
        agents=payload_agents,
        description=payload.get("description", ""),
        instructions=payload.get("role", None),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        supervisor_llm=supervisor_llm,
        mentalist_llm=mentalist_llm,
        use_mentalist=True if payload.get("plannerId", None) is not None else False,
        inspectors=inspectors,
        inspector_targets=inspector_targets,
        api_key=api_key,
        status=AssetStatus(payload["status"]),
    )
    team_agent.url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}/run")

    # fill up dependencies
    all_tasks = {}
    for agent in team_agent.agents:
        for task in agent.tasks:
            all_tasks[task.name] = task

    for idx, agent in enumerate(team_agent.agents):
        for i, task in enumerate(agent.tasks):
            for j, dependency in enumerate(task.dependencies or []):
                if isinstance(dependency, Text):
                    task_dependency = all_tasks.get(dependency, None)
                    if task_dependency:
                        team_agent.agents[idx].tasks[i].dependencies[j] = task_dependency
                    else:
                        raise Exception(f"Team Agent Creation Error: Task dependency not found - {dependency}")
    return team_agent
