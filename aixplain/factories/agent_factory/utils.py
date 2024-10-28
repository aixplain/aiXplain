__author__ = "thiagocastroferreira"

import aixplain.utils.config as config
from aixplain.enums import Function, Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.agent import Agent, ModelTool, PipelineTool
from typing import Dict, Text
from urllib.parse import urljoin

GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_agent(payload: Dict, api_key: Text = config.TEAM_API_KEY) -> Agent:
    """Instantiate a new agent in the platform."""
    tools_dict = payload["assets"]
    tools = []
    for i, tool in enumerate(tools_dict):
        if tool["type"] == "model":
            for supplier in Supplier:
                if tool["supplier"] is not None and tool["supplier"].lower() in [
                    supplier.value["code"].lower(),
                    supplier.value["name"].lower(),
                ]:
                    tool["supplier"] = supplier
                    break

            tool = ModelTool(
                function=Function(tool.get("function", None)),
                supplier=tool["supplier"],
                version=tool["version"],
                model=tool["assetId"],
            )
        elif tool["type"] == "pipeline":
            tool = PipelineTool(description=tool["description"], pipeline=tool["assetId"])
        else:
            raise Exception("Agent Creation Error: Tool type not supported.")
        tools.append(tool)

    agent = Agent(
        id=payload["id"] if "id" in payload else "",
        name=payload.get("name", ""),
        tools=tools,
        description=payload.get("description", ""),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        api_key=api_key,
        status=AssetStatus(payload["status"]),
    )
    agent.url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    return agent
