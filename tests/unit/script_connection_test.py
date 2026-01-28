import pytest
import requests_mock
from urllib.parse import urljoin
from unittest.mock import patch

from aixplain.factories import AgentFactory, ModelFactory
from aixplain.modules.model.connection import ConnectionTool
from aixplain.utils import config


# Python sandbox integration ID
PYTHON_SANDBOX_ID = "688779d8bfb8e46c273982ca"


def _setup_python_sandbox_mocks(mock, connection_id="693026cc427d05e696f3c7db"):
    """Helper function to set up all the mocks needed for Python sandbox integration."""
    # Mock the Python sandbox integration model fetch
    url = urljoin(config.BACKEND_URL, f"sdk/models/{PYTHON_SANDBOX_ID}")
    python_sandbox_headers = {
        "Authorization": f"Token {config.TEAM_API_KEY}",
        "Content-Type": "application/json",
    }
    python_sandbox_response = {
        "id": PYTHON_SANDBOX_ID,
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
            {
                "name": "auth_schemes",
                "code": '["NO_AUTH"]'
            },
            {
                "name": "NO_AUTH-inputs",
                "code": '[{"name":"code","displayName":"Python Code","type":"string","description":"","required":true, "subtype": "file", "fileConfiguration": { "limit": 1, "extensions": ["py"] }}, {"name":"function_name","displayName":"Main Function Name","type":"string","description":"","required":true}]'
            }
        ],
    }
    mock.get(url, headers=python_sandbox_headers, json=python_sandbox_response)

    # Mock the POST request to create the connection (when connect() calls run())
    run_url = f"{config.MODELS_RUN_URL}/{PYTHON_SANDBOX_ID}".replace("api/v1/execute", "api/v2/execute")
    run_headers = {
        "x-api-key": config.TEAM_API_KEY,
        "Content-Type": "application/json",
    }
    run_response = {
        "status": "SUCCESS",
        "completed": True,
        "data": {"id": connection_id},
    }
    mock.post(run_url, headers=run_headers, json=run_response)

    # Mock the GET request to fetch the created connection
    connection_url = urljoin(config.BACKEND_URL, f"sdk/models/{connection_id}")
    connection_response = {
        "id": connection_id,
        "name": "Test Connection Tool",
        "description": "Test Connection Tool description",
        "function": {"id": "utilities"},
        "functionType": "connection",
        "supplier": "aixplain",
        "version": {"id": "pythonscript"},
        "status": "onboarded",
        "pricing": {"currency": "USD", "value": 0.0},
        "params": [],
    }
    mock.get(connection_url, headers=python_sandbox_headers, json=connection_response)

    # Mock the POST request to list actions (when ConnectionTool.__init__ calls _get_actions())
    list_actions_url = f"{config.MODELS_RUN_URL}/{connection_id}".replace("api/v1/execute", "api/v2/execute")
    list_actions_headers = {
        "x-api-key": config.TEAM_API_KEY,
        "Content-Type": "application/json",
    }
    list_actions_response = {
        "status": "SUCCESS",
        "completed": True,
        "data": [
            {
                "name": "test_function",
                "displayName": "test_function",
                "description": "Test function"
            }
        ],
    }
    mock.post(list_actions_url, headers=list_actions_headers, json=list_actions_response)

    return connection_id


def test_create_custom_python_code_tool_with_string_code():
    """Test creating a connection tool with string code."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        code = "def test_function(input_string: str) -> str:\n    return 'Hello, world!'\n"
        tool = ModelFactory.create_script_connection_tool(
            name="Test Tool",
            code=code,
            description="Test description"
        )
        
        assert isinstance(tool, ConnectionTool)
        assert tool.id == connection_id
        assert tool.name == "Test Connection Tool"
        assert tool.description == "Test Connection Tool description"
        assert len(tool.actions) == 1
        assert tool.actions[0].name == "test_function"


def test_create_custom_python_code_tool_with_callable():
    """Test creating a connection tool with a callable function."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        def my_function(x: int) -> int:
            """A test function."""
            return x * 2
        
        tool = ModelFactory.create_script_connection_tool(
            name="Test Tool",
            code=my_function,
            description="Test description"
        )
        
        assert isinstance(tool, ConnectionTool)
        assert tool.id == connection_id


def test_create_custom_python_code_tool_no_functions():
    """Test that creating a tool with code containing no functions raises an error."""
    with requests_mock.Mocker() as mock:
        _setup_python_sandbox_mocks(mock)
        
        code = "x = 5\ny = 10\nprint(x + y)"
        
        with pytest.raises(Exception) as exc_info:
            ModelFactory.create_script_connection_tool(
                name="Test Tool",
                code=code,
                description="Test description"
            )
        
        assert "No functions found in the code" in str(exc_info.value)


