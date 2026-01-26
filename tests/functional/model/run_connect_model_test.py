import os
from aixplain.enums import ResponseStatus
from aixplain.factories import ModelFactory
from aixplain.modules.model.integration import Integration, AuthenticationSchema
from aixplain.modules.model.connection import ConnectionTool
from aixplain.modules.model.mcp_connection import MCPConnection


def test_run_connect_model():
    # get slack connector
    connector = ModelFactory.get("686432941223092cb4294d3f")

    assert isinstance(connector, Integration)
    assert connector.id == "686432941223092cb4294d3f"
    assert connector.name == "Slack"

    response = connector.connect(
        authentication_schema=AuthenticationSchema.BEARER_TOKEN,
        data={"token": os.getenv("SLACK_TOKEN")},
    )
    assert response.status == ResponseStatus.SUCCESS, (
        f"Connection failed: {response.error_message if hasattr(response, 'error_message') else 'Unknown error'}. Response data: {response.data}"
    )
    assert "id" in response.data, f"Response data does not contain 'id'. Response data: {response.data}"
    connection_id = response.data["id"]
    # get slack connection
    connection = ModelFactory.get(connection_id)
    assert isinstance(connection, ConnectionTool)
    assert connection.id == connection_id
    assert connection.actions is not None

    action = [action for action in connection.actions if action.code == "SLACK_CHAT_POST_MESSAGE"]
    assert len(action) > 0
    action = action[0]
    response = connection.run(action, {"text": "This is a test!", "channel": "C084G435LR5"})
    assert response.status == ResponseStatus.SUCCESS
    connection.delete()


def test_run_mcp_connect_model():
    # get slack connector
    connector = ModelFactory.get("686eb9cd26480723d0634d3e")

    assert isinstance(connector, Integration)
    assert connector.id == "686eb9cd26480723d0634d3e"

    assert connector.name == "MCP Server"

    url = "https://mcp.zapier.com/api/mcp/s/OTJiMjVlYjEtMGE4YS00OTVjLWIwMGYtZDJjOGVkNTc4NjFkOjI0MTNjNzg5LWZlNGMtNDZmNC05MDhmLWM0MGRlNDU4ZmU1NA=="
    response = connector.connect(data=url)
    assert response.status == ResponseStatus.SUCCESS, (
        f"MCP connection failed: {response.error_message if hasattr(response, 'error_message') else 'Unknown error'}. Response data: {response.data}"
    )
    assert "id" in response.data, f"Response data does not contain 'id'. Response data: {response.data}"
    connection_id = response.data["id"]
    # get slack connection
    connection = ModelFactory.get(connection_id)
    assert isinstance(connection, MCPConnection)
    assert connection.id == connection_id
    assert connection.actions is not None

    action = [action for action in connection.actions if action.code == "SLACK_CHAT_POST_MESSAGE"]
    assert len(action) > 0
    action = action[0]
    response = connection.run(action, {"text": "This is a test!", "channel": "C084G435LR5"})
    assert response.status == ResponseStatus.SUCCESS
    connection.delete()


def test_create_script_connection_tool():
    # get python sandbox integration
    connector = ModelFactory.get("688779d8bfb8e46c273982ca")

    assert isinstance(connector, Integration)
    assert connector.id == "688779d8bfb8e46c273982ca"
    assert connector.name == "Python Sandbox"

    response = connector.connect(
        authentication_schema=AuthenticationSchema.NO_AUTH,
        data={
            "code": "def test_function():\n    return 'Hello, world!'",
            "function_name": "test_function",
        },
    )
    assert response.status == ResponseStatus.SUCCESS
    assert "id" in response.data
    connection_id = response.data["id"]
    # get slack connection
    connection = ModelFactory.get(connection_id)
    assert isinstance(connection, ConnectionTool)
    assert connection.id == connection_id
    assert connection.actions is not None

    action = [action for action in connection.actions if action.code == "test_function"]
    assert len(action) > 0
    action = action[0]
    response = connection.run(inputs={}, action=action)
    assert response.status == ResponseStatus.SUCCESS
    assert response.data["data"] == "Hello, world!"
    connection.delete()


def test_run_script_connection_tool():
    def test_function():
        return "Hello, world!"

    tool = ModelFactory.create_script_connection_tool(
        name="My Test Tool", code=test_function, function_name="test_function"
    )
    response = tool.run(inputs={}, action=tool.actions[0])
    assert response.status == ResponseStatus.SUCCESS
    assert response.data["data"] == "Hello, world!"
    tool.delete()


def test_run_script_connection_tool_with_complex_inputs():
    def test_all_types(s: str, i: int, f: float, lst: list, d: dict):
        return f"String: {s}\nInt: {i}\nFloat: {f}\nList: {lst}\nDict: {d}"

    tool = ModelFactory.create_script_connection_tool(
        name="My Test Tool",
        code=test_all_types,
    )
    response = tool.run(
        inputs={"s": "test", "i": 1, "f": 1.0, "lst": [1, 2, 3], "d": {"a": 1, "b": 2}},
        action=tool.actions[0],
    )
    assert response.status == ResponseStatus.SUCCESS
    assert response.data["data"] == "String: test\nInt: 1\nFloat: 1\nList: [1, 2, 3]\nDict: {'a': 1, 'b': 2}"
    tool.delete()
