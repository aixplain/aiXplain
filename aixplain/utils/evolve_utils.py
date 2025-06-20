import yaml
from typing import Union
from aixplain.enums import Function, Supplier
from aixplain.modules.agent import Agent
from aixplain.modules.team_agent import TeamAgent
from aixplain.factories import AgentFactory, TeamAgentFactory


def parse_tools(tools: list) -> list:
    obj_tools = []
    for tool in tools:
        if tool.strip() == "translation":
            obj_tools.append(
                AgentFactory.create_model_tool(
                    function=Function.TRANSLATION,
                    supplier=Supplier.GOOGLE,
                )
            )
        elif tool.strip() == "speech-recognition":
            obj_tools.append(
                AgentFactory.create_model_tool(
                    function=Function.SPEECH_RECOGNITION,
                    supplier=Supplier.GOOGLE,
                )
            )
        elif tool.strip() == "text-to-speech":
            obj_tools.append(
                AgentFactory.create_model_tool(
                    function=Function.SPEECH_SYNTHESIS,
                    supplier=Supplier.GOOGLE,
                )
            )
        elif tool.strip() == "serper_search":
            obj_tools.append(AgentFactory.create_model_tool(model="65c51c556eb563350f6e1bb1"))
        elif tool.strip() == "website_search":
            obj_tools.append(AgentFactory.create_model_tool(model="6736411cf127849667606689"))
        elif tool.strip() == "website_scrape":
            obj_tools.append(AgentFactory.create_model_tool(model="6748e4746eb5633559668a15"))
        else:
            continue
    return obj_tools


def from_yaml(
    yaml_code: str,
    llm_id: str,
) -> Union[TeamAgent, Agent]:
    team_config = yaml.safe_load(yaml_code)

    agents_data = team_config["agents"]
    tasks_data = team_config.get("tasks", [])
    system_data = team_config["system"] if "system" in team_config else {"query": ""}
    expected_output = system_data.get("expected_output")
    team_name = system_data.get("name")
    team_description = system_data.get("description", "")
    team_instructions = system_data.get("instructions", "")

    # Create agent mapping by name for easier task assignment
    agents_mapping = {}
    agent_objs = []

    # Parse agents
    for agent_entry in agents_data:
        # Handle different YAML structures
        if isinstance(agent_entry, dict):
            # Case 1: Standard structure - {agent_name: {role: ..., goal: ..., backstory: ...}}
            for agent_name, agent_info in agent_entry.items():
                # Check if agent_info is a list (malformed YAML structure)
                if isinstance(agent_info, list):
                    # Handle malformed structure where agent_info is a list
                    # This happens when YAML has unquoted keys that create nested structures
                    continue
                elif isinstance(agent_info, dict):
                    agent_role = agent_info["role"]
                    agent_goal = agent_info["goal"]
                    agent_backstory = agent_info["backstory"]

                    description = f"## ROLE\n{agent_role}\n\n## GOAL\n{agent_goal}\n\n## BACKSTORY\n{agent_backstory}"
                    agent_obj = AgentFactory.create(
                        name=agent_name.replace("_", " "),
                        description=description,
                        tasks=[],  # Tasks will be assigned later
                        tools=parse_tools(agent_info.get("tools", [])),
                        llm_id=llm_id,
                    )
                    agents_mapping[agent_name] = agent_obj
                    agent_objs.append(agent_obj)
        elif isinstance(agent_entry, list):
            # Case 2: Handle list structure (alternative YAML format)
            for item in agent_entry:
                if isinstance(item, dict):
                    for agent_name, agent_info in item.items():
                        if isinstance(agent_info, dict):
                            agent_role = agent_info["role"]
                            agent_goal = agent_info["goal"]
                            agent_backstory = agent_info["backstory"]

                            description = f"## ROLE\n{agent_role}\n\n## GOAL\n{agent_goal}\n\n## BACKSTORY\n{agent_backstory}"
                            agent_tools = parse_tools(agent_info.get("tools", []))
                            agent_obj = AgentFactory.create(
                                name=agent_name.replace("_", " "),
                                description=description,
                                tools=agent_tools,
                                tasks=[],
                                llm_id=llm_id,
                            )
                            agents_mapping[agent_name] = agent_obj
                            agent_objs.append(agent_obj)

    # Parse tasks and assign them to the corresponding agents
    for task_entry in tasks_data:
        # Handle different YAML structures for tasks
        if isinstance(task_entry, dict):
            # Case 1: Standard structure - {task_name: {description: ..., expected_output: ..., agent: ...}}
            for task_name, task_info in task_entry.items():
                # Check if task_info is a list (malformed YAML structure)
                if isinstance(task_info, list):
                    # Handle malformed structure where task_info is a list
                    continue
                elif isinstance(task_info, dict):
                    description = task_info["description"]
                    expected_output = task_info["expected_output"]
                    dependencies = task_info.get("dependencies", [])
                    agent_name = task_info["agent"]
                    task_obj = AgentFactory.create_task(
                        name=task_name.replace("_", " "),
                        description=description,
                        expected_output=expected_output,
                        dependencies=dependencies,
                    )

                    # Assign the task to the corresponding agent
                    if agent_name in agents_mapping:
                        agent = agents_mapping[agent_name]
                        agent.tasks.append(task_obj)
                    else:
                        raise ValueError(f"Agent '{agent_name}' referenced in tasks not found.")
        elif isinstance(task_entry, list):
            # Case 2: Handle list structure (alternative YAML format)
            for item in task_entry:
                if isinstance(item, dict):
                    for task_name, task_info in item.items():
                        if isinstance(task_info, dict):
                            description = task_info["description"]
                            expected_output = task_info["expected_output"]
                            dependencies = task_info.get("dependencies", [])
                            agent_name = task_info["agent"]

                            task_obj = AgentFactory.create_task(
                                name=task_name.replace("_", " "),
                                description=description,
                                expected_output=expected_output,
                                dependencies=dependencies,
                            )

                            # Assign the task to the corresponding agent
                            if agent_name in agents_mapping:
                                agent = agents_mapping[agent_name]
                                agent.tasks.append(task_obj)
                            else:
                                raise ValueError(f"Agent '{agent_name}' referenced in tasks not found.")

    team = TeamAgentFactory.create(
        name=team_name,
        description=team_description,
        instructions=team_instructions,
        agents=agent_objs,
        llm_id=llm_id,
        use_mentalist=True,
        inspectors=[],
    )
    return team
