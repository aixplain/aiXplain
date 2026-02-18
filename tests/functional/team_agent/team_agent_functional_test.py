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


@pytest.fixture
def resource_tracker():
    """Tracks resources created during a test for guaranteed cleanup."""
    resources = []
    yield resources
    for resource in reversed(resources):
        try:
            resource.delete()
        except Exception:
            pass


@pytest.fixture(scope="module", params=read_data(RUN_FILE))
def run_input_map(request):
    return request.param


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_end2end(run_input_map, resource_tracker, TeamAgentFactory):
    agents = create_agents_from_input_map(run_input_map)
    for agent in agents:
        resource_tracker.append(agent)
    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
    )
    resource_tracker.append(team_agent)

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
    assert response["data"]["output"] is not None


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_draft_team_agent_update(run_input_map, resource_tracker, TeamAgentFactory):
    agents = create_agents_from_input_map(run_input_map, deploy=False)
    for agent in agents:
        resource_tracker.append(agent)
    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
    )
    resource_tracker.append(team_agent)

    team_agent_name = str(uuid4()).replace("-", "")
    team_agent.name = team_agent_name
    team_agent.update()
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent.name == team_agent_name
    assert team_agent.status == AssetStatus.DRAFT


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_nested_deployment_chain(resource_tracker, TeamAgentFactory):
    """Test that deploying a team agent properly deploys all nested components (tools -> agents -> team)"""
    # Create first agent with translation tool (in DRAFT state)
    translation_function = Function.TRANSLATION
    function_params = translation_function.get_parameters()
    function_params.targetlanguage = "es"
    function_params.sourcelanguage = "en"
    translation_tool = AgentFactory.create_model_tool(
        function=translation_function,
        description="Translation tool from English to Spanish",
        supplier=Supplier.AZURE,
    )

    translation_agent_name = f"TrA {str(uuid4())[:8]}"
    translation_agent = AgentFactory.create(
        name=translation_agent_name,
        description="Agent for translation",
        instructions="Translate text from English to Spanish",
        llm_id="6646261c6eb563165658bbb1",
        tools=[translation_tool],
    )
    resource_tracker.append(translation_agent)
    assert translation_agent.status == AssetStatus.DRAFT
    # Create second agent with text generation tool (in DRAFT state)
    text_gen_tool = AgentFactory.create_model_tool(
        function=Function.TEXT_GENERATION,
        description="Text generation tool",
        supplier=Supplier.OPENAI,
    )

    text_gen_agent_name = f"TGA {str(uuid4())[:8]}"
    text_gen_agent = AgentFactory.create(
        name=text_gen_agent_name,
        description="Agent for text generation",
        instructions="Generate creative text based on input",
        llm_id="6646261c6eb563165658bbb1",
        tools=[text_gen_tool],
    )
    resource_tracker.append(text_gen_agent)
    assert text_gen_agent.status == AssetStatus.DRAFT

    # Create team agent with both agents (in DRAFT state)
    team_agent_name = f"MFT {str(uuid4())[:8]}"
    team_agent = TeamAgentFactory.create(
        name=team_agent_name,
        description="Team that can translate and generate text",
        agents=[translation_agent, text_gen_agent],
        llm_id="6646261c6eb563165658bbb1",
    )
    resource_tracker.append(team_agent)
    assert team_agent.status == AssetStatus.DRAFT
    for agent in team_agent.agents:
        assert agent.status == AssetStatus.DRAFT

    # Deploy team agent - this should trigger deployment of all nested components
    team_agent.deploy()

    # Verify team agent is deployed
    team_agent = TeamAgentFactory.get(team_agent.id)
    assert team_agent.status == AssetStatus.ONBOARDED

    # Verify all agents are deployed
    for agent in team_agent.agents:
        agent_obj = AgentFactory.get(agent.id)
        assert agent_obj.status == AssetStatus.ONBOARDED
        # Verify all tools are deployed
        for tool in agent_obj.tools:
            assert tool.status == AssetStatus.ONBOARDED


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_fail_non_existent_llm(run_input_map, resource_tracker, TeamAgentFactory):
    agents = create_agents_from_input_map(run_input_map, deploy=False)
    for agent in agents:
        resource_tracker.append(agent)

    with pytest.raises(Exception) as exc_info:
        TeamAgentFactory.create(
            name=f"NEL {str(uuid4())[:8]}",
            description="",
            llm_id="non_existent_llm",
            agents=agents,
        )
    assert (
        str(exc_info.value)
        == "TeamAgent Onboarding Error: LLM non_existent_llm does not exist for Main LLM. To resolve this, set the following LLM parameters to a valid LLM object or LLM ID: llm, supervisor_llm, mentalist_llm."
    )


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_add_remove_agents_from_team_agent(run_input_map, resource_tracker, TeamAgentFactory):
    agents = create_agents_from_input_map(run_input_map, deploy=False)
    for agent in agents:
        resource_tracker.append(agent)
    team_agent = create_team_agent(
        TeamAgentFactory,
        agents,
        run_input_map,
        use_mentalist=True,
    )
    resource_tracker.append(team_agent)

    assert team_agent is not None
    assert team_agent.status == AssetStatus.DRAFT

    new_agent_name = f"NA {str(uuid4())[:8]}"
    new_agent = AgentFactory.create(
        name=new_agent_name,
        description="Agent added to team",
        instructions="Agent added to team",
        llm_id=run_input_map["llm_id"],
    )
    resource_tracker.append(new_agent)
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


