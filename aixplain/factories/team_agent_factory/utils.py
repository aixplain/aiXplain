__author__ = "lucaspavanelli"

import logging
from typing import Dict, Text, List
from urllib.parse import urljoin

import aixplain.utils.config as config
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.agent import Agent
from aixplain.modules.agent.agent_task import AgentTask
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.team_agent import TeamAgent, InspectorTarget
from typing import Dict, Text, List, Optional
from urllib.parse import urljoin


GPT_4o_ID = "6646261c6eb563165658bbb1"


def build_team_agent(payload: Dict, agents: List[Agent] = None, api_key: Text = config.TEAM_API_KEY) -> TeamAgent:
    """Instantiate a new team agent in the platform."""
    from aixplain.factories.agent_factory import AgentFactory

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

    inspector_targets = [InspectorTarget(target.lower()) for target in payload.get("inspectorTargets", [])]

    team_agent = TeamAgent(
        id=payload.get("id", ""),
        name=payload.get("name", ""),
        agents=payload_agents,
        description=payload.get("description", ""),
        supplier=payload.get("teamId", None),
        version=payload.get("version", None),
        cost=payload.get("cost", None),
        llm_id=payload.get("llmId", GPT_4o_ID),
        use_mentalist=True if payload.get("plannerId", None) is not None else False,
        use_inspector=True if payload.get("inspectorId", None) is not None else False,
        max_inspectors=payload.get("maxInspectors", 1),
        inspector_targets=inspector_targets,
        api_key=api_key,
        status=AssetStatus(payload["status"]),
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
                        raise Exception(f"Team Agent Creation Error: Task dependency not found - {dependency}")
    return team_agent


def parse_tool_from_yaml(tool: str) -> ModelTool:
    from aixplain.enums import Function

    if tool.strip() == "translation":
        return ModelTool(
            function=Function.TRANSLATION,
        )
    elif tool.strip() == "speech-recognition":
        return ModelTool(
            function=Function.SPEECH_RECOGNITION,
        )
    elif tool.strip() == "text-to-speech":
        return ModelTool(
            function=Function.SPEECH_SYNTHESIS,
        )
    elif tool.strip() == "serper_search":
        return ModelTool(model="65c51c556eb563350f6e1bb1")
    elif tool.strip() == "website_search":
        return ModelTool(model="6736411cf127849667606689")
    elif tool.strip() == "website_scrape":
        return ModelTool(model="6748e4746eb5633559668a15")
    elif tool.strip() == "website_crawl":
        return ModelTool(model="6748d4cff12784b6014324e2")
    else:
        raise Exception(f"Tool {tool} in yaml not found.")


def build_team_agent_from_yaml(yaml_code: str, llm_id: str, api_key: str, team_id: Optional[str] = None) -> TeamAgent:
    import yaml
    from aixplain.factories import AgentFactory, TeamAgentFactory

    team_config = yaml.safe_load(yaml_code)

    agents_data = team_config["agents"]
    tasks_data = team_config.get("tasks", [])
    system_data = team_config["system"] if "system" in team_config else {"query": "", "name": "Test Team"}
    team_name = system_data["name"]

    # Create agent mapping by name for easier task assignment
    agents_mapping = {}
    agent_objs = []

    # Parse agents
    for agent_entry in agents_data:
        for agent_name, agent_info in agent_entry.items():
            agent_role = agent_info["role"]
            agent_goal = agent_info["goal"]
            agent_backstory = agent_info["backstory"]

            description = f"You are an expert {agent_role}. {agent_backstory} Your primary goal is to {agent_goal}. Use your expertise to ensure the success of your tasks."
            agent_obj = Agent(
                id="",
                name=agent_name.replace("_", " "),
                description=description,
                instructions=description,
                tasks=[],  # Tasks will be assigned later
                tools=[parse_tool_from_yaml(tool) for tool in agent_info.get("tools", []) if tool != "language_model"],
                llmId=llm_id,
            )
            agents_mapping[agent_name] = agent_obj
            agent_objs.append(agent_obj)

    # Parse tasks and assign them to the corresponding agents
    for task in tasks_data:
        for task_name, task_info in task.items():
            description = task_info["description"]
            expected_output = task_info["expected_output"]
            dependencies = task_info.get("dependencies", [])
            agent_name = task_info["agent"]

            task_obj = AgentTask(
                name=task_name,
                description=description,
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
            description=agent.instructions,
            instructions=agent.instructions,
            tools=agent.tools,
            llm_id=llm_id,
            tasks=agent.tasks,
        )

    return TeamAgentFactory.create(
        name=team_name,
        agents=agent_objs,
        llm_id=llm_id,
        api_key=api_key,
        use_mentalist=True,
        use_inspector=False,
    )
