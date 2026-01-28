import pytest
import requests_mock
from aixplain.factories import AgentFactory
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules import Agent, Model
from aixplain.modules.agent import OutputFormat
from aixplain.utils import config
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.python_interpreter_tool import PythonInterpreterTool
from aixplain.modules.agent.utils import process_variables
from aixplain.modules.model.connection import ConnectionTool
from urllib.parse import urljoin
from unittest.mock import patch
from aixplain.enums import Function, Supplier
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData
from pydantic import BaseModel
import json


def test_fail_no_data_query():
    agent = Agent(
        "123",
        "Test Agent(-)",
        "Sample Description",
        instructions="Test Agent Instructions",
    )
    with pytest.raises(Exception) as exc_info:
        agent.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_must_be_provided():
    agent = Agent(
        "123",
        "Test Agent",
        "Sample Description",
        instructions="Test Agent Instructions",
    )
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={})
    assert str(exc_info.value) == "When providing a dictionary, 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    agent = Agent(
        "123",
        "Test Agent",
        "Sample Description",
        instructions="Test Agent Instructions",
    )
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=[
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            ],
        )

    assert str(exc_info.value) == "When providing 'content', query must be text."


def test_fail_content_exceed_maximum():
    agent = Agent(
        "123",
        "Test Agent",
        "Sample Description",
        instructions="Test Agent Instructions",
    )
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
            data={"query": "Transcribe the audios:"},
            content=[
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            ],
        )
    assert str(exc_info.value) == "The maximum number of content inputs is 3."


def test_fail_key_not_found():
    agent = Agent(
        "123",
        "Test Agent",
        "Sample Description",
        instructions="Test Agent Instructions",
    )
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
            data={"query": "Translate the text: {{input1}}"},
            content={"input2": "Hello, how are you?"},
        )
    assert str(exc_info.value) == "Key 'input2' not found in query."


def test_success_query_content():
    agent = Agent(
        "123",
        "Test Agent(-)",
        "Sample Description",
        instructions="Test Agent Instructions",
    )
    with requests_mock.Mocker() as mock:
        url = agent.url
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"data": "Hello, how are you?", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(
            data={"query": "Translate the text: {{input1}}"},
            content={"input1": "Hello, how are you?"},
        )
    assert isinstance(response, AgentResponse)
    assert response["status"] == ref_response["status"]
    assert isinstance(response.data, AgentResponseData)
    assert response["url"] == ref_response["data"]


def test_invalid_pipelinetool(mocker):
    mocker.patch(
        "aixplain.factories.model_factory.ModelFactory.get",
        return_value=Model(
            id="6646261c6eb563165658bbb1",
            name="Test Model",
            function=Function.TEXT_GENERATION,
        ),
    )
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test",
            description="Test Description",
            instructions="Test Instructions",
            tools=[PipelineTool(pipeline="309851793", description="Test")],
            llm_id="6646261c6eb563165658bbb1",
        )
    assert (
        str(exc_info.value)
        == "Pipeline Tool Unavailable. Make sure Pipeline '309851793' exists or you have access to it."
    )


def test_invalid_llm_id():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="Test", description="", instructions="", tools=[], llm_id="123")
    assert str(exc_info.value) == "Large Language Model with ID '123' not found."