def test_create_custom_python_code_tool_multiple_functions_no_specification():
    """Test that creating a tool with multiple functions without specifying function_name raises an error."""
    with requests_mock.Mocker() as mock:
        _setup_python_sandbox_mocks(mock)
        
        code = """def function1(x: int) -> int:
    return x * 2

def function2(y: str) -> str:
    return y.upper()
"""
        
        with pytest.raises(Exception) as exc_info:
            AgentFactory.create_custom_python_code_tool(
                name="Test Tool",
                code=code,
                description="Test description"
            )
        
        assert "Multiple functions found in the code" in str(exc_info.value)
        assert "function1" in str(exc_info.value)
        assert "function2" in str(exc_info.value)


def test_create_custom_python_code_tool_multiple_functions_with_specification():
    """Test creating a tool with multiple functions when function_name is specified."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        code = """def function1(x: int) -> int:
    return x * 2

def function2(y: str) -> str:
    return y.upper()
"""
        
        tool = AgentFactory.create_custom_python_code_tool(
            name="Test Tool",
            code=code,
            description="Test description",
            function_name="function1"
        )
        
        assert isinstance(tool, ConnectionTool)
        assert tool.id == connection_id


def test_create_custom_python_code_tool_invalid_function_name():
    """Test that specifying an invalid function_name raises an error."""
    with requests_mock.Mocker() as mock:
        _setup_python_sandbox_mocks(mock)
        
        code = "def valid_function(x: int) -> int:\n    return x * 2\n"
        
        with pytest.raises(Exception) as exc_info:
            AgentFactory.create_custom_python_code_tool(
                name="Test Tool",
                code=code,
                description="Test description",
                function_name="invalid_function"
            )
        
        assert "Function name invalid_function not found in the code" in str(exc_info.value)
        assert "valid_function" in str(exc_info.value)


def test_create_custom_python_code_tool_single_function_auto_detection():
    """Test that a single function is automatically detected."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        code = "def my_single_function(input_string: str) -> str:\n    return 'Hello!'\n"
        
        tool = AgentFactory.create_custom_python_code_tool(
            name="Test Tool",
            code=code,
            description="Test description"
        )
        
        assert isinstance(tool, ConnectionTool)
        assert tool.id == connection_id


def test_create_custom_python_code_tool_with_different_function_signatures():
    """Test creating tools with different function signatures."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        # Test with no parameters
        code1 = "def no_params() -> str:\n    return 'test'\n"
        tool1 = AgentFactory.create_custom_python_code_tool(
            name="Tool 1",
            code=code1,
            description="No params"
        )
        assert isinstance(tool1, ConnectionTool)
        
        # Test with multiple parameters
        code2 = "def multi_params(a: int, b: str, c: float) -> dict:\n    return {'a': a, 'b': b, 'c': c}\n"
        tool2 = AgentFactory.create_custom_python_code_tool(
            name="Tool 2",
            code=code2,
            description="Multiple params"
        )
        assert isinstance(tool2, ConnectionTool)
        
        # Test with optional parameters
        code3 = "def optional_params(x: int, y: int = 10) -> int:\n    return x + y\n"
        tool3 = AgentFactory.create_custom_python_code_tool(
            name="Tool 3",
            code=code3,
            description="Optional params"
        )
        assert isinstance(tool3, ConnectionTool)


def test_create_custom_python_code_tool_actions_retrieval():
    """Test that actions are properly retrieved from the connection tool."""
    with requests_mock.Mocker() as mock:
        connection_id = "test_connection_123"
        
        # Set up all mocks with custom connection_id
        url = urljoin(config.BACKEND_URL, f"sdk/models/{PYTHON_SANDBOX_ID}")
        python_sandbox_headers = {
            "Authorization": f"Token {config.TEAM_API_KEY}",
            "Content-Type": "application/json",
        }
        python_sandbox_response = {
            "id": PYTHON_SANDBOX_ID,
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
                {
                    "name": "auth_schemes",
                    "code": '["NO_AUTH"]'
                },
                {
                    "name": "NO_AUTH-inputs",
                    "code": '[{"name":"code","displayName":"Python Code","type":"string","description":"","required":true, "subtype": "file", "fileConfiguration": { "limit": 1, "extensions": ["py"] }}, {"name":"function_name","displayName":"Main Function Name","type":"string","description":"","required":true}]'
                }
            ],
        }
        mock.get(url, headers=python_sandbox_headers, json=python_sandbox_response)

        # Mock the POST request to create the connection
        run_url = f"{config.MODELS_RUN_URL}/{PYTHON_SANDBOX_ID}".replace("api/v1/execute", "api/v2/execute")
        run_headers = {
            "x-api-key": config.TEAM_API_KEY,
            "Content-Type": "application/json",
        }
        run_response = {
            "status": "SUCCESS",
            "completed": True,
            "data": {"id": connection_id},
        }
        mock.post(run_url, headers=run_headers, json=run_response)

        # Mock the GET request to fetch the created connection
        connection_url = urljoin(config.BACKEND_URL, f"sdk/models/{connection_id}")
        connection_response = {
            "id": connection_id,
            "name": "Test Connection Tool",
            "description": "Test Connection Tool description",
            "function": {"id": "utilities"},
            "functionType": "connection",
            "supplier": "aixplain",
            "version": {"id": "pythonscript"},
            "status": "onboarded",
            "pricing": {"currency": "USD", "value": 0.0},
            "params": [],
        }
        mock.get(connection_url, headers=python_sandbox_headers, json=connection_response)

        # Mock the POST request to list actions with multiple actions
        list_actions_url = f"{config.MODELS_RUN_URL}/{connection_id}".replace("api/v1/execute", "api/v2/execute")
        list_actions_headers = {
            "x-api-key": config.TEAM_API_KEY,
            "Content-Type": "application/json",
        }
        list_actions_response = {
            "status": "SUCCESS",
            "completed": True,
            "data": [
                {
                    "name": "action1",
                    "displayName": "Action 1",
                    "description": "First action"
                },
                {
                    "name": "action2",
                    "displayName": "Action 2",
                    "description": "Second action"
                }
            ],
        }
        mock.post(list_actions_url, headers=list_actions_headers, json=list_actions_response)
        
        code = "def action1(x: int) -> int:\n    return x * 2\n"
        tool = AgentFactory.create_custom_python_code_tool(
            name="Test Tool",
            code=code,
            description="Test description"
        )
        
        assert len(tool.actions) == 2
        assert tool.actions[0].name == "Action 1"
        assert tool.actions[0].code == "action1"
        assert tool.actions[0].description == "First action"
        assert tool.actions[1].name == "Action 2"
        assert tool.actions[1].code == "action2"
        assert tool.actions[1].description == "Second action"


def test_create_custom_python_code_tool_with_complex_code():
    """Test creating a tool with more complex Python code."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        code = """import json
