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
import os
from dotenv import load_dotenv
from uuid import uuid4

load_dotenv()

import pytest

from aixplain import aixplain_v2 as v2
from aixplain.factories import AgentFactory, TeamAgentFactory, ModelFactory
from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier

from tests.functional.team_agent.test_utils import (
    RUN_FILE,
    read_data,
    create_agents_from_input_map,
    create_team_agent,
)


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

    agents = create_agents_from_input_map(run_input_map)
    team_agent = create_team_agent(
        TeamAgentFactory, agents, run_input_map, use_mentalist=True, inspectors=[], inspector_targets=None
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

    agents = create_agents_from_input_map(run_input_map, deploy=False)
    team_agent = create_team_agent(
        TeamAgentFactory, agents, run_input_map, use_mentalist=True, inspectors=[], inspector_targets=None
    )

    team_agent_name = str(uuid4()).replace("-", "")
    team_agent.name = team_agent_name
    team_agent.update()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent.name == team_agent_name
    assert team_agent.status == AssetStatus.DRAFT


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_fail_non_existent_llm(run_input_map, TeamAgentFactory):
    for team in TeamAgentFactory.list()["results"]:
        team.delete()
    for agent in AgentFactory.list()["results"]:
        agent.delete()

    agents = create_agents_from_input_map(run_input_map, deploy=False)

    with pytest.raises(Exception) as exc_info:
        TeamAgentFactory.create(
            name="Non Existent LLM",
            description="",
            llm_id="non_existent_llm",
            agents=agents,
        )
    assert str(exc_info.value) == "Large Language Model with ID 'non_existent_llm' not found."


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_add_remove_agents_from_team_agent(run_input_map, delete_agents_and_team_agents, TeamAgentFactory):
    assert delete_agents_and_team_agents

    agents = create_agents_from_input_map(run_input_map, deploy=False)
    team_agent = create_team_agent(
        TeamAgentFactory, agents, run_input_map, use_mentalist=True, inspectors=[], inspector_targets=None
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


def test_team_agent_with_parameterized_agents(run_input_map, delete_agents_and_team_agents):
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
        instructions="Agent that performs searches. Once you have the results, return them in a list as the output.",
        llm_id=run_input_map["llm_id"],
        tools=[search_tool],
    )
    search_agent.deploy()

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
        instructions="Agent that translates text from English to Portuguese",
        llm_id=run_input_map["llm_id"],
        tools=[translation_tool],
    )
    translation_agent.deploy()
    team_agent = create_team_agent(
        TeamAgentFactory,
        [search_agent, translation_agent],
        run_input_map,
        use_mentalist=True,
        inspectors=[],
        inspector_targets=None,
    )

    # Deploy team agent
    team_agent.deploy()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent.status == AssetStatus.ONBOARDED

    search_response = team_agent.run(
        data="What are the top 5 fruits consumed in the world in 2024? Search for it in the web and then translate the result."
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


def test_team_agent_with_instructions(delete_agents_and_team_agents):
    assert delete_agents_and_team_agents

    agent_1 = AgentFactory.create(
        name="Agent 1",
        description="Translation agent",
        tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION, supplier=Supplier.MICROSOFT)],
        llm_id="6646261c6eb563165658bbb1",
    )

    agent_2 = AgentFactory.create(
        name="Agent 2",
        description="Translation agent",
        tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION, supplier=Supplier.GOOGLE)],
        llm_id="6646261c6eb563165658bbb1",
    )

    team_agent = TeamAgentFactory.create(
        name="Team Agent",
        agents=[agent_1, agent_2],
        description="Team agent",
        instructions="Use only 'Agent 2' to solve the tasks.",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=True,
        use_inspector=False,
    )

    response = team_agent.run(data="Translate 'cat' to Portuguese")
    assert response.status == "SUCCESS"
    assert "gato" in response.data["output"]

    mentalist_steps = [json.loads(step) for step in eval(response.data["intermediate_steps"][0]["output"])]

    called_agents = set([step["agent"] for step in mentalist_steps])
    assert len(called_agents) == 1
    assert "Agent 2" in called_agents

    team_agent.delete()
    agent_1.delete()
    agent_2.delete()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory, v2.TeamAgent])
def test_team_agent_llm_parameter_preservation(delete_agents_and_team_agents, run_input_map, TeamAgentFactory):
    """Test that LLM parameters like temperature are preserved for all LLM roles in team agents."""
    assert delete_agents_and_team_agents

    # Create a regular agent first
    agents = create_agents_from_input_map(run_input_map, deploy=True)

    # Get LLM instances and customize their temperatures
    supervisor_llm = ModelFactory.get("671be4886eb56397e51f7541")  # Anthropic Claude 3.5 Sonnet v1
    mentalist_llm = ModelFactory.get("671be4886eb56397e51f7541")  # Anthropic Claude 3.5 Sonnet v1

    # Set custom temperatures
    supervisor_llm.temperature = 0.1
    mentalist_llm.temperature = 0.3

    # Create a team agent with custom LLMs
    team_agent = TeamAgentFactory.create(
        name="LLM Parameter Test Team Agent",
        agents=agents,
        supervisor_llm=supervisor_llm,
        mentalist_llm=mentalist_llm,
        llm_id="671be4886eb56397e51f7541",  # Still required even with custom LLMs
        description="A team agent for testing LLM parameter preservation",
        use_mentalist=True,
    )

    # Verify that temperature settings were preserved
    assert team_agent.supervisor_llm.temperature == 0.1
    assert team_agent.mentalist_llm.temperature == 0.3

    # Verify that the team agent's LLMs are the same instances as the originals
    assert id(team_agent.supervisor_llm) == id(supervisor_llm)
    assert id(team_agent.mentalist_llm) == id(mentalist_llm)

    # Clean up
    team_agent.delete()


