__author__ = "thiagocastroferreira"

from aixplain.modules.agent import Agent, ModelTool, PipelineTool
from typing import Dict


def build_agent(payload: Dict) -> Agent:
    """Instantiate a new agent in the platform."""
    tools = payload["tools"]
    for i, tool in enumerate(tools):
        if "function" in tool:
            tool = ModelTool(**tool)
        elif "id" in tool:
            tool = PipelineTool(name=tool["name"], description=tool["description"], pipeline=tool["id"])
        else:
            raise Exception("Agent Creation Error: Tool type not supported.")
        tools[i] = tool

    agent = Agent(
        id=payload["id"],
        name=payload["name"] if "name" in payload else "",
        tools=tools,
        description=payload["description"] if "description" in payload else "",
        supplier=payload["supplier"] if "supplier" in payload else None,
        version=payload["version"] if "version" in payload else None,
        cost=payload["cost"] if "cost" in payload else None,
        llm_id=payload["language_model_id"] if "language_model_id" in payload else None,
        api_key=payload["api_key"],
    )
    agent.url = "http://54.86.247.242:8000/async-execute"
    return agent