def test_team_agent_tasks(resource_tracker):
    agent_name = f"TSA {str(uuid4())[:8]}"
    agent = AgentFactory.create(
        name=agent_name,
        description="You are a test agent that always returns the same answer",
        tools=[
            AgentFactory.create_model_tool(function=Function.TRANSLATION, supplier=Supplier.AZURE),
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
    resource_tracker.append(agent)

    team_agent_name = f"TMA {str(uuid4())[:8]}"
    team_agent = TeamAgentFactory.create(
        name=team_agent_name,
        agents=[agent],
        description="Teste",
    )
    resource_tracker.append(team_agent)
    response = team_agent.run(data="Translate 'teste'")
    assert response.status == "SUCCESS"
    assert "test" in response.data["output"]


@pytest.mark.skip(reason="Tools not available - uses ConnectionTool model")
def test_team_agent_with_parameterized_agents(run_input_map, resource_tracker):
    """Test team agent with agents that have parameterized tools"""
    # Create first agent with search tool
    search_model = ModelFactory.get("692f18557b2cc45d29150cb0")
    model_params = search_model.get_parameters()
    model_params.numResults = 5
    search_tool = AgentFactory.create_model_tool(
        model=search_model, description="Search tool with custom number of results"
    )

    search_agent_name = f"SA {str(uuid4())[:8]}"
    search_agent = AgentFactory.create(
        name=search_agent_name,
        description="This agent is used to search for information in the web.",
        instructions="Agent that performs searches. Once you have the results, return them in a list as the output.",
        llm_id=run_input_map["llm_id"],
        tools=[search_tool],
    )
    resource_tracker.append(search_agent)
    search_agent.deploy()

    # Create second agent with translation tool
    translation_function = Function.TRANSLATION
    function_params = translation_function.get_parameters()
    function_params.targetlanguage = "pt"
    function_params.sourcelanguage = "en"
    translation_tool = AgentFactory.create_model_tool(
        function=translation_function,
        description="Translation tool with source language",
        supplier=Supplier.AZURE,
    )

    translation_agent_name = f"TrA {str(uuid4())[:8]}"
    translation_agent = AgentFactory.create(
        name=translation_agent_name,
        description="This agent is used to translate text from one language to another.",
        instructions="Agent that translates text from English to Portuguese",
        llm_id=run_input_map["llm_id"],
        tools=[translation_tool],
    )
    resource_tracker.append(translation_agent)
    translation_agent.deploy()
    team_agent = create_team_agent(
        TeamAgentFactory,
        [search_agent, translation_agent],
        run_input_map,
        use_mentalist=True,
    )
    resource_tracker.append(team_agent)

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
    assert search_agent_name in called_agents
    assert translation_agent_name in called_agents


def test_team_agent_with_instructions(resource_tracker):
    agent_1_name = f"A1 {str(uuid4())[:8]}"
    agent_1 = AgentFactory.create(
        name=agent_1_name,
        description="Translation agent",
        tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION, supplier=Supplier.AZURE)],
        llm_id="6646261c6eb563165658bbb1",
    )
    resource_tracker.append(agent_1)

    agent_2_name = f"A2 {str(uuid4())[:8]}"
    agent_2 = AgentFactory.create(
        name=agent_2_name,
        description="Translation agent",
        tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION, supplier=Supplier.GOOGLE)],
        llm_id="6646261c6eb563165658bbb1",
    )
    resource_tracker.append(agent_2)

    team_agent_name = f"TTA {str(uuid4())[:8]}"
    team_agent = TeamAgentFactory.create(
        name=team_agent_name,
        agents=[agent_1, agent_2],
        description="Team agent",
        instructions=f"Use only '{agent_2_name}' to solve the tasks.",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=True,
    )
    resource_tracker.append(team_agent)

    response = team_agent.run(data="Translate 'cat' to Portuguese")
    assert response.status == "SUCCESS"
    assert "gato" in response.data["output"]

    mentalist_steps = [json.loads(step) for step in response.data["intermediate_steps"][0]["output"]]

    called_agents = set([step["agent"] for step in mentalist_steps])
    assert len(called_agents) == 1
    assert agent_2_name in called_agents


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_team_agent_llm_parameter_preservation(resource_tracker, run_input_map, TeamAgentFactory):
    """Test that LLM parameters like temperature are preserved for all LLM roles in team agents."""
    # Create a regular agent first
    agents = create_agents_from_input_map(run_input_map, deploy=True)
    for agent in agents:
        resource_tracker.append(agent)

    # Get LLM instances and customize their temperatures
    supervisor_llm = ModelFactory.get("671be4886eb56397e51f7541")  # Anthropic Claude 3.5 Sonnet v1
    mentalist_llm = ModelFactory.get("671be4886eb56397e51f7541")  # Anthropic Claude 3.5 Sonnet v1

    # Set custom temperatures
    supervisor_llm.temperature = 0.1
    mentalist_llm.temperature = 0.3

    # Create a team agent with custom LLMs
    team_agent_name = f"LPTTA {str(uuid4())[:8]}"
    team_agent = TeamAgentFactory.create(
        name=team_agent_name,
        agents=agents,
        supervisor_llm=supervisor_llm,
        mentalist_llm=mentalist_llm,
        llm_id="671be4886eb56397e51f7541",  # Still required even with custom LLMs
        description="A team agent for testing LLM parameter preservation",
        use_mentalist=True,
    )
    resource_tracker.append(team_agent)

    # Verify that temperature settings were preserved
    assert team_agent.supervisor_llm.temperature == 0.1
    assert team_agent.mentalist_llm.temperature == 0.3

    # Verify that the team agent's LLMs are the same instances as the originals
    assert id(team_agent.supervisor_llm) == id(supervisor_llm)
    assert id(team_agent.mentalist_llm) == id(mentalist_llm)


