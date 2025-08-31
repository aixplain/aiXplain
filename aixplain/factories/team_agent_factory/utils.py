__author__ = "lucaspavanelli"

import logging
from typing import Dict, Text, List, Optional
from urllib.parse import urljoin

import aixplain.utils.config as config
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.agent import Agent
from aixplain.modules.agent.agent_task import AgentTask
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.team_agent import TeamAgent, InspectorTarget
from aixplain.modules.team_agent.inspector import Inspector
from aixplain.factories.agent_factory import AgentFactory
from aixplain.factories.model_factory import ModelFactory
from aixplain.modules.model.model_parameters import ModelParameters
from aixplain.modules.agent.output_format import OutputFormat

GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_team_agent(payload: Dict, agents: List[Agent] = None, api_key: Text = config.TEAM_API_KEY) -> TeamAgent:
    """Build a TeamAgent instance from configuration payload.

    This function creates a TeamAgent instance from a configuration payload,
    handling the setup of agents, LLMs, inspectors, and task dependencies.

    Args:
        payload (Dict): Configuration dictionary containing:
            - id: Optional team agent ID
            - name: Team agent name
            - agents: List of agent configurations
            - description: Optional description
            - instructions: Optional instructions
            - teamId: Optional supplier information
            - version: Optional version
            - cost: Optional cost information
            - llmId: LLM model ID (defaults to GPT-4)
            - plannerId: Optional planner model ID
            - inspectors: Optional list of inspector configurations
            - inspectorTargets: Optional list of inspection targets
            - status: Team agent status
            - tools: Optional list of tool configurations
        agents (List[Agent], optional): Pre-instantiated agent objects. If not
            provided, agents will be instantiated from IDs in the payload.
            Defaults to None.
        api_key (Text, optional): API key for authentication. Defaults to
            config.TEAM_API_KEY.

    Returns:
        TeamAgent: Configured team agent instance with all components initialized.

    Raises:
        Exception: If a task dependency referenced in an agent's configuration
            cannot be found.
    """
    agents_dict = payload["agents"]
    payload_agents = agents
    if payload_agents is None:
        payload_agents = []
        for i, agent in enumerate(agents_dict):
            try:
                payload_agents.append(AgentFactory.get(agent["assetId"]))
            except Exception:
                logging.warning(
                    f"Agent {agent['assetId']} not found. Make sure it exists or you have access to it. "
                    "If you think this is an error, please contact the administrators."
                )
                continue

    # Ensure custom classes are instantiated: for compatibility with backend return format
    inspectors = []
    for inspector_data in payload.get("inspectors", []):
        try:
            if isinstance(inspector_data, Inspector):
                inspectors.append(inspector_data)
            else:
                # Handle both old format and new format with policy_type
                if hasattr(Inspector, "model_validate"):
                    inspectors.append(Inspector.model_validate(inspector_data))
                else:
                    inspectors.append(Inspector(**inspector_data))
        except Exception as e:
            logging.warning(f"Failed to create inspector from data: {e}")
            continue

    inspector_targets = [InspectorTarget(target.lower()) for target in payload.get("inspectorTargets", [])]

    # Get LLMs from tools if present
    supervisor_llm = None
    mentalist_llm = None

    # First check if we have direct LLM objects in the payload
    if "supervisor_llm" in payload:
        supervisor_llm = payload["supervisor_llm"]
    if "mentalist_llm" in payload:
        mentalist_llm = payload["mentalist_llm"]
    # Otherwise create from the parameters
    elif "tools" in payload:
        for tool in payload["tools"]:
            if tool["type"] == "llm":
                llm = ModelFactory.get(payload["llmId"], api_key=api_key)
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
                    llm.model_params = ModelParameters(params_dict)

                # Assign LLM based on description
                if tool["description"] == "supervisor":
                    supervisor_llm = llm
                elif tool["description"] == "mentalist":
                    mentalist_llm = llm

    team_agent = TeamAgent(
        id=payload.get("id", ""),
        name=payload.get("name", ""),
        agents=payload_agents,
        description=payload.get("description", ""),
        instructions=payload.get("instructions", None),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        supervisor_llm=supervisor_llm,
        mentalist_llm=mentalist_llm,
        use_mentalist=True if payload.get("plannerId", None) is not None else False,
        inspectors=inspectors,
        inspector_targets=inspector_targets,
        api_key=api_key,
        status=AssetStatus(payload["status"]),
        output_format=OutputFormat(payload.get("outputFormat", OutputFormat.TEXT)),
        expected_output=payload.get("expectedOutput", None),
    )
    team_agent.url = urljoin(config.BACKEND_URL, f"sdk/agent-communities/{team_agent.id}/run")

    # fill up dependencies
    all_tasks = {}
    for agent in team_agent.agents:
        for task in agent.tasks:
            all_tasks[task.name] = task

    for idx, agent in enumerate(team_agent.agents):
        for i, task in enumerate(agent.tasks):
            for j, dependency in enumerate(task.dependencies or []):
                if isinstance(dependency, Text):
                    task_dependency = all_tasks.get(dependency, None)
                    if task_dependency:
                        team_agent.agents[idx].tasks[i].dependencies[j] = task_dependency
                    else:
                        team_agent.agents[idx].tasks[i].dependencies[j] = None

    return team_agent


