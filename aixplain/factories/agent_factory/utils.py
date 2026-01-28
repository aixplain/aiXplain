"""Utils for building tools and agents."""

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
from aixplain.modules.agent.tool.sql_tool import SQLTool
from aixplain.modules.agent.output_format import OutputFormat
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
        actions = None
        if isinstance(tool, ConnectionTool):
            parameters = tool.get_parameters()
            # Extract action codes from action_scope if it's set
            if tool.action_scope is not None and len(tool.action_scope) > 0:
                actions = [action.code for action in tool.action_scope]
        elif hasattr(tool, "get_parameters") and tool.get_parameters() is not None:
            parameters = tool.get_parameters().to_list()
        payload = {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "supplier": (tool.supplier.value["code"] if isinstance(tool.supplier, Supplier) else tool.supplier),
            "parameters": parameters,
            "function": (tool.function if hasattr(tool, "function") and tool.function is not None else None),
            "type": "model",
            "version": tool.version if hasattr(tool, "version") else None,
            "assetId": tool.id,
        }
        # Add actions field if it exists
        if actions is not None:
            payload["actions"] = actions
        return payload

def build_tool(tool: Dict):
    """Build a tool from a dictionary.

    Args:
        tool (Dict): Tool dictionary.

    Returns:
        Tool: Tool object.
    """
    tool_type = (tool.get("type") or "").lower() 

    if tool_type == "model":
        supplier_val = tool.get("supplier", "aixplain") 
        supplier = "aixplain"
        for supplier_ in Supplier:
            if isinstance(supplier_val, str): 
                if supplier_val is not None and supplier_val.lower() in [ 
                    supplier_.value["code"].lower(),
                    supplier_.value["name"].lower(),
                ]:
                    supplier = supplier_
                    break

        function = None 
        function_name = tool.get("function", None) 
        if function_name is not None: 
            try:
                function = Function(function_name)
            except ValueError:
                valid_functions = [func.value for func in Function]
                raise ValueError(
                    f"Function {function_name} is not a valid function. The valid functions are: {valid_functions}"
                )

        version = tool.get("version", None) 

        params = tool.get("parameters", [])
        if params is None: 
            params = []

        tool = ModelTool(
            function=function,
            supplier=supplier,
            version=version,
            model=tool["assetId"],
            description=tool.get("description", ""),
            parameters=params,
        )

    elif tool_type == "pipeline":
        tool = PipelineTool(description=tool["description"], pipeline=tool["assetId"])

    elif tool_type == "utility":
        tool = PythonInterpreterTool()

    elif tool_type == "sql":
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
    """Build a Large Language Model (LLM) instance from a dictionary configuration.

    This function attempts to create an LLM instance either from a cached LLM object
    in the payload or by creating a new instance using the provided configuration.

    Args:
        payload (Dict): Dictionary containing LLM configuration and possibly a cached
            LLM object.
        api_key (Text, optional): API key for authentication. Defaults to config.TEAM_API_KEY.

    Returns:
        LLM: Instantiated LLM object with configured parameters.
    """
    # Get LLM from tools if present
    llm = None
    # First check if we have the LLM object
    if "llm" in payload:
        llm = payload["llm"]
    # Otherwise create from the parameters
    elif "tools" in payload:
        for tool in payload["tools"]:
            if tool["type"] == "llm" and tool["description"] == "main":
                llm = get_llm_instance(payload["llmId"], api_key=api_key, use_cache=True)
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
                        params_dict[param["name"]] = {
                            "required": False,
                            "value": param["value"],
                        }
                    # Create ModelParameters and set it on the LLM
                    from aixplain.modules.model.model_parameters import ModelParameters

                    llm.model_params = ModelParameters(params_dict)
                break
    return llm


def build_agent(payload: Dict, tools: List[Tool] = None, api_key: Text = config.TEAM_API_KEY) -> Agent:
    """Build an agent instance from a dictionary configuration.

    This function creates an agent with its associated tools, LLM, and tasks based
    on the provided configuration.

    Args:
        payload (Dict): Dictionary containing agent configuration including tools,
            LLM settings, and tasks.
        tools (List[Tool], optional): List of pre-configured tools to use. If None,
            tools will be built from the payload. Defaults to None.
        api_key (Text, optional): API key for authentication. Defaults to config.TEAM_API_KEY.

    Returns:
        Agent: Instantiated agent object with configured tools, LLM, and tasks.

    Raises:
        ValueError: If a tool type is not supported.
        AssertionError: If tool configuration is invalid.
    """
    import logging
    logging.info('build agent')
    logging.info(payload)
    tools_dict = payload["assets"]
    logging.info("tools dicts")
    logging.info(tools_dict)
    payload_tools = tools
    if payload_tools is None:
        payload_tools = []
        # Use parallel tool building with ThreadPoolExecutor for better performance
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def build_tool_safe(tool_data):
            """Build a single tool with error handling."""
            try:
                return build_tool(tool_data)
            except (ValueError, AssertionError) as e:
                logging.warning(str(e))
                return None
            except Exception:
                logging.warning(
                    f"Tool {tool_data['assetId']} is not available. Make sure it exists or you have access to it. "
                    "If you think this is an error, please contact the administrators."
                )
                return None

        # Build all tools in parallel (only if there are tools to build)
        if len(tools_dict) > 0:
            with ThreadPoolExecutor(max_workers=min(len(tools_dict), 10)) as executor:
                # Submit all tool build tasks
                future_to_tool = {executor.submit(build_tool_safe, tool): tool for tool in tools_dict}

                # Collect results as they complete
                for future in as_completed(future_to_tool):
                    tool_result = future.result()
                    if tool_result is not None:
                        payload_tools.append(tool_result)
            logging.info("payload tools")
            logging.info(payload_tools)

    llm = build_llm(payload, api_key)

    agent = Agent(
        id=payload["id"] if "id" in payload else "",
        name=payload.get("name", ""),
        tools=payload_tools,
        description=payload.get("description", ""),
        instructions=payload.get("instructions"),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        llm=llm,
        api_key=api_key,
        status=AssetStatus(payload["status"]),
        output_format=OutputFormat(payload.get("outputFormat", OutputFormat.TEXT)),
        expected_output=payload.get("expectedOutput", None),
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