def test_invalid_agent_name():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="[Test]",
            description="",
            instructions="",
            tools=[],
            llm_id="6646261c6eb563165658bbb1",
        )
    assert str(exc_info.value) == (
        "Agent Creation Error: Agent name contains invalid characters. "
        "Only alphanumeric characters, spaces, hyphens, and brackets are allowed."
    )


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_create_agent(mock_model_factory_get):
    from aixplain.enums import Supplier, Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
    )
    mock_model_factory_get.return_value = mock_model

    with requests_mock.Mocker() as mock:
        with patch(
            "aixplain.modules.model.utils.parse_code",
            return_value=(
                "utility_model_test",
                [],
                "utility_model_test",
                "test_name",
            ),
        ):
            url = urljoin(config.BACKEND_URL, "sdk/agents")
            headers = {
                "x-api-key": config.TEAM_API_KEY,
                "Content-Type": "application/json",
            }

            ref_response = {
                "id": "123",
                "name": "Test Agent(-)",
                "description": "Test Agent Description",
                "instructions": "Test Agent Instruction",
                "teamId": "123",
                "version": "1.0",
                "status": "draft",
                "llmId": "6646261c6eb563165658bbb1",
                "pricing": {"currency": "USD", "value": 0.0},
                "assets": [
                    {
                        "type": "model",
                        "description": "Test Tool",
                        "name": "text-generation-openai",
                        "parameters": [],
                        "function": "text-generation",
                        "supplier": {"id": 529, "name": "openai", "code": "openai"},
                        "version": None,
                        "assetId": None,
                        "actions": [],
                    },
                    {
                        "type": "utility",
                        "description": "A Python shell. Use this to execute python commands. Input should be a valid python command.",
                        "name": None,
                        "parameters": None,
                        "utility": "custom_python_code",
                        "utilityCode": None,
                    },
                    {
                        "type": "model",
                        "description": "Test Script Connection Tool description",
                        "name": "Test Script Connection Tool",
                        "parameters": [],
                        "function": "utilities",
                        "supplier": {"id": 1, "name": "aixplain", "code": "aixplain"},
                        "version": "pythonscript",
                        "assetId": "693026cc427d05e696f3c7db",
                        "actions": ["print_hello_world"],
                    },
                ],
            }
            mock.post(url, headers=headers, json=ref_response)

            url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
            model_ref_response = {
                "id": "6646261c6eb563165658bbb1",
                "name": "Test LLM",
                "description": "Test LLM Description",
                "function": {"id": "text-generation"},
                "supplier": "openai",
                "version": {"id": "1.0"},
                "status": "onboarded",
                "pricing": {"currency": "USD", "value": 0.0},
            }
            mock.get(url, headers=headers, json=model_ref_response)

            # Mock the Python sandbox integration model fetch
            python_sandbox_id = "688779d8bfb8e46c273982ca"
            url = urljoin(config.BACKEND_URL, f"sdk/models/{python_sandbox_id}")
            python_sandbox_response = {
                "id": python_sandbox_id,
                "name": "Python Sandbox",
                "description": "Python Sandbox Integration",
                "function": {"id": "utilities"},
                "functionType": "connector",
                "supplier": "aixplain",
                "version": {"id": "pythonscript"},
                "status": "onboarded",
                "pricing": {"currency": "USD", "value": 0.0},
                "authentication_methods": ["no-auth"],
                "params": [],
                "attributes": [
                    {"name": "auth_schemes", "code": '["NO_AUTH"]'},
                    {
                        "name": "NO_AUTH-inputs",
                        "code": '[{"name":"code","displayName":"Python Code","type":"string","description":"","required":true, "subtype": "file", "fileConfiguration": { "limit": 1, "extensions": ["py"] }}, {"name":"function_name","displayName":"Main Function Name","type":"string","description":"","required":true}]',
                    },
                ],
            }
            mock.get(url, headers=headers, json=python_sandbox_response)

            # Mock the POST request to create the connection (when connect() calls run())
            connection_id = "693026cc427d05e696f3c7db"
            run_url = f"{config.MODELS_RUN_URL}/{python_sandbox_id}".replace("api/v1/execute", "api/v2/execute")
            run_response = {
                "status": "SUCCESS",
                "completed": True,
                "data": {"id": connection_id},
            }
            mock.post(run_url, headers=headers, json=run_response)

            # Mock the GET request to fetch the created connection
            connection_url = urljoin(config.BACKEND_URL, f"sdk/models/{connection_id}")
            connection_response = {
                "id": connection_id,
                "name": "Test Script Connection Tool",
                "description": "Test Script Connection Tool description",
                "function": {"id": "utilities"},
                "functionType": "connection",
                "supplier": "aixplain",
                "version": {"id": "pythonscript"},
                "status": "onboarded",
                "pricing": {"currency": "USD", "value": 0.0},
                "params": [],
            }
            mock.get(connection_url, headers=headers, json=connection_response)

            # Mock the POST request to list actions (when ConnectionTool.__init__ calls _get_actions())
            list_actions_url = f"{config.MODELS_RUN_URL}/{connection_id}".replace("api/v1/execute", "api/v2/execute")
            list_actions_response = {
                "status": "SUCCESS",
                "completed": True,
                "data": [
                    {"name": "print_hello_world", "displayName": "print_hello_world", "description": "Test function"}
                ],
            }
            mock.post(list_actions_url, headers=headers, json=list_actions_response)

            agent = AgentFactory.create(
                name="Test Agent(-)",
                description="Test Agent Description",
                instructions="Test Agent Instructions",
                llm_id="6646261c6eb563165658bbb1",
                tools=[
                    AgentFactory.create_model_tool(
                        supplier=Supplier.OPENAI,
                        function="text-generation",
                        description="Test Tool",
                    ),
                    AgentFactory.create_python_interpreter_tool(),
                    AgentFactory.create_custom_python_code_tool(
                        name="Test Script Connection Tool",
                        code="def print_hello_world(input_string: str) -> str:\n    return 'Hello, world!'\n",
                        description="Test Script Connection Tool description",
                    ),
                ],
            )

    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert agent.instructions == ref_response["instructions"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]
    assert agent.tools[0].description == ref_response["assets"][0]["description"]
    assert isinstance(agent.tools[0], ModelTool)
    assert agent.tools[1].description == ref_response["assets"][1]["description"]
    assert isinstance(agent.tools[1], PythonInterpreterTool)
    assert agent.tools[2].description == ref_response["assets"][2]["description"]
    assert isinstance(agent.tools[2], ConnectionTool)
    assert agent.status == AssetStatus.DRAFT