def parse_tool_from_yaml(tool: str) -> ModelTool:
    from aixplain.enums import Function

    tool_name = tool.strip()
    if tool_name == "translation":
        return ModelTool(
            function=Function.TRANSLATION,
        )
    elif tool_name == "speech-recognition":
        return ModelTool(
            function=Function.SPEECH_RECOGNITION,
        )
    elif tool_name == "text-to-speech":
        return ModelTool(
            function=Function.SPEECH_SYNTHESIS,
        )
    elif tool_name == "llm":
        return ModelTool(function=Function.TEXT_GENERATION)
    elif tool_name == "serper_search":
        return ModelTool(model="65c51c556eb563350f6e1bb1")
    elif tool.strip() == "website_search":
        return ModelTool(model="6736411cf127849667606689")
    elif tool.strip() == "website_scrape":
        return ModelTool(model="6748e4746eb5633559668a15")
    elif tool.strip() == "website_crawl":
        return ModelTool(model="6748d4cff12784b6014324e2")
    else:
        raise Exception(f"Tool {tool} in yaml not found.")


import yaml


def is_yaml_formatted(text):
    """
    Check if a string is valid YAML format with additional validation.

    Args:
        text (str): The string to check

    Returns:
        bool: True if valid YAML, False otherwise
    """
    if not text or not isinstance(text, str):
        return False

    # Strip whitespace
    text = text.strip()

    # Empty string is valid YAML
    if not text:
        return True

    try:
        parsed = yaml.safe_load(text)

        # If it's just a plain string without YAML structure,
        # we might want to consider it as non-YAML
        # This is optional depending on your requirements
        if isinstance(parsed, str) and "\n" not in text and ":" not in text:
            return False

        return True
    except yaml.YAMLError:
        return False


def build_team_agent_from_yaml(yaml_code: str, llm_id: str, api_key: str, team_id: Optional[str] = None) -> TeamAgent:
    import yaml
    from aixplain.factories import AgentFactory, TeamAgentFactory

    # check if it is a yaml or just as string
    if not is_yaml_formatted(yaml_code):
        return None
    team_config = yaml.safe_load(yaml_code)

    agents_data = team_config.get("agents", [])
    tasks_data = team_config.get("tasks", [])
    system_data = team_config.get("system", {"query": "", "name": "Test Team"})
    team_name = system_data.get("name", "")
    team_description = system_data.get("description", "")
    team_instructions = system_data.get("instructions", "")
    llm = ModelFactory.get(llm_id)
    # Create agent mapping by name for easier task assignment
    agents_mapping = {}
    agent_objs = []

    # Parse agents
    for agent_entry in agents_data:
        agent_name = list(agent_entry.keys())[0]
        agent_info = agent_entry[agent_name]
        agent_instructions = agent_info.get("instructions", "")
        agent_description = agent_info["description"]
        agent_name = agent_name.replace("_", " ")
        agent_name = f"{agent_name} agent" if not agent_name.endswith(" agent") else agent_name
        agent_obj = Agent(
            id="",
            name=agent_name,
            description=agent_description,
            instructions=agent_instructions,
            tasks=[],  # Tasks will be assigned later
            tools=[parse_tool_from_yaml(tool) for tool in agent_info.get("tools", []) if tool != "language_model"],
            llm=llm,
        )
        agents_mapping[agent_name] = agent_obj
        agent_objs.append(agent_obj)

    # Parse tasks and assign them to the corresponding agents
    for task in tasks_data:
        for task_name, task_info in task.items():
            task_description = task_info.get("description", "")
            expected_output = task_info.get("expected_output", "")
            dependencies = task_info.get("dependencies", [])
            agent_name = task_info.get("agent", "")
            agent_name = agent_name.replace("_", " ")
            agent_name = f"{agent_name} agent" if not agent_name.endswith(" agent") else agent_name

            task_obj = AgentTask(
                name=task_name,
                description=task_description,
                expected_output=expected_output,
                dependencies=dependencies,
            )

            # Assign the task to the corresponding agent
            if agent_name in agents_mapping:
                agent = agents_mapping[agent_name]
                agent.tasks.append(task_obj)
            else:
                raise Exception(f"Agent '{agent_name}' referenced in tasks not found.")

    for i, agent in enumerate(agent_objs):
        agent_objs[i] = AgentFactory.create(
            name=agent.name,
            description=agent.description,
            instructions=agent.instructions,
            tools=agent.tools,
            llm=llm,
            tasks=agent.tasks,
        )
    return TeamAgentFactory.create(
        name=team_name,
        description=team_description,
        instructions=team_instructions,
        agents=agent_objs,
        llm=llm,
        api_key=api_key,
        use_mentalist=True,
        inspectors=[],
    )
