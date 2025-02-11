__author__ = "lucaspavanelli"

import aixplain.utils.config as config
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.team_agent import TeamAgent
from typing import Dict, Text
from urllib.parse import urljoin

GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_team_agent(payload: Dict, api_key: Text = config.TEAM_API_KEY) -> TeamAgent:
    """Instantiate a new team agent in the platform."""
    from aixplain.factories.agent_factory import AgentFactory

    agents_dict = payload["agents"]
    agents = []
    for i, agent in enumerate(agents_dict):
        agent = AgentFactory.get(agent["assetId"])
        agents.append(agent)

    team_agent = TeamAgent(
        id=payload.get("id", ""),
        name=payload.get("name", ""),
        agents=agents,
        description=payload.get("description", ""),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        use_mentalist_and_inspector=True if payload["plannerId"] is not None else False,
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