def test_to_dict():
    agent = Agent(
        id="",
        name="Test Agent(-)",
        description="Test Agent Description",
        instructions="Test Agent Instructions",
        llm_id="6646261c6eb563165658bbb1",
        tools=[AgentFactory.create_model_tool(function="text-generation")],
        api_key="test_api_key",
        status=AssetStatus.DRAFT,
    )

    agent_json = agent.to_dict()
    assert agent_json["id"] == ""
    assert agent_json["name"] == "Test Agent(-)"
    assert agent_json["description"] == "Test Agent Description"
    assert agent_json["instructions"] == "Test Agent Instructions"
    assert agent_json["llmId"] == "6646261c6eb563165658bbb1"
    assert agent_json["assets"][0]["function"] == "text-generation"
    assert agent_json["assets"][0]["type"] == "model"
    assert agent_json["status"] == "draft"


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_update_success(mock_model_factory_get):
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
    )
    mock_model_factory_get.return_value = mock_model

    agent = Agent(
        id="123",
        name="Test Agent(-)",
        description="Test Agent Description",
        instructions="Test Agent Instructions",
        llm_id="6646261c6eb563165658bbb1",
        tools=[AgentFactory.create_model_tool(function="text-generation")],
    )

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {
            "id": "123",
            "name": "Test Agent(-)",
            "description": "Test Agent Description",
            "instructions": "Test Agent Instructions",
            "teamId": "123",
            "version": "1.0",
            "status": "onboarded",
            "llmId": "6646261c6eb563165658bbb1",
            "pricing": {"currency": "USD", "value": 0.0},
            "assets": [
                {
                    "type": "model",
                    "supplier": "openai",
                    "version": "1.0",
                    "assetId": "6646261c6eb563165658bbb1",
                    "function": "text-generation",
                }
            ],
        }
        mock.put(url, headers=headers, json=ref_response)

        url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
        model_ref_response = {
            "id": "6646261c6eb563165658bbb1",
            "name": "Test LLM",
            "description": "Test LLM Description",
            "function": {"id": "text-generation"},
            "supplier": "openai",
            "version": {"id": "1.0"},
            "status": "onboarded",
            "pricing": {"currency": "USD", "value": 0.0},
        }
        mock.get(url, headers=headers, json=model_ref_response)

        # Capture warnings
        with pytest.warns(
            DeprecationWarning,
            match="update\(\) is deprecated and will be removed in a future version. Please use save\(\) instead.",  # noqa: W605
        ):
            agent.update()

    assert agent.id == ref_response["id"]
    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert agent.instructions == ref_response["instructions"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_save_success(mock_model_factory_get):
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
    )
    mock_model_factory_get.return_value = mock_model

    agent = Agent(
        id="123",
        name="Test Agent(-)",
        description="Test Agent Description",
        instructions="Test Agent Instructions",
        llm_id="6646261c6eb563165658bbb1",
        tools=[AgentFactory.create_model_tool(function="text-generation")],
    )

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {
            "id": "123",
            "name": "Test Agent(-)",
            "description": "Test Agent Description",
            "instructions": "Test Agent Instructions",
            "teamId": "123",
            "version": "1.0",
            "status": "onboarded",
            "llmId": "6646261c6eb563165658bbb1",
            "pricing": {"currency": "USD", "value": 0.0},
            "assets": [
                {
                    "type": "model",
                    "supplier": "openai",
                    "version": "1.0",
                    "assetId": "6646261c6eb563165658bbb1",
                    "function": "text-generation",
                }
            ],
        }
        mock.put(url, headers=headers, json=ref_response)

        url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
        model_ref_response = {
            "id": "6646261c6eb563165658bbb1",
            "name": "Test LLM",
            "description": "Test LLM Description",
            "function": {"id": "text-generation"},
            "supplier": "openai",
            "version": {"id": "1.0"},
            "status": "onboarded",
            "pricing": {"currency": "USD", "value": 0.0},
        }
        mock.get(url, headers=headers, json=model_ref_response)

        import warnings

        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")  # Trigger all warnings

            # Call the save method
            agent.save()

            # Assert no warnings were triggered
            assert len(w) == 0, f"Warnings were raised: {[str(warning.message) for warning in w]}"

    assert agent.id == ref_response["id"]
    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert agent.instructions == ref_response["instructions"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]


def test_run_success():
    agent = Agent(
        "123",
        "Test Agent(-)",
        "Sample Description",
        instructions="Test Agent Instructions",
    )
    url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    agent.url = url
    with requests_mock.Mocker() as mock:
        headers = {
            "x-api-key": config.AIXPLAIN_API_KEY,
            "Content-Type": "application/json",
        }

        ref_response = {"data": "www.aixplain.com", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(
            data={"query": "Hello, how are you?"},
            max_iterations=10,
            output_format=OutputFormat.MARKDOWN,
        )
    assert isinstance(response, AgentResponse)
    assert response["status"] == "IN_PROGRESS"
    assert response["url"] == ref_response["data"]


def test_run_variable_missing():
    """Test that agent runs successfully even when variables are missing from data/parameters."""
    agent = Agent(
        "123",
        "Test Agent",
        "Agent description",
        instructions="Translate the input data into {target_language}",
    )

    # Mock the agent URL and response
    url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    agent.url = url

    with requests_mock.Mocker() as mock:
        headers = {
            "x-api-key": config.AIXPLAIN_API_KEY,
            "Content-Type": "application/json",
        }
        ref_response = {"data": "www.aixplain.com", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        # This should not raise an exception anymore - missing variables are silently ignored
        response = agent.run_async(data={"query": "Hello, how are you?"}, output_format=OutputFormat.MARKDOWN)

    # Verify the response is successful
    assert isinstance(response, AgentResponse)
    assert response["status"] == "IN_PROGRESS"
    assert response["url"] == ref_response["data"]


def test_process_variables():
    query = "Hello, how are you?"
    data = {"target_language": "English"}
    agent_description = "Translate the input data into {target_language}"
    assert process_variables(query=query, data=data, parameters={}, agent_description=agent_description) == {
        "input": "Hello, how are you?",
        "target_language": "English",
    }


def test_fail_utilities_without_model():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test",
            tools=[ModelTool(function=Function.UTILITIES)],
            llm_id="6646261c6eb563165658bbb1",
        )
    assert str(exc_info.value) == "Agent Creation Error: Utility function must be used with an associated model."


def test_agent_api_key_propagation():
    """Test that the api_key is properly propagated to tools when creating an agent"""
    custom_api_key = "custom_test_key"
    tool = AgentFactory.create_model_tool(function="text-generation")
    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Description",
        instructions="Test Agent Instructions",
        tools=[tool],
        api_key=custom_api_key,
    )

    # Check that the agent has the correct api_key
    assert agent.api_key == custom_api_key
    # Check that the tool received the agent's api_key
    assert agent.tools[0].api_key == custom_api_key


def test_agent_default_api_key():
    """Test that the default api_key is used when none is provided"""
    tool = AgentFactory.create_model_tool(function="text-generation")
    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Description",
        instructions="Test Agent Instructions",
        tools=[tool],
    )

    # Check that the agent has the default api_key
    assert agent.api_key == config.TEAM_API_KEY
    # Check that the tool has the default api_key
    assert agent.tools[0].api_key == config.TEAM_API_KEY


def test_agent_optional_instructions():
    """Test that Agent can be created with optional instructions"""
    agent = Agent(id="123", name="Test Agent", description="Test Description")

    # Check that the agent was created successfully
    assert agent.id == "123"
    assert agent.name == "Test Agent"
    assert agent.description == "Test Description"
    assert agent.instructions is None


