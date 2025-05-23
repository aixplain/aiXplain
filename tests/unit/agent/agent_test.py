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
from aixplain.modules.agent.tool.custom_python_code_tool import CustomPythonCodeTool
from aixplain.modules.agent.utils import process_variables
from urllib.parse import urljoin
from unittest.mock import patch
from aixplain.enums import Function, Supplier
from aixplain.modules.agent.agent_response import AgentResponse
from aixplain.modules.agent.agent_response_data import AgentResponseData


def test_fail_no_data_query():
    agent = Agent("123", "Test Agent(-)", "Sample Description", "Test Agent Role")
    with pytest.raises(Exception) as exc_info:
        agent.run_async()
    assert str(exc_info.value) == "Either 'data' or 'query' must be provided."


def test_fail_query_must_be_provided():
    agent = Agent("123", "Test Agent", "Sample Description", "Test Agent Role")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={})
    assert str(exc_info.value) == "When providing a dictionary, 'query' must be provided."


def test_fail_query_as_text_when_content_not_empty():
    agent = Agent("123", "Test Agent", "Sample Description", "Test Agent Role")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(
            data={"query": "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav"},
            content=[
                "https://aixplain-platform-assets.s3.amazonaws.com/samples/en/CPAC1x2.wav",
            ],
        )

    assert str(exc_info.value) == "When providing 'content', query must be text."


def test_fail_content_exceed_maximum():
    agent = Agent("123", "Test Agent", "Sample Description", "Test Agent Role")
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
    agent = Agent("123", "Test Agent", "Sample Description", "Test Agent Role")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input2": "Hello, how are you?"})
    assert str(exc_info.value) == "Key 'input2' not found in query."


def test_success_query_content():
    agent = Agent("123", "Test Agent(-)", "Sample Description", "Test Agent Role")
    with requests_mock.Mocker() as mock:
        url = agent.url
        headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}
        ref_response = {"data": "Hello, how are you?", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(data={"query": "Translate the text: {{input1}}"}, content={"input1": "Hello, how are you?"})
    assert isinstance(response, AgentResponse)
    assert response["status"] == ref_response["status"]
    assert isinstance(response.data, AgentResponseData)
    assert response["url"] == ref_response["data"]


def test_invalid_pipelinetool(mocker):
    mocker.patch(
        "aixplain.factories.model_factory.ModelFactory.get",
        return_value=Model(id="6646261c6eb563165658bbb1", name="Test Model", function=Function.TEXT_GENERATION),
    )
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(
            name="Test",
            description="Test Description",
            instructions="Test Role",
            tools=[PipelineTool(pipeline="309851793", description="Test")],
            llm_id="6646261c6eb563165658bbb1",
        )
    assert str(exc_info.value) == "Pipeline Tool Unavailable. Make sure Pipeline '309851793' exists or you have access to it."


def test_invalid_llm_id():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="Test", description="", instructions="", tools=[], llm_id="123")
    assert str(exc_info.value) == "Large Language Model with ID '123' not found."


def test_invalid_agent_name():
    with pytest.raises(Exception) as exc_info:
        AgentFactory.create(name="[Test]", description="", instructions="", tools=[], llm_id="6646261c6eb563165658bbb1")
    assert str(exc_info.value) == (
        "Agent Creation Error: Agent name contains invalid characters. "
        "Only alphanumeric characters, spaces, hyphens, and brackets are allowed."
    )


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_create_agent(mock_model_factory_get):
    from aixplain.enums import Supplier, Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1", name="Test LLM", description="Test LLM Description", function=Function.TEXT_GENERATION
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
            headers = {"x-api-key": config.TEAM_API_KEY, "Content-Type": "application/json"}

            ref_response = {
                "id": "123",
                "name": "Test Agent(-)",
                "description": "Test Agent Description",
                "role": "Test Agent Role",
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
                        "utilityCode": "def main(query: str) -> str:\n    return 'Hello, how are you?'",
                        "description": "Test Tool",
                        "name": "Test Tool",
                    },
                    {
                        "type": "utility",
                        "utility": "custom_python_code",
                        "description": "A Python shell. Use this to execute python commands. Input should be a valid python command.",
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
                name="Test Agent(-)",
                description="Test Agent Description",
                instructions="Test Agent Role",
                llm_id="6646261c6eb563165658bbb1",
                tools=[
                    AgentFactory.create_model_tool(
                        supplier=Supplier.OPENAI, function="text-generation", description="Test Tool"
                    ),
                    AgentFactory.create_custom_python_code_tool(
                        code="def main(query: str) -> str:\n    return 'Hello, how are you?'",
                        description="Test Tool",
                        name="Test Tool",
                    ),
                    AgentFactory.create_python_interpreter_tool(),
                ],
            )

    assert agent.name == ref_response["name"]
    assert agent.description == ref_response["description"]
    assert agent.instructions == ref_response["role"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]
    assert agent.tools[0].description == ref_response["assets"][0]["description"]
    assert isinstance(agent.tools[0], ModelTool)
    assert agent.tools[1].description == ref_response["assets"][1]["description"]
    assert isinstance(agent.tools[1], CustomPythonCodeTool)
    assert agent.tools[2].description == ref_response["assets"][2]["description"]
    assert isinstance(agent.tools[2], PythonInterpreterTool)
    assert agent.status == AssetStatus.DRAFT


