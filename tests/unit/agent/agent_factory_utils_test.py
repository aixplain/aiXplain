import pytest
from unittest.mock import Mock, patch, MagicMock
from aixplain.factories.agent_factory.utils import build_tool, build_agent
from aixplain.enums import Function, Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.pipeline import Pipeline
from aixplain.modules.agent.tool.model_tool import ModelTool
from aixplain.modules.agent.tool.pipeline_tool import PipelineTool
from aixplain.modules.agent.tool.python_interpreter_tool import PythonInterpreterTool
from aixplain.modules.agent.tool.sql_tool import SQLTool
from aixplain.modules.agent import Agent
from aixplain.modules.agent.agent_task import WorkflowTask
from aixplain.factories import ModelFactory, PipelineFactory
import os


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    mock = MagicMock()
    mock.id = "test_model"
    mock.function = Function.SPEECH_RECOGNITION
    mock.supplier = Supplier.AIXPLAIN
    mock.description = "Test model"
    mock.model_params = None
    mock.to_dict.return_value = {
        "id": "test_model",
        "function": "speech-recognition",
        "supplier": "aixplain",
        "description": "Test model",
    }
    return mock


@pytest.fixture(autouse=True)
def mock_model_factory(mock_model):
    """Mock the ModelFactory.get method for all tests."""
    with patch.object(ModelFactory, "get", return_value=mock_model) as mock:
        yield mock


@pytest.fixture
def mock_tools():
    """Create mock tools for testing."""
    return [Mock(spec=ModelTool), Mock(spec=PipelineTool)]


@pytest.mark.parametrize(
    "tool_dict,expected_error",
    [
        pytest.param(
            {
                "type": "model",
                "supplier": "aixplain",
                "version": "1.0",
                "assetId": "test_model",
                "description": "Test model",
                "function": "invalid_function",
            },
            "Function invalid_function is not a valid function",
            id="invalid_function",
        ),
        pytest.param(
            {"type": "invalid_type", "description": "Test tool"},
            "Agent Creation Error: Tool type not supported",
            id="invalid_tool_type",
        ),
    ],
)
def test_build_tool_error_cases(tool_dict, expected_error):
    """Test various error cases when building tools."""
    with pytest.raises(Exception) as exc_info:
        build_tool(tool_dict)
    assert expected_error in str(exc_info.value)


@pytest.mark.parametrize(
    "tool_dict,expected_type,expected_attrs",
    [
        pytest.param(
            {
                "type": "model",
                "supplier": "aixplain",
                "version": "1.0",
                "assetId": "test_model",
                "description": "Test model",
                "function": "speech-recognition",
            },
            ModelTool,
            {
                "function": Function.SPEECH_RECOGNITION,
                "supplier": Supplier.AIXPLAIN,
                "version": "1.0",
                "model": "test_model",
                "description": "Test model",
            },
            id="model_tool_basic",
        ),
        pytest.param(
            {
                "type": "model",
                "supplier": "aixplain",
                "version": "1.0",
                "assetId": "test_model",
                "description": "Test model",
                "function": "speech-recognition",
                "parameters": [{"name": "language", "value": "en"}],
            },
            ModelTool,
            {
                "function": Function.SPEECH_RECOGNITION,
                "supplier": Supplier.AIXPLAIN,
                "version": "1.0",
                "model": "test_model",
                "description": "Test model",
                "parameters": [{"name": "language", "value": "en"}],
            },
            id="model_tool_with_params",
        ),
        pytest.param(
            {
                "type": "pipeline",
                "description": "Test pipeline",
                "assetId": "test_pipeline",
            },
            PipelineTool,
            {"description": "Test pipeline", "pipeline": "test_pipeline"},
            id="pipeline_tool",
        ),
        pytest.param(
            {"type": "utility", "description": "Test utility"},
            PythonInterpreterTool,
            {},
            id="python_interpreter_tool",
        ),
        pytest.param(
            {
                "type": "sql",
                "name": "Test SQL",
                "description": "Test SQL",
                "parameters": [
                    {"name": "database", "value": "s3://test_db.db"},
                    {"name": "schema", "value": "public"},
                    {"name": "tables", "value": "table1,table2"},
                    {"name": "enable_commit", "value": True},
                ],
            },
            SQLTool,
            {
                "name": "Test SQL",
                "description": "Test SQL",
                "database": "s3://test_db.db",
                "schema": "public",
                "tables": ["table1", "table2"],
                "enable_commit": True,
            },
            id="sql_tool_boolean_commit",
        ),
        pytest.param(
            {
                "type": "sql",
                "name": "Test SQL",
                "description": "Test SQL with string enable_commit",
                "parameters": [
                    {"name": "database", "value": "s3://test_db.db"},
                    {"name": "schema", "value": "public"},
                    {"name": "tables", "value": "table1"},
                    {"name": "enable_commit", "value": True},
                ],
            },
            SQLTool,
            {
                "name": "Test SQL",
                "description": "Test SQL with string enable_commit",
                "database": "s3://test_db.db",
                "schema": "public",
                "tables": ["table1"],
                "enable_commit": True,
            },
            id="sql_tool_string_commit",
        ),
    ],
)
def test_build_tool_success_cases(tool_dict, expected_type, expected_attrs, mock_model, mocker):
    """Test successful tool creation with various configurations."""
    mocker.patch.object(ModelFactory, "get", return_value=mock_model)
    mocker.patch(
        "aixplain.modules.model.utils.parse_code_decorated",
        return_value=("print('Hello World')", [], "Test description", "test_name"),
    )
    mocker.patch(
        "os.path.exists",
        lambda path: True if path == "test_db.db" else os.path.exists(path),
    )
    mocker.patch(
        "aixplain.factories.file_factory.FileFactory.upload",
        return_value="s3://mocked-file-path/test_db.db",
    )
    if tool_dict["type"] == "pipeline":
        mocker.patch.object(
            PipelineFactory,
            "get",
            return_value=Pipeline(
                id=tool_dict["assetId"],
                description=tool_dict["description"],
                name="Pipeline",
                api_key="",
            ),
        )

    tool = build_tool(tool_dict)
    assert isinstance(tool, expected_type)

    for attr, value in expected_attrs.items():
        if attr == "model":
            assert tool.model == mock_model
        elif attr == "database" and value == "test_db.db":
            assert getattr(tool, attr) == "s3://mocked-file-path/test_db.db"
        else:
            assert getattr(tool, attr) == value


