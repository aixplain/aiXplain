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
import copy
import json
from dotenv import load_dotenv

load_dotenv()
from aixplain.factories import AgentFactory, TeamAgentFactory
from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from uuid import uuid4

import pytest

RUN_FILE = "tests/functional/agent/data/agent_test_end2end.json"


def read_data(data_path):
    return json.load(open(data_path, "r"))


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


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


def test_end2end(run_input_map, delete_agents_and_team_agents):
    assert delete_agents_and_team_agents
    tools = []
    if "model_tools" in run_input_map:
        for tool in run_input_map["model_tools"]:
            tool_ = copy.copy(tool)
            for supplier in Supplier:
                if tool["supplier"] is not None and tool["supplier"].lower() in [
                    supplier.value["code"].lower(),
                    supplier.value["name"].lower(),
                ]:
                    tool_["supplier"] = supplier
                    break
            tools.append(AgentFactory.create_model_tool(**tool_))
    if "pipeline_tools" in run_input_map:
        for tool in run_input_map["pipeline_tools"]:
            tools.append(AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"]))

    agent = AgentFactory.create(
        name=run_input_map["agent_name"], description=run_input_map["agent_name"], llm_id=run_input_map["llm_id"], tools=tools
    )
    assert agent is not None
    assert agent.status == AssetStatus.DRAFT
    # deploy agent
    agent.deploy()
    assert agent.status == AssetStatus.ONBOARDED

    agent = AgentFactory.get(agent.id)
    assert agent is not None
    response = agent.run(data=run_input_map["query"])
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert "data" in response
    assert response["data"]["session_id"] is not None
    assert response["data"]["output"] is not None
    agent.delete()


def test_list_agents():
    agents = AgentFactory.list()
    assert "results" in agents
    agents_result = agents["results"]
    assert type(agents_result) is list


def test_update_draft_agent(run_input_map, delete_agents_and_team_agents):
    assert delete_agents_and_team_agents

    tools = []
    if "model_tools" in run_input_map:
        for tool in run_input_map["model_tools"]:
            tool_ = copy.copy(tool)
            for supplier in Supplier:
                if tool["supplier"] is not None and tool["supplier"].lower() in [
                    supplier.value["code"].lower(),
                    supplier.value["name"].lower(),
                ]:
                    tool_["supplier"] = supplier
                    break
            tools.append(AgentFactory.create_model_tool(**tool_))
    if "pipeline_tools" in run_input_map:
        for tool in run_input_map["pipeline_tools"]:
            tools.append(AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"]))

    agent = AgentFactory.create(
        name=run_input_map["agent_name"], description=run_input_map["agent_name"], llm_id=run_input_map["llm_id"], tools=tools
    )

    agent_name = str(uuid4()).replace("-", "")
    agent.name = agent_name
    agent.update()

    agent = AgentFactory.get(agent.id)
    assert agent.name == agent_name
    assert agent.status == AssetStatus.DRAFT
    agent.delete()


def test_fail_non_existent_llm(delete_agents_and_team_agents):
    assert delete_agents_and_team_agents
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test Agent",
            description="Test description",
            llm_id="non_existent_llm",
            tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION)],
        )
    assert str(exc_info.value) == "Large Language Model with ID 'non_existent_llm' not found."


def test_delete_agent_in_use(delete_agents_and_team_agents):
    assert delete_agents_and_team_agents
    agent = AgentFactory.create(
        name="Test Agent",
        description="Test description",
        tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION)],
    )
    TeamAgentFactory.create(
        name="Test Team Agent",
        agents=[agent],
        description="Test description",
        use_mentalist_and_inspector=True,
    )

    with pytest.raises(Exception) as exc_info:
        agent.delete()
    assert str(exc_info.value) == "Agent Deletion Error (HTTP 403): err.agent_is_in_use."


def test_update_tools_of_agent(run_input_map, delete_agents_and_team_agents):
    assert delete_agents_and_team_agents

    agent = AgentFactory.create(
        name=run_input_map["agent_name"], description=run_input_map["agent_name"], llm_id=run_input_map["llm_id"]
    )
    assert agent is not None
    assert agent.status == AssetStatus.DRAFT
    assert len(agent.tools) == 0 

    tools = []
    if "model_tools" in run_input_map:
        for tool in run_input_map["model_tools"]:
            tool_ = copy.copy(tool)
            for supplier in Supplier:
                if tool["supplier"] is not None and tool["supplier"].lower() in [
                    supplier.value["code"].lower(),
                    supplier.value["name"].lower(),
                ]:
                    tool_["supplier"] = supplier
                    break
            tools.append(AgentFactory.create_model_tool(**tool_))

    if "pipeline_tools" in run_input_map:
        for tool in run_input_map["pipeline_tools"]:
            tools.append(AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"]))

    agent.tools = tools
    agent.update()

    agent = AgentFactory.get(agent.id)
    assert len(agent.tools) == len(tools)  

    removed_tool = agent.tools.pop()
    agent.update()

    agent = AgentFactory.get(agent.id)
    assert len(agent.tools) == len(tools) - 1 
    assert removed_tool not in agent.tools 

    agent.delete()
