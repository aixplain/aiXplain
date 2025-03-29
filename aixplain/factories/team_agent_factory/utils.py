__author__ = "lucaspavanelli"

import logging
from typing import Dict, Text, List
from urllib.parse import urljoin

import aixplain.utils.config as config
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent, InspectorTarget


GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_team_agent(payload: Dict, agents: List[Agent] = None, api_key: Text = config.TEAM_API_KEY) -> TeamAgent:
    """Instantiate a new team agent in the platform."""
    from aixplain.factories.agent_factory import AgentFactory

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

    inspector_targets = [InspectorTarget(target.lower()) for target in payload.get("inspectorTargets", [])]

    team_agent = TeamAgent(
        id=payload.get("id", ""),
        name=payload.get("name", ""),
        agents=payload_agents,
        description=payload.get("description", ""),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        use_mentalist=True if payload.get("plannerId", None) is not None else False,
        use_inspector=True if payload.get("inspectorId", None) is not None else False,
        max_inspectors=payload.get("maxInspectors", 1),
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