def test_agent_factory_create_without_instructions():
    """Test AgentFactory.create() payload when no instructions are provided"""
    from aixplain.factories import AgentFactory
    from unittest.mock import patch
    import requests_mock
    from urllib.parse import urljoin
    from aixplain.utils import config

    with patch("aixplain.factories.model_factory.ModelFactory.get") as mock_model_factory_get:
        from aixplain.enums import Function
        from aixplain.modules.model import Model

        # Mock the LLM model
        mock_model = Model(
            id="6646261c6eb563165658bbb1",
            name="Test LLM",
            description="Test LLM Description",
            function=Function.TEXT_GENERATION,
        )
        mock_model_factory_get.return_value = mock_model

        with requests_mock.Mocker() as mock:
            url = urljoin(config.BACKEND_URL, "sdk/agents")
            headers = {"x-api-key": config.TEAM_API_KEY}

            # Mock response from server
            ref_response = {
                "id": "123",
                "name": "Test Agent",
                "description": "Test Agent Description",
                "instructions": "Test Agent Description",  # Should fallback to description
                "teamId": "123",
                "version": "1.0",
                "status": "draft",
                "llmId": "6646261c6eb563165658bbb1",
                "assets": [],
            }
            mock.post(url, headers=headers, json=ref_response)

            # Mock LLM GET request
            url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
            model_ref_response = {
                "id": "6646261c6eb563165658bbb1",
                "name": "Test LLM",
                "description": "Test LLM Description",
                "function": {"id": "text-generation"},
                "supplier": "openai",
                "version": {"id": "1.0"},
                "status": "onboarded",
                "pricing": {"currency": "USD", "value": 0.0},
            }
            mock.get(url, headers=headers, json=model_ref_response)

            # Create agent without instructions
            agent = AgentFactory.create(
                name="Test Agent",
                description="Test Agent Description",
                # No instructions parameter
                llm_id="6646261c6eb563165658bbb1",
            )

            # Verify the agent was created with fallback instructions
            assert agent.instructions == "Test Agent Description"  # Should fallback to description
            assert agent.name == "Test Agent"
            assert agent.description == "Test Agent Description"

            # Check the request payload that was sent
            sent_request = mock.request_history[0]
            sent_payload = sent_request.json()

            # The Instructions should be set to description when instructions is None
            assert sent_payload["instructions"] == "Test Agent Description"
            assert sent_payload["description"] == "Test Agent Description"


def test_agent_to_dict_payload_without_instructions():
    """Test Agent.to_dict() payload when instructions is None"""
    # Create agent with no instructions
    agent = Agent(id="123", name="Test Agent", description="Test Description")

    # Get the payload
    payload = agent.to_dict()

    # Check that Instructions falls back to description when instructions is None
    assert payload["instructions"] == "Test Description"  # Should fallback to description
    assert payload["description"] == "Test Description"
    assert agent.instructions is None


def test_agent_to_dict_payload_with_instructions():
    """Test Agent.to_dict() payload when instructions is provided"""
    # Create agent with instructions
    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Description",
        instructions="Custom Instructions",
    )

    # Get the payload
    payload = agent.to_dict()

    # Check that Instructions uses instructions when provided
    assert payload["instructions"] == "Custom Instructions"
    assert payload["description"] == "Test Description"
    assert agent.instructions == "Custom Instructions"


def test_agent_factory_create_with_explicit_none_instructions():
    """Test AgentFactory.create() payload when instructions=None is explicitly passed"""
    from aixplain.factories import AgentFactory
    from unittest.mock import patch
    import requests_mock
    from urllib.parse import urljoin
    from aixplain.utils import config

    with patch("aixplain.factories.model_factory.ModelFactory.get") as mock_model_factory_get:
        from aixplain.enums import Function
        from aixplain.modules.model import Model

        # Mock the LLM model
        mock_model = Model(
            id="6646261c6eb563165658bbb1",
            name="Test LLM",
            description="Test LLM Description",
            function=Function.TEXT_GENERATION,
        )
        mock_model_factory_get.return_value = mock_model

        with requests_mock.Mocker() as mock:
            url = urljoin(config.BACKEND_URL, "sdk/agents")
            headers = {"x-api-key": config.TEAM_API_KEY}

            # Mock response from server
            ref_response = {
                "id": "123",
                "name": "Test Agent",
                "description": "Test Agent Description",
                "instructions": "Test Agent Description",  # Should fallback to description
                "teamId": "123",
                "version": "1.0",
                "status": "draft",
                "llmId": "6646261c6eb563165658bbb1",
                "assets": [],
            }
            mock.post(url, headers=headers, json=ref_response)

            # Mock LLM GET request
            url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
            model_ref_response = {
                "id": "6646261c6eb563165658bbb1",
                "name": "Test LLM",
                "description": "Test LLM Description",
                "function": {"id": "text-generation"},
                "supplier": "openai",
                "version": {"id": "1.0"},
                "status": "onboarded",
                "pricing": {"currency": "USD", "value": 0.0},
            }
            mock.get(url, headers=headers, json=model_ref_response)

            # Create agent with explicit instructions=None
            agent = AgentFactory.create(
                name="Test Agent",
                description="Test Agent Description",
                instructions=None,  # Explicitly set to None
                llm_id="6646261c6eb563165658bbb1",
            )

            # Verify the agent was created with fallback instructions
            assert agent.instructions == "Test Agent Description"  # Should fallback to description

            # Check the request payload that was sent
            sent_request = mock.request_history[0]
            sent_payload = sent_request.json()

            # The Instructions should be set to description when instructions is None
            assert sent_payload["instructions"] == "Test Agent Description"
            assert sent_payload["description"] == "Test Agent Description"


