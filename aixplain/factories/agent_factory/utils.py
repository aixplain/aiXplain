__author__ = "thiagocastroferreira"

import logging
import aixplain.utils.config as config
from aixplain.utils.llm_utils import get_llm_instance
from aixplain.enums import Function, Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.llm_model import LLM
from aixplain.modules.agent import Agent
from aixplain.modules.agent.tool import Tool
from aixplain.modules.agent.agent_task import AgentTask
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.modules.agent.tool.python_interpreter_tool import PythonInterpreterTool
from aixplain.modules.agent.tool.custom_python_code_tool import CustomPythonCodeTool
from aixplain.modules.agent.tool.sql_tool import SQLTool
from aixplain.modules.model import Model
from aixplain.modules.model.connection import ConnectionTool
from typing import Dict, Text, List, Union
from urllib.parse import urljoin

GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_tool_payload(tool: Union[Tool, Model]):
    """Build a tool payload from a tool or model object.

    Args:
        tool (Union[Tool, Model]): The tool or model object to build the payload from.

    Returns:
        Dict: The tool payload.
    """
    if isinstance(tool, Tool):
        return tool.to_dict()
    else:
        parameters = None
        if isinstance(tool, ConnectionTool):
            parameters = tool.get_parameters()
        elif hasattr(tool, "get_parameters") and tool.get_parameters() is not None:
            parameters = tool.get_parameters().to_list()
        return {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "supplier": tool.supplier.value["code"] if isinstance(tool.supplier, Supplier) else tool.supplier,
            "parameters": parameters,
            "function": tool.function if hasattr(tool, "function") and tool.function is not None else None,
            "type": "model",
            "version": tool.version if hasattr(tool, "version") else None,
            "assetId": tool.id,
        }


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
        name = tool.get("name", "SQLTool")
        parameters = {parameter["name"]: parameter["value"] for parameter in tool.get("parameters", [])}
        database = parameters.get("database")
        schema = parameters.get("schema")
        tables = parameters.get("tables", None)
        tables = tables.split(",") if tables is not None else None
        enable_commit = parameters.get("enable_commit", False)
        tool = SQLTool(
            name=name,
            description=tool["description"],
            database=database,
            schema=schema,
            tables=tables,
            enable_commit=enable_commit,
        )
    else:
        raise ValueError("Agent Creation Error: Tool type not supported.")

    return tool


def build_llm(payload: Dict, api_key: Text = config.TEAM_API_KEY) -> LLM:
    """Build a LLM from a dictionary."""
    # Get LLM from tools if present
    llm = None
    # First check if we have the LLM object
    if "llm" in payload:
        llm = payload["llm"]
    # Otherwise create from the parameters
    elif "tools" in payload:
        for tool in payload["tools"]:
            if tool["type"] == "llm" and tool["description"] == "main":

                llm = get_llm_instance(payload["llmId"], api_key=api_key)
                # Set parameters from the tool
                if "parameters" in tool:
                    # Apply all parameters directly to the LLM properties
                    for param in tool["parameters"]:
                        param_name = param["name"]
                        param_value = param["value"]
                        # Apply any parameter that exists as an attribute on the LLM
                        if hasattr(llm, param_name):
                            setattr(llm, param_name, param_value)

                    # Also set model_params for completeness
                    # Convert parameters list to dictionary format expected by ModelParameters
                    params_dict = {}
                    for param in tool["parameters"]:
                        params_dict[param["name"]] = {"required": False, "value": param["value"]}
                    # Create ModelParameters and set it on the LLM
                    from aixplain.modules.model.model_parameters import ModelParameters

                    llm.model_params = ModelParameters(params_dict)
                break
    return llm


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

    llm = build_llm(payload, api_key)

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
        llm=llm,
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
