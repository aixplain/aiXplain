__author__ = "thiagocastroferreira"

from aixplain.enums.function import Function
from aixplain.modules.agent import Agent, Tool
from typing import Dict


def build_agent(payload: Dict) -> Agent:
    """Instantiate a new agent in the platform."""
    tools = payload["tools"]
    for i, tool in enumerate(tools):
        try:
            function = Function(tool)
        except Exception:
            function = tool

        tools[i] = Tool(name=tool, description=tool, function=function, supplier=None)

    agent = Agent(
        id=payload["id"],
        name=payload["name"] if "name" in payload else "",
        tools=tools,
        description=payload["description"] if "description" in payload else "",
        supplier=payload["supplier"] if "supplier" in payload else None,
        version=payload["version"] if "version" in payload else None,
        cost=payload["cost"] if "cost" in payload else None,
    )
    agent.url = "http://54.86.247.242:8000/execute"
    return agent