def test_agent_multiple_tools_api_key():
    """Test that api_key is properly propagated to multiple tools"""
    custom_api_key = "custom_test_key"
    tools = [
        AgentFactory.create_model_tool(function="text-generation"),
        AgentFactory.create_python_interpreter_tool(),
    ]

    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Description",
        instructions="Test Agent Instructions",
        tools=tools,
        api_key=custom_api_key,
    )

    # Check that all tools received the agent's api_key
    for tool in agent.tools:
        assert tool.api_key == custom_api_key


def test_agent_api_key_in_requests():
    """Test that the api_key is properly used in API requests"""
    custom_api_key = "custom_test_key"
    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Description",
        instructions="Test Agent Instructions",
        api_key=custom_api_key,
    )

    with requests_mock.Mocker() as mock:
        url = agent.url
        # The custom api_key should be used in the headers
        headers = {"x-api-key": custom_api_key, "Content-Type": "application/json"}
        ref_response = {"data": "test_url", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(data={"query": "Test query"})

        # Verify that the request was made with the correct api_key
        assert mock.last_request.headers["x-api-key"] == custom_api_key
        assert response["status"] == "IN_PROGRESS"
        assert response["url"] == "test_url"


def test_create_agent_task():
    task = AgentFactory.create_task(name="Test Task", description="Test Description", expected_output="Test Output")
    assert task.name == "Test Task"
    assert task.description == "Test Description"
    assert task.expected_output == "Test Output"
    assert task.dependencies == []

    task_dict = task.to_dict()
    assert task_dict["name"] == "Test Task"
    assert task_dict["description"] == "Test Description"
    assert task_dict["expectedOutput"] == "Test Output"
    assert task_dict["dependencies"] == []


def test_agent_response():
    from aixplain.modules.agent.agent_response import AgentResponse, AgentResponseData

    response = AgentResponse(
        data=AgentResponseData(
            input="input",
            output="output",
            intermediate_steps=[],
            execution_stats={},
            session_id="session_id",
        ),
        status="SUCCESS",
        url="test_url",
        details={"details": "test_details"},
    )
    # test getters
    assert response["data"]["input"] == "input"
    assert response.data.input == "input"
    assert response["data"]["output"] == "output"
    assert response.data.output == "output"
    assert response["data"]["intermediate_steps"] == []
    assert response.data.intermediate_steps == []
    assert response["data"]["execution_stats"] == {}
    assert response.data.execution_stats == {}
    assert response["data"]["session_id"] == "session_id"
    assert response.data.session_id == "session_id"
    assert response["status"] == "SUCCESS"
    assert response.status == "SUCCESS"
    assert response["url"] == "test_url"
    assert response["details"] == {"details": "test_details"}
    # test setters
    response["status"] = "FAILED"
    assert response.status == "FAILED"
    response.data["input"] = "new_input"
    assert response.data.input == "new_input"
    response.data.output = "new_output"
    assert response["data"]["output"] == "new_output"


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_create_agent_with_model_instance(mock_model_factory_get):
    from aixplain.enums import Supplier, Function
    from aixplain.modules.model.model_parameters import ModelParameters

    # Create model parameters
    model_params = {
        "temperature": {"required": True},
        "max_tokens": {"required": False},
    }

    # Create a Model instance to pass as a tool
    model_tool = Model(
        id="model123",
        name="Test Model",
        description="Test Model Description",
        supplier=Supplier.AIXPLAIN,
        function=Function.TEXT_GENERATION,
        version="1.0",
        model_params=model_params,
    )

    # Mock the LLM model factory response
    llm_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
        model_params=model_params,
    )

    def validate_side_effect(model_id, *args, **kwargs):
        if model_id == "model123":
            return model_tool
        elif model_id == "6646261c6eb563165658bbb1":
            return llm_model
        return None

    mock_model_factory_get.side_effect = validate_side_effect

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        ref_response = {
            "id": "123",
            "name": "Test Agent",
            "description": "Test Agent Description",
            "teamId": "123",
            "version": "1.0",
            "status": "draft",
            "llmId": "6646261c6eb563165658bbb1",
            "pricing": {"currency": "USD", "value": 0.0},
            "assets": [
                {
                    "type": "model",
                    "supplier": "aixplain",
                    "version": "1.0",
                    "assetId": "model123",
                    "function": "text-generation",
                    "description": "Test Model Description",
                }
            ],
        }
        mock.post(url, headers=headers, json=ref_response)

        url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
        model_ref_response = {
            "id": "6646261c6eb563165658bbb1",
            "name": "Test LLM",
            "description": "Test LLM Description",
            "function": {"id": "text-generation"},
            "supplier": "aixplain",
            "version": {"id": "1.0"},
            "status": "onboarded",
            "pricing": {"currency": "USD", "value": 0.0},
        }
        mock.get(url, headers=headers, json=model_ref_response)

        agent = AgentFactory.create(
            name="Test Agent",
            description="Test Agent Description",
            llm_id="6646261c6eb563165658bbb1",
            tools=[model_tool],
        )

    # Verify the agent was created correctly
    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert len(agent.tools) == 1

    # Verify the tool was converted correctly
    tool = agent.tools[0]
    assert isinstance(tool, Model)
    assert tool.id == "model123"
    assert tool.name == model_tool.name
    assert tool.function == model_tool.function
    assert tool.supplier == model_tool.supplier
    assert isinstance(tool.model_params, ModelParameters)
    assert tool.model_params.parameters["temperature"].required
    assert not tool.model_params.parameters["max_tokens"].required


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_create_agent_with_mixed_tools(mock_model_factory_get):
    from aixplain.enums import Supplier, Function
    from aixplain.modules import Model
    from aixplain.modules.model.model_parameters import ModelParameters

    # Create model parameters for different models
    text_gen_params = {
        "temperature": {"required": True},
        "max_tokens": {"required": False},
    }

    classification_params = {
        "threshold": {"required": True},
        "labels": {"required": True},
    }

    # Create a Model instance for the first tool
    model_tool = Model(
        id="model123",
        name="Test Model",
        description="Test Model Description",
        supplier=Supplier.AIXPLAIN,
        function=Function.TEXT_GENERATION,
        version="1.0",
        model_params=text_gen_params,
    )

    # Create a Model instance for the second tool
    openai_model = Model(
        id="openai-model",
        name="OpenAI Model",
        description="Regular Tool",
        supplier=Supplier.OPENAI,
        function=Function.TEXT_CLASSIFICATION,
        version="1.0",
        model_params=classification_params,
    )

    # Mock the LLM model factory response
    llm_model = Model(
        id="6646261c6eb563165658bbb1",
        name="Test LLM",
        description="Test LLM Description",
        function=Function.TEXT_GENERATION,
        model_params=text_gen_params,
    )

    # Mock the validate method to return different models based on the model ID
    def validate_side_effect(model_id, *args, **kwargs):
        if model_id == "model123":
            return model_tool
        elif model_id == "openai-model":
            return openai_model
        elif model_id == "6646261c6eb563165658bbb1":
            return llm_model
        return None

    mock_model_factory_get.side_effect = validate_side_effect

    # Create a regular ModelTool instance
    regular_tool = AgentFactory.create_model_tool(
        function=Function.TEXT_CLASSIFICATION,
        supplier=Supplier.OPENAI,
        model="openai-model",
        description="Regular Tool",
    )

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, "sdk/agents")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

        ref_response = {
            "id": "123",
            "name": "Test Agent",
            "description": "Test Agent Description",
            "teamId": "123",
            "version": "1.0",
            "status": "draft",
            "llmId": "6646261c6eb563165658bbb1",
            "pricing": {"currency": "USD", "value": 0.0},
            "assets": [
                {
                    "type": "model",
                    "supplier": "aixplain",
                    "version": "1.0",
                    "assetId": "model123",
                    "function": "text-generation",
                    "description": "Test Model Description",
                },
                {
                    "type": "model",
                    "supplier": "openai",
                    "version": "1.0",
                    "assetId": "openai-model",
                    "function": "text-classification",
                    "description": "Regular Tool",
                },
            ],
        }
        mock.post(url, headers=headers, json=ref_response)

        url = urljoin(config.BACKEND_URL, "sdk/models/6646261c6eb563165658bbb1")
        model_ref_response = {
            "id": "6646261c6eb563165658bbb1",
            "name": "Test LLM",
            "description": "Test LLM Description",
            "function": {"id": "text-generation"},
            "supplier": "aixplain",
            "version": {"id": "1.0"},
            "status": "onboarded",
            "pricing": {"currency": "USD", "value": 0.0},
        }
        mock.get(url, headers=headers, json=model_ref_response)

        agent = AgentFactory.create(
            name="Test Agent",
            description="Test Agent Description",
            llm_id="6646261c6eb563165658bbb1",
            tools=[model_tool, regular_tool],
        )

    # Verify the agent was created correctly
    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert len(agent.tools) == 2

    # Verify the first tool (Model instance converted to ModelTool)
    tool1 = agent.tools[0]
    assert isinstance(tool1, Model)
    assert tool1.id == "model123"
    assert tool1.name == model_tool.name
    assert tool1.function == model_tool.function
    assert tool1.supplier == model_tool.supplier
    assert isinstance(tool1.model_params, ModelParameters)
    assert tool1.model_params.parameters["temperature"].required
    assert not tool1.model_params.parameters["max_tokens"].required

    # Verify the second tool (regular ModelTool)
    tool2 = agent.tools[1]
    assert isinstance(tool2, ModelTool)
    assert tool2.model.id == "openai-model"
    assert tool2.function == Function.TEXT_CLASSIFICATION
    assert tool2.supplier == Supplier.OPENAI
    assert isinstance(tool2.model, Model)
    assert isinstance(tool2.model.model_params, ModelParameters)
    assert tool2.model.model_params.parameters["threshold"].required
    assert tool2.model.model_params.parameters["labels"].required


