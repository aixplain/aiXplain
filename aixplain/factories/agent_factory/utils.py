__author__ = "thiagocastroferreira"

import logging
import aixplain.utils.config as config
from aixplain.enums import Function, Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.agent import Agent
from aixplain.modules.agent.tool import Tool
from aixplain.modules.agent.agent_task import AgentTask
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.modules.agent.tool.python_interpreter_tool import PythonInterpreterTool
from aixplain.modules.agent.tool.custom_python_code_tool import CustomPythonCodeTool
from aixplain.modules.agent.tool.sql_tool import SQLTool
from typing import Dict, Text, List
from urllib.parse import urljoin

GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_tool(tool: Dict):
    """Build a tool from a dictionary.

    Args:
        tool (Dict): Tool dictionary.

    Returns:
        Tool: Tool object.
    """
    if tool["type"] == "model":
        supplier = "aixplain"
        for supplier_ in Supplier:
            if isinstance(tool["supplier"], str):
                if tool["supplier"] is not None and tool["supplier"].lower() in [
                    supplier_.value["code"].lower(),
                    supplier_.value["name"].lower(),
                ]:
                    supplier = supplier_
                    break
        assert "function" in tool, "Function is required for model tools"
        function_name = tool.get("function")
        try:
            function = Function(function_name)
        except ValueError:
            valid_functions = [func.value for func in Function]
            raise ValueError(f"Function {function_name} is not a valid function. The valid functions are: {valid_functions}")
        tool = ModelTool(
            function=function,
            supplier=supplier,
            version=tool["version"],
            model=tool["assetId"],
            description=tool.get("description", ""),
            parameters=tool.get("parameters", None),
        )
    elif tool["type"] == "pipeline":
        tool = PipelineTool(description=tool["description"], pipeline=tool["assetId"])
    elif tool["type"] == "utility":
        if tool.get("utilityCode", None) is not None:
            tool = CustomPythonCodeTool(description=tool["description"], code=tool["utilityCode"])
        else:
            tool = PythonInterpreterTool()
    elif tool["type"] == "sql":
        parameters = {parameter["name"]: parameter["value"] for parameter in tool.get("parameters", [])}
        database = parameters.get("database")
        schema = parameters.get("schema")
        tables = parameters.get("tables", None)
        tables = tables.split(",") if tables is not None else None
        enable_commit = parameters.get("enable_commit", False)
        tool = SQLTool(
            description=tool["description"], database=database, schema=schema, tables=tables, enable_commit=enable_commit
        )
    else:
        raise ValueError("Agent Creation Error: Tool type not supported.")

    return tool


def build_agent(payload: Dict, tools: List[Tool] = None, api_key: Text = config.TEAM_API_KEY) -> Agent:
    """Instantiate a new agent in the platform."""
    tools_dict = payload["assets"]
    payload_tools = tools
    if payload_tools is None:
        payload_tools = []
        for tool in tools_dict:
            try:
                payload_tools.append(build_tool(tool))
            except (ValueError, AssertionError) as e:
                logging.warning(str(e))
                continue
            except Exception:
                logging.warning(
                    f"Tool {tool['assetId']} is not available. Make sure it exists or you have access to it. "
                    "If you think this is an error, please contact the administrators."
                )
                continue

    agent = Agent(
        id=payload["id"] if "id" in payload else "",
        name=payload.get("name", ""),
        tools=payload_tools,
        description=payload.get("description", ""),
        instructions=payload.get("role", ""),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        api_key=api_key,
        status=AssetStatus(payload["status"]),
        tasks=[
            AgentTask(
                name=task["name"],
                description=task["description"],
                expected_output=task.get("expectedOutput", None),
                dependencies=task.get("dependencies", []),
            )
            for task in payload.get("tasks", [])
        ],
    )
    agent.url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    return agent
