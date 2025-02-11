__author__ = "lucaspavanelli"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import json
from dotenv import load_dotenv

load_dotenv()
from aixplain.factories import AgentFactory, TeamAgentFactory, ModelFactory
from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from copy import copy
from uuid import uuid4
import pytest

from aixplain import aixplain_v2 as v2

RUN_FILE = "tests/functional/team_agent/data/team_agent_test_end2end.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="function")
def delete_agents_and_team_agents():
    for team_agent in TeamAgentFactory.list()["results"]:
        team_agent.delete()
    for agent in AgentFactory.list()["results"]:
        agent.delete()

    yield True

    for team_agent in TeamAgentFactory.list()["results"]:
        team_agent.delete()
    for agent in AgentFactory.list()["results"]:
        agent.delete()


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_end2end(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    assert delete_agents_and_team_agents

    agents = []
    for agent in run_input_map["agents"]:
        tools = []
        if "model_tools" in agent:
            for tool in agent["model_tools"]:
                tool_ = copy(tool)
                for supplier in Supplier:
                    if tool["supplier"] is not None and tool["supplier"].lower() in [
                        supplier.value["code"].lower(),
                        supplier.value["name"].lower(),
                    ]:
                        tool_["supplier"] = supplier
                        break
                tools.append(AgentFactory.create_model_tool(**tool_))
        if "pipeline_tools" in agent:
            for tool in agent["pipeline_tools"]:
                tools.append(AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"]))

        agent = AgentFactory.create(
            name=agent["agent_name"],
            description=agent["agent_name"],
            instructions=agent["agent_name"],
            llm_id=agent["llm_id"],
            tools=tools,
        )
        agent.deploy()
        agents.append(agent)

    team_agent = TeamAgentFactory.create(
        name=run_input_map["team_agent_name"],
        agents=agents,
        description=run_input_map["team_agent_name"],
        llm_id=run_input_map["llm_id"],
        use_mentalist_and_inspector=True,
    )

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT
    # deploy team agent
    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent is not None
    assert team_agent.status == AssetStatus.ONBOARDED
    response = team_agent.run(data=run_input_map["query"])

    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert "data" in response
    assert response["data"]["session_id"] is not None
    assert response["data"]["output"] is not None

    team_agent.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_draft_team_agent_update(run_input_map, TeamAgentFactory):
    for team in TeamAgentFactory.list()["results"]:
        team.delete()
    for agent in AgentFactory.list()["results"]:
        agent.delete()

    agents = []
    for agent in run_input_map["agents"]:
        tools = []
        if "model_tools" in agent:
            for tool in agent["model_tools"]:
                tool_ = copy(tool)
                for supplier in Supplier:
                    if tool["supplier"] is not None and tool["supplier"].lower() in [
                        supplier.value["code"].lower(),
                        supplier.value["name"].lower(),
                    ]:
                        tool_["supplier"] = supplier
                        break
                tools.append(AgentFactory.create_model_tool(**tool_))
        if "pipeline_tools" in agent:
            for tool in agent["pipeline_tools"]:
                tools.append(AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"]))

        agent = AgentFactory.create(
            name=agent["agent_name"],
            description=agent["agent_name"],
            instructions=agent["agent_name"],
            llm_id=agent["llm_id"],
            tools=tools,
        )
        agents.append(agent)

    team_agent = TeamAgentFactory.create(
        name=run_input_map["team_agent_name"],
        agents=agents,
        description=run_input_map["team_agent_name"],
        llm_id=run_input_map["llm_id"],
        use_mentalist_and_inspector=True,
    )

    team_agent_name = str(uuid4()).replace("-", "")
    team_agent.name = team_agent_name
    team_agent.update()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent.name == team_agent_name
    assert team_agent.status == AssetStatus.DRAFT


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_fail_non_existent_llm(TeamAgentFactory):
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test Agent",
            description="",
            instructions="",
            llm_id="non_existent_llm",
            tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION)],
        )
    assert str(exc_info.value) == "Large Language Model with ID 'non_existent_llm' not found."


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_add_remove_agents_from_team_agent(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    assert delete_agents_and_team_agents

    agents = []
    for agent in run_input_map["agents"]:
        tools = []
        if "model_tools" in agent:
            for tool in agent["model_tools"]:
                tool_ = copy(tool)
                for supplier in Supplier:
                    if tool["supplier"] is not None and tool["supplier"].lower() in [
                        supplier.value["code"].lower(),
                        supplier.value["name"].lower(),
                    ]:
                        tool_["supplier"] = supplier
                        break
                tools.append(AgentFactory.create_model_tool(**tool_))
        if "pipeline_tools" in agent:
            for tool in agent["pipeline_tools"]:
                tools.append(AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"]))

        agent = AgentFactory.create(
            name=agent["agent_name"],
            description=agent["agent_name"],
            instructions=agent["agent_name"],
            llm_id=agent["llm_id"],
            tools=tools,
        )
        agents.append(agent)

    team_agent = TeamAgentFactory.create(
        name=run_input_map["team_agent_name"],
        agents=agents,
        description=run_input_map["team_agent_name"],
        llm_id=run_input_map["llm_id"],
        use_mentalist_and_inspector=True,
    )

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    new_agent = AgentFactory.create(
        name="New Agent",
        description="Agent added to team",
        instructions="Agent added to team",
        llm_id=run_input_map["llm_id"],
    )
    team_agent.agents.append(new_agent)
    team_agent.update()

    team_agent = TeamAgentFactory.get(team_agent.id)
    assert new_agent.id in [agent.id for agent in team_agent.agents]
    assert len(team_agent.agents) == len(agents) + 1

    removed_agent = team_agent.agents.pop(0)
    team_agent.update()

    team_agent = TeamAgentFactory.get(team_agent.id)
    assert removed_agent.id not in [agent.id for agent in team_agent.agents]
    assert len(team_agent.agents) == len(agents)

    team_agent.delete()
    new_agent.delete()


def test_team_agent_tasks(delete_agents_and_team_agents):
    assert delete_agents_and_team_agents
    agent = AgentFactory.create(
        name="Teste",
        description="You are a test agent that always returns the same answer",
        tools=[
            AgentFactory.create_model_tool(function=Function.TRANSLATION, supplier=Supplier.MICROSOFT),
        ],
        tasks=[
            AgentFactory.create_task(
                name="en_pt",
                description="Translate the given text from English to Portuguese",
                expected_output="The translated text",
                dependencies=["pt_en"],
            ),
            AgentFactory.create_task(
                name="pt_en",
                description="Translate the given text from Portuguese to English",
                expected_output="The translated text",
            ),
        ],
    )

    team_agent = TeamAgentFactory.create(
        name="Teste",
        agents=[agent],
        description="Teste",
    )
    response = team_agent.run(data="Translate 'teste'")
    assert response.status == "SUCCESS"
    assert "teste" in response.data["output"]


def test_team_agent_with_parameterized_agents(delete_agents_and_team_agents):
    """Test team agent with agents that have parameterized tools"""
    assert delete_agents_and_team_agents

    # Create first agent with search tool
    search_model = ModelFactory.get("65c51c556eb563350f6e1bb1")
    model_params = search_model.get_parameters()
    model_params.numResults = 5
    search_tool = AgentFactory.create_model_tool(model=search_model, description="Search tool with custom number of results")

    search_agent = AgentFactory.create(
        name="Search Agent",
        description="This agent is used to search for information in the web.",
        instructions="Agent that performs searches",
        llm_id="677c16166eb563bb611623c1",
        tools=[search_tool],
    )

    # Create second agent with translation tool
    translation_function = Function.TRANSLATION
    function_params = translation_function.get_parameters()
    function_params.targetlanguage = "pt"
    function_params.sourcelanguage = "en"
    translation_tool = AgentFactory.create_model_tool(
        function=translation_function, description="Translation tool with source language", supplier="microsoft"
    )

    translation_agent = AgentFactory.create(
        name="Translation Agent",
        description="This agent is used to translate text from one language to another.",
        instructions="Agent that performs translations",
        llm_id="677c16166eb563bb611623c1",
        tools=[translation_tool],
    )

    # Create team agent with both parameterized agents
    team_agent = TeamAgentFactory.create(
        name="Parameterized Team Agent",
        agents=[search_agent, translation_agent],
        description="Team agent with parameterized tools",
        llm_id="677c16166eb563bb611623c1",
        use_mentalist_and_inspector=True,
    )

    # Deploy team agent
    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent.status == AssetStatus.ONBOARDED

    search_response = team_agent.run(
        data="What are the top researchers in the field of AI? Search for it in the web. Then translate the result."
    )
    assert search_response.status == "SUCCESS"
    assert "data" in search_response
    assert "intermediate_steps" in search_response.data
    assert len(search_response.data["intermediate_steps"]) > 0
    intermediate_steps = search_response.data["intermediate_steps"]
    called_agents = [step["agent"] for step in intermediate_steps]
    assert "Search Agent" in called_agents
    assert "Translation Agent" in called_agents

    # Cleanup
    team_agent.delete()
    search_agent.delete()
    translation_agent.delete()