@pytest.mark.parametrize(
    "supplier_input,expected_supplier,should_fail",
    [
        ("aixplain", "AIXPLAIN", False),  # Basic case
        ("OpenAI", "OPENAI", False),  # Mixed case
        ("invalid-supplier", None, True),  # Invalid supplier case
    ],
)
def test_create_model_tool_with_text_supplier(supplier_input, expected_supplier, should_fail):
    from aixplain.enums import Function, Supplier

    if should_fail:
        with pytest.raises(Exception) as exc_info:
            tool = AgentFactory.create_model_tool(
                function=Function.TEXT_GENERATION,
                supplier=supplier_input,
                description="Test Tool",
            )
        assert supplier_input in str(exc_info.value)
    else:
        # Create ModelTool with supplier as text
        tool = AgentFactory.create_model_tool(
            function=Function.TEXT_GENERATION,
            supplier=supplier_input,
            description="Test Tool",
        )

        # Verify the tool was created correctly
        assert isinstance(tool.supplier, Supplier)
        assert tool.supplier.name == expected_supplier
        assert tool.function == Function.TEXT_GENERATION
        assert tool.description == "Test Tool"


def test_agent_response_repr():
    from aixplain.enums import ResponseStatus
    from aixplain.modules.agent.agent_response import AgentResponse, AgentResponseData

    # Test case 1: Basic representation
    response = AgentResponse(
        status=ResponseStatus.SUCCESS,
        data=AgentResponseData(input="test input"),
        completed=True,
    )
    repr_str = repr(response)

    # Verify the representation starts with "AgentResponse("
    assert repr_str.startswith("AgentResponse(")
    assert repr_str.endswith(")")

    # Verify key fields are present and correct
    assert "status=SUCCESS" in repr_str
    assert "completed=True" in repr_str

    # Test case 2: Complex representation with all fields
    response = AgentResponse(
        status=ResponseStatus.SUCCESS,
        data=AgentResponseData(
            input="test input",
            output="test output",
            session_id="test_session",
            intermediate_steps=["step1", "step2"],
            execution_stats={"time": 1.0},
        ),
        details={"test": "details"},
        completed=True,
        error_message="no error",
        used_credits=0.5,
        run_time=1.0,
        usage={"tokens": 100},
        url="http://test.url",
    )
    repr_str = repr(response)

    # Verify all fields are present and formatted correctly
    assert "status=SUCCESS" in repr_str
    assert "completed=True" in repr_str
    assert "error_message='no error'" in repr_str
    assert "used_credits=0.5" in repr_str
    assert "run_time=1.0" in repr_str
    assert "url='http://test.url'" in repr_str
    assert "details={'test': 'details'}" in repr_str
    assert "usage={'tokens': 100}" in repr_str

    # Most importantly, verify that 'status' is complete (not 'tatus')
    assert "status=" in repr_str  # Should find complete field name