from typing import Dict, List

def process_data(data: Dict[str, List[int]]) -> str:
    \"\"\"Process a dictionary of lists and return JSON string.\"\"\"
    result = {}
    for key, values in data.items():
        result[key] = sum(values)
    return json.dumps(result)
"""
        
        tool = AgentFactory.create_custom_python_code_tool(
            name="Complex Tool",
            code=code,
            description="Processes complex data structures"
        )
        
        assert isinstance(tool, ConnectionTool)
        assert tool.id == connection_id


def test_create_custom_python_code_tool_minimal_parameters():
    """Test creating a tool with minimal parameters (only code)."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        code = "def simple() -> str:\n    return 'simple'\n"
        
        tool = AgentFactory.create_custom_python_code_tool(
            code=code,
            name="Minimal Tool"
        )
        
        assert isinstance(tool, ConnectionTool)
        assert tool.id == connection_id


def test_create_custom_python_code_tool_with_nested_functions():
    """Test creating a tool with nested functions (should only detect top-level functions)."""
    with requests_mock.Mocker() as mock:
        connection_id = _setup_python_sandbox_mocks(mock)
        
        code = """def outer_function(x: int) -> int:
    def inner_function(y: int) -> int:
        return y * 2
    return inner_function(x)
"""
        
        tool = AgentFactory.create_custom_python_code_tool(
            name="Nested Tool",
            code=code,
            description="Has nested functions"
        )
        
        assert isinstance(tool, ConnectionTool)
        assert tool.id == connection_id
        # Should only detect outer_function, not inner_function
        # The function_name should be "outer_function" (auto-detected)


def test_create_custom_python_code_tool_with_class():
    """Test that code with classes but no functions raises an error."""
    with requests_mock.Mocker() as mock:
        _setup_python_sandbox_mocks(mock)
        
        code = """class MyClass:
    def __init__(self):
        self.value = 10
    
    def method(self):
        return self.value
"""
        
        with pytest.raises(Exception) as exc_info:
            AgentFactory.create_custom_python_code_tool(
                name="Test Tool",
                code=code,
                description="Test description"
            )
        
        # Methods inside classes are not detected as top-level functions
        assert "No functions found in the code" in str(exc_info.value)


def test_create_custom_python_code_tool_error_handling():
    """Test error handling when connection creation fails."""
    with requests_mock.Mocker() as mock:
        # Set up mocks but make the connection creation fail
        url = urljoin(config.BACKEND_URL, f"sdk/models/{PYTHON_SANDBOX_ID}")
        python_sandbox_headers = {
            "Authorization": f"Token {config.TEAM_API_KEY}",
            "Content-Type": "application/json",
        }
        python_sandbox_response = {
            "id": PYTHON_SANDBOX_ID,
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
                {
                    "name": "auth_schemes",
                    "code": '["NO_AUTH"]'
                }
            ],
        }
        mock.get(url, headers=python_sandbox_headers, json=python_sandbox_response)
        
        # Make the connection creation fail
        run_url = f"{config.MODELS_RUN_URL}/{PYTHON_SANDBOX_ID}".replace("api/v1/execute", "api/v2/execute")
        run_headers = {
            "x-api-key": config.TEAM_API_KEY,
            "Content-Type": "application/json",
        }
        mock.post(run_url, headers=run_headers, json={"status": "FAILED", "error_message": "Connection failed"}, status_code=500)
        
        code = "def test_function(x: int) -> int:\n    return x * 2\n"
        
        with pytest.raises(Exception) as exc_info:
            AgentFactory.create_custom_python_code_tool(
                name="Test Tool",
                code=code,
                description="Test description"
            )
        
        assert "Failed to create" in str(exc_info.value)

