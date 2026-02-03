"""
Utility functions for safely deleting agents and team agents in tests.

This module provides helper functions that delete agents by ID without
building full objects, avoiding issues with missing model dependencies.
"""
import os
from typing import List, Dict, Any
from aixplain.utils import config
from aixplain.utils.request_utils import _request_with_retry
from urllib.parse import urljoin


def get_team_agent_ids() -> List[str]:
    """
    Get list of team agent IDs without building full objects.
    
    Returns:
        List[str]: List of team agent IDs, empty list if error occurs
    """
    try:
        url = urljoin(config.BACKEND_URL, "sdk/agent-communities")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        
        if 200 <= r.status_code < 300:
            team_agents_data = r.json()
            return [ta.get('id') for ta in team_agents_data if ta.get('id')]
        else:
            print(f"Warning: Failed to list team agents: HTTP {r.status_code}")
            return []
    except Exception as e:
        print(f"Warning: Failed to list team agents: {e}")
        return []


def get_agent_ids() -> List[str]:
    """
    Get list of agent IDs without building full objects.
    
    Returns:
        List[str]: List of agent IDs, empty list if error occurs
    """
    try:
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        r = _request_with_retry("get", url, headers=headers)
        
        if 200 <= r.status_code < 300:
            agents_data = r.json()
            return [agent.get('id') for agent in agents_data if agent.get('id')]
        else:
            print(f"Warning: Failed to list agents: HTTP {r.status_code}")
            return []
    except Exception as e:
        print(f"Warning: Failed to list agents: {e}")
        return []


def delete_team_agent_by_id(team_agent_id: str) -> bool:
    """
    Delete a team agent by ID.
    
    Args:
        team_agent_id: The ID of the team agent to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent_id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        r = _request_with_retry("delete", url, headers=headers)
        
        if r.status_code == 200:
            return True
        else:
            print(f"Warning: Failed to delete team agent {team_agent_id}: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"Warning: Failed to delete team agent {team_agent_id}: {e}")
        return False


def delete_agent_by_id(agent_id: str) -> bool:
    """
    Delete an agent by ID.
    
    Args:
        agent_id: The ID of the agent to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent_id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        r = _request_with_retry("delete", url, headers=headers)
        
        if r.status_code == 200:
            return True
        else:
            print(f"Warning: Failed to delete agent {agent_id}: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"Warning: Failed to delete agent {agent_id}: {e}")
        return False


BACKEND_URL = os.environ.get("BACKEND_URL", "")

def get_env_from_backend_url(url: str) -> str:
    url = url.lower()
    if "dev" in url:
        return "dev"
    if "test" in url:
        return "test"
    return "prod"


ENV = get_env_from_backend_url(BACKEND_URL)


def safe_delete_all_agents_and_team_agents():
    """
    Safely delete all agents and team agents.
    
    This function deletes team agents first (since agents might be used by team agents),
    then deletes individual agents. It handles errors gracefully and continues
    processing even if some deletions fail.
    """
    if ENV not in {"dev", "test"}:
        raise RuntimeError(
            f"Refusing to delete agents in ENV='{ENV}'. "
            f"BACKEND_URL='{BACKEND_URL}'"
        )
    # Delete team agents first
    team_agent_ids = get_team_agent_ids()
    for team_agent_id in team_agent_ids:
        delete_team_agent_by_id(team_agent_id)
    # Delete agents
    agent_ids = get_agent_ids()
    for agent_id in agent_ids:
        delete_agent_by_id(agent_id)
