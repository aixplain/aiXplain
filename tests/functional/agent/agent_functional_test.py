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
from aixplain.factories import AgentFactory, TeamAgentFactory, ModelFactory
from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.function import Function
from aixplain.enums.supplier import Supplier
from uuid import uuid4

import pytest

from aixplain import aixplain_v2 as v2

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


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_end2end(run_input_map, delete_agents_and_team_agents, AgentFactory):
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
        name=run_input_map["agent_name"],
        description=run_input_map["agent_name"],
        instructions=run_input_map["agent_name"],
        llm_id=run_input_map["llm_id"],
        tools=tools,
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


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_python_interpreter_tool(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    tool = AgentFactory.create_python_interpreter_tool()
    assert tool is not None
    assert tool.name == "Python Interpreter"
    assert tool.description == "A Python shell. Use this to execute python commands. Input should be a valid python command."

    agent = AgentFactory.create(
        name="Python Developer",
        description="A Python developer agent. If you get an error from a tool, try to fix it.",
        instructions="A Python developer agent. If you get an error from a tool, try to fix it.",
        tools=[tool],
    )
    assert agent is not None
    response = agent.run("Solve the equation $\\frac{v^2}{2} + 7v - 16 = 0$ to find the value of $v$.")
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert len(response["data"]["intermediate_steps"]) > 0
    intermediate_step = response["data"]["intermediate_steps"][0]
    assert len(intermediate_step["tool_steps"]) > 0
    assert intermediate_step["tool_steps"][0]["tool"] == "Custom Code Tool"
    agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_custom_code_tool(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    tool = AgentFactory.create_custom_python_code_tool(
        description="Add two numbers",
        code='def main(aaa: int, bbb: int) -> int:\n    """Add two numbers"""\n    return aaa + bbb',
    )
    assert tool is not None
    assert tool.description == "Add two numbers"
    assert tool.code == 'def main(aaa: int, bbb: int) -> int:\n    """Add two numbers"""\n    return aaa + bbb'
    agent = AgentFactory.create(
        name="Add Numbers Agent",
        description="Add two numbers. Do not directly answer. Use the tool to add the numbers.",
        instructions="Add two numbers. Do not directly answer. Use the tool to add the numbers.",
        tools=[tool],
    )
    assert agent is not None
    response = agent.run("How much is 12342 + 112312? Do not directly answer the question, call the tool.")
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert "124654" in response["data"]["output"]
    agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_list_agents(AgentFactory):
    agents = AgentFactory.list()
    assert "results" in agents
    agents_result = agents["results"]
    assert type(agents_result) is list


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_update_draft_agent(run_input_map, delete_agents_and_team_agents, AgentFactory):
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
        name=run_input_map["agent_name"],
        description=run_input_map["agent_name"],
        instructions=run_input_map["agent_name"],
        llm_id=run_input_map["llm_id"],
        tools=tools,
    )

    agent_name = str(uuid4()).replace("-", "")
    agent.name = agent_name
    agent.update()

    agent = AgentFactory.get(agent.id)
    assert agent.name == agent_name
    assert agent.status == AssetStatus.DRAFT
    agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_fail_non_existent_llm(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test Agent",
            description="Test description",
            instructions="Test Agent Role",
            llm_id="non_existent_llm",
            tools=[AgentFactory.create_model_tool(function=Function.TRANSLATION)],
        )
    assert str(exc_info.value) == "Large Language Model with ID 'non_existent_llm' not found."


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_delete_agent_in_use(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    agent = AgentFactory.create(
        name="Test Agent",
        description="Test description",
        instructions="Test Agent Role",
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


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_update_tools_of_agent(run_input_map, delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents

    agent = AgentFactory.create(
        name=run_input_map["agent_name"],
        description=run_input_map["agent_name"],
        instructions=run_input_map["agent_name"],
        llm_id=run_input_map["llm_id"],
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


@pytest.mark.parametrize(
    "tool_config",
    [
        {
            "type": "search",
            "model": "65c51c556eb563350f6e1bb1",
            "query": "What is the weather in New York?",
            "description": "Search tool with custom number of results",
            "expected_tool_input": "'numResults': 5",
        },
        {
            "type": "translation",
            "supplier": "Microsoft",
            "function": "translation",
            "query": "Translate: Olá, como vai você?",
            "description": "Translation tool with target language",
            "expected_tool_input": "targetlanguage",
        },
    ],
)
def test_specific_model_parameters_e2e(tool_config, delete_agents_and_team_agents):
    assert delete_agents_and_team_agents
    """Test end-to-end agent execution with specific model parameters"""
    # Create tool based on config
    if tool_config["type"] == "search":
        search_model = ModelFactory.get(tool_config["model"])
        model_params = search_model.get_parameters()
        model_params.numResults = 5
        tool = AgentFactory.create_model_tool(model=search_model, description=tool_config["description"])
    else:
        function = Function(tool_config["function"])
        function_params = function.get_parameters()
        function_params.sourcelanguage = "pt"
        tool = AgentFactory.create_model_tool(function=function, description=tool_config["description"], supplier="microsoft")

    # Verify tool parameters
    params = tool.get_parameters()
    assert len(params) == 1
    assert params[0]["name"] == ("numResults" if tool_config["type"] == "search" else "sourcelanguage")
    assert params[0]["value"] == (5 if tool_config["type"] == "search" else "pt")

    # Create and run agent
    agent = AgentFactory.create(
        name="Test Parameter Agent",
        description="Test agent with parameterized tools",
        tools=[tool],
        llm_id="6626a3a8c8f1d089790cf5a2",  # Using LLM ID from test data
    )

    # Run agent
    response = agent.run(data=tool_config["query"])

    # Verify response
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert "data" in response
    assert response["data"]["output"] is not None

    # Verify tool was used in execution
    assert len(response["data"]["intermediate_steps"]) > 0
    tool_used = False
    for step in response["data"]["intermediate_steps"]:
        if tool_config["expected_tool_input"] in step["tool_steps"][0]["input"]:
            tool_used = True
            break
    assert tool_used, "Tool was not used in execution"


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_sql_tool(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    try:
        import os

        # Create test SQLite database
        with open("ftest.db", "w") as f:
            f.write("")

        tool = AgentFactory.create_sql_tool(
            description="Execute an SQL query and return the result",
            source="ftest.db",
            source_type="sqlite",
            enable_commit=True,
        )
        assert tool is not None
        assert tool.description == "Execute an SQL query and return the result"

        agent = AgentFactory.create(
            name="Teste",
            description="You are a test agent that search for employee information in a database",
            tools=[tool],
        )
        assert agent is not None

        response = agent.run("Create a table called Person with the following columns: id, name, age, salary, department")
        assert response is not None
        assert response["completed"] is True
        assert response["status"].lower() == "success"

        response = agent.run("Insert the following data into the Person table: 1, Eve, 30, 50000, Sales")
        assert response is not None
        assert response["completed"] is True
        assert response["status"].lower() == "success"

        response = agent.run("What is the name of the employee with the highest salary?")
        assert response is not None
        assert response["completed"] is True
        assert response["status"].lower() == "success"
        assert "eve" in str(response["data"]["output"]).lower()
    finally:
        os.remove("ftest.db")
        agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory, v2.Agent])
def test_sql_tool_with_csv(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    try:
        import os
        import pandas as pd

        # remove test.csv if it exists
        if os.path.exists("test.csv"):
            os.remove("test.csv")

        # remove test.db if it exists
        if os.path.exists("test.db"):
            os.remove("test.db")

        # Create a more comprehensive test dataset
        df = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
                "department": ["Sales", "IT", "Sales", "Marketing", "IT"],
                "salary": [75000, 85000, 72000, 68000, 90000],
            }
        )
        df.to_csv("test.csv", index=False)

        # Create SQL tool from CSV
        tool = AgentFactory.create_sql_tool(
            description="Execute SQL queries on employee data", source="test.csv", source_type="csv", tables=["employees"]
        )

        # Verify tool setup
        assert tool is not None
        assert tool.description == "Execute SQL queries on employee data"
        assert tool.database.endswith(".db")
        assert tool.tables == ["employees"]
        assert (
            tool.schema
            == 'CREATE TABLE employees (\n                    "id" INTEGER, "name" TEXT, "department" TEXT, "salary" INTEGER\n                )'  # noqa: W503
        )
        assert not tool.enable_commit  # must be False by default

        # Create an agent with the SQL tool
        agent = AgentFactory.create(
            name="SQL Query Agent",
            description="I am an agent that helps query employee information from a database.",
            instructions="Help users query employee information from the database. Use SQL queries to get the requested information.",
            tools=[tool],
        )
        assert agent is not None

        # Test 1: Basic SELECT query
        response = agent.run("Who are all the employees in the Sales department?")
        assert response["completed"] is True
        assert response["status"].lower() == "success"
        assert "alice" in response["data"]["output"].lower()
        assert "charlie" in response["data"]["output"].lower()

        # Test 2: Aggregation query
        response = agent.run("What is the average salary in each department?")
        assert response["completed"] is True
        assert response["status"].lower() == "success"
        assert "sales" in response["data"]["output"].lower()
        assert "it" in response["data"]["output"].lower()
        assert "marketing" in response["data"]["output"].lower()

        # Test 3: Complex query with conditions
        response = agent.run("Who is the highest paid employee in the IT department?")
        assert response["completed"] is True
        assert response["status"].lower() == "success"
        assert "eve" in response["data"]["output"].lower()

    finally:
        # Cleanup
        os.remove("test.csv")
        os.remove("test.db")
        agent.delete()
