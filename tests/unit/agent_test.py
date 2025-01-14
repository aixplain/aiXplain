import pytest
import requests_mock
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules import Agent
from aixplain.modules.agent import OutputFormat
from aixplain.utils import config
from aixplain.factories import AgentFactory
from aixplain.modules.agent import PipelineTool, ModelTool, PythonInterpreterTool, CustomPythonCodeTool
from aixplain.modules.agent.utils import process_variables
from urllib.parse import urljoin
from unittest.mock import patch
from aixplain.enums.function import Function


def test_fail_no_data_query():
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_must_be_provided():
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={})
    assert str(exc_info.value) == "When providing a dictionary, 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=["https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"],
        )
    assert str(exc_info.value) == "When providing 'content', query must be text."


def test_fail_content_exceed_maximum():
    agent = Agent("123", "Test Agent", "Sample Description")
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
    agent = Agent("123", "Test Agent", "Sample Description")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input2": "Hello, how are you?"})
    assert str(exc_info.value) == "Key 'input2' not found in query."


def test_success_query_content():
    agent = Agent("123", "Test Agent", "Sample Description")
    with requests_mock.Mocker() as mock:
        url = agent.url
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"data": "Hello, how are you?", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input1": "Hello, how are you?"})
    assert response["status"] == ref_response["status"]
    assert response["url"] == ref_response["data"]


def test_invalid_pipelinetool():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test",
            description="Test Description",
            tools=[PipelineTool(pipeline="309851793", description="Test")],
            llm_id="6646261c6eb563165658bbb1",
        )
    assert str(exc_info.value) == "Pipeline Tool Unavailable. Make sure Pipeline '309851793' exists or you have access to it."


def test_invalid_modeltool():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="Test", tools=[ModelTool(model="309851793")], llm_id="6646261c6eb563165658bbb1")
    assert str(exc_info.value) == "Model Tool Unavailable. Make sure Model '309851793' exists or you have access to it."


def test_invalid_llm_id():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="Test", description="", tools=[], llm_id="123")
    assert str(exc_info.value) == "Large Language Model with ID '123' not found."


def test_invalid_agent_name():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="[Test]", description="", tools=[], llm_id="6646261c6eb563165658bbb1")
    assert str(exc_info.value) == "Agent Creation Error: Agent name must not contain special characters."


def test_create_agent():
    from aixplain.enums import Supplier

    with requests_mock.Mocker() as mock:
        with patch(
            "aixplain.modules.model.utils.parse_code",
            return_value=(
                "utility_model_test",
                [],
                "utility_model_test",
            ),
        ):
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
                        "supplier": "openai",
                        "version": "1.0",
                        "assetId": "6646261c6eb563165658bbb1",
                        "function": "text-generation",
                        "description": "Test Tool",
                    },
                    {
                        "type": "utility",
                        "utility": "custom_python_code",
                        "description": "",
                    },
                    {
                        "type": "utility",
                        "utility": "custom_python_code",
                        "utilityCode": "def main(query: str) -> str:\n    return 'Hello, how are you?'",
                        "description": "Test Tool",
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

            agent = AgentFactory.create(
                name="Test Agent",
                description="Test Agent Description",
                llm_id="6646261c6eb563165658bbb1",
                tools=[
                    AgentFactory.create_model_tool(
                        supplier=Supplier.OPENAI, function="text-generation", description="Test Tool"
                    ),
                    AgentFactory.create_custom_python_code_tool(
                        code="def main(query: str) -> str:\n    return 'Hello, how are you?'", description="Test Tool"
                    ),
                    AgentFactory.create_python_interpreter_tool(),
                ],
            )

    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]
    assert agent.tools[0].description == ref_response["assets"][0]["description"]
    assert isinstance(agent.tools[0], ModelTool)
    assert agent.tools[1].description == ref_response["assets"][1]["description"]
    assert isinstance(agent.tools[1], PythonInterpreterTool)
    assert agent.tools[2].description == ref_response["assets"][2]["description"]
    assert agent.tools[2].code == ref_response["assets"][2]["utilityCode"]
    assert isinstance(agent.tools[2], CustomPythonCodeTool)
    assert agent.status == AssetStatus.DRAFT


