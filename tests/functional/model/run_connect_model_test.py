import os
from aixplain.enums import ResponseStatus
from aixplain.factories import ModelFactory
from aixplain.modules.model.integration import Integration, AuthenticationSchema
from aixplain.modules.model.connection import ConnectionTool
from aixplain.modules.model.mcp_connection import MCPConnection


def test_run_connect_model():
    # get slack connector
    connector = ModelFactory.get("67eff5c0e05614297caeef98")

    assert isinstance(connector, Integration)
    assert connector.id == "67eff5c0e05614297caeef98"
    assert connector.name == "Slack"

    response = connector.connect(
        authentication_schema=AuthenticationSchema.BEARER,
        token=os.getenv("SLACK_TOKEN"),
    )
    assert response.status == ResponseStatus.SUCCESS
    assert "id" in response.data
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


def test_run_mcp_connect_model():
    # get slack connector
    connector = ModelFactory.get("686eb9cd26480723d0634d3e")

    assert isinstance(connector, Integration)
    assert connector.id == "686eb9cd26480723d0634d3e"

    assert connector.name == ""

    url = "https://mcp.zapier.com/api/mcp/s/OTJiMjVlYjEtMGE4YS00OTVjLWIwMGYtZDJjOGVkNTc4NjFkOjI0MTNjNzg5LWZlNGMtNDZmNC05MDhmLWM0MGRlNDU4ZmU1NA=="
    response = connector.connect(data=url)
    assert response.status == ResponseStatus.SUCCESS
    assert "id" in response.data
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
