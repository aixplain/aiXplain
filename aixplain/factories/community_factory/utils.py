__author__ = "lucaspavanelli"

import aixplain.utils.config as config
from aixplain.enums.asset_status import AssetStatus
from aixplain.factories.agent_factory.utils import build_agent
from aixplain.modules.community import Community
from typing import Dict, Text
from urllib.parse import urljoin

GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_community(payload: Dict, api_key: Text = config.TEAM_API_KEY) -> Community:
    """Instantiate a new community in the platform."""
    agents = payload["agents"]
    for i, agent in enumerate(tools):
        agent = build_agent(agent, api_key)
        agents[i] = agent

    community = Community(
        id=payload["id"],
        name=payload["name"] if "name" in payload else "",
        agents=agents,
        description=payload["description"] if "description" in payload else "",
        supplier=payload["teamId"] if "teamId" in payload else None,
        version=payload["version"] if "version" in payload else None,
        cost=payload["cost"] if "cost" in payload else None,
        llm_id=payload["llmId"] if "llmId" in payload else GPT_4o_ID,
        api_key=api_key,
        status=AssetStatus(payload["status"]),
    )
    community.url = urljoin(config.BACKEND_URL, f"sdk/community/{community.id}/run")
    return community