def test_to_dict():
    agent = Agent(
        id="",
        name="Test Agent",
        description="Test Agent Description",
        llm_id="6646261c6eb563165658bbb1",
        tools=[AgentFactory.create_model_tool(function="text-generation")],
        api_key="test_api_key",
        status=AssetStatus.DRAFT,
    )

    agent_json = agent.to_dict()
    assert agent_json["id"] == ""
    assert agent_json["name"] == "Test Agent"
    assert agent_json["description"] == "Test Agent Description"
    assert agent_json["llmId"] == "6646261c6eb563165658bbb1"
    assert agent_json["assets"][0]["function"] == "text-generation"
    assert agent_json["assets"][0]["type"] == "model"
    assert agent_json["status"] == "draft"


def test_update_success():
    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Agent Description",
        llm_id="6646261c6eb563165658bbb1",
        tools=[AgentFactory.create_model_tool(function="text-generation")],
    )

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {
            "id": "123",
            "name": "Test Agent",
            "description": "Test Agent Description",
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
            match="update\(\) is deprecated and will be removed in a future version. Please use save\(\) instead.",
        ):
            agent.update()

    assert agent.id == ref_response["id"]
    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]


def test_save_success():
    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Agent Description",
        llm_id="6646261c6eb563165658bbb1",
        tools=[AgentFactory.create_model_tool(function="text-generation")],
    )

    with requests_mock.Mocker() as mock:
        url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}")
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {
            "id": "123",
            "name": "Test Agent",
            "description": "Test Agent Description",
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
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]


def test_run_success():
    agent = Agent("123", "Test Agent", "Sample Description")
    url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    agent.url = url
    with requests_mock.Mocker() as mock:
        headers = {"x-api-key": config.AIXPLAIN_API_KEY, "Content-Type": "application/json"}

        ref_response = {"data": "www.aixplain.com", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(
            data={"query": "Hello, how are you?"}, max_iterations=10, output_format=OutputFormat.MARKDOWN
        )
    assert response["status"] == "IN_PROGRESS"
    assert response["url"] == ref_response["data"]


def test_run_variable_error():
    agent = Agent("123", "Test Agent", "Translate the input data into {target_language}")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={"query": "Hello, how are you?"}, output_format=OutputFormat.MARKDOWN)
    assert (
        str(exc_info.value)
        == "Variable 'target_language' not found in data or parameters. This variable is required by the agent according to its description ('Translate the input data into {target_language}')."
    )


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
        AgentFactory.create(name="Test", tools=[ModelTool(function=Function.UTILITIES)], llm_id="6646261c6eb563165658bbb1")
    assert str(exc_info.value) == "Agent Creation Error: Utility function must be used with an associated model."


def test_agent_api_key_propagation():
    """Test that the api_key is properly propagated to tools when creating an agent"""
    custom_api_key = "custom_test_key"
    tool = AgentFactory.create_model_tool(function="text-generation")
    agent = Agent(id="123", name="Test Agent", description="Test Description", tools=[tool], api_key=custom_api_key)

    # Check that the agent has the correct api_key
    assert agent.api_key == custom_api_key
    # Check that the tool received the agent's api_key
    assert agent.tools[0].api_key == custom_api_key


def test_agent_default_api_key():
    """Test that the default api_key is used when none is provided"""
    tool = AgentFactory.create_model_tool(function="text-generation")
    agent = Agent(id="123", name="Test Agent", description="Test Description", tools=[tool])

    # Check that the agent has the default api_key
    assert agent.api_key == config.TEAM_API_KEY
    # Check that the tool has the default api_key
    assert agent.tools[0].api_key == config.TEAM_API_KEY


def test_agent_multiple_tools_api_key():
    """Test that api_key is properly propagated to multiple tools"""
    custom_api_key = "custom_test_key"
    tools = [
        AgentFactory.create_model_tool(function="text-generation"),
        AgentFactory.create_python_interpreter_tool(),
        AgentFactory.create_custom_python_code_tool(
            code="def main(query: str) -> str:\n    return 'Hello'", description="Test Tool"
        ),
    ]

    agent = Agent(id="123", name="Test Agent", description="Test Description", tools=tools, api_key=custom_api_key)

    # Check that all tools received the agent's api_key
    for tool in agent.tools:
        assert tool.api_key == custom_api_key


def test_agent_api_key_in_requests():
    """Test that the api_key is properly used in API requests"""
    custom_api_key = "custom_test_key"
    agent = Agent(id="123", name="Test Agent", description="Test Description", api_key=custom_api_key)

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
