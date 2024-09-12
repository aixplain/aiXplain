__author__ = "lucaspavanelli"

import aixplain.utils.config as config
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.team_agent import TeamAgent
from aixplain.factories.agent_factory import AgentFactory
from typing import Dict, Text
from urllib.parse import urljoin

GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_team_agent(payload: Dict, api_key: Text = config.TEAM_API_KEY) -> TeamAgent:
    """Instantiate a new team agent in the platform."""
    agents = payload["agents"]
    for i, agent in enumerate(agents):
        agent = AgentFactory.get(agent["assetId"])
        agents[i] = agent

    team_agent = TeamAgent(
        id=payload["id"],
        name=payload["name"] if "name" in payload else "",
        agents=agents,
        description=payload["description"] if "description" in payload else "",
        supplier=payload["teamId"] if "teamId" in payload else None,
        version=payload["version"] if "version" in payload else None,
        cost=payload["cost"] if "cost" in payload else None,
        llm_id=payload["llmId"] if "llmId" in payload else GPT_4o_ID,
        use_mentalist_and_inspector=True if "plannerId" in payload and payload["plannerId"] is not None else False,
        api_key=api_key,
        status=AssetStatus(payload["status"]),
    )
    team_agent.url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}/run")
    return team_agent
