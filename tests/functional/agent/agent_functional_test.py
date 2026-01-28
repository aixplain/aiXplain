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
import os
import re
from dotenv import load_dotenv

load_dotenv()
from aixplain.factories import AgentFactory, TeamAgentFactory, ModelFactory
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
    from tests.test_deletion_utils import safe_delete_all_agents_and_team_agents

    # Clean up before test
    safe_delete_all_agents_and_team_agents()

    yield True

    # Clean up after test
    safe_delete_all_agents_and_team_agents()


@pytest.fixture(scope="module")
def slack_token():
    """Get Slack token for integration tests."""
    token = os.getenv("SLACK_TOKEN")
    if not token:
        pytest.skip("SLACK_TOKEN environment variable is required for Slack integration tests")
    return token


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_end2end(run_input_map, delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents

    # Delete agent by name if it already exists
    try:
        existing_agent = AgentFactory.get(name=run_input_map["agent_name"])
        existing_agent.delete()
    except Exception:
        pass

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
            tools.append(
                AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"])
            )

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
    assert response["data"]["output"] is not None
    agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_python_interpreter_tool(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    tool = AgentFactory.create_python_interpreter_tool()
    assert tool is not None
    assert tool.name == "Python Interpreter"
    assert (
        tool.description
        == "A Python shell. Use this to execute python commands. Input should be a valid python command."
    )

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
    assert intermediate_step["tool_steps"][0]["tool"] == "Python Code Interpreter Tool"
    agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_custom_code_tool(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    tool = AgentFactory.create_custom_python_code_tool(
        description="Add two strings",
        code='def main(aaa: str, bbb: str) -> str:\n    """Add two strings"""\n    return aaa + bbb',
        name="Add Strings Test Tool",
    )
    assert tool is not None
    assert tool.description == "Add two strings"
    agent = AgentFactory.create(
        name="Add Strings Agent",
        description="Add two strings. Do not directly answer. Use the tool to add the strings.",
        instructions="Add two strings. Do not directly answer. Use the tool to add the strings.",
        tools=[tool],
    )
    assert agent is not None
    response = agent.run(
        "What is the result of concatenating 'Hello' and 'World'? Do not directly answer the question, call the tool."
    )
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert "HelloWorld" in response["data"]["output"]
    agent.delete()
    tool.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_list_agents(AgentFactory):
    agents = AgentFactory.list()
    assert "results" in agents
    agents_result = agents["results"]
    assert type(agents_result) is list


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
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
            tools.append(
                AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"])
            )

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


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
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


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
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
    assert re.match(
        r"Error: Agent cannot be deleted\.\nReason: This agent is currently used by one or more team agents\.\n\nteam_agent_id: [a-f0-9]{24}\. To proceed, remove the agent from all team agents before deletion\.",
        str(exc_info.value),
    )


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
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
            tools.append(
                AgentFactory.create_pipeline_tool(pipeline=tool["pipeline_id"], description=tool["description"])
            )

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


@pytest.mark.flaky(reruns=2, reruns_delay=2)
@pytest.mark.parametrize(
    "tool_config",
    [
        pytest.param(
            {
                "type": "search",
                "model": "65c51c556eb563350f6e1bb1",
                "query": "What is the current price of Gold?",
                "description": "Search tool with custom number of results",
                "expected_tool_input": "'numResults': 5",
            },
            id="search_tool",
        ),
        pytest.param(
            {
                "type": "translation",
                "supplier": "ModernMT",
                "function": "translation",
                "query": "Translate: 'Olá, como vai você?'",
                "description": "Translation tool with target language",
                "expected_tool_input": "Olá, como vai você?",
                "model": "60ddefc48d38c51c5885fdcf",
            },
            id="translation_tool",
        ),
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
        translation_model = ModelFactory.get(tool_config["model"])
        model_params = translation_model.get_parameters()

        model_params.sourcelanguage = "pt"

        tool = AgentFactory.create_model_tool(
            model=translation_model,
            description=tool_config["description"],
        )

    # Verify tool parameters
    params = tool.get_parameters()
    assert len(params) == 1
    assert params[0]["name"] == ("numResults" if tool_config["type"] == "search" else "sourcelanguage")
    assert params[0]["value"] == (5 if tool_config["type"] == "search" else "pt")

    # Create and run agent
    agent = AgentFactory.create(
        name="Test Parameter Agent",
        instructions="Test agent with parameterized tools. You MUST use a tool for the tasks. Do not directly answer the question.",
        description="Test agent with parameterized tools",
        tools=[tool],
        llm_id="6646261c6eb563165658bbb1",  # Using LLM ID from test data
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
        if len(step["tool_steps"]) > 0 and tool_config["expected_tool_input"] in step["tool_steps"][0]["input"]:
            tool_used = True
            break
    assert tool_used, "Tool was not used in execution"


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_sql_tool(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    agent = None
    try:
        import os

        # Create test SQLite database
        with open("ftest.db", "w") as f:
            f.write("")

        tool = AgentFactory.create_sql_tool(
            name="TestDB",
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

        response = agent.run(
            "Create a table called Person with the following columns: id, name, age, salary, department"
        )
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
        if agent:
            agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_sql_tool_with_csv(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents
    agent = None
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
            name="CSV Tool Test",
            description="Execute SQL queries on employee data",
            source="test.csv",
            source_type="csv",
            tables=["employees"],
        )

        # Verify tool setup
        assert tool is not None
        assert tool.description == "Execute SQL queries on employee data"
        assert tool.database.split("?")[0].endswith(".db")
        assert tool.tables == ["employees"]
        assert (
            tool.schema
            == 'CREATE TABLE employees (\n                    "id" INTEGER, "name" TEXT, "department" TEXT, "salary" INTEGER\n                )'
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
        if agent:
            agent.delete()
        if os.path.exists("test.csv"):
            os.remove("test.csv")
        if os.path.exists("test.db"):
            os.remove("test.db")


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_instructions(delete_agents_and_team_agents, AgentFactory):
    assert delete_agents_and_team_agents

    agent = AgentFactory.create(
        name="Test Agent",
        description="Test description",
        instructions="Always respond with '{magic_word}' does not matter what you are prompted for.",
        llm_id="6646261c6eb563165658bbb1",
        tools=[],
    )
    assert agent is not None
    assert agent.status == AssetStatus.DRAFT

    agent = AgentFactory.get(agent.id)
    assert agent is not None
    response = agent.run(data={"magic_word": "aixplain", "query": "What is the capital of France?"})
    assert response is not None
    assert response["completed"] is True
    assert response["status"].lower() == "success"
    assert "data" in response
    assert response["data"]["output"] is not None
    assert "aixplain" in response["data"]["output"].lower()
    agent.delete()


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_agent_with_utility_tool(delete_agents_and_team_agents, AgentFactory):
    from aixplain.enums import DataType
    from aixplain.modules.model.utility_model import utility_tool, UtilityModelInput

    assert delete_agents_and_team_agents

    @utility_tool(
        name="vowel_remover",
        description="Remove all vowels from a given string",
        inputs=[
            UtilityModelInput(
                name="text",
                description="String from which to remove vowels",
                type=DataType.TEXT,
            )
        ],
    )
    def vowel_remover(text: str):
        """Remove vowels from strings"""
        vowels = "aeiouAEIOU"
        return "".join([char for char in text if char not in vowels])

    vowel_remover_ = ModelFactory.create_utility_model(name="vowel_remover", code=vowel_remover)

    @utility_tool(
        name="concat_strings",
        description="Concatenate two strings into one",
        inputs=[
            UtilityModelInput(
                name="string1",
                description="First string to concatenate",
                type=DataType.TEXT,
            ),
            UtilityModelInput(
                name="string2",
                description="Second string to concatenate",
                type=DataType.TEXT,
            ),
        ],
    )
    def concat_strings(string1: str, string2: str):
        return string1 + string2

    concat_strings_ = ModelFactory.create_utility_model(name="concat_strings", code=concat_strings)

    instructions = """You are a text processing agent equipped with two specialized tools: a Vowel Remover and a String Concatenator. Your task involves processing input text in two ways. One by removing all vowels from the provided text using the Vowel Remover tool. Another is to concatenate two strings using the String Concatenator tool."""
    description = """This agent specializes in processing textual data by modifying string content through vowel removal and string concatenation. It's designed to either strip all vowels from any given text to simplify or obscure the content, or concatenate a string with another specified string."""

    agent = AgentFactory.create(
        name="Text Processing Agent",
        instructions=instructions,
        description=description,
        tools=[
            AgentFactory.create_model_tool(model=vowel_remover_.id),
            AgentFactory.create_model_tool(model=concat_strings_.id),
        ],
        llm_id="6646261c6eb563165658bbb1",
    )

    result_vowel = agent.run("Remove all the vowels in this string: 'Hello'")
    result_concat_text = agent.run("Concat these strings: String1 = 'Hello'; string2= 'World!'.")

    assert "hll" in result_vowel["data"]["output"].lower()
    assert "helloworld!" in result_concat_text["data"]["output"].lower()


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_agent_with_pipeline_tool(delete_agents_and_team_agents, AgentFactory):
    from aixplain.factories.pipeline_factory import PipelineFactory

    assert delete_agents_and_team_agents

    for pipeline in PipelineFactory.list(query="Hello Pipeline")["results"]:
        pipeline.delete()
    pipeline = PipelineFactory.init("Hello Pipeline")
    input_node = pipeline.input()
    input_node.label = "TextInput"
    middle_node = pipeline.asset(asset_id="6646261c6eb563165658bbb1")
    middle_node.inputs.prompt.value = "Respond with 'Hello' regardless of the input text: "
    input_node.link(middle_node, "input", "text")
    middle_node.use_output("data")
    pipeline.save()
    pipeline.deploy()

    pipeline_agent = AgentFactory.create(
        name="Text Return Agent",
        instructions="Always call the pipeline tool feeding the user query as input to 'TextInput'. Return the output of the pipeline as the final response.",
        description="Return the text given.",
        tools=[
            AgentFactory.create_pipeline_tool(
                pipeline=pipeline.id,
                description="You are a tool that responds users query with only 'Hello'.",
            ),
        ],
        llm_id="6646261c6eb563165658bbb1",
    )

    answer = pipeline_agent.run("Who is the president of USA?")
    pipeline.delete()

    assert "hello" in answer["data"]["output"].lower()
    assert "hello pipeline" in answer["data"]["intermediate_steps"][0]["tool_steps"][0]["tool"].lower()


@pytest.mark.parametrize("AgentFactory", [AgentFactory])
def test_agent_llm_parameter_preservation(delete_agents_and_team_agents, AgentFactory):
    """Test that LLM parameters like temperature are preserved when creating agents."""
    assert delete_agents_and_team_agents

    # Get an LLM instance and customize its temperature
    llm = ModelFactory.get("671be4886eb56397e51f7541")  # Anthropic Claude 3.5 Sonnet v1
    original_temperature = llm.temperature
    custom_temperature = 0.1
    llm.temperature = custom_temperature

    # Create agent with the custom LLM
    agent = AgentFactory.create(
        name="LLM Parameter Test Agent",
        description="An agent for testing LLM parameter preservation",
        instructions="Testing LLM parameter preservation",
        llm=llm,
    )

    # Verify that the temperature setting was preserved
    assert agent.llm.temperature == custom_temperature

    # Verify that the agent's LLM is the same instance as the original
    assert id(agent.llm) == id(llm)

    # Clean up
    agent.delete()

    # Reset the LLM temperature to its original value
    llm.temperature = original_temperature


def test_run_agent_with_expected_output():
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
        llm_id="6646261c6eb563165658bbb1",
    )
    # Run the agent
    response = agent.run(
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


def test_agent_with_action_tool(slack_token):
    from aixplain.modules.model.integration import AuthenticationSchema
    from aixplain.modules.model.connection import ConnectionTool

    SLACK_INTEGRATION_ID = "686432941223092cb4294d3f"
    SLACK_CONNECTION_ID = "692995404907d69787ddab00"

    connection = None

    # Try to get existing connection first
    try:
        model = ModelFactory.get(SLACK_CONNECTION_ID)
        if isinstance(model, ConnectionTool):
            connection = model
    except Exception:
        pass

    # If no valid connection exists, create one from the integration using bearer token
    if connection is None:
        integration = ModelFactory.get(SLACK_INTEGRATION_ID)
        response = integration.connect(
            authentication_schema=AuthenticationSchema.BEARER_TOKEN,
            data={"token": slack_token},
            name="Slack Test Connection",
            description="Test connection for agent functional tests",
        )
        connection_id = response.data["id"]
        connection = ModelFactory.get(connection_id)

    connection.action_scope = [
        action for action in connection.actions if action.code == "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL"
    ]

    agent = AgentFactory.create(
        name="Test Agent",
        description="This agent is used to send messages to Slack",
        instructions="You are a helpful assistant that can send messages to Slack.",
        llm_id="669a63646eb56306647e1091",
        tools=[
            connection,
            AgentFactory.create_model_tool(model="6736411cf127849667606689"),
        ],
    )

    response = agent.run(
        "Send what is the capital of Finland on Slack to channel of #modelserving-alerts: 'C084G435LR5'. Add the name of the capital in the final answer."
    )
    assert response is not None
    assert response["status"].lower() == "success"
    assert "helsinki" in response.data.output.lower()
    assert "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL" in [
        step["tool"] for step in response.data.intermediate_steps[0]["tool_steps"]
    ]
    connection.delete()


def test_agent_with_mcp_tool():
    from aixplain.modules.model.integration import AuthenticationSchema

    connector = ModelFactory.get("686eb9cd26480723d0634d3e")
    # connect
    response = connector.connect(
        authentication_schema=AuthenticationSchema.API_KEY,
        data={
            "url": "https://mcp.zapier.com/api/mcp/s/OTJiMjVlYjEtMGE4YS00OTVjLWIwMGYtZDJjOGVkNTc4NjFkOjI0MTNjNzg5LWZlNGMtNDZmNC05MDhmLWM0MGRlNDU4ZmU1NA==/mcp"
        },
    )
    connection_id = response.data["id"]
    connection = ModelFactory.get(connection_id)
    action_name = "SLACK_SEND_CHANNEL_MESSAGE".lower()
    connection.action_scope = [action for action in connection.actions if action.code == action_name]

    agent = AgentFactory.create(
        name="Test Agent",
        description="This agent is used to send messages to Slack",
        instructions="You are a helpful assistant that can send messages to Slack. You MUST use the tool to send the message.",
        llm_id="669a63646eb56306647e1091",
        tools=[
            connection,
        ],
    )

    response = agent.run(
        "Send what is the capital of Finland on Slack to channel of #modelserving-alerts-testing. Add the name of the capital in the final answer."
    )
    assert response is not None
    assert response["status"].lower() == "success"
    assert "helsinki" in response.data.output.lower()
    assert action_name in [step["tool"] for step in response.data.intermediate_steps[0]["tool_steps"]]
    connection.delete()