@pytest.mark.parametrize(
    "payload,expected_attrs",
    [
        pytest.param(
            {
                "id": "test_agent",
                "name": "Test Agent",
                "description": "Test Description",
                "instructions": "Test Instructions",
                "teamId": "test_team",
                "version": "1.0",
                "cost": 10.0,
                "status": "onboarded",
                "assets": [],
                "tasks": [
                    {
                        "name": "Task 1",
                        "description": "Task 1 Description",
                        "expectedOutput": "Expected Output 1",
                        "dependencies": ["dep1", "dep2"],
                    }
                ],
            },
            {
                "id": "test_agent",
                "name": "Test Agent",
                "description": "Test Description",
                "instructions": "Test Instructions",
                "supplier": "test_team",
                "version": "1.0",
                "cost": 10.0,
                "status": AssetStatus.ONBOARDED,
                "tasks": [
                    {
                        "name": "Task 1",
                        "description": "Task 1 Description",
                        "expected_output": "Expected Output 1",
                        "dependencies": ["dep1", "dep2"],
                    }
                ],
            },
            id="agent_with_tasks",
        ),
        pytest.param(
            {
                "id": "test_agent",
                "name": "Test Agent",
                "status": "onboarded",
                "assets": [
                    {
                        "type": "model",
                        "supplier": "aixplain",
                        "version": "1.0",
                        "assetId": "test_model",
                        "description": "Test model",
                        "function": "speech-recognition",
                    },
                    {
                        "type": "pipeline",
                        "description": "Test pipeline",
                        "assetId": "test_pipeline",
                    },
                ],
            },
            {
                "id": "test_agent",
                "name": "Test Agent",
                "status": AssetStatus.ONBOARDED,
                "tools": [{"type": ModelTool}, {"type": PipelineTool}],
            },
            id="agent_with_tools",
        ),
    ],
)
def test_build_agent_success_cases(payload, expected_attrs, mock_tools, mocker):
    """Test successful agent creation with various configurations."""
    mocker.patch.object(
        PipelineFactory,
        "get",
        return_value=Pipeline(id="test_pipeline", description="Test pipeline", name="Pipeline", api_key=""),
    )

    agent = build_agent(payload, tools=mock_tools if "assets" not in payload else None)
    assert isinstance(agent, Agent)

    for attr, value in expected_attrs.items():
        if attr == "tasks":
            assert len(agent.workflow_tasks) == len(value)
            for task, expected_task in zip(agent.workflow_tasks, value):
                assert isinstance(task, WorkflowTask)
                for task_attr, task_value in expected_task.items():
                    assert getattr(task, task_attr) == task_value
        elif attr == "tools":
            assert len(agent.tools) == len(value)
            for tool, expected_tool in zip(agent.tools, value):
                assert isinstance(tool, expected_tool["type"])
        else:
            assert getattr(agent, attr) == value


@pytest.mark.parametrize(
    "payload,expected_error",
    [
        pytest.param(
            {
                "id": "test_agent",
                "name": "Test Agent",
                "status": "onboarded",
                "assets": [
                    {
                        "type": "invalid_type",
                        "description": "Test tool",
                        "assetId": "invalid_asset",
                    }
                ],
            },
            "Agent Creation Error: Tool type not supported",
            id="invalid_tool_type",
        ),
        pytest.param(
            {
                "id": "test_agent",
                "name": "Test Agent",
                "status": "onboarded",
                "assets": [
                    {
                        "type": "model",
                        "supplier": "aixplain",
                        "version": "1.0",
                        "assetId": "test_model",
                        "description": "Test model",
                        "function": "invalid_function",
                    }
                ],
            },
            "Function invalid_function is not a valid function",
            id="invalid_function",
        ),
    ],
)
def test_build_agent_with_invalid_tool(payload, expected_error):
    """Test that building an agent with an invalid tool handles the error gracefully."""
    with patch("logging.warning") as mock_warning:
        agent = build_agent(payload)
        assert isinstance(agent, Agent)
        assert len(agent.tools) == 0
        mock_warning.assert_called_once()
        assert expected_error in mock_warning.call_args[0][0]