def test_to_dict():
    agent = Agent(
        id="",
        name="Test Agent(-)",
        description="Test Agent Description",
        instructions="Test Agent Role",
        llm_id="6646261c6eb563165658bbb1",
        tools=[AgentFactory.create_model_tool(function="text-generation")],
        api_key="test_api_key",
        status=AssetStatus.DRAFT,
    )

    agent_json = agent.to_dict()
    assert agent_json["id"] == ""
    assert agent_json["name"] == "Test Agent(-)"
    assert agent_json["description"] == "Test Agent Description"
    assert agent_json["role"] == "Test Agent Role"
    assert agent_json["llmId"] == "6646261c6eb563165658bbb1"
    assert agent_json["assets"][0]["function"] == "text-generation"
    assert agent_json["assets"][0]["type"] == "model"
    assert agent_json["status"] == "draft"


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_update_success(mock_model_factory_get):
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1", name="Test LLM", description="Test LLM Description", function=Function.TEXT_GENERATION
    )
    mock_model_factory_get.return_value = mock_model

    agent = Agent(
        id="123",
        name="Test Agent(-)",
        description="Test Agent Description",
        instructions="Test Agent Role",
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
            "role": "Test Agent Role",
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
    assert agent.instructions == ref_response["role"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]


@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_save_success(mock_model_factory_get):
    from aixplain.enums import Function

    # Mock the model factory response
    mock_model = Model(
        id="6646261c6eb563165658bbb1", name="Test LLM", description="Test LLM Description", function=Function.TEXT_GENERATION
    )
    mock_model_factory_get.return_value = mock_model

    agent = Agent(
        id="123",
        name="Test Agent(-)",
        description="Test Agent Description",
        instructions="Test Agent Role",
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
            "role": "Test Agent Role",
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
    assert agent.instructions == ref_response["role"]
    assert agent.llm_id == ref_response["llmId"]
    assert agent.tools[0].function.value == ref_response["assets"][0]["function"]


def test_run_success():
    agent = Agent("123", "Test Agent(-)", "Sample Description", "Test Agent Role")
    url = urljoin(config.BACKEND_URL, f"sdk/agents/{agent.id}/run")
    agent.url = url
    with requests_mock.Mocker() as mock:
        headers = {"x-api-key": config.AIXPLAIN_API_KEY, "Content-Type": "application/json"}

        ref_response = {"data": "www.aixplain.com", "status": "IN_PROGRESS"}
        mock.post(url, headers=headers, json=ref_response)

        response = agent.run_async(
            data={"query": "Hello, how are you?"}, max_iterations=10, output_format=OutputFormat.MARKDOWN
        )
    assert isinstance(response, AgentResponse)
    assert response["status"] == "IN_PROGRESS"
    assert response["url"] == ref_response["data"]


def test_run_variable_error():
    agent = Agent("123", "Test Agent", "Agent description", "Translate the input data into {target_language}")
    with pytest.raises(Exception) as exc_info:
        agent.run_async(data={"query": "Hello, how are you?"}, output_format=OutputFormat.MARKDOWN)
    assert str(exc_info.value) == (
        "Variable 'target_language' not found in data or parameters. "
        "This variable is required by the agent according to its description "
        "('Translate the input data into {target_language}')."
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
    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Description",
        instructions="Test Agent Role",
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
    agent = Agent(id="123", name="Test Agent", description="Test Description", instructions="Test Agent Role", tools=[tool])

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
            code="def main(query: str) -> str:\n    return 'Hello'", description="Test Tool", name="Test Tool"
        ),
    ]

    agent = Agent(
        id="123",
        name="Test Agent",
        description="Test Description",
        instructions="Test Agent Role",
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
        id="123", name="Test Agent", description="Test Description", instructions="Test Agent Role", api_key=custom_api_key
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
    assert task.dependencies is None

    task_dict = task.to_dict()
    assert task_dict["name"] == "Test Task"
    assert task_dict["description"] == "Test Description"
    assert task_dict["expectedOutput"] == "Test Output"
    assert task_dict["dependencies"] is None


def test_agent_response():
    from aixplain.modules.agent.agent_response import AgentResponse, AgentResponseData

    response = AgentResponse(
        data=AgentResponseData(
            input="input", output="output", intermediate_steps=[], execution_stats={}, session_id="session_id"
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


def test_custom_python_code_tool_initialization(mocker):
    """Test basic initialization of CustomPythonCodeTool"""
    mocker.patch(
        "aixplain.modules.model.utils.parse_code_decorated",
        return_value=("def main(query: str) -> str:\n    return 'Hello'", [], "Test description", "HelloWorld"),
    )

    code = "def main(query: str) -> str:\n    return 'Hello'"
    description = "Test description"
    tool = CustomPythonCodeTool(code=code, description=description, name="HelloWorld")

    assert tool.code == code
    assert tool.description == description
    assert tool.name == "HelloWorld"


def test_custom_python_code_tool_to_dict(mocker):
    """Test the to_dict method of CustomPythonCodeTool"""
    mocker.patch(
        "aixplain.modules.model.utils.parse_code_decorated",
        return_value=("def main(query: str) -> str:\n    return 'Hello'", [], "Test description", "HelloWorld"),
    )
    code = "def main(query: str) -> str:\n    return 'Hello'"
    description = "Test description"
    tool = CustomPythonCodeTool(code=code, description=description)

    tool_dict = tool.to_dict()
    assert tool_dict["type"] == "utility"
    assert tool_dict["utility"] == "custom_python_code"
    assert tool_dict["utilityCode"] == code
    assert tool_dict["description"] == description


def test_custom_python_code_tool_validation():
    """Test validation of CustomPythonCodeTool"""
    with patch(
        "aixplain.modules.model.utils.parse_code",
        return_value=(
            "def main(query: str) -> str:\n    return 'Hello'",  # code
            [],  # inputs
            "Parsed description",  # description
            "test_name",  # name
        ),
    ):
        code = "def main(query: str) -> str:\n    return 'Hello'"
        tool = CustomPythonCodeTool(code=code)
        tool.validate()
        assert tool.code == code
        assert tool.description == "Parsed description"
        assert tool.name == "test_name"


def test_custom_python_code_tool_validation_missing_description(mocker):
    """Test validation fails when description is missing"""
    mocker.patch(
        "aixplain.modules.model.utils.parse_code_decorated",
        return_value=("def main(query: str) -> str:\n    return 'Hello'", [], "", "HelloWorld"),
    )

    code = "def main(query: str) -> str:\n    return 'Hello'"
    with pytest.raises(AssertionError) as exc_info:
        CustomPythonCodeTool(code=code)
    assert str(exc_info.value) == "Custom Python Code Tool Error: Tool description is required"


def test_custom_python_code_tool_validation_missing_code():
    """Test validation fails when code is missing"""
    with patch(
        "aixplain.modules.model.utils.parse_code",
        return_value=("", [], "Parsed description", "test_name"),  # code  # inputs  # description  # name
    ):
        with pytest.raises(AssertionError) as exc_info:
            CustomPythonCodeTool(code="", description="Test description")
        assert str(exc_info.value) == "Custom Python Code Tool Error: Code is required"



@patch("aixplain.factories.model_factory.ModelFactory.get")
def test_create_agent_with_model_instance(mock_model_factory_get):
    from aixplain.enums import Supplier, Function
    from aixplain.modules.model.model_parameters import ModelParameters

    # Create model parameters
    model_params = {"temperature": {"required": True}, "max_tokens": {"required": False}}

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
    text_gen_params = {"temperature": {"required": True}, "max_tokens": {"required": False}}

    classification_params = {"threshold": {"required": True}, "labels": {"required": True}}

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
                function=Function.TEXT_GENERATION, supplier=supplier_input, description="Test Tool"
            )
        assert supplier_input in str(exc_info.value)
    else:
        # Create ModelTool with supplier as text
        tool = AgentFactory.create_model_tool(
            function=Function.TEXT_GENERATION, supplier=supplier_input, description="Test Tool"
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
    response = AgentResponse(status=ResponseStatus.SUCCESS, data=AgentResponseData(input="test input"), completed=True)
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
        AgentFactory.create(name="Test Agent", description="Test Agent Description", tools=[tool1, tool2])
    assert "Agent Creation Error - Duplicate tool names found: Test Model. Make sure all tool names are unique." in str(
        exc_info.value
    )
