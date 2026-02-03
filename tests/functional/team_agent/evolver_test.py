"""Tests for team agent evolver functionality."""

import pytest
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from aixplain.enums import ResponseStatus
from aixplain.factories.agent_factory import AgentFactory
from aixplain.factories.team_agent_factory import TeamAgentFactory
import time
import uuid


team_dict = {
    "team_agent_name": "Test Text Speech Team",
    "llm_id": "6646261c6eb563165658bbb1",
    "llm_name": "GPT4o",
    "query": "Translate this text into Portuguese: 'This is a test'. Translate to pt and synthesize in audio",
    "description": "You are a text translation and speech synthesizing agent. You will be provided a text in the source language and expected to translate and synthesize in the target language.",
    "agents": [
        {
            "agent_name": "Text Translation agent",
            "llm_id": "6646261c6eb563165658bbb1",
            "llm_name": "GPT4o",
            "description": "Text Translator",
            "instructions": "You are a text translation agent. You will be provided a text in the source language and expected to translate in the target language.",
            "tasks": [
                {
                    "name": "Text translation",
                    "description": "Translate a text from source language (English) to target language (Portuguese)",
                    "expected_output": "target language text",
                }
            ],
            "model_tools": [{"function": "translation", "supplier": "AWS"}],
        },
        {
            "agent_name": "Test Speech Synthesis agent",
            "llm_id": "6646261c6eb563165658bbb1",
            "llm_name": "GPT4o",
            "description": "Speech Synthesizer",
            "instructions": "You are a speech synthesizing agent. You will be provided a text to synthesize into audio and return the audio link.",
            "tasks": [
                {
                    "name": "Speech synthesis",
                    "description": "Synthesize a text from text to speech",
                    "expected_output": "audio link of the synthesized text",
                    "dependencies": ["Text translation"],
                }
            ],
            "model_tools": [{"function": "speech_synthesis", "supplier": "Google"}],
        },
    ],
}


def parse_tools(tools_info):
    """Parse tool information into AgentFactory model tools."""
    tools = []
    for tool in tools_info:
        function_enum = Function[tool["function"].upper().replace(" ", "_")]
        supplier_enum = Supplier[tool["supplier"].upper().replace(" ", "_")]
        tools.append(AgentFactory.create_model_tool(function=function_enum, supplier=supplier_enum))
    return tools


def build_team_agent_from_json(team_config: dict):
    """Build a team agent from JSON configuration."""
    agents_data = team_config["agents"]
    tasks_data = team_config.get("tasks", [])

    agent_objs = []
    for agent_entry in agents_data:
        agent_name = agent_entry["agent_name"]
        agent_description = agent_entry["description"]
        agent_instructions = agent_entry["instructions"]
        agent_llm_id = agent_entry.get("llm_id", None)

        agent_tasks = []
        for task in tasks_data:
            task_name = task.get("task_name", "")
            task_info = task

            if agent_name == task_info["agent"]:
                task_obj = AgentFactory.create_task(
                    name=task_name.replace("_", " "),
                    description=task_info.get("description", ""),
                    expected_output=task_info.get("expected_output", ""),
                    dependencies=[t.replace("_", " ") for t in task_info.get("dependencies", [])],
                )
                agent_tasks.append(task_obj)

        if "model_tools" in agent_entry:
            agent_tools = parse_tools(agent_entry["model_tools"])
        else:
            agent_tools = []

        agent_obj = AgentFactory.create(
            name=agent_name.replace("_", " "),
            description=agent_description,
            instructions=agent_instructions,
            tools=agent_tools,
            workflow_tasks=agent_tasks,
            llm_id=agent_llm_id,
        )
        agent_objs.append(agent_obj)

    return TeamAgentFactory.create(
        name=team_config["team_agent_name"],
        agents=agent_objs,
        description=team_config["description"],
        llm_id=team_config.get("llm_id", None),
        use_mentalist=True,
    )


@pytest.fixture(scope="function")
def delete_agents_and_team_agents():
    """Fixture to clean up agents and team agents before and after tests."""
    from tests.test_deletion_utils import safe_delete_all_agents_and_team_agents

    # Clean up before test
    safe_delete_all_agents_and_team_agents()

    yield True

    # Clean up after test
    safe_delete_all_agents_and_team_agents()


@pytest.fixture
def team_agent(delete_agents_and_team_agents):
    """Create a team agent with unique names to avoid conflicts."""
    assert delete_agents_and_team_agents
    # Create unique names to avoid conflicts
    unique_suffix = str(uuid.uuid4())[:8]
    team_config = team_dict.copy()
    team_config["team_agent_name"] = f"Test Text Speech Team {unique_suffix}"

    # Update agent names to be unique as well
    agents = team_config["agents"].copy()
    for agent in agents:
        agent["agent_name"] = f"{agent['agent_name']} {unique_suffix}"
    team_config["agents"] = agents

    return build_team_agent_from_json(team_config)


def test_evolver_output(team_agent):
    """Test that evolver produces expected output structure."""
    response = team_agent.evolve_async()
    poll_url = response["url"]
    result = team_agent.poll(poll_url)

    while result.status == ResponseStatus.IN_PROGRESS:
        time.sleep(30)
        result = team_agent.poll(poll_url)

    assert result["status"] == ResponseStatus.SUCCESS, "Final result should have a 'SUCCESS' status"
    assert "evolved_agent" in result["data"], "Data should contain 'evolved_agent'"
    assert "evaluation_report" in result["data"], "Data should contain 'evaluation_report'"
    assert "criteria" in result["data"], "Data should contain 'criteria'"
    assert "archive" in result["data"], "Data should contain 'archive'"
    assert isinstance(result.data["evolved_agent"], type(team_agent)), (
        "Evolved agent should be an instance of the team agent"
    )


def test_evolver_with_custom_llm_id(team_agent):
    """Test evolver functionality with custom LLM ID."""
    from aixplain.factories.model_factory import ModelFactory

    custom_llm_id = "6646261c6eb563165658bbb1"  # GPT-4o ID
    model = ModelFactory.get(model_id=custom_llm_id)

    # Test with llm parameter
    response = team_agent.evolve(llm=model)

    assert response is not None
    assert response.data["evolved_agent"] is not None
    assert response.data["evolved_agent"].llm_id == custom_llm_id
    assert isinstance(response.data["evolved_agent"], type(team_agent)), (
        "Evolved agent should be an instance of the team agent"
    )