def test_run_team_agent_with_expected_output():
    from pydantic import BaseModel
    from typing import Optional, List
    from aixplain.modules.agent import AgentResponse
    from aixplain.modules.agent.output_format import OutputFormat

    class Person(BaseModel):
        name: str
        age: int
        city: Optional[str] = None

    class Response(BaseModel):
        result: List[Person]

    INSTRUCTIONS = """Answer questions based on the following context:

+-----------------+-------+----------------+
| Name            |   Age | City           |
+=================+=======+================+
| João Silva      |    34 | São Paulo      |
+-----------------+-------+----------------+
| Maria Santos    |    28 | Rio de Janeiro |
+-----------------+-------+----------------+
| Pedro Oliveira  |    45 |                |
+-----------------+-------+----------------+
| Ana Costa       |    19 | Recife         |
+-----------------+-------+----------------+
| Carlos Pereira  |    52 | Belo Horizonte |
+-----------------+-------+----------------+
| Beatriz Lima    |    31 |                |
+-----------------+-------+----------------+
| Lucas Ferreira  |    25 | Curitiba       |
+-----------------+-------+----------------+
| Julia Rodrigues |    41 | Salvador       |
+-----------------+-------+----------------+
| Miguel Almeida  |    37 |                |
+-----------------+-------+----------------+
| Sofia Carvalho  |    29 | Brasília       |
+-----------------+-------+----------------+"""

    agent = AgentFactory.create(
        name="Test Agent",
        description="Test description",
        instructions=INSTRUCTIONS,
        tasks=[
            AgentFactory.create_task(
                name="Task 1",
                description="Check table for information about people related to the query",
                expected_output="A table with the following columns: Name, Age, City",
            )
        ],
        llm_id="6646261c6eb563165658bbb1",
    )

    team_agent = TeamAgentFactory.create(
        name="Team Agent",
        agents=[agent],
        description="Team agent",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=False,
        use_inspector=False,
    )

    # Run the team agent
    response = team_agent.run("Who have more than 30 years old?", output_format=OutputFormat.JSON, expected_output=Response)

    # Verify response basics
    assert response is not None
    assert isinstance(response, AgentResponse)

    try:
        response_json = json.loads(response.data.output)
    except Exception:
        import re

        response_json = re.search(r"```json(.*?)```", response.data.output, re.DOTALL).group(1)
        response_json = json.loads(response_json)
    assert "result" in response_json
    assert len(response_json["result"]) > 0

    more_than_30_years_old = [
        "João Silva",
        "Pedro Oliveira",
        "Carlos Pereira",
        "Beatriz Lima",
        "Julia Rodrigues",
        "Miguel Almeida",
        "Sofia Carvalho",
    ]

    for person in response_json["result"]:
        assert "name" in person
        assert "age" in person
        assert "city" in person
        assert person["name"] in more_than_30_years_old


def test_team_agent_with_slack_connector():
    from aixplain.modules.model.integration import AuthenticationSchema

    connector = ModelFactory.get("67eff5c0e05614297caeef98")
    # connect
    response = connector.connect(authentication_schema=AuthenticationSchema.BEARER, token=os.getenv("SLACK_TOKEN"))
    connection_id = response.data["id"]

    connection = ModelFactory.get(connection_id)
    connection.action_scope = [action for action in connection.actions if action.code == "SLACK_CHAT_POST_MESSAGE"]

    agent = AgentFactory.create(
        name="Test Agent",
        description="This agent is used to send messages to Slack",
        instructions="You are a helpful assistant that can answer questions based on a large knowledge base and send messages to Slack.",
        llm_id="669a63646eb56306647e1091",
        tasks=[
            AgentFactory.create_task(
                name="Task 1",
                description="Check knowledge base for information about the query and send the response to Slack",
                expected_output="A message sent to Slack",
            )
        ],
        tools=[
            connection,
            AgentFactory.create_model_tool(model="6736411cf127849667606689"),
        ],
    )

    team_agent = TeamAgentFactory.create(
        name="Team Agent",
        agents=[agent],
        description="Team agent",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=False,
        use_inspector=False,
    )

    response = team_agent.run(
        "Send what is the capital of Senegal on Slack to channel of #modelserving-alerts: 'C084G435LR5'. Add the name of the capital in the final answer."
    )
    assert response["status"].lower() == "success"
    assert "dakar" in response.data.output.lower()

    team_agent.delete()
    agent.delete()
    connection.delete()
