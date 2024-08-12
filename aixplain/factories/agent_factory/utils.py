__author__ = "thiagocastroferreira"

import aixplain.utils.config as config
from aixplain.enums import Function, Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.agent import Agent, ModelTool, PipelineTool
from typing import Dict, Text
from urllib.parse import urljoin


def build_agent(payload: Dict, api_key: Text = config.TEAM_API_KEY) -> Agent:
    """Instantiate a new agent in the platform."""
    tools = payload["assets"]
    for i, tool in enumerate(tools):
        if tool["type"] == "model":
            for supplier in Supplier:
                if tool["supplier"] is not None and tool["supplier"].lower() in [
                    supplier.value["code"].lower(),
                    supplier.value["name"].lower(),
                ]:
                    tool["supplier"] = supplier
                    break

            tool = ModelTool(
                function=Function(tool["function"]) if tool["function"] is not None else None,
                supplier=tool["supplier"],
                version=tool["version"],
                model=tool["assetId"],
            )
        elif tool["type"] == "pipeline":
            tool = PipelineTool(description=tool["description"], pipeline=tool["assetId"])
        else:
            raise Exception("Agent Creation Error: Tool type not supported.")
        tools[i] = tool

    agent = Agent(
        id=payload["id"],
        name=payload["name"] if "name" in payload else "",
        tools=tools,
        description=payload["description"] if "description" in payload else "",
        supplier=payload["teamId"] if "teamId" in payload else None,
        version=payload["version"] if "version" in payload else None,
        cost=payload["cost"] if "cost" in payload else None,
        llm_id=payload["llmId"] if "llmId" in payload else "6646261c6eb563165658bbb1",
        api_key=api_key,
        status=AssetStatus(payload["status"]),
    )
    agent.url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    return agent