@pytest.mark.parametrize(
    "function,supplier,model,expected_name",
    [
        (Function.TRANSLATION, None, None, "translation"),
        (Function.TEXT_GENERATION, Supplier.AIXPLAIN, None, "text-generation-aixplain"),
        (Function.TEXT_GENERATION, Supplier.OPENAI, None, "text-generation-openai"),
        (
            Function.TEXT_GENERATION,
            Supplier.AIXPLAIN,
            Model(id="123", name="Test Model"),
            "text-generation-aixplain-test_model",
        ),
    ],
)
def test_set_tool_name(function, supplier, model, expected_name):
    from aixplain.modules.agent.tool.model_tool import set_tool_name

    name = set_tool_name(function, supplier, model)
    assert name == expected_name


def test_create_agent_with_duplicate_tool_names(mocker):
    from aixplain.factories import AgentFactory
    from aixplain.modules import Model
    from aixplain.modules.agent.tool.model_tool import ModelTool

    mocker.patch(
        "aixplain.factories.model_factory.ModelFactory.get",
        return_value=Model(id="123", name="Test Model", function=Function.TEXT_GENERATION),
    )

    # Create a ModelTool with a specific name
    tool1 = ModelTool(model="123", name="Test Model")
    tool2 = ModelTool(model="123", name="Test Model")
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test Agent",
            description="Test Agent Description",
            tools=[tool1, tool2],
        )
    assert "Agent Creation Error - Duplicate tool names found: Test Model. Make sure all tool names are unique." in str(
        exc_info.value
    )


def test_agent_task_serialization():
    """Test AgentTask to_dict/from_dict round-trip serialization."""
    from aixplain.modules.agent.agent_task import AgentTask

    # Create test task
    task = AgentTask(
        name="Test Task",
        description="A test task for validation",
        expected_output="Expected output description",
        dependencies=["task1", "task2"],
    )

    # Test to_dict
    task_dict = task.to_dict()
    expected_keys = {"name", "description", "expectedOutput", "dependencies"}
    assert set(task_dict.keys()) == expected_keys
    assert task_dict["name"] == "Test Task"
    assert task_dict["description"] == "A test task for validation"
    assert task_dict["expectedOutput"] == "Expected output description"
    assert task_dict["dependencies"] == ["task1", "task2"]

    # Test from_dict
    reconstructed_task = AgentTask.from_dict(task_dict)

    # Verify round-trip
    assert task.name == reconstructed_task.name
    assert task.description == reconstructed_task.description
    assert task.expected_output == reconstructed_task.expected_output
    assert task.dependencies == reconstructed_task.dependencies


def test_agent_task_serialization_with_task_dependencies():
    """Test AgentTask serialization when dependencies are AgentTask objects."""
    from aixplain.modules.agent.agent_task import AgentTask

    # Create dependency tasks
    dep_task1 = AgentTask(
        name="Dependency Task 1",
        description="First dependency",
        expected_output="Dep output 1",
    )
    dep_task2 = AgentTask(
        name="Dependency Task 2",
        description="Second dependency",
        expected_output="Dep output 2",
    )

    # Create main task with AgentTask dependencies
    main_task = AgentTask(
        name="Main Task",
        description="Main task with AgentTask dependencies",
        expected_output="Main output",
        dependencies=[dep_task1, dep_task2, "string_dependency"],
    )

    # Test to_dict - should convert AgentTask dependencies to names
    task_dict = main_task.to_dict()
    assert task_dict["dependencies"] == [
        "Dependency Task 1",
        "Dependency Task 2",
        "string_dependency",
    ]

    # Test from_dict - dependencies will be strings
    reconstructed_task = AgentTask.from_dict(task_dict)
    assert reconstructed_task.dependencies == [
        "Dependency Task 1",
        "Dependency Task 2",
        "string_dependency",
    ]


