import os
import json
import logging
from datetime import datetime
from enum import Enum
from urllib.parse import urljoin
from typing import Dict, Optional, List, Tuple, Union, Text
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from aixplain.utils.cache_utils import save_to_cache, load_from_cache, CACHE_FOLDER
from aixplain.enums import Supplier
from aixplain.modules.agent.tool import Tool  

AGENT_CACHE_FILE = f"{CACHE_FOLDER}/agents.json"
LOCK_FILE = f"{AGENT_CACHE_FILE}.lock"  

def load_agents(cache_expiry: Optional[int] = None) -> Tuple[Enum, Dict]:
    """
    Load AI agents from cache or fetch from backend if not cached.
    Only agents with status "onboarded" should be cached.

    Args:
        cache_expiry (int, optional): Expiry time in seconds. Default is 24 hours.

    Returns:
        Tuple[Enum, Dict]: (Enum of agent IDs, Dictionary with agent details)
    """
    if cache_expiry is None:
        cache_expiry = 86400 

    os.makedirs(CACHE_FOLDER, exist_ok=True)

    cached_data = load_from_cache(AGENT_CACHE_FILE, LOCK_FILE)

    if cached_data is not None:
        return parse_agents(cached_data)

    api_key = config.TEAM_API_KEY
    backend_url = config.BACKEND_URL
    url = urljoin(backend_url, "sdk/agents")
    headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    try:
        response = _request_with_retry("get", url, headers=headers)
        response.raise_for_status() 
        agents_data = response.json()
    except Exception as e:
        logging.error(f"Failed to fetch agents from API: {e}")
        return Enum("Agent", {}), {}  


    onboarded_agents = [agent for agent in agents_data if agent.get("status", "").lower() == "onboarded"]

    save_to_cache(AGENT_CACHE_FILE, {"items": onboarded_agents}, LOCK_FILE)

    return parse_agents({"items": onboarded_agents})


def parse_agents(agents_data: Dict) -> Tuple[Enum, Dict]:
    """
    Convert agent data into an Enum and dictionary format for easy use.

    Args:
        agents_data (Dict): JSON response with agents list.

    Returns:
        - agents_enum: Enum with agent IDs.
        - agents_details: Dictionary containing all agent parameters.
    """
    if not agents_data["items"]: 
        logging.warning("No onboarded agents found.")
        return Enum("Agent", {}), {}

    agents_enum = Enum(
        "Agent",
        {a["id"].upper().replace("-", "_"): a["id"] for a in agents_data["items"]},
        type=str,
    )

    agents_details = {
        agent["id"]: {
            "id": agent["id"],
            "name": agent.get("name", ""),
            "description": agent.get("description", ""),
            "role": agent.get("role", ""),
            "tools": [Tool(t) if isinstance(t, dict) else t for t in agent.get("tools", [])],
            "llm_id": agent.get("llm_id", "6646261c6eb563165658bbb1"),
            "supplier": agent.get("supplier", "aiXplain"),
            "version": agent.get("version", "1.0"),
            "status": agent.get("status", "onboarded"),
            "created_at": agent.get("created_at", ""),
            "tasks": agent.get("tasks", []),
            **agent, 
        }
        for agent in agents_data["items"]
    }

    return agents_enum, agents_details


Agent, AgentDetails = load_agents()