def test_run_team_agent_with_expected_output(resource_tracker):
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

    agent_name = f"TA {str(uuid4())[:8]}"
    agent = AgentFactory.create(
        name=agent_name,
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
    resource_tracker.append(agent)

    team_agent_name = f"TTA {str(uuid4())[:8]}"
    team_agent = TeamAgentFactory.create(
        name=team_agent_name,
        agents=[agent],
        description="Team agent",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=False,
    )
    resource_tracker.append(team_agent)

    # Run the team agent
    response = team_agent.run(
        "Who have more than 30 years old?",
        output_format=OutputFormat.JSON,
        expected_output=Response,
    )

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


@pytest.mark.skip(reason="Tools not available")
def test_team_agent_with_slack_connector(resource_tracker):
    from aixplain.modules.model.integration import AuthenticationSchema

    connector = ModelFactory.get("686432941223092cb4294d3f")
    # connect
    response = connector.connect(
        authentication_schema=AuthenticationSchema.BEARER_TOKEN,
        data={"token": os.getenv("SLACK_TOKEN")},
    )

    connection_id = response.data["id"]

    connection = ModelFactory.get(connection_id)
    connection.action_scope = [
        action for action in connection.actions if action.code == "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"
    ]

    agent_name = f"TA {str(uuid4())[:8]}"
    agent = AgentFactory.create(
        name=agent_name,
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
    resource_tracker.append(agent)

    team_agent_name = f"TTA {str(uuid4())[:8]}"
    team_agent = TeamAgentFactory.create(
        name=team_agent_name,
        agents=[agent],
        description="Team agent",
        llm_id="6646261c6eb563165658bbb1",
        use_mentalist=False,
    )
    resource_tracker.append(team_agent)
    resource_tracker.append(connection)

    response = team_agent.run(
        "Send what is the capital of Senegal on Slack to channel of #modelserving-alerts: 'C084G435LR5'. Add the name of the capital in the final answer."
    )
    assert response["status"].lower() == "success"
    assert "dakar" in response.data.output.lower()


@pytest.mark.parametrize("TeamAgentFactory", [TeamAgentFactory])
def test_multiple_teams_with_shared_deployed_agent(resource_tracker, TeamAgentFactory):
    """Test that multiple team agents can share the same deployed agent without name conflicts"""
    # Create and deploy a shared agent first
    translation_tool = AgentFactory.create_model_tool(
        function=Function.TRANSLATION,
        description="Translation tool from English to Spanish",
        supplier=Supplier.AZURE,
    )

    shared_agent_name = f"STA {str(uuid4())[:8]}"
    shared_agent = AgentFactory.create(
        name=shared_agent_name,
        description="Agent for translation shared between teams",
        instructions="Translate text from English to Spanish",
        llm_id="6646261c6eb563165658bbb1",
        tools=[translation_tool],
    )
    resource_tracker.append(shared_agent)

    # Deploy the shared agent first
    shared_agent.deploy()
    shared_agent = AgentFactory.get(shared_agent.id)
    assert shared_agent.status == AssetStatus.ONBOARDED

    # Create first team agent with the shared agent
    team_agent_1_name = f"TTA1 {str(uuid4())[:8]}"
    team_agent_1 = TeamAgentFactory.create(
        name=team_agent_1_name,
        description="First team using shared agent",
        agents=[shared_agent],
        llm_id="6646261c6eb563165658bbb1",
    )
    resource_tracker.append(team_agent_1)
    assert team_agent_1.status == AssetStatus.DRAFT

    # Deploy first team agent - should succeed without trying to redeploy the shared agent
    team_agent_1.deploy()
    team_agent_1 = TeamAgentFactory.get(team_agent_1.id)
    assert team_agent_1.status == AssetStatus.ONBOARDED

    # Create second team agent with the same shared agent
    team_agent_2_name = f"TTA2 {str(uuid4())[:8]}"
    team_agent_2 = TeamAgentFactory.create(
        name=team_agent_2_name,
        description="Second team using shared agent",
        agents=[shared_agent],
        llm_id="6646261c6eb563165658bbb1",
    )
    resource_tracker.append(team_agent_2)
    assert team_agent_2.status == AssetStatus.DRAFT

    # Deploy second team agent - should succeed without trying to redeploy the shared agent
    # This should NOT throw a name_already_exists error
    team_agent_2.deploy()
    team_agent_2 = TeamAgentFactory.get(team_agent_2.id)
    assert team_agent_2.status == AssetStatus.ONBOARDED

    # Verify both team agents are deployed and functional
    response_1 = team_agent_1.run(data="Hello world")
    assert response_1 is not None
    assert response_1["completed"] is True
    assert response_1["status"].lower() == "success"

    response_2 = team_agent_2.run(data="Hello world")
    assert response_2 is not None
    assert response_2["completed"] is True
    assert response_2["status"].lower() == "success"

    # Verify the shared agent is still deployed and accessible
    shared_agent_refreshed = AgentFactory.get(shared_agent.id)
    assert shared_agent_refreshed.status == AssetStatus.ONBOARDED