def test_agent_serialization_completeness():
    """Test that Agent to_dict includes all necessary fields."""
    from aixplain.modules.agent.agent_task import AgentTask

    # Create test tasks
    task1 = AgentTask(name="Task 1", description="First task", expected_output="Output 1")
    task2 = AgentTask(
        name="Task 2",
        description="Second task",
        expected_output="Output 2",
        dependencies=["Task 1"],
    )

    # Create test agent with comprehensive data
    agent = Agent(
        id="test-agent-123",
        name="Test Agent",
        description="A test agent for validation",
        instructions="You are a helpful test agent",
        tools=[],  # Empty for simplicity
        llm_id="6646261c6eb563165658bbb1",
        api_key="test-api-key",
        supplier="aixplain",
        version="1.0.0",
        cost={"input": 0.01, "output": 0.02},
        status=AssetStatus.DRAFT,
        tasks=[task1, task2],
    )

    # Test to_dict includes all expected fields
    agent_dict = agent.to_dict()

    required_fields = {
        "llmId",
        "version",
        "instructions",
        "api_key",
        "supplier",
        "outputFormat",
        "status",
        "name",
        "description",
        "cost",
        "tools",
        "assets",
        "tasks",
        "expectedOutput",
        "id",
    }

    assert set(agent_dict.keys()) == required_fields

    # Verify field values
    assert agent_dict["id"] == "test-agent-123"
    assert agent_dict["name"] == "Test Agent"
    assert agent_dict["description"] == "A test agent for validation"
    assert agent_dict["instructions"] == "You are a helpful test agent"
    assert agent_dict["llmId"] == "6646261c6eb563165658bbb1"
    assert agent_dict["api_key"] == "test-api-key"
    assert agent_dict["supplier"] == "aixplain"
    assert agent_dict["version"] == "1.0.0"
    assert agent_dict["cost"] == {"input": 0.01, "output": 0.02}
    assert agent_dict["status"] == "draft"
    assert isinstance(agent_dict["assets"], list)
    assert isinstance(agent_dict["tasks"], list)
    assert len(agent_dict["tasks"]) == 2
    assert agent_dict["outputFormat"] == "text"
    assert agent_dict["expectedOutput"] is None

    # Verify task serialization
    task_dict = agent_dict["tasks"][0]
    assert task_dict["name"] == "Task 1"
    assert task_dict["description"] == "First task"
    assert task_dict["expectedOutput"] == "Output 1"


def test_agent_serialization_with_llm():
    """Test Agent to_dict when LLM instance is provided."""
    from unittest.mock import Mock

    # Mock LLM with parameters
    mock_llm = Mock()
    mock_llm.id = "custom-llm-id"
    mock_parameters = Mock()
    mock_parameters.to_list.return_value = [{"name": "temperature", "value": 0.7}]
    mock_llm.get_parameters.return_value = mock_parameters

    agent = Agent(
        id="test-agent",
        name="Test Agent",
        description="Test description",
        llm=mock_llm,
        llm_id="fallback-llm-id",
    )

    agent_dict = agent.to_dict()

    # Should use LLM instance ID instead of llm_id
    assert agent_dict["llmId"] == "custom-llm-id"

    # Should include LLM parameters in tools section
    assert len(agent_dict["tools"]) == 1
    llm_tool = agent_dict["tools"][0]
    assert llm_tool["type"] == "llm"
    assert llm_tool["description"] == "main"
    assert llm_tool["parameters"] == [{"name": "temperature", "value": 0.7}]


def test_agent_serialization_instructions_fallback():
    """Test Agent to_dict instructions field fallback behavior."""
    # Test with instructions provided
    agent_with_instructions = Agent(
        id="test1",
        name="Test Agent 1",
        description="Test description",
        instructions="Custom instructions",
    )

    dict1 = agent_with_instructions.to_dict()
    assert dict1["instructions"] == "Custom instructions"

    # Test without instructions (should fall back to description)
    agent_without_instructions = Agent(id="test2", name="Test Agent 2", description="Test description")

    dict2 = agent_without_instructions.to_dict()
    assert dict2["instructions"] == "Test description"


@pytest.mark.parametrize(
    "status_input,expected_output",
    [
        (AssetStatus.DRAFT, "draft"),
        (AssetStatus.ONBOARDED, "onboarded"),
        (AssetStatus.COMPLETED, "completed"),
    ],
)
def test_agent_serialization_status_enum(status_input, expected_output):
    """Test Agent to_dict properly serializes AssetStatus enum."""
    agent = Agent(
        id="test-agent",
        name="Test Agent",
        description="Test description",
        status=status_input,
    )

    agent_dict = agent.to_dict()
    assert agent_dict["status"] == expected_output


class _EOUser(BaseModel):
    id: int
    name: str = "alice"


def _schema_for(cls):
    return cls.model_json_schema() if hasattr(cls, "model_json_schema") else cls.schema()


def test_run_normalizes_expected_output_pydantic_class_in_execution_params():
    agent = Agent(
        id="eo-agent-norm-1",
        name="EO Agent",
        description="ensure expected_output is normalized",
        expected_output=_EOUser,
    )

    run_url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    agent.url = run_url

    with requests_mock.Mocker() as mock:
        headers = {"x-api-key": config.AIXPLAIN_API_KEY, "Content-Type": "application/json"}
        mock.post(run_url, headers=headers, json={"data": "dummy", "status": "IN_PROGRESS"})

        agent.run_async(data={"query": "hi"})

        sent = mock.last_request.json()
        assert "executionParams" in sent
        assert "expectedOutput" in sent["executionParams"]

        eo = sent["executionParams"]["expectedOutput"]
        assert isinstance(eo, str), "expectedOutput must be a JSON string"
        assert json.loads(eo) == _schema_for(_EOUser), "expectedOutput schema doesn't match model schema"


def test_run_normalizes_expected_output_tuple_to_list_in_execution_params():
    agent = Agent(
        id="eo-agent-norm-2",
        name="EO Agent 2",
        description="tuple normalization",
        expected_output=(1, 2, 3),
    )

    run_url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    agent.url = run_url

    with requests_mock.Mocker() as mock:
        headers = {"x-api-key": config.AIXPLAIN_API_KEY, "Content-Type": "application/json"}
        mock.post(run_url, headers=headers, json={"data": "dummy", "status": "IN_PROGRESS"})

        agent.run_async(data={"query": "hi"})

        sent = mock.last_request.json()
        assert "executionParams" in sent
        assert "expectedOutput" in sent["executionParams"]
        assert sent["executionParams"]["expectedOutput"] == "[1, 2, 3]", "tuple should normalize to JSON string"
